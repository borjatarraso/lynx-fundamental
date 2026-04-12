"""Textual UI for Lynx Fundamental Analysis."""

from __future__ import annotations

from typing import Optional

from textual import work
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
        height: auto;
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
            self._start_analysis(self._last_identifier, force_refresh=True)

    def _on_search_result(self, identifier: str) -> None:
        if not identifier:
            return
        self._start_analysis(identifier)

    def _start_analysis(self, identifier: str, force_refresh: bool = False) -> None:
        self._last_identifier = identifier
        self._set_status(f"[bold cyan]Analyzing {identifier}...[/]\n\n[dim]Fetching data, please wait...[/]")
        self._do_analysis(identifier, force_refresh)

    @work(thread=True, exclusive=True)
    def _do_analysis(self, identifier: str, force_refresh: bool = False) -> None:
        """Run analysis in a background thread. Uses call_from_thread to update UI."""
        from lynx.core.storage import is_testing
        from lynx.core.analyzer import run_full_analysis

        try:
            refresh = force_refresh or is_testing()
            report = run_full_analysis(
                identifier,
                download_reports=True,
                download_news=True,
                refresh=refresh,
            )
            self.report = report
            self.call_from_thread(self._render_report, report)
        except Exception as e:
            error_msg = str(e) if str(e) else type(e).__name__
            self.call_from_thread(
                self._set_status,
                f"[bold red]Error:[/] {error_msg}\n\n[dim]Press A to try again[/]",
            )

    def _set_status(self, message: str) -> None:
        """Show a status message, removing any existing report widgets."""
        self._clear_report()
        try:
            status = self.query_one("#status-area", Static)
            status.update(message)
            status.display = True
        except Exception:
            pass

    def _clear_report(self) -> None:
        """Safely remove all report-related widgets."""
        for selector in ("#report-container",):
            try:
                self.query_one(selector).remove()
            except Exception:
                pass

    def _render_report(self, report: AnalysisReport) -> None:
        """Build and mount the full report UI. Called from the main thread."""
        try:
            self._clear_report()

            # Hide status
            try:
                self.query_one("#status-area", Static).display = False
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

            tabs = TabbedContent(
                TabPane("Valuation", _build_valuation(report), id="tab-val"),
                TabPane("Profitability", _build_profitability(report), id="tab-prof"),
                TabPane("Solvency", _build_solvency(report), id="tab-solv"),
                TabPane("Growth", _build_growth(report), id="tab-growth"),
                TabPane("Moat", _build_moat(report), id="tab-moat"),
                TabPane("Intrinsic Value", _build_iv(report), id="tab-iv"),
                TabPane("Financials", _build_financials(report), id="tab-fin"),
                TabPane("Filings", _build_filings(report), id="tab-filings"),
                TabPane("News", _build_news(report), id="tab-news"),
            )

            container = Vertical(
                Static(profile_text, id="profile-panel"),
                tabs,
                id="report-container",
            )

            self.mount(container, before=self.query_one(Footer))

        except Exception as e:
            self._set_status(
                f"[bold red]Display error:[/] {type(e).__name__}: {e}\n\n[dim]Press A to try again[/]"
            )


# ======================================================================
# Table builders — standalone, defensive, no exceptions
# ======================================================================

def _build_valuation(report: AnalysisReport) -> DataTable:
    v = report.valuation
    t = DataTable(zebra_stripes=True)
    t.add_columns("Metric", "Value", "Assessment")
    _r3(t, "P/E (Trailing)", _num(v.pe_trailing), _ape(v.pe_trailing))
    _r3(t, "P/E (Forward)", _num(v.pe_forward), _ape(v.pe_forward))
    _r3(t, "P/B Ratio", _num(v.pb_ratio), _thr(v.pb_ratio, [(1, "Below Book"), (1.5, "Cheap"), (3, "Fair")], "Premium"))
    _r3(t, "P/S Ratio", _num(v.ps_ratio), "")
    _r3(t, "P/FCF", _num(v.p_fcf), _thr(v.p_fcf, [(10, "Cheap"), (20, "Fair")], "Expensive"))
    _r3(t, "EV/EBITDA", _num(v.ev_ebitda), _thr(v.ev_ebitda, [(8, "Cheap"), (12, "Fair"), (18, "Expensive")], "Very Expensive"))
    _r3(t, "EV/Revenue", _num(v.ev_revenue), "")
    _r3(t, "PEG Ratio", _num(v.peg_ratio), _thr(v.peg_ratio, [(1, "Undervalued"), (2, "Fair")], "Overvalued"))
    _r3(t, "Earnings Yield", _pct(v.earnings_yield), "")
    _r3(t, "Dividend Yield", _pct(v.dividend_yield), "")
    _r3(t, "P/Tangible Book", _num(v.price_to_tangible_book), _thr(v.price_to_tangible_book, [(0.67, "Deep Value"), (1, "Below Book"), (1.5, "Near Book")], "Premium"))
    _r3(t, "P/NCAV (Net-Net)", _num(v.price_to_ncav), _thr(v.price_to_ncav, [(0.67, "Classic Net-Net"), (1, "Below NCAV"), (1.5, "Near NCAV")], "Above NCAV"))
    _r3(t, "Enterprise Value", _money(v.enterprise_value), "")
    _r3(t, "Market Cap", _money(v.market_cap), "")
    return t


def _build_profitability(report: AnalysisReport) -> DataTable:
    p = report.profitability
    t = DataTable(zebra_stripes=True)
    t.add_columns("Metric", "Value", "Assessment")
    _r3(t, "ROE", _pct(p.roe), _thr(p.roe, [(0, "Negative"), (0.10, "Below Avg"), (0.15, "Good"), (0.20, "Excellent")], "Outstanding"))
    _r3(t, "ROA", _pct(p.roa), _thr(p.roa, [(0, "Negative"), (0.05, "Low"), (0.10, "Good")], "Excellent"))
    _r3(t, "ROIC", _pct(p.roic), _thr(p.roic, [(0, "Negative"), (0.07, "Below WACC"), (0.10, "Good"), (0.15, "Wide Moat")], "Exceptional"))
    _r3(t, "Gross Margin", _pct(p.gross_margin), "")
    _r3(t, "Operating Margin", _pct(p.operating_margin), "")
    _r3(t, "Net Margin", _pct(p.net_margin), "")
    _r3(t, "FCF Margin", _pct(p.fcf_margin), "")
    _r3(t, "EBITDA Margin", _pct(p.ebitda_margin), "")
    return t


def _build_solvency(report: AnalysisReport) -> DataTable:
    s = report.solvency
    t = DataTable(zebra_stripes=True)
    t.add_columns("Metric", "Value", "Assessment")
    _r3(t, "Debt/Equity", _num(s.debt_to_equity), _thr(s.debt_to_equity, [(0.3, "Very Conservative"), (0.5, "Conservative"), (1.0, "Moderate"), (2.0, "High")], "Very High"))
    _r3(t, "Debt/EBITDA", _num(s.debt_to_ebitda), _thr(s.debt_to_ebitda, [(1, "Very Low"), (2, "Manageable"), (3, "Moderate")], "Heavy"))
    _r3(t, "Current Ratio", _num(s.current_ratio), _thr(s.current_ratio, [(1.0, "Liquidity Risk"), (1.5, "Adequate"), (2.0, "Good")], "Strong"))
    _r3(t, "Quick Ratio", _num(s.quick_ratio), "")
    _r3(t, "Interest Coverage", _num(s.interest_coverage, 1), "")
    _r3(t, "Altman Z-Score", _num(s.altman_z_score), _thr(s.altman_z_score, [(1.81, "Distress"), (2.99, "Grey Zone")], "Safe"))
    _r3(t, "Cash Burn Rate (/yr)", _money(s.cash_burn_rate), _burn(s.cash_burn_rate))
    _r3(t, "Cash Runway", f"{s.cash_runway_years:.1f} yrs" if s.cash_runway_years is not None else "N/A", "")
    _r3(t, "Working Capital", _money(s.working_capital), "")
    _r3(t, "Cash Per Share", f"${s.cash_per_share:.2f}" if s.cash_per_share is not None else "N/A", "")
    _r3(t, "NCAV Per Share", f"${s.ncav_per_share:.4f}" if s.ncav_per_share is not None else "N/A", "")
    _r3(t, "Total Debt", _money(s.total_debt), "")
    _r3(t, "Total Cash", _money(s.total_cash), "")
    _r3(t, "Net Debt", _money(s.net_debt), "")
    return t


def _build_growth(report: AnalysisReport) -> DataTable:
    g = report.growth
    t = DataTable(zebra_stripes=True)
    t.add_columns("Metric", "Value")
    _r2(t, "Revenue Growth (YoY)", _pct(g.revenue_growth_yoy))
    _r2(t, "Revenue CAGR (3Y)", _pct(g.revenue_cagr_3y))
    _r2(t, "Revenue CAGR (5Y)", _pct(g.revenue_cagr_5y))
    _r2(t, "Earnings Growth (YoY)", _pct(g.earnings_growth_yoy))
    _r2(t, "Earnings CAGR (3Y)", _pct(g.earnings_cagr_3y))
    _r2(t, "Earnings CAGR (5Y)", _pct(g.earnings_cagr_5y))
    _r2(t, "FCF Growth (YoY)", _pct(g.fcf_growth_yoy))
    _r2(t, "Book Value Growth (YoY)", _pct(g.book_value_growth_yoy))
    _r2(t, "Share Dilution (YoY)", _pct(g.shares_growth_yoy))
    return t


def _build_moat(report: AnalysisReport) -> DataTable:
    m = report.moat
    tier = _get_tier(report)
    t = DataTable(zebra_stripes=True)
    t.add_columns("Indicator", "Assessment")
    _r2(t, "Moat Score", f"{m.moat_score:.1f}/100" if m.moat_score is not None else "N/A")
    _r2(t, "Competitive Position", _s(m.competitive_position))

    if tier in (CompanyTier.MEGA, CompanyTier.LARGE, CompanyTier.MID):
        _r2(t, "ROIC Consistency", _s(m.roic_consistency))
        _r2(t, "Margin Stability", _s(m.margin_stability))
        _r2(t, "Revenue Predictability", _s(m.revenue_predictability))
        _r2(t, "Efficient Scale", _s(m.efficient_scale))
        _r2(t, "Switching Costs", _s(m.switching_costs) if m.switching_costs else "Requires qualitative review")
        _r2(t, "Network Effects", _s(m.network_effects) if m.network_effects else "Requires qualitative review")
        _r2(t, "Cost Advantages", _s(m.cost_advantages) if m.cost_advantages else "Not detected")
        _r2(t, "Intangible Assets", _s(m.intangible_assets) if m.intangible_assets else "Not detected")
    else:
        _r2(t, "Asset Backing", _s(m.asset_backing))
        _r2(t, "Revenue Status", _s(m.revenue_predictability))
        _r2(t, "Niche Position", _s(m.niche_position))
        _r2(t, "Dilution / Insider", _s(m.insider_alignment))
        if m.intangible_assets:
            _r2(t, "Intangible Assets", _s(m.intangible_assets))
        if m.cost_advantages:
            _r2(t, "Cost Advantages", _s(m.cost_advantages))

    if m.roic_history:
        _r2(t, "ROIC Trend", " -> ".join(_pctplain(r) for r in reversed(m.roic_history)))
    if m.gross_margin_history:
        _r2(t, "Gross Margin Trend", " -> ".join(_pctplain(r) for r in reversed(m.gross_margin_history)))
    return t


def _build_iv(report: AnalysisReport) -> DataTable:
    iv = report.intrinsic_value
    t = DataTable(zebra_stripes=True)
    t.add_columns("Method", "Value", "Margin of Safety")
    primary = _s(iv.primary_method)
    secondary = _s(iv.secondary_method)

    def tag(name: str) -> str:
        if name in primary:
            return "(primary) "
        if name in secondary:
            return "(secondary) "
        return ""

    _r3(t, "Current Price", f"${iv.current_price:.2f}" if iv.current_price else "N/A", "")
    _r3(t, f"{tag('DCF')}DCF (10Y)", f"${iv.dcf_value:.2f}" if iv.dcf_value else "N/A", _mos(iv.margin_of_safety_dcf))
    _r3(t, f"{tag('Graham')}Graham Number", f"${iv.graham_number:.2f}" if iv.graham_number else "N/A", _mos(iv.margin_of_safety_graham))
    _r3(t, f"{tag('NCAV')}NCAV (Net-Net)", f"${iv.ncav_value:.4f}" if iv.ncav_value is not None else "N/A", _mos(iv.margin_of_safety_ncav))
    _r3(t, f"{tag('Asset')}Tangible Book/Share", f"${iv.asset_based_value:.4f}" if iv.asset_based_value else "N/A", _mos(iv.margin_of_safety_asset))
    if iv.lynch_fair_value:
        _r3(t, "Lynch Fair Value", f"${iv.lynch_fair_value:.2f}", "")
    return t


def _build_financials(report: AnalysisReport) -> DataTable:
    t = DataTable(zebra_stripes=True)
    t.add_columns("Period", "Revenue", "Gross Profit", "Op Income", "Net Income", "FCF", "Equity", "Debt")
    for st in (report.financials or [])[:5]:
        t.add_row(
            _s(st.period), _money(st.revenue), _money(st.gross_profit),
            _money(st.operating_income), _money(st.net_income),
            _money(st.free_cash_flow), _money(st.total_equity), _money(st.total_debt),
        )
    return t


def _build_filings(report: AnalysisReport) -> DataTable:
    t = DataTable(zebra_stripes=True)
    t.add_columns("Type", "Filed", "Period", "Downloaded")
    for f in (report.filings or [])[:20]:
        t.add_row(_s(f.form_type), _s(f.filing_date), _s(f.period), "Yes" if f.local_path else "No")
    return t


def _build_news(report: AnalysisReport) -> DataTable:
    t = DataTable(zebra_stripes=True)
    t.add_columns("#", "Title", "Source", "Date")
    for i, n in enumerate((report.news or [])[:20], 1):
        title_raw = n.title or ""
        title = title_raw[:70] + ("..." if len(title_raw) > 70 else "")
        t.add_row(str(i), title, _s(n.source), _s(n.published))
    return t


# ======================================================================
# Safe helpers — NEVER raise, ALWAYS return str
# ======================================================================

def _r3(table: DataTable, c1: str, c2: str, c3: str) -> None:
    """Add a 3-column row. Guarantees string values."""
    table.add_row(str(c1), str(c2), str(c3))


def _r2(table: DataTable, c1: str, c2: str) -> None:
    """Add a 2-column row. Guarantees string values."""
    table.add_row(str(c1), str(c2))


def _s(val) -> str:
    if val is None:
        return "N/A"
    return str(val)


def _num(val, digits: int = 2) -> str:
    if val is None:
        return "N/A"
    try:
        return f"{float(val):,.{digits}f}"
    except Exception:
        return "N/A"


def _pct(val) -> str:
    if val is None:
        return "N/A"
    try:
        return f"{float(val) * 100:.2f}%"
    except Exception:
        return "N/A"


def _pctplain(val) -> str:
    if val is None:
        return "N/A"
    try:
        return f"{float(val) * 100:.1f}%"
    except Exception:
        return "N/A"


def _money(val) -> str:
    if val is None:
        return "N/A"
    try:
        v = float(val)
        if abs(v) >= 1e12:
            return f"${v / 1e12:,.2f}T"
        if abs(v) >= 1e9:
            return f"${v / 1e9:,.2f}B"
        if abs(v) >= 1e6:
            return f"${v / 1e6:,.2f}M"
        return f"${v:,.0f}"
    except Exception:
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
    except Exception:
        return "N/A"


def _ape(val) -> str:
    if val is None:
        return ""
    try:
        v = float(val)
        if v < 0: return "Negative earnings"
        if v < 10: return "Very cheap"
        if v < 15: return "Value range"
        if v < 20: return "Fair"
        if v < 30: return "Expensive"
        return "Very expensive"
    except Exception:
        return ""


def _burn(val) -> str:
    if val is None:
        return ""
    try:
        v = float(val)
        if v == 0: return "Not burning cash"
        if v < 0: return "Burning cash"
        return "Cash flow positive"
    except Exception:
        return ""


def _thr(val, thresholds: list[tuple], over_label: str) -> str:
    if val is None:
        return ""
    try:
        v = float(val)
        for threshold, label in thresholds:
            if v < threshold:
                return label
        return over_label
    except Exception:
        return ""


def _safe_tier(tier) -> str:
    if isinstance(tier, CompanyTier):
        return tier.value
    return str(tier) if tier else "N/A"


def _get_tier(report: AnalysisReport) -> CompanyTier:
    try:
        tier = report.profile.tier
        if isinstance(tier, CompanyTier):
            return tier
    except Exception:
        pass
    return CompanyTier.NANO


def run_tui() -> None:
    """Launch the Textual UI."""
    app = LynxApp()
    app.run()
