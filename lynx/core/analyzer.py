"""Main analysis orchestrator — ties all modules together.

Supports cache-first loading: when a previous analysis exists on disk for a
ticker, it is returned directly without any network calls.  Pass refresh=True
to force a fresh download.

Progressive analysis: ``run_progressive_analysis`` accepts an *on_progress*
callback that is invoked after each stage completes so that UIs can render
sections as data becomes available instead of waiting for the full pipeline.
"""

from __future__ import annotations

import dataclasses
from concurrent.futures import ThreadPoolExecutor
from typing import Callable, Optional

from rich.console import Console

from lynx.core.fetcher import fetch_company_profile, fetch_financial_statements, fetch_info
from lynx.core.news import fetch_all_news
from lynx.core.reports import download_top_filings, fetch_sec_filings
from lynx.core.storage import (
    get_cache_age_hours,
    has_cache,
    load_cached_report,
    save_analysis_report,
)
from lynx.core.ticker import resolve_identifier
from lynx.metrics.calculator import (
    calc_efficiency,
    calc_growth,
    calc_intrinsic_value,
    calc_moat,
    calc_profitability,
    calc_solvency,
    calc_valuation,
)
from lynx.models import (
    AnalysisReport,
    CompanyProfile,
    CompanyTier,
    EfficiencyMetrics,
    Filing,
    FinancialStatement,
    GrowthMetrics,
    IntrinsicValue,
    MoatIndicators,
    NewsArticle,
    ProfitabilityMetrics,
    SolvencyMetrics,
    ValuationMetrics,
    classify_tier,
)

console = Console(stderr=True)

# Type alias for progress callbacks.
# The callback receives (stage_name, partial_report).
ProgressCallback = Callable[[str, AnalysisReport], None]


def run_full_analysis(
    identifier: str,
    download_reports: bool = True,
    download_news: bool = True,
    max_filings: int = 10,
    verbose: bool = False,
    refresh: bool = False,
) -> AnalysisReport:
    """Run a complete fundamental analysis for a given ticker or ISIN.

    By default, returns cached data if available.  Set refresh=True to force
    a fresh download from all sources.

    This is the synchronous, non-progressive entry point — it blocks until
    the full report is ready.  For progressive (section-by-section) display,
    use ``run_progressive_analysis`` instead.
    """
    return run_progressive_analysis(
        identifier=identifier,
        download_reports=download_reports,
        download_news=download_news,
        max_filings=max_filings,
        verbose=verbose,
        refresh=refresh,
        on_progress=None,
    )


def run_progressive_analysis(
    identifier: str,
    download_reports: bool = True,
    download_news: bool = True,
    max_filings: int = 10,
    verbose: bool = False,
    refresh: bool = False,
    on_progress: Optional[ProgressCallback] = None,
) -> AnalysisReport:
    """Run a progressive fundamental analysis, notifying after each stage.

    Stages emitted via *on_progress* (in order):
        profile, financials, valuation, profitability, solvency, growth,
        moat, intrinsic_value, filings, news, conclusion, complete.

    If *on_progress* is ``None`` the function behaves identically to
    ``run_full_analysis``.
    """

    def _notify(stage: str, report: AnalysisReport) -> None:
        if on_progress is not None:
            on_progress(stage, report)

    # ── 1. Resolve identifier ────────────────────────────────────────
    console.print(f"[bold cyan]Resolving identifier:[/] {identifier}")
    ticker, isin = resolve_identifier(identifier)
    console.print(
        f"[green]Ticker:[/] {ticker}"
        + (f"  [dim]ISIN: {isin}[/dim]" if isin else "")
    )

    # ── 2. Check cache (unless refresh requested) ────────────────────
    if not refresh and has_cache(ticker):
        age = get_cache_age_hours(ticker)
        age_str = f"{age:.1f}h ago" if age is not None else "unknown age"
        console.print(f"[bold green]Using cached data[/] [dim](fetched {age_str})[/]")
        cached = load_cached_report(ticker)
        if cached:
            try:
                report = _dict_to_report(cached)
            except Exception as exc:
                console.print(
                    f"[yellow]Cached data is corrupt ({exc}), re-fetching...[/]"
                )
            else:
                if isin and report.profile.isin is None:
                    report.profile.isin = isin
                console.print(
                    f"[green]{report.profile.name}[/] — "
                    f"{report.profile.sector or 'N/A'} / "
                    f"{report.profile.industry or 'N/A'}"
                    f"  [bold][{_tier_color(report.profile.tier)}]"
                    f"{report.profile.tier.value}[/]"
                )
                console.print("[dim]Use --refresh to force fresh data download.[/]")
                _notify("complete", report)
                return report

    # ── 3. Fresh fetch — profile ─────────────────────────────────────
    if refresh:
        console.print("[yellow]Refreshing data from network...[/]")

    console.print("[cyan]Fetching company profile...[/]")
    info = fetch_info(ticker)
    profile = fetch_company_profile(ticker, info=info)
    profile.isin = isin

    # Try to retrieve ISIN from yfinance if not already known
    if not profile.isin:
        try:
            import yfinance as yf
            fetched_isin = yf.Ticker(ticker).isin
            if fetched_isin and fetched_isin != "-":
                profile.isin = fetched_isin
                console.print(f"[green]ISIN:[/] {fetched_isin}")
        except Exception:
            pass

    tier = classify_tier(profile.market_cap)
    profile.tier = tier
    console.print(
        f"[green]{profile.name}[/] — "
        f"{profile.sector or 'N/A'} / {profile.industry or 'N/A'}"
        f"  [bold][{_tier_color(tier)}]{tier.value}[/]"
    )

    report = AnalysisReport(profile=profile)
    _notify("profile", report)

    # ── 4. Financial statements ──────────────────────────────────────
    console.print("[cyan]Fetching financial statements...[/]")
    statements = fetch_financial_statements(ticker)
    console.print(f"[green]Retrieved {len(statements)} annual periods[/]")

    report.financials = statements
    _notify("financials", report)

    # ── 5. Metric calculations (fast, CPU-bound) ─────────────────────
    console.print("[cyan]Calculating metrics...[/]")

    report.valuation = calc_valuation(info, statements, tier)
    _notify("valuation", report)

    report.profitability = calc_profitability(info, statements, tier)
    _notify("profitability", report)

    report.solvency = calc_solvency(info, statements, tier)
    _notify("solvency", report)

    report.growth = calc_growth(statements, tier)
    _notify("growth", report)

    report.efficiency = calc_efficiency(info, statements, tier)

    report.moat = calc_moat(
        report.profitability, report.growth, report.solvency,
        statements, info, tier,
    )
    _notify("moat", report)

    report.intrinsic_value = calc_intrinsic_value(
        info, statements, report.growth, report.solvency, tier,
    )
    _notify("intrinsic_value", report)

    # ── 6. Filings + news (I/O-bound — fetched in parallel) ─────────
    #
    # Rich Console is not thread-safe, so we avoid printing from worker
    # threads.  Progress messages are printed from the main thread
    # before/after each future completes.  Exceptions in either future
    # are caught so a network error doesn't abort the whole analysis.
    _ticker, _max = ticker, max_filings  # bind for lambda clarity

    with ThreadPoolExecutor(max_workers=2) as pool:
        filings_future = None
        news_future = None

        if download_reports:
            console.print("[cyan]Fetching SEC filings...[/]")
            filings_future = pool.submit(
                lambda: fetch_sec_filings(_ticker),
            )

        if download_news:
            console.print("[cyan]Fetching news...[/]")
            news_future = pool.submit(
                lambda: fetch_all_news(_ticker, profile.name),
            )

        if filings_future is not None:
            try:
                fl = filings_future.result()
                console.print(f"[green]Found {len(fl)} filings[/]")
                if fl:
                    console.print(
                        f"[cyan]Downloading top {_max} filings...[/]"
                    )
                    download_top_filings(_ticker, fl, max_count=_max)
                report.filings = fl
                _notify("filings", report)
            except Exception as exc:
                console.print(
                    f"[yellow]Filings fetch failed: {exc}[/]"
                )

        if news_future is not None:
            try:
                nw = news_future.result()
                console.print(f"[green]Found {len(nw)} articles[/]")
                report.news = nw
                _notify("news", report)
            except Exception as exc:
                console.print(
                    f"[yellow]News fetch failed: {exc}[/]"
                )

    # ── 7. Conclusion ────────────────────────────────────────────────
    _notify("conclusion", report)

    # ── 8. Save ──────────────────────────────────────────────────────
    console.print("[cyan]Saving analysis...[/]")
    path = save_analysis_report(ticker, _report_to_dict(report))
    console.print(f"[bold green]Analysis saved to:[/] {path}")
    _notify("complete", report)

    return report


# ---------------------------------------------------------------------------
# Serialization: report <-> dict
# ---------------------------------------------------------------------------

def _report_to_dict(report: AnalysisReport) -> dict:
    """Convert AnalysisReport to a JSON-serializable dict.

    Handles *None* metric sections gracefully — they are stored as ``None``
    in the resulting dict so that ``_dict_to_report`` can reconstruct them.
    """
    def _dc(obj):
        if obj is None:
            return None
        if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
            return {k: _dc(v) for k, v in dataclasses.asdict(obj).items()}
        if isinstance(obj, list):
            return [_dc(i) for i in obj]
        return obj
    return _dc(report)


def _dict_to_report(d: dict) -> AnalysisReport:
    """Reconstruct an AnalysisReport from a cached JSON dict."""
    profile = _build_dc(CompanyProfile, d.get("profile", {}))
    # Restore the tier enum
    tier_raw = d.get("profile", {}).get("tier", "")
    profile.tier = _parse_tier(tier_raw)

    def _maybe(cls, key):
        """Build a dataclass from *d[key]*, returning None when absent."""
        raw = d.get(key)
        if raw is None:
            return None
        return _build_dc(cls, raw)

    return AnalysisReport(
        profile=profile,
        valuation=_maybe(ValuationMetrics, "valuation"),
        profitability=_maybe(ProfitabilityMetrics, "profitability"),
        solvency=_maybe(SolvencyMetrics, "solvency"),
        growth=_maybe(GrowthMetrics, "growth"),
        efficiency=_maybe(EfficiencyMetrics, "efficiency"),
        moat=_maybe(MoatIndicators, "moat"),
        intrinsic_value=_maybe(IntrinsicValue, "intrinsic_value"),
        financials=[_build_dc(FinancialStatement, s) for s in d.get("financials", [])],
        filings=[_build_dc(Filing, f) for f in d.get("filings", [])],
        news=[_build_dc(NewsArticle, n) for n in d.get("news", [])],
        fetched_at=d.get("fetched_at", ""),
    )


def _build_dc(cls, data: dict):
    """Build a dataclass from a dict, ignoring unknown keys."""
    import dataclasses as dc
    field_names = {f.name for f in dc.fields(cls)}
    filtered = {k: v for k, v in data.items() if k in field_names}
    return cls(**filtered)


def _parse_tier(raw) -> CompanyTier:
    """Parse a tier value from JSON (could be the enum value string)."""
    if isinstance(raw, CompanyTier):
        return raw
    raw_str = str(raw)
    for t in CompanyTier:
        if t.value == raw_str or t.name == raw_str:
            return t
    return CompanyTier.NANO


def _tier_color(tier) -> str:
    return {
        CompanyTier.MEGA: "bold green",
        CompanyTier.LARGE: "green",
        CompanyTier.MID: "cyan",
        CompanyTier.SMALL: "yellow",
        CompanyTier.MICRO: "#ff8800",
        CompanyTier.NANO: "bold red",
    }.get(tier, "white")
