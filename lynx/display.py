"""Rich console display for analysis reports — tier-aware.

Critical metrics are highlighted with a marker.  Irrelevant metrics are
dimmed or hidden entirely.  Assessment thresholds shift by company tier.
"""

from __future__ import annotations

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from lynx.metrics.relevance import get_relevance
from lynx.models import AnalysisReport, CompanyTier, Relevance

console = Console()

# Relevance display styles
_STYLE = {
    Relevance.CRITICAL: ("bold", "[bold cyan]*[/] "),     # star marker
    Relevance.RELEVANT: ("", "  "),
    Relevance.CONTEXTUAL: ("dim", "  "),
    Relevance.IRRELEVANT: ("dim strike", "  "),
}


def _tier_color(tier: CompanyTier) -> str:
    return {
        CompanyTier.MEGA: "bold green",
        CompanyTier.LARGE: "green",
        CompanyTier.MID: "cyan",
        CompanyTier.SMALL: "yellow",
        CompanyTier.MICRO: "#ff8800",
        CompanyTier.NANO: "bold red",
    }.get(tier, "white")


def _tier_label(tier: CompanyTier) -> str:
    return {
        CompanyTier.MEGA: "MEGA CAP — Full Traditional Analysis",
        CompanyTier.LARGE: "LARGE CAP — Full Traditional Analysis",
        CompanyTier.MID: "MID CAP — Blended Analysis (traditional + growth focus)",
        CompanyTier.SMALL: "SMALL CAP — Balance Sheet & Growth Focus",
        CompanyTier.MICRO: "MICRO CAP — Survival & Asset-Based Analysis",
        CompanyTier.NANO: "NANO CAP — Speculative / Asset-Based Only",
    }.get(tier, "UNKNOWN")


# ---- Formatters ----

def _isna(val) -> bool:
    """Check if a value is None or NaN."""
    if val is None:
        return True
    try:
        import math
        return math.isnan(val)
    except (TypeError, ValueError):
        return False

def fmt_pct(val, digits: int = 2) -> str:
    if _isna(val):
        return "[dim]N/A[/]"
    return f"{val * 100:.{digits}f}%"

def fmt_num(val, digits: int = 2) -> str:
    if _isna(val):
        return "[dim]N/A[/]"
    return f"{val:,.{digits}f}"

def fmt_money(val) -> str:
    if _isna(val):
        return "[dim]N/A[/]"
    if abs(val) >= 1_000_000_000_000:
        return f"${val / 1_000_000_000_000:,.2f}T"
    if abs(val) >= 1_000_000_000:
        return f"${val / 1_000_000_000:,.2f}B"
    if abs(val) >= 1_000_000:
        return f"${val / 1_000_000:,.2f}M"
    return f"${val:,.0f}"

def fmt_score(val) -> str:
    if val is None:
        return "[dim]N/A[/]"
    if val >= 70:
        return f"[bold green]{val:.1f}/100[/]"
    if val >= 45:
        return f"[bold yellow]{val:.1f}/100[/]"
    if val >= 20:
        return f"[bold #ff8800]{val:.1f}/100[/]"
    return f"[bold red]{val:.1f}/100[/]"

def _mos_color(val) -> str:
    if val is None:
        return "[dim]N/A[/]"
    pct = val * 100
    if pct > 25:
        return f"[bold green]{pct:.1f}% (Undervalued)[/]"
    if pct > 0:
        return f"[yellow]{pct:.1f}% (Slight Undervalue)[/]"
    return f"[bold red]{pct:.1f}% (Overvalued)[/]"


# ---- Metric row helper ----

def _add_metric_row(
    table: Table,
    label: str,
    value: str,
    assessment: str,
    relevance: Relevance,
    *,
    has_assessment_col: bool = True,
):
    """Add a row styled by relevance.  IRRELEVANT rows are skipped."""
    if relevance == Relevance.IRRELEVANT:
        return
    style, prefix = _STYLE[relevance]
    styled_label = f"{prefix}[{style}]{label}[/]" if style else f"{prefix}{label}"
    styled_val = f"[{style}]{value}[/]" if style else value
    if has_assessment_col:
        styled_assess = f"[{style}]{assessment}[/]" if style else assessment
        table.add_row(styled_label, styled_val, styled_assess)
    else:
        table.add_row(styled_label, styled_val)


# ======================================================================
# Main entry point
# ======================================================================

def display_full_report(report: AnalysisReport) -> None:
    """Render the complete report at once (classic mode)."""
    _display_header(report)
    _display_profile(report)
    if report.valuation:
        _display_valuation(report)
    if report.profitability:
        _display_profitability(report)
    if report.solvency:
        _display_solvency(report)
    if report.growth:
        _display_growth(report)
    if report.moat:
        _display_moat(report)
    if report.intrinsic_value:
        _display_intrinsic_value(report)
    _display_financials(report)
    _display_filings(report)
    _display_news(report)
    if report.valuation:  # conclusion needs metrics
        _display_conclusion(report)
    console.print()


_progressive_stages_seen: set[str] = set()


def display_report_stage(stage: str, report: AnalysisReport) -> None:
    """Render a single stage of the report (progressive mode).

    Called by the progress callback so each section is displayed as soon
    as its data becomes available.  Callbacks are always dispatched to
    the main/UI thread in all modes, so concurrent access does not occur.
    """
    global _progressive_stages_seen

    if stage == "profile":
        _progressive_stages_seen = {"profile"}
        _display_header(report)
        _display_profile(report)
    elif stage == "financials":
        _progressive_stages_seen.add("financials")
        _display_financials(report)
    elif stage == "valuation":
        _progressive_stages_seen.add("valuation")
        _display_valuation(report)
    elif stage == "profitability":
        _progressive_stages_seen.add("profitability")
        _display_profitability(report)
    elif stage == "solvency":
        _progressive_stages_seen.add("solvency")
        _display_solvency(report)
    elif stage == "growth":
        _progressive_stages_seen.add("growth")
        _display_growth(report)
    elif stage == "moat":
        _progressive_stages_seen.add("moat")
        _display_moat(report)
    elif stage == "intrinsic_value":
        _progressive_stages_seen.add("intrinsic_value")
        _display_intrinsic_value(report)
    elif stage == "filings":
        _progressive_stages_seen.add("filings")
        _display_filings(report)
    elif stage == "news":
        _progressive_stages_seen.add("news")
        _display_news(report)
    elif stage == "conclusion":
        _progressive_stages_seen.add("conclusion")
        _display_conclusion(report)
    elif stage == "complete":
        if not _progressive_stages_seen:
            # Cached report — only "complete" was emitted; render everything.
            display_full_report(report)
        else:
            console.print()
        _progressive_stages_seen = set()


# ======================================================================
# Header & profile (extracted for progressive display)
# ======================================================================

def _display_header(report: AnalysisReport) -> None:
    """Render the report header and tier banner."""
    p = report.profile
    tier = p.tier

    header = Text()
    header.append(f"  {p.name}", style="bold white on blue")
    header.append(f"  ({p.ticker})", style="bold cyan on blue")
    if p.isin:
        header.append(f"  ISIN: {p.isin}", style="dim on blue")
    console.print(Panel(header, title="[bold]LYNX Fundamental Analysis[/]", border_style="blue"))

    tc = _tier_color(tier)
    console.print(Panel(
        f"[{tc}]{_tier_label(tier)}[/]\n"
        f"[dim]* = critical metric for this tier  |  dimmed = less relevant for this tier[/]",
        border_style=tc,
        title=f"[{tc}]{tier.value}[/]",
    ))


def _display_profile(report: AnalysisReport) -> None:
    """Render the company profile card."""
    p = report.profile
    profile_table = Table(show_header=False, box=None, padding=(0, 2))
    profile_table.add_column("Key", style="bold")
    profile_table.add_column("Value")
    profile_table.add_row("Sector", p.sector or "N/A")
    profile_table.add_row("Industry", p.industry or "N/A")
    profile_table.add_row("Country", p.country or "N/A")
    profile_table.add_row("Exchange", p.exchange or "N/A")
    profile_table.add_row("Market Cap", fmt_money(p.market_cap))
    profile_table.add_row("Employees", f"{p.employees:,}" if p.employees else "N/A")
    profile_table.add_row("Website", p.website or "N/A")
    console.print(Panel(profile_table, title="[bold]Company Profile[/]", border_style="cyan"))

    if p.description:
        desc = p.description[:500] + ("..." if len(p.description) > 500 else "")
        console.print(Panel(desc, title="[bold]Business Description[/]", border_style="dim"))

    _display_sector_industry(report)


def _display_sector_industry(report: AnalysisReport) -> None:
    """Render sector and industry insight panels after the profile."""
    try:
        from lynx.metrics.sector_insights import get_sector_insight, get_industry_insight
    except ImportError:
        return

    p = report.profile
    sector_info = get_sector_insight(p.sector)
    industry_info = get_industry_insight(p.industry)

    if sector_info:
        t = Table(show_header=False, box=None, padding=(0, 1))
        t.add_column("Key", style="bold cyan", min_width=20)
        t.add_column("Value")
        t.add_row("Overview", sector_info.overview)
        t.add_row("Critical Metrics", ", ".join(sector_info.critical_metrics))
        t.add_row("Key Risks", ", ".join(sector_info.key_risks))
        t.add_row("What to Watch", ", ".join(sector_info.what_to_watch))
        t.add_row("Typical Valuation", sector_info.typical_valuation)
        console.print(Panel(
            t,
            title=f"[bold]Sector: {sector_info.sector}[/]",
            border_style="blue",
        ))

    if industry_info:
        t = Table(show_header=False, box=None, padding=(0, 1))
        t.add_column("Key", style="bold cyan", min_width=20)
        t.add_column("Value")
        t.add_row("Overview", industry_info.overview)
        t.add_row("Critical Metrics", ", ".join(industry_info.critical_metrics))
        t.add_row("Key Risks", ", ".join(industry_info.key_risks))
        t.add_row("What to Watch", ", ".join(industry_info.what_to_watch))
        t.add_row("Typical Valuation", industry_info.typical_valuation)
        console.print(Panel(
            t,
            title=f"[bold]Industry: {industry_info.industry}[/]",
            border_style="blue",
        ))


# ======================================================================
# Section displays — all tier-aware
# ======================================================================

def _display_valuation(report: AnalysisReport) -> None:
    v = report.valuation
    if v is None:
        return
    tier = report.profile.tier
    rel = lambda key: get_relevance(key, tier, "valuation")

    t = Table(title="Valuation Metrics", show_lines=True, border_style="yellow")
    t.add_column("Metric", style="bold", min_width=22)
    t.add_column("Value", justify="right", min_width=15)
    t.add_column("Assessment", min_width=28)

    _add_metric_row(t, "P/E (Trailing)", fmt_num(v.pe_trailing), _assess_pe(v.pe_trailing, tier), rel("pe_trailing"))
    _add_metric_row(t, "P/E (Forward)", fmt_num(v.pe_forward), _assess_pe(v.pe_forward, tier), rel("pe_forward"))
    _add_metric_row(t, "P/B Ratio", fmt_num(v.pb_ratio), _assess_pb(v.pb_ratio, tier), rel("pb_ratio"))
    _add_metric_row(t, "P/S Ratio", fmt_num(v.ps_ratio), _assess_ps(v.ps_ratio, tier), rel("ps_ratio"))
    _add_metric_row(t, "P/FCF", fmt_num(v.p_fcf), _assess_pfcf(v.p_fcf, tier), rel("p_fcf"))
    _add_metric_row(t, "EV/EBITDA", fmt_num(v.ev_ebitda), _assess_ev_ebitda(v.ev_ebitda, tier), rel("ev_ebitda"))
    _add_metric_row(t, "EV/Revenue", fmt_num(v.ev_revenue), _assess_ev_revenue(v.ev_revenue, tier), rel("ev_revenue"))
    _add_metric_row(t, "PEG Ratio", fmt_num(v.peg_ratio), _assess_peg(v.peg_ratio), rel("peg_ratio"))
    _add_metric_row(t, "Earnings Yield", fmt_pct(v.earnings_yield), _assess_earnings_yield(v.earnings_yield), rel("earnings_yield"))
    _add_metric_row(t, "Dividend Yield", fmt_pct(v.dividend_yield), _assess_dividend_yield(v.dividend_yield, tier), rel("dividend_yield"))
    _add_metric_row(t, "P/Tangible Book", fmt_num(v.price_to_tangible_book), _assess_ptb(v.price_to_tangible_book), rel("price_to_tangible_book"))
    _add_metric_row(t, "P/NCAV (Net-Net)", fmt_num(v.price_to_ncav), _assess_pncav(v.price_to_ncav), rel("price_to_ncav"))

    console.print(t)


def _display_profitability(report: AnalysisReport) -> None:
    p = report.profitability
    if p is None:
        return
    tier = report.profile.tier
    rel = lambda key: get_relevance(key, tier, "profitability")

    t = Table(title="Profitability Metrics", show_lines=True, border_style="green")
    t.add_column("Metric", style="bold", min_width=22)
    t.add_column("Value", justify="right", min_width=15)
    t.add_column("Assessment", min_width=28)

    _add_metric_row(t, "ROE", fmt_pct(p.roe), _assess_roe(p.roe, tier), rel("roe"))
    _add_metric_row(t, "ROA", fmt_pct(p.roa), _assess_roa(p.roa), rel("roa"))
    _add_metric_row(t, "ROIC", fmt_pct(p.roic), _assess_roic(p.roic, tier), rel("roic"))
    _add_metric_row(t, "Gross Margin", fmt_pct(p.gross_margin), _assess_gross_margin(p.gross_margin, tier), rel("gross_margin"))
    _add_metric_row(t, "Operating Margin", fmt_pct(p.operating_margin), _assess_operating_margin(p.operating_margin, tier), rel("operating_margin"))
    _add_metric_row(t, "Net Margin", fmt_pct(p.net_margin), _assess_net_margin(p.net_margin, tier), rel("net_margin"))
    _add_metric_row(t, "FCF Margin", fmt_pct(p.fcf_margin), _assess_fcf_margin(p.fcf_margin, tier), rel("fcf_margin"))
    _add_metric_row(t, "EBITDA Margin", fmt_pct(p.ebitda_margin), _assess_ebitda_margin(p.ebitda_margin, tier), rel("ebitda_margin"))

    console.print(t)


def _display_solvency(report: AnalysisReport) -> None:
    s = report.solvency
    if s is None:
        return
    tier = report.profile.tier
    rel = lambda key: get_relevance(key, tier, "solvency")

    title = "Solvency & Financial Health"
    if tier in (CompanyTier.MICRO, CompanyTier.NANO):
        title = "Survival & Financial Health"
    elif tier == CompanyTier.SMALL:
        title = "Balance Sheet Strength"

    t = Table(title=title, show_lines=True, border_style="red")
    t.add_column("Metric", style="bold", min_width=22)
    t.add_column("Value", justify="right", min_width=15)
    t.add_column("Assessment", min_width=28)

    _add_metric_row(t, "Debt/Equity", fmt_num(s.debt_to_equity), _assess_de(s.debt_to_equity, tier), rel("debt_to_equity"))
    _add_metric_row(t, "Debt/EBITDA", fmt_num(s.debt_to_ebitda), _assess_debt_ebitda(s.debt_to_ebitda), rel("debt_to_ebitda"))
    _add_metric_row(t, "Current Ratio", fmt_num(s.current_ratio), _assess_current(s.current_ratio, tier), rel("current_ratio"))
    _add_metric_row(t, "Quick Ratio", fmt_num(s.quick_ratio), _assess_quick(s.quick_ratio), rel("quick_ratio"))
    _add_metric_row(t, "Interest Coverage", fmt_num(s.interest_coverage, 1), _assess_interest_coverage(s.interest_coverage, tier), rel("interest_coverage"))
    _add_metric_row(t, "Altman Z-Score", fmt_num(s.altman_z_score), _assess_zscore(s.altman_z_score), rel("altman_z_score"))

    # Survival metrics (shown for small/micro/nano)
    _add_metric_row(t, "Cash Burn Rate (/yr)", fmt_money(s.cash_burn_rate), _assess_burn(s.cash_burn_rate), rel("cash_burn_rate"))
    _add_metric_row(t, "Cash Runway", _fmt_runway(s.cash_runway_years), _assess_runway(s.cash_runway_years), rel("cash_runway_years"))
    _add_metric_row(t, "Working Capital", fmt_money(s.working_capital), _assess_wc(s.working_capital), rel("working_capital"))
    _add_metric_row(t, "Cash Per Share", f"${s.cash_per_share:.2f}" if s.cash_per_share else "[dim]N/A[/]", "", rel("cash_per_share"))
    _add_metric_row(t, "NCAV Per Share", f"${s.ncav_per_share:.4f}" if s.ncav_per_share is not None else "[dim]N/A[/]", _assess_ncav_vs_price(s.ncav_per_share, report), rel("ncav_per_share"))

    # Always show absolute numbers
    _add_metric_row(t, "Total Debt", fmt_money(s.total_debt), "", Relevance.RELEVANT)
    _add_metric_row(t, "Total Cash", fmt_money(s.total_cash), "", Relevance.RELEVANT)
    _add_metric_row(t, "Net Debt", fmt_money(s.net_debt), "", Relevance.RELEVANT)

    console.print(t)


def _display_growth(report: AnalysisReport) -> None:
    g = report.growth
    if g is None:
        return
    tier = report.profile.tier
    rel = lambda key: get_relevance(key, tier, "growth")

    t = Table(title="Growth Metrics", show_lines=True, border_style="magenta")
    t.add_column("Metric", style="bold", min_width=22)
    t.add_column("Value", justify="right", min_width=15)
    t.add_column("Assessment", min_width=28)

    _add_metric_row(t, "Revenue Growth (YoY)", fmt_pct(g.revenue_growth_yoy), _assess_growth(g.revenue_growth_yoy), rel("revenue_growth_yoy"))
    _add_metric_row(t, "Revenue CAGR (3Y)", fmt_pct(g.revenue_cagr_3y), _assess_cagr(g.revenue_cagr_3y), rel("revenue_cagr_3y"))
    _add_metric_row(t, "Revenue CAGR (5Y)", fmt_pct(g.revenue_cagr_5y), _assess_cagr(g.revenue_cagr_5y), rel("revenue_cagr_5y"))
    _add_metric_row(t, "Earnings Growth (YoY)", fmt_pct(g.earnings_growth_yoy), _assess_growth(g.earnings_growth_yoy), rel("earnings_growth_yoy"))
    _add_metric_row(t, "Earnings CAGR (3Y)", fmt_pct(g.earnings_cagr_3y), _assess_cagr(g.earnings_cagr_3y), rel("earnings_cagr_3y"))
    _add_metric_row(t, "Earnings CAGR (5Y)", fmt_pct(g.earnings_cagr_5y), _assess_cagr(g.earnings_cagr_5y), rel("earnings_cagr_5y"))
    _add_metric_row(t, "FCF Growth (YoY)", fmt_pct(g.fcf_growth_yoy), _assess_growth(g.fcf_growth_yoy), Relevance.RELEVANT)
    _add_metric_row(t, "Book Value Growth (YoY)", fmt_pct(g.book_value_growth_yoy), _assess_growth(g.book_value_growth_yoy), Relevance.RELEVANT)

    # Share dilution — critical for small/micro
    dilution_assess = _assess_dilution(g.shares_growth_yoy, tier)
    _add_metric_row(t, "Share Dilution (YoY)", fmt_pct(g.shares_growth_yoy), dilution_assess, rel("shares_growth_yoy"))

    console.print(t)


def _display_moat(report: AnalysisReport) -> None:
    m = report.moat
    if m is None:
        return
    tier = report.profile.tier

    title = "Economic Moat Analysis"
    if tier in (CompanyTier.MICRO, CompanyTier.NANO):
        title = "Competitive Position & Viability"
    elif tier == CompanyTier.SMALL:
        title = "Competitive Position Analysis"

    t = Table(title=title, show_lines=True, border_style="bold yellow")
    t.add_column("Indicator", style="bold", min_width=22)
    t.add_column("Assessment", ratio=1)

    t.add_row("Position Score", fmt_score(m.moat_score))
    t.add_row("Competitive Position", m.competitive_position or "[dim]N/A[/]")

    if tier in (CompanyTier.MEGA, CompanyTier.LARGE, CompanyTier.MID):
        # Traditional moat indicators
        t.add_row("ROIC Consistency", m.roic_consistency or "[dim]N/A[/]")
        t.add_row("Margin Stability", m.margin_stability or "[dim]N/A[/]")
        t.add_row("Revenue Predictability", m.revenue_predictability or "[dim]N/A[/]")
        t.add_row("Efficient Scale", m.efficient_scale or "[dim]N/A[/]")
        t.add_row("Switching Costs", m.switching_costs or "[dim]Requires qualitative review[/]")
        t.add_row("Network Effects", m.network_effects or "[dim]Requires qualitative review[/]")
        t.add_row("Cost Advantages", m.cost_advantages or "[dim]Not detected[/]")
        t.add_row("Intangible Assets", m.intangible_assets or "[dim]Not detected[/]")
    else:
        # Small/micro moat indicators
        t.add_row("[bold cyan]*[/] Asset Backing", m.asset_backing or "[dim]N/A[/]")
        t.add_row("[bold cyan]*[/] Revenue Status", m.revenue_predictability or "[dim]N/A[/]")
        t.add_row("[bold cyan]*[/] Niche Position", m.niche_position or "[dim]N/A[/]")
        t.add_row("[bold cyan]*[/] Dilution / Insider", m.insider_alignment or "[dim]N/A[/]")
        if m.intangible_assets:
            t.add_row("Intangible Assets", m.intangible_assets)
        if m.cost_advantages:
            t.add_row("Cost Advantages", m.cost_advantages)

    # Trends (filter out None values for clean display)
    roic_vals = [r for r in m.roic_history if r is not None]
    if roic_vals:
        hist = " -> ".join(fmt_pct(r) for r in reversed(roic_vals))
        t.add_row("ROIC Trend", hist)
    gm_vals = [r for r in m.gross_margin_history if r is not None]
    if gm_vals:
        hist = " -> ".join(fmt_pct(r) for r in reversed(gm_vals))
        t.add_row("Gross Margin Trend", hist)

    console.print(t)


def _display_intrinsic_value(report: AnalysisReport) -> None:
    iv = report.intrinsic_value
    if iv is None:
        return
    tier = report.profile.tier

    t = Table(title="Intrinsic Value Estimates", show_lines=True, border_style="bold green")
    t.add_column("Method", style="bold", min_width=28)
    t.add_column("Value", justify="right", min_width=15)
    t.add_column("Margin of Safety", min_width=30)

    price_str = f"${iv.current_price:.2f}" if iv.current_price else "[dim]N/A[/]"
    t.add_row("Current Price", price_str, "")

    # Method labels with primary/secondary markers
    def _marker(method_name: str) -> str:
        if iv.primary_method and method_name in iv.primary_method:
            return "[bold green](primary)[/] "
        if iv.secondary_method and method_name in iv.secondary_method:
            return "[cyan](secondary)[/] "
        return "[dim](reference)[/] "

    # DCF — primary for large/mega, reference for micro
    if tier in (CompanyTier.MEGA, CompanyTier.LARGE, CompanyTier.MID):
        dcf_label = _marker("DCF") + "DCF (10Y)"
        t.add_row(dcf_label,
                  f"${iv.dcf_value:.2f}" if iv.dcf_value else "[dim]N/A[/]",
                  _mos_color(iv.margin_of_safety_dcf))
    elif iv.dcf_value:
        t.add_row("[dim](unreliable for this tier)[/] DCF",
                  f"[dim]${iv.dcf_value:.2f}[/]",
                  "[dim]Not reliable for micro/small caps[/]")

    # Graham Number — primary for small, secondary for large
    graham_label = _marker("Graham") + "Graham Number"
    t.add_row(graham_label,
              f"${iv.graham_number:.2f}" if iv.graham_number else "[dim]N/A[/]",
              _mos_color(iv.margin_of_safety_graham))

    # NCAV / Net-Net — primary for micro, irrelevant for large
    if tier in (CompanyTier.MICRO, CompanyTier.NANO, CompanyTier.SMALL):
        ncav_label = _marker("NCAV") + "NCAV (Net-Net)"
        t.add_row(ncav_label,
                  f"${iv.ncav_value:.4f}" if iv.ncav_value is not None else "[dim]N/A (negative)[/]",
                  _mos_color(iv.margin_of_safety_ncav))

    # Asset-based — primary for micro/nano, secondary for small
    if tier in (CompanyTier.MICRO, CompanyTier.NANO, CompanyTier.SMALL, CompanyTier.MID):
        asset_label = _marker("Asset") + "Tangible Book / Share"
        t.add_row(asset_label,
                  f"${iv.asset_based_value:.4f}" if iv.asset_based_value else "[dim]N/A[/]",
                  _mos_color(iv.margin_of_safety_asset))

    # Lynch Fair Value
    if iv.lynch_fair_value:
        t.add_row("[dim](reference)[/] Lynch Fair Value",
                  f"${iv.lynch_fair_value:.2f}", "")

    # Methodology note
    console.print(t)
    if tier in (CompanyTier.MICRO, CompanyTier.NANO):
        console.print(
            "[dim]  Note: For micro/nano caps, NCAV and tangible book are more reliable "
            "than DCF. DCF requires predictable cash flows which small companies lack.[/]"
        )


def _display_conclusion(report: AnalysisReport) -> None:
    from lynx.core.conclusion import generate_conclusion

    c = generate_conclusion(report)
    tier = report.profile.tier

    verdict_colors = {
        "Strong Buy": "bold green", "Buy": "green",
        "Hold": "yellow", "Caution": "#ff8800", "Avoid": "bold red",
    }
    vc = verdict_colors.get(c.verdict, "white")

    # Verdict panel
    console.print(Panel(
        f"[{vc}]{c.verdict}[/]  —  Score: {fmt_score(c.overall_score)}\n\n"
        f"{c.summary}\n\n"
        f"[dim]{c.tier_note}[/]",
        title="[bold]Assessment Conclusion[/]",
        border_style=vc,
    ))

    # Category breakdown
    t = Table(title="Category Scores", show_lines=True, border_style="cyan")
    t.add_column("Category", style="bold", min_width=16)
    t.add_column("Score", justify="right", min_width=10)
    t.add_column("Summary", min_width=40)
    for cat in ("valuation", "profitability", "solvency", "growth", "moat"):
        score = c.category_scores.get(cat, 0)
        summary = c.category_summaries.get(cat, "")
        t.add_row(cat.title(), fmt_score(score), summary)
    console.print(t)

    # Strengths & Risks
    if c.strengths or c.risks:
        sr = Table(show_header=True, border_style="green")
        sr.add_column("Strengths", style="green", ratio=1)
        sr.add_column("Risks", style="red", ratio=1)
        max_len = max(len(c.strengths), len(c.risks))
        for i in range(max_len):
            s = c.strengths[i] if i < len(c.strengths) else ""
            r = c.risks[i] if i < len(c.risks) else ""
            sr.add_row(s, r)
        console.print(sr)


def _display_financials(report: AnalysisReport) -> None:
    if not report.financials:
        return
    t = Table(title="Financial Statements Summary (Annual)", show_lines=True, border_style="cyan")
    t.add_column("Period", style="bold")
    for label in ["Revenue", "Gross Profit", "Op. Income", "Net Income", "FCF", "Total Equity", "Total Debt"]:
        t.add_column(label, justify="right")
    for s in report.financials[:5]:
        t.add_row(
            s.period, fmt_money(s.revenue), fmt_money(s.gross_profit),
            fmt_money(s.operating_income), fmt_money(s.net_income),
            fmt_money(s.free_cash_flow), fmt_money(s.total_equity), fmt_money(s.total_debt),
        )
    console.print(t)


def _display_filings(report: AnalysisReport) -> None:
    if not report.filings:
        return
    t = Table(title=f"SEC Filings (showing top {min(len(report.filings), 15)})", border_style="yellow")
    t.add_column("Type", style="bold")
    t.add_column("Filed")
    t.add_column("Period")
    t.add_column("Downloaded", justify="center")
    for f in report.filings[:15]:
        downloaded = "[green]Yes[/]" if f.local_path else "[dim]No[/]"
        t.add_row(f.form_type, f.filing_date, f.period, downloaded)
    console.print(t)


def _display_news(report: AnalysisReport) -> None:
    if not report.news:
        return
    t = Table(title=f"Recent News ({len(report.news)} articles)", border_style="magenta")
    t.add_column("#", style="dim", width=3)
    t.add_column("Title", ratio=3)
    t.add_column("Source", ratio=1)
    t.add_column("Date", ratio=1)
    for i, n in enumerate(report.news[:15], 1):
        raw_title = n.title or ""
        title = raw_title[:70] + ("..." if len(raw_title) > 70 else "")
        t.add_row(str(i), title, n.source or "", n.published or "")
    console.print(t)


# ======================================================================
# Assessment functions — tier-aware thresholds
# ======================================================================

def _assess_pe(val, tier: CompanyTier) -> str:
    if val is None: return ""
    if val < 0: return "[red]Negative earnings[/]"
    # Small/micro caps naturally trade at lower multiples
    if tier in (CompanyTier.SMALL, CompanyTier.MICRO, CompanyTier.NANO):
        if val < 8: return "[green]Very cheap[/]"
        if val < 12: return "[green]Cheap (value range)[/]"
        if val < 18: return "[yellow]Fair[/]"
        return "[#ff8800]Expensive for size[/]"
    # Standard large-cap thresholds
    if val < 10: return "[green]Very cheap[/]"
    if val < 15: return "[green]Cheap (value range)[/]"
    if val < 20: return "[yellow]Fair[/]"
    if val < 30: return "[#ff8800]Expensive[/]"
    return "[red]Very expensive[/]"

def _assess_pb(val, tier: CompanyTier) -> str:
    if val is None: return ""
    if tier in (CompanyTier.MICRO, CompanyTier.NANO, CompanyTier.SMALL):
        if val < 0.67: return "[bold green]Deep value (below 2/3 book)[/]"
        if val < 1: return "[green]Below book value[/]"
        if val < 1.5: return "[green]Near book value[/]"
        if val < 2.5: return "[yellow]Above book[/]"
        return "[#ff8800]Premium to book[/]"
    if val < 1: return "[green]Below book value[/]"
    if val < 1.5: return "[green]Cheap[/]"
    if val < 3: return "[yellow]Fair[/]"
    return "[#ff8800]Premium[/]"

def _assess_ps(val, tier: CompanyTier) -> str:
    if val is None: return ""
    if val < 1: return "[green]Very cheap[/]"
    if val < 2: return "[green]Cheap[/]"
    if val < 5: return "[yellow]Fair[/]"
    return "[#ff8800]Expensive[/]"

def _assess_pfcf(val, tier: CompanyTier) -> str:
    if val is None: return ""
    if val < 10: return "[green]Cheap[/]"
    if val < 20: return "[yellow]Fair[/]"
    return "[#ff8800]Expensive[/]"

def _assess_ev_ebitda(val, tier: CompanyTier) -> str:
    if val is None: return ""
    if val < 8: return "[green]Cheap[/]"
    if val < 12: return "[yellow]Fair[/]"
    if val < 18: return "[#ff8800]Expensive[/]"
    return "[red]Very expensive[/]"

def _assess_peg(val) -> str:
    if val is None: return ""
    if val < 0: return "[dim]Negative growth[/]"
    if val < 1: return "[green]Undervalued vs growth[/]"
    if val < 2: return "[yellow]Fair[/]"
    return "[#ff8800]Overvalued vs growth[/]"

def _assess_ptb(val) -> str:
    if val is None: return ""
    if val < 0.67: return "[bold green]Deep value[/]"
    if val < 1: return "[green]Below tangible book[/]"
    if val < 1.5: return "[yellow]Near tangible book[/]"
    return "[#ff8800]Premium to tangible[/]"

def _assess_pncav(val) -> str:
    if val is None: return ""
    if val < 0.67: return "[bold green]Classic net-net (Graham)[/]"
    if val < 1: return "[green]Below NCAV[/]"
    if val < 1.5: return "[yellow]Near NCAV[/]"
    return "[#ff8800]Above NCAV[/]"

def _assess_roe(val, tier: CompanyTier) -> str:
    if val is None: return ""
    if val < 0: return "[red]Negative[/]"
    if tier in (CompanyTier.MICRO, CompanyTier.NANO):
        if val > 0.10: return "[green]Positive ROE[/]"
        return "[yellow]Low but positive[/]"
    if val > 0.20: return "[green]Excellent[/]"
    if val > 0.15: return "[green]Good[/]"
    if val > 0.10: return "[yellow]Average[/]"
    return "[#ff8800]Below average[/]"

def _assess_roa(val) -> str:
    if val is None: return ""
    if val < 0: return "[red]Negative[/]"
    if val > 0.10: return "[green]Excellent[/]"
    if val > 0.05: return "[yellow]Good[/]"
    return "[#ff8800]Low[/]"

def _assess_roic(val, tier: CompanyTier) -> str:
    if val is None: return ""
    if val < 0: return "[red]Negative — destroying value[/]"
    if tier in (CompanyTier.MICRO, CompanyTier.NANO):
        if val > 0.08: return "[green]Positive — generating returns[/]"
        return "[yellow]Low returns[/]"
    if val > 0.15: return "[green]Wide moat signal[/]"
    if val > 0.10: return "[green]Good capital allocation[/]"
    if val > 0.07: return "[yellow]Average[/]"
    return "[#ff8800]Below WACC likely[/]"

def _assess_gross_margin(val, tier: CompanyTier) -> str:
    if val is None: return ""
    if val <= 0: return "[red]No gross profit[/]"
    if tier in (CompanyTier.MICRO, CompanyTier.NANO):
        if val > 0.40: return "[green]High margins — niche/IP signal[/]"
        if val > 0.20: return "[yellow]Moderate[/]"
        return "[#ff8800]Low margins[/]"
    if val > 0.60: return "[green]Strong pricing power[/]"
    if val > 0.40: return "[green]Good[/]"
    if val > 0.20: return "[yellow]Average[/]"
    return "[#ff8800]Thin margins[/]"

def _assess_de(val, tier: CompanyTier) -> str:
    if val is None: return ""
    if val < 0: return "[green]Net cash position[/]"
    if tier in (CompanyTier.MICRO, CompanyTier.NANO):
        # Micro caps should have very low debt
        if val < 0.2: return "[green]Very low debt[/]"
        if val < 0.5: return "[yellow]Moderate for size[/]"
        return "[red]High debt — risky for micro cap[/]"
    if val < 0.3: return "[green]Very conservative[/]"
    if val < 0.5: return "[green]Conservative[/]"
    if val < 1.0: return "[yellow]Moderate[/]"
    if val < 2.0: return "[#ff8800]High leverage[/]"
    return "[red]Very high leverage[/]"

def _assess_debt_ebitda(val) -> str:
    if val is None: return ""
    if val < 1: return "[green]Very low debt burden[/]"
    if val < 2: return "[green]Manageable[/]"
    if val < 3: return "[yellow]Moderate[/]"
    return "[#ff8800]Heavy debt[/]"

def _assess_current(val, tier: CompanyTier) -> str:
    if val is None: return ""
    if tier in (CompanyTier.MICRO, CompanyTier.NANO, CompanyTier.SMALL):
        # Higher bar for small companies
        if val > 3.0: return "[green]Very strong liquidity[/]"
        if val > 2.0: return "[green]Strong[/]"
        if val > 1.5: return "[yellow]Adequate[/]"
        if val > 1.0: return "[#ff8800]Tight — monitor closely[/]"
        return "[red]Liquidity risk[/]"
    if val > 2.0: return "[green]Strong liquidity[/]"
    if val > 1.5: return "[green]Good[/]"
    if val > 1.0: return "[yellow]Adequate[/]"
    return "[red]Liquidity risk[/]"

def _assess_quick(val) -> str:
    if val is None: return ""
    if val > 1.5: return "[green]Strong[/]"
    if val > 1.0: return "[yellow]Adequate[/]"
    return "[#ff8800]Weak[/]"

def _assess_zscore(val) -> str:
    if val is None: return ""
    if val > 2.99: return "[green]Safe zone[/]"
    if val > 1.81: return "[yellow]Grey zone[/]"
    return "[red]Distress zone[/]"

def _assess_burn(val) -> str:
    if val is None: return ""
    if val == 0: return "[green]Not burning cash[/]"
    if val < 0: return f"[red]Burning {fmt_money(abs(val))}/yr[/]"
    return "[green]Cash flow positive[/]"

def _fmt_runway(val) -> str:
    if val is None: return "[dim]N/A[/]"
    return f"{val:.1f} years"

def _assess_runway(val) -> str:
    if val is None: return ""
    if val > 5: return "[green]Ample runway[/]"
    if val > 3: return "[green]Comfortable[/]"
    if val > 1.5: return "[yellow]Adequate[/]"
    if val > 0.5: return "[#ff8800]Tight — may need financing[/]"
    return "[bold red]Critical — fundraising imminent[/]"

def _assess_wc(val) -> str:
    if val is None: return ""
    if val > 0: return "[green]Positive[/]"
    return "[red]Negative working capital[/]"

def _assess_ncav_vs_price(ncav_ps, report: AnalysisReport) -> str:
    if ncav_ps is None: return ""
    if report.intrinsic_value is None: return ""
    price = report.intrinsic_value.current_price
    if ncav_ps <= 0: return "[dim]Negative NCAV[/]"
    if price and ncav_ps > 0:
        if price < ncav_ps * 0.67:
            return "[bold green]Below 2/3 NCAV — classic net-net[/]"
        if price < ncav_ps:
            return "[green]Below NCAV[/]"
    return ""

def _assess_dilution(val, tier: CompanyTier) -> str:
    if val is None: return ""
    if val < -0.02: return "[green]Buybacks — shareholder friendly[/]"
    if val < 0.01: return "[green]Minimal dilution[/]"
    if val < 0.05: return "[yellow]Modest dilution (<5%)[/]"
    if val < 0.10: return "[#ff8800]Significant dilution (5-10%)[/]"
    return "[bold red]Heavy dilution (>10%) — value destruction[/]"

def _assess_ev_revenue(val, tier: CompanyTier) -> str:
    if val is None: return ""
    if val < 0: return "[dim]Negative EV[/]"
    if tier in (CompanyTier.MICRO, CompanyTier.NANO):
        if val < 0.5: return "[green]Very cheap[/]"
        if val < 1.5: return "[green]Cheap[/]"
        if val < 3: return "[yellow]Fair[/]"
        return "[#ff8800]Expensive for size[/]"
    if val < 1: return "[green]Very cheap[/]"
    if val < 3: return "[green]Cheap[/]"
    if val < 5: return "[yellow]Fair[/]"
    if val < 8: return "[#ff8800]Expensive[/]"
    return "[red]Very expensive[/]"

def _assess_earnings_yield(val) -> str:
    if val is None: return ""
    if val > 0.10: return "[green]Excellent yield[/]"
    if val > 0.07: return "[green]Good yield[/]"
    if val > 0.05: return "[yellow]Fair yield[/]"
    if val > 0: return "[#ff8800]Low yield[/]"
    return "[red]Negative earnings[/]"

def _assess_dividend_yield(val, tier: CompanyTier) -> str:
    if val is None: return ""
    if val <= 0: return "[dim]No dividend[/]"
    if val > 0.06: return "[#ff8800]Very high — check sustainability[/]"
    if val > 0.04: return "[green]High yield[/]"
    if val > 0.02: return "[green]Moderate yield[/]"
    return "[yellow]Low yield[/]"

def _assess_operating_margin(val, tier: CompanyTier) -> str:
    if val is None: return ""
    if val < 0: return "[red]Operating loss[/]"
    if tier in (CompanyTier.MICRO, CompanyTier.NANO):
        if val > 0.15: return "[green]Strong for size[/]"
        if val > 0.05: return "[yellow]Moderate[/]"
        return "[#ff8800]Thin margins[/]"
    if val > 0.25: return "[green]Excellent[/]"
    if val > 0.15: return "[green]Good[/]"
    if val > 0.05: return "[yellow]Moderate[/]"
    return "[#ff8800]Thin margins[/]"

def _assess_net_margin(val, tier: CompanyTier) -> str:
    if val is None: return ""
    if val < 0: return "[red]Loss-making[/]"
    if val > 0.20: return "[green]Excellent[/]"
    if val > 0.10: return "[green]Good[/]"
    if val > 0.05: return "[yellow]Fair[/]"
    return "[#ff8800]Thin[/]"

def _assess_fcf_margin(val, tier: CompanyTier) -> str:
    if val is None: return ""
    if val < 0: return "[red]Negative FCF[/]"
    if val > 0.20: return "[green]Excellent cash generation[/]"
    if val > 0.10: return "[green]Strong[/]"
    if val > 0.05: return "[yellow]Moderate[/]"
    return "[#ff8800]Weak cash conversion[/]"

def _assess_ebitda_margin(val, tier: CompanyTier) -> str:
    if val is None: return ""
    if val < 0: return "[red]Negative EBITDA[/]"
    if val > 0.30: return "[green]Excellent[/]"
    if val > 0.15: return "[green]Good[/]"
    if val > 0.05: return "[yellow]Moderate[/]"
    return "[#ff8800]Thin margins[/]"

def _assess_interest_coverage(val, tier: CompanyTier) -> str:
    if val is None: return ""
    if val > 8: return "[green]Very strong[/]"
    if val > 4: return "[green]Strong[/]"
    if val > 2: return "[yellow]Adequate[/]"
    if val > 1: return "[#ff8800]Tight[/]"
    return "[bold red]Cannot cover interest[/]"

def _assess_growth(val) -> str:
    if val is None: return ""
    if val > 0.25: return "[green]Very strong growth[/]"
    if val > 0.10: return "[green]Good growth[/]"
    if val > 0: return "[yellow]Positive[/]"
    if val > -0.10: return "[#ff8800]Slight decline[/]"
    return "[red]Significant decline[/]"

def _assess_cagr(val) -> str:
    if val is None: return ""
    if val > 0.15: return "[green]Excellent[/]"
    if val > 0.08: return "[green]Good[/]"
    if val > 0: return "[yellow]Positive[/]"
    if val > -0.05: return "[#ff8800]Slight decline[/]"
    return "[red]Declining[/]"
