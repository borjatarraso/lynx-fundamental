"""Textual UI for Lynx Fundamental Analysis."""

from __future__ import annotations

import webbrowser

from textual import work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import (
    Button,
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


# ======================================================================
# About modal
# ======================================================================

class AboutModal(ModalScreen):
    BINDINGS = [Binding("escape", "dismiss_modal", "Close")]

    def compose(self) -> ComposeResult:
        from lynx import get_about_text
        about = get_about_text()
        with Vertical(id="about-dialog"):
            yield Label(
                f"[bold blue]{about['name']}[/]",
                id="about-title",
            )
            yield Static(
                f"Version {about['version']} ({about['year']})\n\n"
                f"[bold]Developed by:[/] {about['author']}\n"
                f"[bold]Contact:[/]      {about['email']}\n"
                f"[bold]License:[/]      {about['license']}\n\n"
                f"{about['description']}\n\n"
                f"[dim]{about['license_text']}[/]",
                id="about-content",
            )
            yield Label(
                "[dim]Press Escape to close[/]",
                id="about-hint",
            )

    def action_dismiss_modal(self) -> None:
        self.dismiss()


# ======================================================================
# Explain modal
# ======================================================================

class ExplainModal(ModalScreen):
    BINDINGS = [Binding("escape", "dismiss_modal", "Close")]

    def __init__(self, metric_key: str, **kwargs) -> None:
        super().__init__(**kwargs)
        self._key = metric_key

    def compose(self) -> ComposeResult:
        from lynx.metrics.explanations import get_explanation
        exp = get_explanation(self._key)
        if exp:
            content = (
                f"[bold]{exp.full_name}[/]\n\n"
                f"{exp.description}\n\n"
                f"[bold cyan]Why it matters:[/]\n{exp.why_used}\n\n"
                f"[bold cyan]Formula:[/]\n[bold]{exp.formula}[/]\n\n"
                f"[dim]Category: {exp.category}[/]"
            )
        else:
            content = f"No explanation available for '{self._key}'."
        with Vertical(id="explain-dialog"):
            yield Label(f"[bold]Metric: {self._key}[/]", id="explain-title")
            yield Static(content, id="explain-content")
            yield Label("[dim]Press Escape to close[/]", id="explain-hint")

    def action_dismiss_modal(self) -> None:
        self.dismiss()


# ======================================================================
# Metric list modal (for browsing explanations)
# ======================================================================

class MetricListModal(ModalScreen[str]):
    BINDINGS = [Binding("escape", "dismiss_modal", "Close")]

    def compose(self) -> ComposeResult:
        from lynx.metrics.explanations import list_metrics
        with Vertical(id="metric-list-dialog"):
            yield Label("[bold]Select a metric to explain[/]", id="metric-list-title")
            t = DataTable(zebra_stripes=True, cursor_type="row", id="metric-list-table")
            t.add_columns("Key", "Name", "Category")
            for m in list_metrics():
                t.add_row(m.key, m.full_name, m.category)
            yield t
            yield Label("[dim]Press Enter to explain, Escape to close[/]", id="metric-list-hint")

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        from lynx.metrics.explanations import list_metrics
        metrics = list_metrics()
        idx = event.cursor_row
        if 0 <= idx < len(metrics):
            self.dismiss(metrics[idx].key)

    def action_dismiss_modal(self) -> None:
        self.dismiss("")


# ======================================================================
# Search modal
# ======================================================================

class SearchModal(ModalScreen[str]):
    BINDINGS = [Binding("escape", "dismiss_modal", "Cancel")]

    def compose(self) -> ComposeResult:
        with Vertical(id="search-dialog"):
            yield Label("Enter Ticker or ISIN", id="search-label")
            yield Input(
                placeholder="e.g. AAPL, MSFT, OCO.V, AT1.DE",
                id="search-input",
            )
            yield Label(
                "[dim]Press Enter to analyze, Escape to cancel[/]",
                id="search-hint",
            )

    def on_input_submitted(self, event: Input.Submitted) -> None:
        value = (event.value or "").strip()
        if len(value) > 100:
            value = value[:100]
        self.dismiss(value)

    def action_dismiss_modal(self) -> None:
        self.dismiss("")


# ======================================================================
# News browser dialog
# ======================================================================

class NewsBrowserDialog(ModalScreen):
    """Dialog shown after opening a news article in the browser."""
    BINDINGS = [Binding("escape", "dismiss_modal", "Close")]

    def compose(self) -> ComposeResult:
        with Vertical(id="news-dialog"):
            yield Label(
                "[bold]News article opened in your default browser.[/]",
                id="news-dialog-label",
            )
            with Horizontal(id="news-dialog-buttons"):
                yield Button("OK", id="news-ok-btn", variant="primary")
                yield Button("Do not show again", id="news-suppress-btn", variant="default")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "news-suppress-btn":
            self.dismiss("suppress")
        else:
            self.dismiss("ok")

    def action_dismiss_modal(self) -> None:
        self.dismiss("ok")


# ======================================================================
# Download result dialog
# ======================================================================

class DownloadResultDialog(ModalScreen):
    """Dialog showing filing download result."""
    BINDINGS = [Binding("escape", "dismiss_modal", "Close")]

    def __init__(self, message: str, success: bool = True, **kwargs) -> None:
        super().__init__(**kwargs)
        self._message = message
        self._success = success

    def compose(self) -> ComposeResult:
        style = "bold green" if self._success else "bold red"
        with Vertical(id="download-dialog"):
            yield Label(
                f"[{style}]{self._message}[/]",
                id="download-dialog-label",
            )
            yield Button("OK", id="download-ok-btn", variant="primary")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss()

    def action_dismiss_modal(self) -> None:
        self.dismiss()


# ======================================================================
# Report view — uses compose() so Textual properly initialises widgets
# ======================================================================

class ReportView(Vertical):
    """Widget that renders a full analysis report using TabbedContent."""

    def __init__(self, report: AnalysisReport, **kwargs) -> None:
        super().__init__(**kwargs)
        self._report = report

    def compose(self) -> ComposeResult:
        r = self._report
        p = r.profile

        tier_str = _safe_tier(p.tier)
        profile_text = (
            f"[bold]{_s(p.name)}[/] ({_s(p.ticker)})  [{tier_str}]"
            + (f"  |  ISIN: {p.isin}" if p.isin else "")
            + f"\n{_s(p.sector)} / {_s(p.industry)}"
            + f"  |  {_s(p.country)}"
            + f"  |  Market Cap: {_money(p.market_cap)}"
        )
        yield Static(profile_text)

        with TabbedContent():
            with TabPane("Valuation"):
                yield _build_valuation(r)
            with TabPane("Profitability"):
                yield _build_profitability(r)
            with TabPane("Solvency"):
                yield _build_solvency(r)
            with TabPane("Growth"):
                yield _build_growth(r)
            with TabPane("Moat"):
                yield _build_moat(r)
            with TabPane("Intrinsic Value"):
                yield _build_iv(r)
            with TabPane("Conclusion"):
                yield _build_conclusion(r)
            with TabPane("Financials"):
                yield _build_financials(r)
            with TabPane("Filings"):
                yield _build_filings(r)
                yield Static(
                    "[dim]Select a row and press [bold]Enter[/bold] to download filing[/]",
                )
            with TabPane("News"):
                yield _build_news(r)
                yield Static(
                    "[dim]Select a row and press [bold]Enter[/bold] to open in browser[/]",
                )


# ======================================================================
# Main application
# ======================================================================

class LynxApp(App):
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
    ReportView {
        height: 1fr;
    }
    #about-dialog {
        width: 80;
        height: auto;
        max-height: 40;
        border: thick $accent;
        background: $surface;
        padding: 1 2;
        margin: 2 4;
    }
    #about-title {
        text-align: center;
        text-style: bold;
        margin-bottom: 1;
    }
    #about-content {
        margin: 0 2;
    }
    #about-hint {
        text-align: center;
        margin-top: 1;
    }
    #news-dialog, #download-dialog {
        width: 60;
        height: auto;
        max-height: 10;
        border: thick $accent;
        background: $surface;
        padding: 1 2;
        margin: 6 10;
    }
    #news-dialog-label, #download-dialog-label {
        text-align: center;
        margin-bottom: 1;
    }
    #news-dialog-buttons {
        align-horizontal: center;
        height: auto;
    }
    #news-dialog-buttons Button {
        margin: 0 1;
    }
    #download-ok-btn {
        margin: 0 auto;
    }
    #explain-dialog {
        width: 80;
        height: auto;
        max-height: 35;
        border: thick $accent;
        background: $surface;
        padding: 1 2;
        margin: 2 4;
    }
    #explain-title {
        text-align: center;
        text-style: bold;
        margin-bottom: 1;
    }
    #explain-content {
        margin: 0 2;
    }
    #explain-hint {
        text-align: center;
        margin-top: 1;
    }
    #metric-list-dialog {
        width: 90;
        height: 35;
        border: thick $accent;
        background: $surface;
        padding: 1 2;
        margin: 2 4;
    }
    #metric-list-title {
        text-align: center;
        text-style: bold;
        margin-bottom: 1;
    }
    #metric-list-hint {
        text-align: center;
        margin-top: 1;
    }
    """

    BINDINGS = [
        Binding("a", "analyze", "Analyze"),
        Binding("q", "quit", "Quit"),
        Binding("r", "refresh", "Refresh"),
        Binding("d", "dark", "Toggle Dark"),
        Binding("f1", "about", "About"),
        Binding("e", "explain", "Explain Metric"),
        Binding("tab", "focus_next", "Next Tab", show=True),
        Binding("shift+tab", "focus_previous", "Prev Tab", show=True),
        Binding("escape", "app.focus('status-area')", "Back", show=False),
    ]

    report: AnalysisReport | None = None
    _last_identifier: str = ""
    _suppress_news_dialog: bool = False

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static(
            "[bold blue]  LYNX FA  [/]\n\n"
            "[bold]Fundamental Analysis Tool[/]\n"
            "[dim]Press [bold]A[/bold] to analyze a stock, "
            "[bold]Q[/bold] to quit[/]\n\n"
            "[dim]Navigation: [bold]Tab[/bold]/[bold]Shift+Tab[/bold] switch tabs  "
            "[bold]\u2190\u2191\u2192\u2193[/bold] arrow keys navigate  "
            "[bold]Escape[/bold] go back[/]",
            id="status-area",
        )
        yield Footer()

    def action_about(self) -> None:
        self.push_screen(AboutModal())

    def action_explain(self) -> None:
        self.push_screen(MetricListModal(), self._on_explain_result)

    def _on_explain_result(self, key: str) -> None:
        if key:
            self.push_screen(ExplainModal(key))

    def action_analyze(self) -> None:
        self.push_screen(SearchModal(), self._on_search_result)

    def action_dark(self) -> None:
        self.theme = (
            "textual-dark"
            if self.theme == "textual-light"
            else "textual-light"
        )

    def action_refresh(self) -> None:
        if self._last_identifier:
            self._start_analysis(self._last_identifier, force_refresh=True)

    def _on_search_result(self, identifier: str) -> None:
        if identifier:
            self._start_analysis(identifier)

    def _start_analysis(self, identifier: str, force_refresh: bool = False) -> None:
        self._last_identifier = identifier
        self._set_status(
            f"[bold cyan]Analyzing {identifier}...[/]\n\n"
            "[dim]Fetching data, please wait...[/]"
        )
        self._do_analysis(identifier, force_refresh)

    @work(thread=True, exclusive=True)
    def _do_analysis(self, identifier: str, force_refresh: bool = False) -> None:
        from lynx.core.analyzer import run_full_analysis
        from lynx.core.storage import is_testing

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
            msg = str(e) if str(e) else type(e).__name__
            self.call_from_thread(
                self._set_status,
                f"[bold red]Error:[/] {msg}\n\n"
                "[dim]Press A to try again[/]",
            )

    def _set_status(self, message: str) -> None:
        self._remove_reports()
        try:
            sa = self.query_one("#status-area", Static)
            sa.update(message)
            sa.display = True
        except Exception:
            pass

    def _remove_reports(self) -> None:
        try:
            for w in list(self.query(ReportView)):
                w.remove()
        except Exception:
            pass

    def _render_report(self, report: AnalysisReport) -> None:
        try:
            self._remove_reports()
            try:
                self.query_one("#status-area", Static).display = False
            except Exception:
                pass
            view = ReportView(report)
            self.mount(view, before=self.query_one(Footer))
        except Exception as e:
            self._set_status(
                f"[bold red]Display error:[/] {type(e).__name__}: {e}\n\n"
                "[dim]Press A to try again[/]"
            )

    # --- DataTable row selection handlers ---

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Handle Enter on a selected row in Filings or News tables."""
        if not self.report:
            return

        # Determine which tab we're in by checking parent TabPane
        table = event.data_table
        tab_pane = table.ancestors_with_self
        tab_label = ""
        for ancestor in table.ancestors_with_self:
            if isinstance(ancestor, TabPane):
                tab_label = ancestor._label  # internal label text
                break

        row_idx = event.cursor_row

        if "Filing" in str(tab_label):
            self._download_filing(row_idx)
        elif "News" in str(tab_label):
            self._open_news(row_idx)

    def _download_filing(self, row_idx: int) -> None:
        if not self.report or not self.report.filings:
            return
        filings = self.report.filings[:20]
        if row_idx < 0 or row_idx >= len(filings):
            return
        filing = filings[row_idx]
        self._do_download_filing(filing)

    @work(thread=True)
    def _do_download_filing(self, filing) -> None:
        from lynx.core.reports import download_filing
        try:
            path = download_filing(self.report.profile.ticker, filing)
            if path:
                self.call_from_thread(
                    self.push_screen,
                    DownloadResultDialog(
                        f"Filing {filing.form_type} ({filing.filing_date}) downloaded.\n"
                        f"Saved to: {path}",
                        success=True,
                    ),
                )
            else:
                self.call_from_thread(
                    self.push_screen,
                    DownloadResultDialog(
                        f"Failed to download {filing.form_type} ({filing.filing_date}).",
                        success=False,
                    ),
                )
        except Exception as e:
            self.call_from_thread(
                self.push_screen,
                DownloadResultDialog(f"Download error: {e}", success=False),
            )

    def _open_news(self, row_idx: int) -> None:
        if not self.report or not self.report.news:
            return
        articles = self.report.news[:20]
        if row_idx < 0 or row_idx >= len(articles):
            return
        article = articles[row_idx]
        if not article.url:
            return

        try:
            webbrowser.open(article.url)
        except Exception:
            pass

        if not self._suppress_news_dialog:
            self.push_screen(
                NewsBrowserDialog(),
                self._on_news_dialog_result,
            )

    def _on_news_dialog_result(self, result: str) -> None:
        if result == "suppress":
            self._suppress_news_dialog = True


# ======================================================================
# Table builders
# ======================================================================

def _build_valuation(r: AnalysisReport) -> DataTable:
    v = r.valuation
    t = DataTable(zebra_stripes=True)
    t.add_columns("Metric", "Value", "Assessment")
    _r3(t, "P/E (Trailing)", _num(v.pe_trailing), _ape(v.pe_trailing))
    _r3(t, "P/E (Forward)", _num(v.pe_forward), _ape(v.pe_forward))
    _r3(t, "P/B Ratio", _num(v.pb_ratio), _thr(v.pb_ratio, [(1, "Below Book"), (1.5, "Cheap"), (3, "Fair")], "Premium"))
    _r3(t, "P/S Ratio", _num(v.ps_ratio), "")
    _r3(t, "P/FCF", _num(v.p_fcf), _thr(v.p_fcf, [(10, "Cheap"), (20, "Fair")], "Expensive"))
    _r3(t, "EV/EBITDA", _num(v.ev_ebitda), _thr(v.ev_ebitda, [(8, "Cheap"), (12, "Fair"), (18, "Expensive")], "Very Expensive"))
    _r3(t, "EV/Revenue", _num(v.ev_revenue), _thr(v.ev_revenue, [(1, "Very cheap"), (3, "Cheap"), (5, "Fair"), (8, "Expensive")], "Very expensive"))
    _r3(t, "PEG Ratio", _num(v.peg_ratio), _thr(v.peg_ratio, [(1, "Undervalued"), (2, "Fair")], "Overvalued"))
    _r3(t, "Earnings Yield", _pct(v.earnings_yield), _yield_assess(v.earnings_yield))
    _r3(t, "Dividend Yield", _pct(v.dividend_yield), _div_assess(v.dividend_yield))
    _r3(t, "P/Tangible Book", _num(v.price_to_tangible_book), _thr(v.price_to_tangible_book, [(0.67, "Deep Value"), (1, "Below Book"), (1.5, "Near Book")], "Premium"))
    _r3(t, "P/NCAV (Net-Net)", _num(v.price_to_ncav), _thr(v.price_to_ncav, [(0.67, "Classic Net-Net"), (1, "Below NCAV"), (1.5, "Near NCAV")], "Above NCAV"))
    _r3(t, "Enterprise Value", _money(v.enterprise_value), "")
    _r3(t, "Market Cap", _money(v.market_cap), "")
    return t


def _build_profitability(r: AnalysisReport) -> DataTable:
    p = r.profitability
    t = DataTable(zebra_stripes=True)
    t.add_columns("Metric", "Value", "Assessment")
    _r3(t, "ROE", _pct(p.roe), _thr(p.roe, [(0, "Negative"), (0.10, "Below Avg"), (0.15, "Good"), (0.20, "Excellent")], "Outstanding"))
    _r3(t, "ROA", _pct(p.roa), _thr(p.roa, [(0, "Negative"), (0.05, "Low"), (0.10, "Good")], "Excellent"))
    _r3(t, "ROIC", _pct(p.roic), _thr(p.roic, [(0, "Negative"), (0.07, "Below WACC"), (0.10, "Good"), (0.15, "Wide Moat")], "Exceptional"))
    _r3(t, "Gross Margin", _pct(p.gross_margin), "")
    _r3(t, "Operating Margin", _pct(p.operating_margin), _margin_assess(p.operating_margin, 0.25, 0.15, 0.05))
    _r3(t, "Net Margin", _pct(p.net_margin), _margin_assess(p.net_margin, 0.20, 0.10, 0.05))
    _r3(t, "FCF Margin", _pct(p.fcf_margin), _margin_assess(p.fcf_margin, 0.20, 0.10, 0.05))
    _r3(t, "EBITDA Margin", _pct(p.ebitda_margin), _margin_assess(p.ebitda_margin, 0.30, 0.15, 0.05))
    return t


def _build_solvency(r: AnalysisReport) -> DataTable:
    s = r.solvency
    t = DataTable(zebra_stripes=True)
    t.add_columns("Metric", "Value", "Assessment")
    _r3(t, "Debt/Equity", _num(s.debt_to_equity), _thr(s.debt_to_equity, [(0.3, "Very Conservative"), (0.5, "Conservative"), (1.0, "Moderate"), (2.0, "High")], "Very High"))
    _r3(t, "Debt/EBITDA", _num(s.debt_to_ebitda), _thr(s.debt_to_ebitda, [(1, "Very Low"), (2, "Manageable"), (3, "Moderate")], "Heavy"))
    _r3(t, "Current Ratio", _num(s.current_ratio), _thr(s.current_ratio, [(1.0, "Liquidity Risk"), (1.5, "Adequate"), (2.0, "Good")], "Strong"))
    _r3(t, "Quick Ratio", _num(s.quick_ratio), "")
    _r3(t, "Interest Coverage", _num(s.interest_coverage, 1), _thr(s.interest_coverage, [(1, "Cannot cover"), (2, "Tight"), (4, "Adequate"), (8, "Strong")], "Very strong"))
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


def _build_growth(r: AnalysisReport) -> DataTable:
    g = r.growth
    t = DataTable(zebra_stripes=True)
    t.add_columns("Metric", "Value", "Assessment")
    _r3(t, "Revenue Growth (YoY)", _pct(g.revenue_growth_yoy), _growth_assess(g.revenue_growth_yoy))
    _r3(t, "Revenue CAGR (3Y)", _pct(g.revenue_cagr_3y), _cagr_assess(g.revenue_cagr_3y))
    _r3(t, "Revenue CAGR (5Y)", _pct(g.revenue_cagr_5y), _cagr_assess(g.revenue_cagr_5y))
    _r3(t, "Earnings Growth (YoY)", _pct(g.earnings_growth_yoy), _growth_assess(g.earnings_growth_yoy))
    _r3(t, "Earnings CAGR (3Y)", _pct(g.earnings_cagr_3y), _cagr_assess(g.earnings_cagr_3y))
    _r3(t, "Earnings CAGR (5Y)", _pct(g.earnings_cagr_5y), _cagr_assess(g.earnings_cagr_5y))
    _r3(t, "FCF Growth (YoY)", _pct(g.fcf_growth_yoy), _growth_assess(g.fcf_growth_yoy))
    _r3(t, "Book Value Growth (YoY)", _pct(g.book_value_growth_yoy), _growth_assess(g.book_value_growth_yoy))
    _r3(t, "Share Dilution (YoY)", _pct(g.shares_growth_yoy), _dilution_assess(g.shares_growth_yoy))
    return t


def _build_moat(r: AnalysisReport) -> DataTable:
    m = r.moat
    tier = _get_tier(r)
    t = DataTable(zebra_stripes=True)
    t.add_columns("Indicator", "Assessment")
    _r2(t, "Score", f"{m.moat_score:.1f}/100" if m.moat_score is not None else "N/A")
    _r2(t, "Position", _s(m.competitive_position))
    if tier in (CompanyTier.MEGA, CompanyTier.LARGE, CompanyTier.MID):
        _r2(t, "ROIC Consistency", _s(m.roic_consistency))
        _r2(t, "Margin Stability", _s(m.margin_stability))
        _r2(t, "Revenue Predictability", _s(m.revenue_predictability))
        _r2(t, "Scale", _s(m.efficient_scale))
        _r2(t, "Switching Costs", _s(m.switching_costs) or "Review needed")
        _r2(t, "Network Effects", _s(m.network_effects) or "Review needed")
        _r2(t, "Cost Advantages", _s(m.cost_advantages) or "Not detected")
        _r2(t, "Intangible Assets", _s(m.intangible_assets) or "Not detected")
    else:
        _r2(t, "Asset Backing", _s(m.asset_backing))
        _r2(t, "Revenue Status", _s(m.revenue_predictability))
        _r2(t, "Niche Position", _s(m.niche_position))
        _r2(t, "Dilution/Insider", _s(m.insider_alignment))
        if m.intangible_assets:
            _r2(t, "Intangible Assets", _s(m.intangible_assets))
        if m.cost_advantages:
            _r2(t, "Cost Advantages", _s(m.cost_advantages))
    roic_vals = [r for r in m.roic_history if r is not None]
    if roic_vals:
        _r2(t, "ROIC Trend", " -> ".join(_pctplain(x) for x in reversed(roic_vals)))
    gm_vals = [r for r in m.gross_margin_history if r is not None]
    if gm_vals:
        _r2(t, "GM Trend", " -> ".join(_pctplain(x) for x in reversed(gm_vals)))
    return t


def _build_iv(r: AnalysisReport) -> DataTable:
    iv = r.intrinsic_value
    t = DataTable(zebra_stripes=True)
    t.add_columns("Method", "Value", "Margin of Safety")
    primary = _s(iv.primary_method)
    secondary = _s(iv.secondary_method)
    def tag(n):
        if n in primary: return "(primary) "
        if n in secondary: return "(secondary) "
        return ""
    _r3(t, "Current Price", f"${iv.current_price:.2f}" if iv.current_price else "N/A", "")
    _r3(t, f"{tag('DCF')}DCF (10Y)", f"${iv.dcf_value:.2f}" if iv.dcf_value else "N/A", _mos(iv.margin_of_safety_dcf))
    _r3(t, f"{tag('Graham')}Graham Number", f"${iv.graham_number:.2f}" if iv.graham_number else "N/A", _mos(iv.margin_of_safety_graham))
    _r3(t, f"{tag('NCAV')}NCAV (Net-Net)", f"${iv.ncav_value:.4f}" if iv.ncav_value is not None else "N/A", _mos(iv.margin_of_safety_ncav))
    _r3(t, f"{tag('Asset')}Tangible Book", f"${iv.asset_based_value:.4f}" if iv.asset_based_value else "N/A", _mos(iv.margin_of_safety_asset))
    if iv.lynch_fair_value:
        _r3(t, "Lynch Fair Value", f"${iv.lynch_fair_value:.2f}", "")
    return t


def _build_conclusion(r: AnalysisReport) -> DataTable:
    from lynx.core.conclusion import generate_conclusion
    c = generate_conclusion(r)
    t = DataTable(zebra_stripes=True)
    t.add_columns("Item", "Details")
    _r2(t, "Verdict", f"{c.verdict} ({c.overall_score:.0f}/100)")
    _r2(t, "Summary", c.summary)
    for cat in ("valuation", "profitability", "solvency", "growth", "moat"):
        score = c.category_scores.get(cat, 0)
        summary = c.category_summaries.get(cat, "")
        _r2(t, f"{cat.title()} ({score:.0f})", summary)
    for i, s in enumerate(c.strengths, 1):
        _r2(t, f"Strength {i}", s)
    for i, risk in enumerate(c.risks, 1):
        _r2(t, f"Risk {i}", risk)
    _r2(t, "Tier Note", c.tier_note)
    return t


def _build_financials(r: AnalysisReport) -> DataTable:
    t = DataTable(zebra_stripes=True)
    t.add_columns("Period", "Revenue", "Gross Profit", "Op Income", "Net Income", "FCF", "Equity", "Debt")
    for st in (r.financials or [])[:5]:
        t.add_row(_s(st.period), _money(st.revenue), _money(st.gross_profit),
                  _money(st.operating_income), _money(st.net_income),
                  _money(st.free_cash_flow), _money(st.total_equity), _money(st.total_debt))
    return t


def _build_filings(r: AnalysisReport) -> DataTable:
    t = DataTable(zebra_stripes=True, cursor_type="row")
    t.add_columns("#", "Type", "Filed", "Period", "Saved")
    for i, f in enumerate((r.filings or [])[:20], 1):
        t.add_row(str(i), _s(f.form_type), _s(f.filing_date), _s(f.period), "Yes" if f.local_path else "No")
    return t


def _build_news(r: AnalysisReport) -> DataTable:
    t = DataTable(zebra_stripes=True, cursor_type="row")
    t.add_columns("#", "Title", "Source", "Date")
    for i, n in enumerate((r.news or [])[:20], 1):
        raw = n.title or ""
        title = raw[:70] + ("..." if len(raw) > 70 else "")
        t.add_row(str(i), title, _s(n.source), _s(n.published))
    return t


# ======================================================================
# Safe formatters
# ======================================================================

def _r3(t: DataTable, c1: str, c2: str, c3: str) -> None:
    t.add_row(str(c1), str(c2), str(c3))

def _r2(t: DataTable, c1: str, c2: str) -> None:
    t.add_row(str(c1), str(c2))

def _s(val) -> str:
    return str(val) if val is not None else "N/A"

def _num(val, digits: int = 2) -> str:
    if val is None: return "N/A"
    try: return f"{float(val):,.{digits}f}"
    except Exception: return "N/A"

def _pct(val) -> str:
    if val is None: return "N/A"
    try: return f"{float(val) * 100:.2f}%"
    except Exception: return "N/A"

def _pctplain(val) -> str:
    if val is None: return "N/A"
    try: return f"{float(val) * 100:.1f}%"
    except Exception: return "N/A"

def _money(val) -> str:
    if val is None: return "N/A"
    try:
        v = float(val)
        if abs(v) >= 1e12: return f"${v/1e12:,.2f}T"
        if abs(v) >= 1e9: return f"${v/1e9:,.2f}B"
        if abs(v) >= 1e6: return f"${v/1e6:,.2f}M"
        return f"${v:,.0f}"
    except Exception: return "N/A"

def _mos(val) -> str:
    if val is None: return "N/A"
    try:
        p = float(val) * 100
        if p > 25: return f"{p:.1f}% (Undervalued)"
        if p > 0: return f"{p:.1f}% (Slight Undervalue)"
        return f"{p:.1f}% (Overvalued)"
    except Exception: return "N/A"

def _ape(val) -> str:
    if val is None: return ""
    try:
        v = float(val)
        if v < 0: return "Negative earnings"
        if v < 10: return "Very cheap"
        if v < 15: return "Value range"
        if v < 20: return "Fair"
        if v < 30: return "Expensive"
        return "Very expensive"
    except Exception: return ""

def _burn(val) -> str:
    if val is None: return ""
    try:
        v = float(val)
        if v == 0: return "Not burning cash"
        if v < 0: return "Burning cash"
        return "Cash flow positive"
    except Exception: return ""

def _thr(val, thresholds, over_label) -> str:
    if val is None: return ""
    try:
        v = float(val)
        for threshold, label in thresholds:
            if v < threshold: return label
        return over_label
    except Exception: return ""

def _yield_assess(val) -> str:
    if val is None: return ""
    try:
        v = float(val)
        if v > 0.10: return "Excellent"
        if v > 0.07: return "Good"
        if v > 0.05: return "Fair"
        if v > 0: return "Low"
        return "Negative"
    except Exception: return ""

def _div_assess(val) -> str:
    if val is None: return ""
    try:
        v = float(val)
        if v <= 0: return "No dividend"
        if v > 0.06: return "Very high"
        if v > 0.04: return "High"
        if v > 0.02: return "Moderate"
        return "Low"
    except Exception: return ""

def _margin_assess(val, exc: float, good: float, fair: float) -> str:
    if val is None: return ""
    try:
        v = float(val)
        if v < 0: return "Negative"
        if v > exc: return "Excellent"
        if v > good: return "Good"
        if v > fair: return "Moderate"
        return "Thin"
    except Exception: return ""

def _growth_assess(val) -> str:
    if val is None: return ""
    try:
        v = float(val)
        if v > 0.25: return "Very strong"
        if v > 0.10: return "Good"
        if v > 0: return "Positive"
        if v > -0.10: return "Slight decline"
        return "Declining"
    except Exception: return ""

def _cagr_assess(val) -> str:
    if val is None: return ""
    try:
        v = float(val)
        if v > 0.15: return "Excellent"
        if v > 0.08: return "Good"
        if v > 0: return "Positive"
        return "Declining"
    except Exception: return ""

def _dilution_assess(val) -> str:
    if val is None: return ""
    try:
        v = float(val)
        if v < -0.02: return "Buybacks"
        if v < 0.01: return "Minimal"
        if v < 0.05: return "Modest (<5%)"
        if v < 0.10: return "Significant"
        return "Heavy dilution"
    except Exception: return ""

def _safe_tier(tier) -> str:
    if isinstance(tier, CompanyTier): return tier.value
    return str(tier) if tier else "N/A"

def _get_tier(r: AnalysisReport) -> CompanyTier:
    try:
        tier = r.profile.tier
        if isinstance(tier, CompanyTier): return tier
    except Exception: pass
    return CompanyTier.NANO

def run_tui() -> None:
    app = LynxApp()
    app.run()
