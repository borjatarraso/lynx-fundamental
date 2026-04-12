"""Textual UI for Lynx Fundamental Analysis."""

from __future__ import annotations

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import (
    DataTable,
    Footer,
    Header,
    Input,
    Label,
    LoadingIndicator,
    Static,
    TabbedContent,
    TabPane,
)

from lynx.models import AnalysisReport


class SearchModal(ModalScreen[str]):
    """Modal dialog for entering a ticker/ISIN."""

    BINDINGS = [Binding("escape", "dismiss_modal", "Cancel")]

    def compose(self) -> ComposeResult:
        with Vertical(id="search-dialog"):
            yield Label("Enter Ticker or ISIN", id="search-label")
            yield Input(placeholder="e.g. AAPL, MSFT, US0378331005", id="search-input")
            yield Label("[dim]Press Enter to analyze, Escape to cancel[/]", id="search-hint")

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.value.strip():
            self.dismiss(event.value.strip())

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
    #welcome {
        text-align: center;
        margin: 4;
    }
    .metric-row {
        height: 1;
    }
    #profile-panel {
        height: auto;
        max-height: 12;
        margin: 0 0 1 0;
    }
    #loading-container {
        align: center middle;
        height: 100%;
    }
    LoadingIndicator {
        height: 3;
    }
    """

    BINDINGS = [
        Binding("a", "analyze", "Analyze"),
        Binding("q", "quit", "Quit"),
        Binding("r", "refresh", "Refresh"),
        Binding("d", "dark", "Toggle Dark"),
    ]

    report: AnalysisReport | None = None

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static(
            "[bold blue]"
            "  LYNX FA  [/]\n\n"
            "[bold]Fundamental Analysis Tool[/]\n"
            "[dim]Press [bold]A[/bold] to analyze a stock, [bold]Q[/bold] to quit[/]",
            id="welcome",
        )
        yield Footer()

    def action_analyze(self) -> None:
        self.push_screen(SearchModal(), self._on_search_result)

    def action_dark(self) -> None:
        self.theme = "textual-dark" if self.theme == "textual-light" else "textual-light"

    def action_refresh(self) -> None:
        if self.report:
            self._show_report(self.report)

    def _on_search_result(self, identifier: str) -> None:
        if not identifier:
            return
        self._run_analysis(identifier)

    def _run_analysis(self, identifier: str) -> None:
        # Show loading state
        welcome = self.query_one("#welcome", Static)
        welcome.update(f"[bold cyan]Analyzing {identifier}...[/]\n\n[dim]Fetching data, please wait...[/]")

        # Run in a worker thread to avoid blocking the UI
        self.run_worker(self._do_analysis(identifier), name="analysis")

    async def _do_analysis(self, identifier: str) -> None:
        from lynx.core.analyzer import run_full_analysis

        try:
            report = await self._run_in_thread(identifier)
            self.report = report
            self.call_from_thread(self._show_report, report)
        except Exception as e:
            self.call_from_thread(self._show_error, str(e))

    def _run_in_thread(self, identifier: str):
        """Wrapper to run sync analysis in a thread."""
        import asyncio
        loop = asyncio.get_event_loop()
        from lynx.core.analyzer import run_full_analysis
        return loop.run_in_executor(
            None,
            lambda: run_full_analysis(identifier, download_reports=True, download_news=True),
        )

    def _show_error(self, msg: str) -> None:
        welcome = self.query_one("#welcome", Static)
        welcome.update(f"[bold red]Error:[/] {msg}\n\n[dim]Press A to try again[/]")

    def _show_report(self, report: AnalysisReport) -> None:
        # Remove the welcome screen and replace with tabs
        welcome = self.query_one("#welcome", Static)
        welcome.remove()

        p = report.profile
        tier_str = p.tier.value if hasattr(p.tier, 'value') else str(p.tier)
        profile_text = (
            f"[bold]{p.name}[/] ({p.ticker})  [{tier_str}]"
            + (f"  |  ISIN: {p.isin}" if p.isin else "")
            + f"\n{p.sector or 'N/A'} / {p.industry or 'N/A'}  |  {p.country or 'N/A'}"
            + f"  |  Market Cap: {_fmt_money(p.market_cap)}"
        )

        content = Vertical(
            Static(profile_text, id="profile-panel"),
            TabbedContent(
                TabPane("Valuation", self._build_valuation_table(report), id="tab-val"),
                TabPane("Profitability", self._build_profitability_table(report), id="tab-prof"),
                TabPane("Solvency", self._build_solvency_table(report), id="tab-solv"),
                TabPane("Growth", self._build_growth_table(report), id="tab-growth"),
                TabPane("Moat", self._build_moat_table(report), id="tab-moat"),
                TabPane("Intrinsic Value", self._build_iv_table(report), id="tab-iv"),
                TabPane("Financials", self._build_financials_table(report), id="tab-fin"),
                TabPane("Filings", self._build_filings_table(report), id="tab-filings"),
                TabPane("News", self._build_news_table(report), id="tab-news"),
            ),
        )

        self.mount(content, before=self.query_one(Footer))

    def _build_valuation_table(self, report: AnalysisReport) -> DataTable:
        v = report.valuation
        table = DataTable(zebra_stripes=True)
        table.add_columns("Metric", "Value", "Assessment")
        rows = [
            ("P/E (Trailing)", _fn(v.pe_trailing), _a_pe(v.pe_trailing)),
            ("P/E (Forward)", _fn(v.pe_forward), _a_pe(v.pe_forward)),
            ("P/B Ratio", _fn(v.pb_ratio), _a_simple(v.pb_ratio, [(1, "Below Book"), (1.5, "Cheap"), (3, "Fair")], "Premium")),
            ("P/S Ratio", _fn(v.ps_ratio), ""),
            ("P/FCF", _fn(v.p_fcf), _a_simple(v.p_fcf, [(10, "Cheap"), (20, "Fair")], "Expensive")),
            ("EV/EBITDA", _fn(v.ev_ebitda), _a_simple(v.ev_ebitda, [(8, "Cheap"), (12, "Fair"), (18, "Expensive")], "Very Expensive")),
            ("EV/Revenue", _fn(v.ev_revenue), ""),
            ("PEG Ratio", _fn(v.peg_ratio), _a_simple(v.peg_ratio, [(1, "Undervalued"), (2, "Fair")], "Overvalued")),
            ("Earnings Yield", _fp(v.earnings_yield), ""),
            ("Dividend Yield", _fp(v.dividend_yield), ""),
            ("Enterprise Value", _fmt_money(v.enterprise_value), ""),
            ("Market Cap", _fmt_money(v.market_cap), ""),
        ]
        for r in rows:
            table.add_row(*r)
        return table

    def _build_profitability_table(self, report: AnalysisReport) -> DataTable:
        p = report.profitability
        table = DataTable(zebra_stripes=True)
        table.add_columns("Metric", "Value", "Assessment")
        rows = [
            ("ROE", _fp(p.roe), _a_simple(p.roe, [(0.10, "Below Avg"), (0.15, "Good"), (0.20, "Excellent")], "Outstanding") if p.roe else ""),
            ("ROA", _fp(p.roa), ""),
            ("ROIC", _fp(p.roic), _a_roic(p.roic)),
            ("Gross Margin", _fp(p.gross_margin), ""),
            ("Operating Margin", _fp(p.operating_margin), ""),
            ("Net Margin", _fp(p.net_margin), ""),
            ("FCF Margin", _fp(p.fcf_margin), ""),
            ("EBITDA Margin", _fp(p.ebitda_margin), ""),
        ]
        for r in rows:
            table.add_row(*r)
        return table

    def _build_solvency_table(self, report: AnalysisReport) -> DataTable:
        s = report.solvency
        table = DataTable(zebra_stripes=True)
        table.add_columns("Metric", "Value", "Assessment")
        rows = [
            ("Debt/Equity", _fn(s.debt_to_equity), ""),
            ("Debt/EBITDA", _fn(s.debt_to_ebitda), ""),
            ("Current Ratio", _fn(s.current_ratio), ""),
            ("Quick Ratio", _fn(s.quick_ratio), ""),
            ("Interest Coverage", _fn(s.interest_coverage), ""),
            ("Altman Z-Score", _fn(s.altman_z_score), _a_zscore(s.altman_z_score)),
            ("Total Debt", _fmt_money(s.total_debt), ""),
            ("Total Cash", _fmt_money(s.total_cash), ""),
            ("Net Debt", _fmt_money(s.net_debt), ""),
        ]
        for r in rows:
            table.add_row(*r)
        return table

    def _build_growth_table(self, report: AnalysisReport) -> DataTable:
        g = report.growth
        table = DataTable(zebra_stripes=True)
        table.add_columns("Metric", "Value")
        rows = [
            ("Revenue Growth (YoY)", _fp(g.revenue_growth_yoy)),
            ("Revenue CAGR (3Y)", _fp(g.revenue_cagr_3y)),
            ("Revenue CAGR (5Y)", _fp(g.revenue_cagr_5y)),
            ("Earnings Growth (YoY)", _fp(g.earnings_growth_yoy)),
            ("Earnings CAGR (3Y)", _fp(g.earnings_cagr_3y)),
            ("Earnings CAGR (5Y)", _fp(g.earnings_cagr_5y)),
            ("FCF Growth (YoY)", _fp(g.fcf_growth_yoy)),
            ("Book Value Growth (YoY)", _fp(g.book_value_growth_yoy)),
        ]
        for r in rows:
            table.add_row(*r)
        return table

    def _build_moat_table(self, report: AnalysisReport) -> DataTable:
        m = report.moat
        table = DataTable(zebra_stripes=True)
        table.add_columns("Indicator", "Assessment")
        rows = [
            ("Moat Score", f"{m.moat_score:.1f}/100" if m.moat_score is not None else "N/A"),
            ("Competitive Position", m.competitive_position or "N/A"),
            ("ROIC Consistency", m.roic_consistency or "N/A"),
            ("Margin Stability", m.margin_stability or "N/A"),
            ("Revenue Predictability", m.revenue_predictability or "N/A"),
            ("Efficient Scale", m.efficient_scale or "N/A"),
            ("Switching Costs", m.switching_costs or "Requires qualitative review"),
            ("Network Effects", m.network_effects or "Requires qualitative review"),
            ("Cost Advantages", m.cost_advantages or "Not detected"),
            ("Intangible Assets", m.intangible_assets or "Not detected"),
        ]
        if m.roic_history:
            hist = " -> ".join(_fp_plain(r) for r in reversed(m.roic_history))
            rows.append(("ROIC Trend", hist))
        if m.gross_margin_history:
            hist = " -> ".join(_fp_plain(r) for r in reversed(m.gross_margin_history))
            rows.append(("Gross Margin Trend", hist))
        for r in rows:
            table.add_row(*r)
        return table

    def _build_iv_table(self, report: AnalysisReport) -> DataTable:
        iv = report.intrinsic_value
        table = DataTable(zebra_stripes=True)
        table.add_columns("Method", "Value", "Margin of Safety")
        rows = [
            ("Current Price", f"${iv.current_price:.2f}" if iv.current_price else "N/A", ""),
            ("DCF (10Y, 10%)", f"${iv.dcf_value:.2f}" if iv.dcf_value else "N/A", _mos(iv.margin_of_safety_dcf)),
            ("Graham Number", f"${iv.graham_number:.2f}" if iv.graham_number else "N/A", _mos(iv.margin_of_safety_graham)),
            ("Lynch Fair Value", f"${iv.lynch_fair_value:.2f}" if iv.lynch_fair_value else "N/A", ""),
        ]
        for r in rows:
            table.add_row(*r)
        return table

    def _build_financials_table(self, report: AnalysisReport) -> DataTable:
        table = DataTable(zebra_stripes=True)
        table.add_columns("Period", "Revenue", "Gross Profit", "Op Income", "Net Income", "FCF", "Equity", "Debt")
        for s in report.financials[:5]:
            table.add_row(
                s.period,
                _fmt_money(s.revenue),
                _fmt_money(s.gross_profit),
                _fmt_money(s.operating_income),
                _fmt_money(s.net_income),
                _fmt_money(s.free_cash_flow),
                _fmt_money(s.total_equity),
                _fmt_money(s.total_debt),
            )
        return table

    def _build_filings_table(self, report: AnalysisReport) -> DataTable:
        table = DataTable(zebra_stripes=True)
        table.add_columns("Type", "Filed", "Period", "Downloaded")
        for f in report.filings[:20]:
            table.add_row(f.form_type, f.filing_date, f.period, "Yes" if f.local_path else "No")
        return table

    def _build_news_table(self, report: AnalysisReport) -> DataTable:
        table = DataTable(zebra_stripes=True)
        table.add_columns("#", "Title", "Source", "Date")
        for i, n in enumerate(report.news[:20], 1):
            title = n.title[:70] + ("..." if len(n.title) > 70 else "")
            table.add_row(str(i), title, n.source or "", n.published or "")
        return table


# Plain text formatters (no Rich markup — for Textual DataTable)

def _fn(val, digits: int = 2) -> str:
    if val is None: return "N/A"
    return f"{val:,.{digits}f}"

def _fp(val) -> str:
    if val is None: return "N/A"
    return f"{val * 100:.2f}%"

def _fp_plain(val) -> str:
    if val is None: return "N/A"
    return f"{val * 100:.1f}%"

def _fmt_money(val) -> str:
    if val is None: return "N/A"
    if abs(val) >= 1_000_000_000_000: return f"${val / 1_000_000_000_000:,.2f}T"
    if abs(val) >= 1_000_000_000: return f"${val / 1_000_000_000:,.2f}B"
    if abs(val) >= 1_000_000: return f"${val / 1_000_000:,.2f}M"
    return f"${val:,.0f}"

def _mos(val) -> str:
    if val is None: return "N/A"
    pct = val * 100
    if pct > 25: return f"{pct:.1f}% (Undervalued)"
    if pct > 0: return f"{pct:.1f}% (Slight Undervalue)"
    return f"{pct:.1f}% (Overvalued)"

def _a_pe(val) -> str:
    if val is None: return ""
    if val < 0: return "Negative earnings"
    if val < 10: return "Very cheap"
    if val < 15: return "Value range"
    if val < 20: return "Fair"
    if val < 30: return "Expensive"
    return "Very expensive"

def _a_roic(val) -> str:
    if val is None: return ""
    if val > 0.15: return "Wide moat signal"
    if val > 0.10: return "Good"
    if val > 0.07: return "Average"
    return "Below WACC"

def _a_zscore(val) -> str:
    if val is None: return ""
    if val > 2.99: return "Safe"
    if val > 1.81: return "Grey zone"
    return "Distress"

def _a_simple(val, thresholds, over_label) -> str:
    if val is None: return ""
    for threshold, label in thresholds:
        if val < threshold:
            return label
    return over_label


def run_tui() -> None:
    """Launch the Textual UI."""
    app = LynxApp()
    app.run()
