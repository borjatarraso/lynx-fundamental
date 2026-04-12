"""Textual UI for Lynx Fundamental Analysis."""

from __future__ import annotations

import asyncio
from typing import Optional

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import (
    DataTable,
    Footer,
    Header,
    Input,
    Label,
    Static,
    TabbedContent,
    TabPane,
)

from lynx.models import AnalysisReport, CompanyTier


class SearchModal(ModalScreen[str]):
    """Modal dialog for entering a ticker/ISIN."""

    BINDINGS = [Binding("escape", "dismiss_modal", "Cancel")]

    def compose(self) -> ComposeResult:
        with Vertical(id="search-dialog"):
            yield Label("Enter Ticker or ISIN", id="search-label")
            yield Input(placeholder="e.g. AAPL, MSFT, OCO.V, AT1.DE", id="search-input")
            yield Label("[dim]Press Enter to analyze, Escape to cancel[/]", id="search-hint")

    def on_input_submitted(self, event: Input.Submitted) -> None:
        self.dismiss(event.value.strip() if event.value else "")

    def action_dismiss_modal(self) -> None:
        self.dismiss("")


class LynxApp(App):
    """Lynx FA Textual UI Application."""

    TITLE = "Lynx Fundamental Analysis"
    SUB_TITLE = "Value Investing & Moat Analysis"
    CSS = """
    #search-dialog {
        width: 60;
        height: auto;
        max-height: 12;
        border: thick $accent;
        background: $surface;
        padding: 1 2;
        margin: 4 8;
    }
    #search-label {
        text-align: center;
        text-style: bold;
        margin-bottom: 1;
    }
    #search-hint {
        text-align: center;
        margin-top: 1;
    }
    #search-input {
        margin: 0 2;
    }
    #status-area {
        text-align: center;
        margin: 4;
    }
    #profile-panel {
        height: auto;
        max-height: 12;
        margin: 0 0 1 0;
    }
    #report-container {
        height: 1fr;
    }
    """

    BINDINGS = [
        Binding("a", "analyze", "Analyze"),
        Binding("q", "quit", "Quit"),
        Binding("r", "refresh", "Refresh"),
        Binding("d", "dark", "Toggle Dark"),
    ]

    report: Optional[AnalysisReport] = None
    _last_identifier: str = ""

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static(
            "[bold blue]  LYNX FA  [/]\n\n"
            "[bold]Fundamental Analysis Tool[/]\n"
            "[dim]Press [bold]A[/bold] to analyze a stock, [bold]Q[/bold] to quit[/]",
            id="status-area",
        )
        yield Footer()

    def action_analyze(self) -> None:
        self.push_screen(SearchModal(), self._on_search_result)

    def action_dark(self) -> None:
        self.theme = "textual-dark" if self.theme == "textual-light" else "textual-light"

    def action_refresh(self) -> None:
        if self._last_identifier:
            self._run_analysis(self._last_identifier, force_refresh=True)

    def _on_search_result(self, identifier: str) -> None:
        if not identifier:
            return
        self._run_analysis(identifier)

    def _run_analysis(self, identifier: str, force_refresh: bool = False) -> None:
        self._last_identifier = identifier
        self._set_status(f"[bold cyan]Analyzing {identifier}...[/]\n\n[dim]Fetching data, please wait...[/]")
        self.run_worker(
            self._do_analysis(identifier, force_refresh),
            name="analysis",
            exclusive=True,
        )

    async def _do_analysis(self, identifier: str, force_refresh: bool = False) -> None:
        from lynx.core.storage import is_testing
        from lynx.core.analyzer import run_full_analysis

        try:
            refresh = force_refresh or is_testing()
            report = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: run_full_analysis(
                    identifier,
                    download_reports=True,
                    download_news=True,
                    refresh=refresh,
                ),
            )
            self.report = report
            self.app.call_from_thread(self._show_report, report)
        except Exception as e:
            self.app.call_from_thread(self._set_status, f"[bold red]Error:[/] {e}\n\n[dim]Press A to try again[/]")

    def _set_status(self, message: str) -> None:
        """Update the status area, removing any existing report."""
        self._remove_report_widgets()
        try:
            status = self.query_one("#status-area", Static)
            status.update(message)
            status.display = True
        except Exception:
            pass

    def _remove_report_widgets(self) -> None:
        """Remove existing report container and profile if present."""
        for widget_id in ("#report-container", "#profile-panel"):
            try:
                widget = self.query_one(widget_id)
                widget.remove()
            except Exception:
                pass

    def _show_report(self, report: AnalysisReport) -> None:
        try:
            # Remove old report widgets
            self._remove_report_widgets()

            # Hide status area
            try:
                status = self.query_one("#status-area", Static)
                status.display = False
            except Exception:
                pass

            p = report.profile
            tier_str = _safe_tier(p.tier)
            profile_text = (
                f"[bold]{_s(p.name)}[/] ({_s(p.ticker)})  [{tier_str}]"
                + (f"  |  ISIN: {p.isin}" if p.isin else "")
                + f"\n{_s(p.sector)} / {_s(p.industry)}  |  {_s(p.country)}"
                + f"  |  Market Cap: {_money(p.market_cap)}"
            )

            content = Vertical(
                Static(profile_text, id="profile-panel"),
                TabbedContent(
                    TabPane("Valuation", _build_valuation(report), id="tab-val"),
                    TabPane("Profitability", _build_profitability(report), id="tab-prof"),
                    TabPane("Solvency", _build_solvency(report), id="tab-solv"),
                    TabPane("Growth", _build_growth(report), id="tab-growth"),
                    TabPane("Moat", _build_moat(report), id="tab-moat"),
                    TabPane("Intrinsic Value", _build_iv(report), id="tab-iv"),
                    TabPane("Financials", _build_financials(report), id="tab-fin"),
                    TabPane("Filings", _build_filings(report), id="tab-filings"),
                    TabPane("News", _build_news(report), id="tab-news"),
                ),
                id="report-container",
            )

            self.mount(content, before=self.query_one(Footer))

        except Exception as e:
            self._set_status(f"[bold red]Display error:[/] {e}\n\n[dim]Press A to try again[/]")


# ======================================================================
# Table builders — all standalone functions, fully defensive
# ======================================================================

def _build_valuation(report: AnalysisReport) -> DataTable:
    v = report.valuation
    table = DataTable(zebra_stripes=True)
    table.add_columns("Metric", "Value", "Assessment")
    _row(table, "P/E (Trailing)", _num(v.pe_trailing), _ape(v.pe_trailing))
    _row(table, "P/E (Forward)", _num(v.pe_forward), _ape(v.pe_forward))
    _row(table, "P/B Ratio", _num(v.pb_ratio), _thresh(v.pb_ratio, [(1, "Below Book"), (1.5, "Cheap"), (3, "Fair")], "Premium"))
    _row(table, "P/S Ratio", _num(v.ps_ratio), "")
    _row(table, "P/FCF", _num(v.p_fcf), _thresh(v.p_fcf, [(10, "Cheap"), (20, "Fair")], "Expensive"))
    _row(table, "EV/EBITDA", _num(v.ev_ebitda), _thresh(v.ev_ebitda, [(8, "Cheap"), (12, "Fair"), (18, "Expensive")], "Very Expensive"))
    _row(table, "EV/Revenue", _num(v.ev_revenue), "")
    _row(table, "PEG Ratio", _num(v.peg_ratio), _thresh(v.peg_ratio, [(1, "Undervalued"), (2, "Fair")], "Overvalued"))
    _row(table, "Earnings Yield", _pct(v.earnings_yield), "")
    _row(table, "Dividend Yield", _pct(v.dividend_yield), "")
    _row(table, "P/Tangible Book", _num(v.price_to_tangible_book), _thresh(v.price_to_tangible_book, [(0.67, "Deep Value"), (1, "Below Book"), (1.5, "Near Book")], "Premium"))
    _row(table, "P/NCAV (Net-Net)", _num(v.price_to_ncav), _thresh(v.price_to_ncav, [(0.67, "Classic Net-Net"), (1, "Below NCAV"), (1.5, "Near NCAV")], "Above NCAV"))
    _row(table, "Enterprise Value", _money(v.enterprise_value), "")
    _row(table, "Market Cap", _money(v.market_cap), "")
    return table


def _build_profitability(report: AnalysisReport) -> DataTable:
    p = report.profitability
    table = DataTable(zebra_stripes=True)
    table.add_columns("Metric", "Value", "Assessment")
    _row(table, "ROE", _pct(p.roe), _thresh(p.roe, [(0, "Negative"), (0.10, "Below Avg"), (0.15, "Good"), (0.20, "Excellent")], "Outstanding"))
    _row(table, "ROA", _pct(p.roa), _thresh(p.roa, [(0, "Negative"), (0.05, "Low"), (0.10, "Good")], "Excellent"))
    _row(table, "ROIC", _pct(p.roic), _thresh(p.roic, [(0, "Negative"), (0.07, "Below WACC"), (0.10, "Good"), (0.15, "Wide Moat")], "Exceptional"))
    _row(table, "Gross Margin", _pct(p.gross_margin), "")
    _row(table, "Operating Margin", _pct(p.operating_margin), "")
    _row(table, "Net Margin", _pct(p.net_margin), "")
    _row(table, "FCF Margin", _pct(p.fcf_margin), "")
    _row(table, "EBITDA Margin", _pct(p.ebitda_margin), "")
    return table


def _build_solvency(report: AnalysisReport) -> DataTable:
    s = report.solvency
    table = DataTable(zebra_stripes=True)
    table.add_columns("Metric", "Value", "Assessment")
    _row(table, "Debt/Equity", _num(s.debt_to_equity), _thresh(s.debt_to_equity, [(0.3, "Very Conservative"), (0.5, "Conservative"), (1.0, "Moderate"), (2.0, "High")], "Very High"))
    _row(table, "Debt/EBITDA", _num(s.debt_to_ebitda), _thresh(s.debt_to_ebitda, [(1, "Very Low"), (2, "Manageable"), (3, "Moderate")], "Heavy"))
    _row(table, "Current Ratio", _num(s.current_ratio), _thresh(s.current_ratio, [(1.0, "Liquidity Risk"), (1.5, "Adequate"), (2.0, "Good")], "Strong"))
    _row(table, "Quick Ratio", _num(s.quick_ratio), "")
    _row(table, "Interest Coverage", _num(s.interest_coverage, 1), "")
    _row(table, "Altman Z-Score", _num(s.altman_z_score), _thresh(s.altman_z_score, [(1.81, "Distress"), (2.99, "Grey Zone")], "Safe"))
    _row(table, "Cash Burn Rate (/yr)", _money(s.cash_burn_rate), _burn(s.cash_burn_rate))
    _row(table, "Cash Runway", f"{s.cash_runway_years:.1f} yrs" if s.cash_runway_years is not None else "N/A", "")
    _row(table, "Working Capital", _money(s.working_capital), "")
    _row(table, "Cash Per Share", f"${s.cash_per_share:.2f}" if s.cash_per_share is not None else "N/A", "")
    _row(table, "NCAV Per Share", f"${s.ncav_per_share:.4f}" if s.ncav_per_share is not None else "N/A", "")
    _row(table, "Total Debt", _money(s.total_debt), "")
    _row(table, "Total Cash", _money(s.total_cash), "")
    _row(table, "Net Debt", _money(s.net_debt), "")
    return table


def _build_growth(report: AnalysisReport) -> DataTable:
    g = report.growth
    table = DataTable(zebra_stripes=True)
    table.add_columns("Metric", "Value")
    _row2(table, "Revenue Growth (YoY)", _pct(g.revenue_growth_yoy))
    _row2(table, "Revenue CAGR (3Y)", _pct(g.revenue_cagr_3y))
    _row2(table, "Revenue CAGR (5Y)", _pct(g.revenue_cagr_5y))
    _row2(table, "Earnings Growth (YoY)", _pct(g.earnings_growth_yoy))
    _row2(table, "Earnings CAGR (3Y)", _pct(g.earnings_cagr_3y))
    _row2(table, "Earnings CAGR (5Y)", _pct(g.earnings_cagr_5y))
    _row2(table, "FCF Growth (YoY)", _pct(g.fcf_growth_yoy))
    _row2(table, "Book Value Growth (YoY)", _pct(g.book_value_growth_yoy))
    _row2(table, "Share Dilution (YoY)", _pct(g.shares_growth_yoy))
    return table


def _build_moat(report: AnalysisReport) -> DataTable:
    m = report.moat
    tier = report.profile.tier if hasattr(report.profile, 'tier') else CompanyTier.NANO
    table = DataTable(zebra_stripes=True)
    table.add_columns("Indicator", "Assessment")
    _row2(table, "Moat Score", f"{m.moat_score:.1f}/100" if m.moat_score is not None else "N/A")
    _row2(table, "Competitive Position", _s(m.competitive_position))

    if isinstance(tier, CompanyTier) and tier in (CompanyTier.MEGA, CompanyTier.LARGE, CompanyTier.MID):
        _row2(table, "ROIC Consistency", _s(m.roic_consistency))
        _row2(table, "Margin Stability", _s(m.margin_stability))
        _row2(table, "Revenue Predictability", _s(m.revenue_predictability))
        _row2(table, "Efficient Scale", _s(m.efficient_scale))
        _row2(table, "Switching Costs", m.switching_costs or "Requires qualitative review")
        _row2(table, "Network Effects", m.network_effects or "Requires qualitative review")
        _row2(table, "Cost Advantages", m.cost_advantages or "Not detected")
        _row2(table, "Intangible Assets", m.intangible_assets or "Not detected")
    else:
        _row2(table, "Asset Backing", _s(m.asset_backing))
        _row2(table, "Revenue Status", _s(m.revenue_predictability))
        _row2(table, "Niche Position", _s(m.niche_position))
        _row2(table, "Dilution / Insider", _s(m.insider_alignment))
        if m.intangible_assets:
            _row2(table, "Intangible Assets", m.intangible_assets)
        if m.cost_advantages:
            _row2(table, "Cost Advantages", m.cost_advantages)

    if m.roic_history:
        hist = " -> ".join(_pct_plain(r) for r in reversed(m.roic_history))
        _row2(table, "ROIC Trend", hist)
    if m.gross_margin_history:
        hist = " -> ".join(_pct_plain(r) for r in reversed(m.gross_margin_history))
        _row2(table, "Gross Margin Trend", hist)
    return table


def _build_iv(report: AnalysisReport) -> DataTable:
    iv = report.intrinsic_value
    table = DataTable(zebra_stripes=True)
    table.add_columns("Method", "Value", "Margin of Safety")
    _row(table, "Current Price", f"${iv.current_price:.2f}" if iv.current_price else "N/A", "")
    primary = iv.primary_method or ""
    secondary = iv.secondary_method or ""

    def _tag(name: str) -> str:
        if name in primary:
            return "(primary) "
        if name in secondary:
            return "(secondary) "
        return ""

    _row(table, f"{_tag('DCF')}DCF (10Y)", f"${iv.dcf_value:.2f}" if iv.dcf_value else "N/A", _mos(iv.margin_of_safety_dcf))
    _row(table, f"{_tag('Graham')}Graham Number", f"${iv.graham_number:.2f}" if iv.graham_number else "N/A", _mos(iv.margin_of_safety_graham))
    _row(table, f"{_tag('NCAV')}NCAV (Net-Net)", f"${iv.ncav_value:.4f}" if iv.ncav_value is not None else "N/A", _mos(iv.margin_of_safety_ncav))
    _row(table, f"{_tag('Asset')}Tangible Book/Share", f"${iv.asset_based_value:.4f}" if iv.asset_based_value else "N/A", _mos(iv.margin_of_safety_asset))
    if iv.lynch_fair_value:
        _row(table, "Lynch Fair Value", f"${iv.lynch_fair_value:.2f}", "")
    return table


def _build_financials(report: AnalysisReport) -> DataTable:
    table = DataTable(zebra_stripes=True)
    table.add_columns("Period", "Revenue", "Gross Profit", "Op Income", "Net Income", "FCF", "Equity", "Debt")
    for s in (report.financials or [])[:5]:
        _row(table,
             _s(s.period), _money(s.revenue), _money(s.gross_profit),
             _money(s.operating_income), _money(s.net_income),
             _money(s.free_cash_flow), _money(s.total_equity), _money(s.total_debt))
    return table


def _build_filings(report: AnalysisReport) -> DataTable:
    table = DataTable(zebra_stripes=True)
    table.add_columns("Type", "Filed", "Period", "Downloaded")
    for f in (report.filings or [])[:20]:
        _row(table, _s(f.form_type), _s(f.filing_date), _s(f.period), "Yes" if f.local_path else "No")
    return table


def _build_news(report: AnalysisReport) -> DataTable:
    table = DataTable(zebra_stripes=True)
    table.add_columns("#", "Title", "Source", "Date")
    for i, n in enumerate((report.news or [])[:20], 1):
        title = (n.title or "")[:70]
        if len(n.title or "") > 70:
            title += "..."
        _row(table, str(i), title, _s(n.source), _s(n.published))
    return table


# ======================================================================
# Safe formatters — never raise, always return a string
# ======================================================================

def _row(table: DataTable, *cells: str) -> None:
    """Add a row to a DataTable, ensuring all values are strings."""
    table.add_row(*(str(c) if c is not None else "N/A" for c in cells))


def _row2(table: DataTable, label: str, value: str) -> None:
    """Add a 2-column row."""
    table.add_row(str(label), str(value) if value is not None else "N/A")


def _s(val) -> str:
    """Safe string — never None."""
    if val is None:
        return "N/A"
    return str(val)


def _num(val, digits: int = 2) -> str:
    if val is None:
        return "N/A"
    try:
        return f"{float(val):,.{digits}f}"
    except (ValueError, TypeError):
        return "N/A"


def _pct(val) -> str:
    if val is None:
        return "N/A"
    try:
        return f"{float(val) * 100:.2f}%"
    except (ValueError, TypeError):
        return "N/A"


def _pct_plain(val) -> str:
    if val is None:
        return "N/A"
    try:
        return f"{float(val) * 100:.1f}%"
    except (ValueError, TypeError):
        return "N/A"


def _money(val) -> str:
    if val is None:
        return "N/A"
    try:
        v = float(val)
        if abs(v) >= 1_000_000_000_000:
            return f"${v / 1_000_000_000_000:,.2f}T"
        if abs(v) >= 1_000_000_000:
            return f"${v / 1_000_000_000:,.2f}B"
        if abs(v) >= 1_000_000:
            return f"${v / 1_000_000:,.2f}M"
        return f"${v:,.0f}"
    except (ValueError, TypeError):
        return "N/A"


def _mos(val) -> str:
    if val is None:
        return "N/A"
    try:
        pct = float(val) * 100
        if pct > 25:
            return f"{pct:.1f}% (Undervalued)"
        if pct > 0:
            return f"{pct:.1f}% (Slight Undervalue)"
        return f"{pct:.1f}% (Overvalued)"
    except (ValueError, TypeError):
        return "N/A"


def _ape(val) -> str:
    if val is None:
        return ""
    try:
        v = float(val)
        if v < 0:
            return "Negative earnings"
        if v < 10:
            return "Very cheap"
        if v < 15:
            return "Value range"
        if v < 20:
            return "Fair"
        if v < 30:
            return "Expensive"
        return "Very expensive"
    except (ValueError, TypeError):
        return ""


def _burn(val) -> str:
    if val is None:
        return ""
    try:
        v = float(val)
        if v == 0:
            return "Not burning cash"
        if v < 0:
            return "Burning cash"
        return "Cash flow positive"
    except (ValueError, TypeError):
        return ""


def _thresh(val, thresholds: list[tuple], over_label: str) -> str:
    if val is None:
        return ""
    try:
        v = float(val)
        for t, label in thresholds:
            if v < t:
                return label
        return over_label
    except (ValueError, TypeError):
        return ""


def _safe_tier(tier) -> str:
    if isinstance(tier, CompanyTier):
        return tier.value
    if tier is None:
        return "N/A"
    return str(tier)


def run_tui() -> None:
    """Launch the Textual UI."""
    app = LynxApp()
    app.run()
