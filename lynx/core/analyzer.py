"""Main analysis orchestrator — ties all modules together.

Supports cache-first loading: when a previous analysis exists on disk for a
ticker, it is returned directly without any network calls.  Pass refresh=True
to force a fresh download.
"""

from __future__ import annotations

import dataclasses
from typing import Optional

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
    """

    # 1. Resolve identifier
    console.print(f"[bold cyan]Resolving identifier:[/] {identifier}")
    ticker, isin = resolve_identifier(identifier)
    console.print(f"[green]Ticker:[/] {ticker}" + (f"  [dim]ISIN: {isin}[/dim]" if isin else ""))

    # 2. Check cache (unless refresh requested)
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
                cached = None
            else:
                if isin and report.profile.isin is None:
                    report.profile.isin = isin
                console.print(
                    f"[green]{report.profile.name}[/] — "
                    f"{report.profile.sector or 'N/A'} / {report.profile.industry or 'N/A'}"
                    f"  [bold][{_tier_color(report.profile.tier)}]{report.profile.tier.value}[/]"
                )
                console.print("[dim]Use --refresh to force fresh data download.[/]")
                return report

    # 3. Fresh fetch from network
    if refresh:
        console.print("[yellow]Refreshing data from network...[/]")

    console.print("[cyan]Fetching company profile...[/]")
    profile = fetch_company_profile(ticker)
    info = fetch_info(ticker)
    profile.isin = isin

    tier = classify_tier(profile.market_cap)
    profile.tier = tier
    console.print(
        f"[green]{profile.name}[/] — {profile.sector or 'N/A'} / {profile.industry or 'N/A'}"
        f"  [bold][{_tier_color(tier)}]{tier.value}[/]"
    )

    console.print("[cyan]Fetching financial statements...[/]")
    statements = fetch_financial_statements(ticker)
    console.print(f"[green]Retrieved {len(statements)} annual periods[/]")

    console.print("[cyan]Calculating metrics...[/]")
    valuation = calc_valuation(info, statements, tier)
    profitability = calc_profitability(info, statements, tier)
    solvency = calc_solvency(info, statements, tier)
    growth = calc_growth(statements, tier)
    efficiency = calc_efficiency(info, statements, tier)
    moat = calc_moat(profitability, growth, solvency, statements, info, tier)
    intrinsic_value = calc_intrinsic_value(info, statements, growth, solvency, tier)

    filings = []
    if download_reports:
        console.print("[cyan]Fetching SEC filings...[/]")
        filings = fetch_sec_filings(ticker)
        console.print(f"[green]Found {len(filings)} filings[/]")
        if filings:
            console.print(f"[cyan]Downloading top {max_filings} filings...[/]")
            download_top_filings(ticker, filings, max_count=max_filings)

    news = []
    if download_news:
        console.print("[cyan]Fetching news...[/]")
        news = fetch_all_news(ticker, profile.name)
        console.print(f"[green]Found {len(news)} articles[/]")

    report = AnalysisReport(
        profile=profile,
        valuation=valuation,
        profitability=profitability,
        solvency=solvency,
        growth=growth,
        efficiency=efficiency,
        moat=moat,
        intrinsic_value=intrinsic_value,
        financials=statements,
        filings=filings,
        news=news,
    )

    console.print("[cyan]Saving analysis...[/]")
    path = save_analysis_report(ticker, _report_to_dict(report))
    console.print(f"[bold green]Analysis saved to:[/] {path}")

    return report


# ---------------------------------------------------------------------------
# Serialization: report <-> dict
# ---------------------------------------------------------------------------

def _report_to_dict(report: AnalysisReport) -> dict:
    """Convert AnalysisReport to a JSON-serializable dict."""
    def _dc(obj):
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

    return AnalysisReport(
        profile=profile,
        valuation=_build_dc(ValuationMetrics, d.get("valuation", {})),
        profitability=_build_dc(ProfitabilityMetrics, d.get("profitability", {})),
        solvency=_build_dc(SolvencyMetrics, d.get("solvency", {})),
        growth=_build_dc(GrowthMetrics, d.get("growth", {})),
        efficiency=_build_dc(EfficiencyMetrics, d.get("efficiency", {})),
        moat=_build_dc(MoatIndicators, d.get("moat", {})),
        intrinsic_value=_build_dc(IntrinsicValue, d.get("intrinsic_value", {})),
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
