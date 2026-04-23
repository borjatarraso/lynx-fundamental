"""Textual UI for Lynx Fundamental Analysis."""

from __future__ import annotations

from textual import work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, VerticalScroll

from lynx_investor_core.pager import PagingAppMixin, tui_paging_bindings
from lynx_investor_core.urlsafe import safe_webbrowser_open
from textual.screen import ModalScreen
from textual.widgets import (
    Button,
    Collapsible,
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
        from lynx import get_about_text, get_logo_ascii
        about = get_about_text()
        logo = get_logo_ascii()
        logo_block = f"[green]{logo}[/]\n\n" if logo else ""
        with Vertical(id="about-dialog"):
            yield Label(
                f"[bold blue]{about['name']}[/]",
                id="about-title",
            )
            yield VerticalScroll(
                Static(
                    f"{logo_block}"
                    f"[bold blue]{about['name']} v{about['version']}[/]\n"
                    f"[dim]Part of {about['suite']} v{about['suite_version']}[/]\n"
                    f"[dim]Released {about['year']}[/]\n\n"
                    f"[bold]Developed by:[/] {about['author']}\n"
                    f"[bold]Contact:[/]      {about['email']}\n"
                    f"[bold]License:[/]      {about['license']}\n\n"
                    f"{about['description']}\n\n"
                    f"[bold cyan]BSD 3-Clause License[/]\n"
                    f"[dim]{about['license_text']}[/]",
                    id="about-content",
                ),
                id="about-scroll",
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
    """Versatile explain dialog for metrics, sections, and conclusion items."""
    BINDINGS = [Binding("escape", "dismiss_modal", "Close")]

    def __init__(self, key: str, kind: str = "metric", **kwargs) -> None:
        """*kind* can be ``metric``, ``section``, or ``conclusion``."""
        super().__init__(**kwargs)
        self._key = key
        self._kind = kind

    def compose(self) -> ComposeResult:
        from lynx.metrics.explanations import (
            get_conclusion_explanation,
            get_explanation,
            get_section_explanation,
        )

        title = ""
        content = ""

        if self._kind == "metric":
            exp = get_explanation(self._key)
            if exp:
                title = exp.full_name
                content = (
                    f"[bold]{exp.full_name}[/]\n\n"
                    f"{exp.description}\n\n"
                    f"[bold cyan]Why it matters:[/]\n{exp.why_used}\n\n"
                    f"[bold cyan]Formula:[/]\n[bold]{exp.formula}[/]\n\n"
                    f"[dim]Category: {exp.category}[/]"
                )
            else:
                title = self._key
                content = f"No explanation available for '{self._key}'."

        elif self._kind == "section":
            sec = get_section_explanation(self._key)
            if sec:
                title = sec["title"]
                content = f"[bold]{sec['title']}[/]\n\n{sec['description']}"
            else:
                title = self._key.title()
                content = f"No section explanation available for '{self._key}'."

        elif self._kind == "conclusion":
            ce = get_conclusion_explanation(self._key)
            if ce:
                title = ce["title"]
                content = f"[bold]{ce['title']}[/]\n\n{ce['description']}"
            else:
                title = "Conclusion"
                content = "No conclusion explanation available."

        with Vertical(id="explain-dialog"):
            yield Label(f"[bold]{title}[/]", id="explain-title")
            yield VerticalScroll(Static(content, id="explain-content"), id="explain-scroll")
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
# Export format modal
# ======================================================================

class ExportModal(ModalScreen[str]):
    BINDINGS = [Binding("escape", "dismiss_modal", "Cancel")]

    def compose(self) -> ComposeResult:
        with Vertical(id="export-dialog"):
            yield Label("[bold]Export Report[/]", id="export-title")
            with Horizontal(id="export-buttons"):
                yield Button("TXT", id="export-txt", variant="primary")
                yield Button("HTML", id="export-html", variant="primary")
                yield Button("PDF", id="export-pdf", variant="primary")
            yield Label("[dim]Select format, or Escape to cancel[/]", id="export-hint")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        fmt = event.button.id.replace("export-", "")
        self.dismiss(fmt)

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

class ReportView(VerticalScroll):
    """Widget that renders analysis report sections progressively.

    Sections are mounted one-by-one via ``add_stage()`` so the user sees
    data as soon as it arrives, rather than waiting for the full pipeline.
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._report: AnalysisReport | None = None
        self._hint_removed: bool = False

    def compose(self) -> ComposeResult:
        # Starts empty — sections are mounted dynamically.
        yield Static(
            "[dim]Fetching data…[/]",
            id="loading-hint",
        )

    def add_stage(self, stage: str, report: AnalysisReport) -> None:
        """Mount the widgets for a given analysis stage."""
        self._report = report

        # Remove the loading hint once (first real content).
        if not self._hint_removed:
            self._hint_removed = True
            try:
                self.query_one("#loading-hint", Static).remove()
            except Exception:
                pass

        if stage == "profile":
            self._mount_profile(report)
        elif stage == "financials":
            self._mount_section(
                "Financials", _build_financials(report),
            )
        elif stage == "valuation":
            self._mount_section("Valuation", _build_valuation(report))
        elif stage == "profitability":
            self._mount_section("Profitability", _build_profitability(report))
        elif stage == "solvency":
            self._mount_section(
                "Solvency & Financial Health", _build_solvency(report),
            )
        elif stage == "growth":
            self._mount_section("Growth", _build_growth(report))
        elif stage == "moat":
            self._mount_section("Moat Analysis", _build_moat(report))
        elif stage == "intrinsic_value":
            self._mount_section("Intrinsic Value", _build_iv(report))
        elif stage == "filings":
            self._mount_filings(report)
        elif stage == "news":
            self._mount_news(report)
        elif stage == "conclusion":
            self._mount_section("Conclusion", _build_conclusion(report))
        elif stage == "complete":
            # If no sections were mounted yet (cached report), render all.
            if not list(self.query(Collapsible)):
                self.render_full(report)

    # ── Internal mount helpers ───────────────────────────────────────

    def _mount_profile(self, r: AnalysisReport) -> None:
        p = r.profile
        desc = _s(p.description) if p.description else "[dim]No description available.[/]"
        if len(desc) > 600:
            desc = desc[:600] + "..."

        profile_section = Collapsible(
            title="Company Profile", collapsed=False, id="sec-profile",
        )
        self.mount(profile_section)

        split = Horizontal(id="profile-split")
        profile_section.mount(split)
        split.mount(_build_profile_table(r))
        split.mount(Static(desc, id="profile-desc"))

        # Sector and industry insights (after profile)
        self._mount_sector_industry(r)

    def _mount_sector_industry(self, r: AnalysisReport) -> None:
        """Mount sector and industry insight collapsibles."""
        from lynx.metrics.sector_insights import get_sector_insight, get_industry_insight

        p = r.profile
        sector_info = get_sector_insight(p.sector)
        industry_info = get_industry_insight(p.industry)

        if sector_info:
            t = _build_insight_table(sector_info)
            c = Collapsible(title=f"Sector: {sector_info.sector}", collapsed=True)
            self.mount(c)
            c.mount(t)

        if industry_info:
            t = _build_insight_table(industry_info)
            c = Collapsible(title=f"Industry: {industry_info.industry}", collapsed=True)
            self.mount(c)
            c.mount(t)

    def _mount_section(self, title: str, widget, section_id: str = "") -> None:
        kwargs = {"title": title, "collapsed": True}
        if section_id:
            kwargs["id"] = section_id
        c = Collapsible(**kwargs)
        self.mount(c)
        c.mount(widget)

    def _mount_filings(self, r: AnalysisReport) -> None:
        c = Collapsible(title="Filings", collapsed=True, id="sec-filings")
        self.mount(c)
        c.mount(_build_filings(r))
        c.mount(Static(
            "[dim]Select a row and press [bold]Enter[/bold] to download filing[/]",
        ))

    def _mount_news(self, r: AnalysisReport) -> None:
        c = Collapsible(title="News", collapsed=True, id="sec-news")
        self.mount(c)
        c.mount(_build_news(r))
        c.mount(Static(
            "[dim]Select a row and press [bold]Enter[/bold] to open in browser[/]",
        ))

    def render_full(self, report: AnalysisReport) -> None:
        """Convenience: mount all sections at once (for cached reports)."""
        stages = [
            "profile", "financials", "valuation", "profitability",
            "solvency", "growth", "moat", "intrinsic_value",
            "filings", "news", "conclusion",
        ]
        for stage in stages:
            self.add_stage(stage, report)


# ======================================================================
# Main application
# ======================================================================

class LynxApp(PagingAppMixin, App):
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
    #profile-split {
        height: auto;
    }
    #profile-split DataTable {
        width: 1fr;
        height: auto;
        max-height: 16;
    }
    #profile-desc {
        width: 1fr;
        padding: 1 2;
        height: auto;
    }
    Collapsible {
        margin: 0 0 1 0;
    }
    #about-dialog {
        width: 76;
        height: auto;
        max-height: 46;
        border: thick $accent;
        background: $surface;
        padding: 1 2;
        margin: 1 2;
    }
    #about-title {
        text-align: center;
        text-style: bold;
        margin-bottom: 1;
    }
    #about-scroll {
        height: auto;
        max-height: 34;
        margin: 0 1;
    }
    #about-content {
        width: 1fr;
        margin: 0 1;
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
        align-horizontal: center;
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
        margin: 0 1;
    }
    #explain-dialog {
        width: 100;
        height: auto;
        max-height: 40;
        border: thick $accent;
        background: $surface;
        padding: 1 2;
        margin: 1 2;
    }
    #explain-title {
        text-align: center;
        text-style: bold;
        margin-bottom: 1;
    }
    #explain-scroll {
        height: auto;
        max-height: 30;
        margin: 0 1;
    }
    #explain-content {
        width: 1fr;
        margin: 0 1;
    }
    #explain-hint {
        text-align: center;
        margin-top: 1;
    }
    #metric-list-dialog {
        width: 100;
        height: 38;
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
    #export-dialog {
        width: 50;
        height: auto;
        max-height: 10;
        border: thick $accent;
        background: $surface;
        padding: 1 2;
        margin: 6 10;
    }
    #export-title {
        text-align: center;
        text-style: bold;
        margin-bottom: 1;
    }
    #export-buttons {
        align-horizontal: center;
        height: auto;
    }
    #export-buttons Button {
        margin: 0 1;
    }
    #export-hint {
        text-align: center;
        margin-top: 1;
    }
    """

    BINDINGS = [
        Binding("a", "analyze", "Analyze"),
        Binding("q", "quit", "Quit"),
        Binding("r", "refresh", "Refresh"),
        Binding("t", "cycle_theme", "Theme"),
        Binding("f1", "about", "About"),
        Binding("e", "explain_context", "Explain"),
        Binding("E", "explain_all", "All Metrics", key_display="shift+e"),
        Binding("i", "info_metric", "Info"),
        Binding("x", "export", "Export"),
        Binding("tab", "focus_next", "Tab:Next"),
        Binding("shift+tab", "focus_previous", "S-Tab:Prev"),
        Binding("enter", "select", "Enter:Open", show=True),
        Binding("space", "toggle_node", "Space:Toggle", show=True),
        Binding("up", "scroll_up", "Up", show=False),
        Binding("down", "scroll_down", "Down", show=False),
        *tui_paging_bindings(),
        Binding("escape", "app.focus('status-area')", "Esc:Back"),
        Binding("ctrl+l", "_ee_lynx", show=False),
        Binding("ctrl+f", "_ee_fortune", show=False),
        Binding("ctrl+m", "_ee_matrix", show=False),
    ]

    report: AnalysisReport | None = None
    _last_identifier: str = ""
    _suppress_news_dialog: bool = False
    _theme_index: int = 0
    _report_view: ReportView | None = None

    def on_mount(self) -> None:
        from lynx.tui.themes import register_all_themes, THEME_NAMES
        try:
            register_all_themes(self)
            self.theme = THEME_NAMES[0]  # lynx-dark
        except Exception:
            pass  # Fall back to Textual's default theme

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static(
            "[bold blue]  lynx-fundamental  [/]\n\n"
            "[bold]Fundamental Analysis Tool[/]\n"
            "[dim]Press [bold]A[/bold] to analyze a stock, "
            "[bold]Q[/bold] to quit[/]\n\n"
            "[dim]Navigation: click section headers to expand/collapse  "
            "[bold]\u2191\u2193[/bold] scroll  "
            "[bold]Escape[/bold] go back[/]",
            id="status-area",
        )
        yield Footer()

    def action_about(self) -> None:
        self.push_screen(AboutModal())

    def action_export(self) -> None:
        if not self.report:
            self._set_status("[yellow]No analysis loaded. Press A to analyze first.[/]")
            return
        self.push_screen(ExportModal(), self._on_export_result)

    def _on_export_result(self, fmt: str) -> None:
        if not fmt or not self.report:
            return
        self._do_export(fmt)

    @work(thread=True)
    def _do_export(self, fmt: str) -> None:
        from lynx.export import ExportFormat, export_report
        try:
            path = export_report(self.report, ExportFormat(fmt))
            self.call_from_thread(
                self.push_screen,
                DownloadResultDialog(f"Report exported to:\n{path}", success=True),
            )
        except Exception as e:
            self.call_from_thread(
                self.push_screen,
                DownloadResultDialog(f"Export failed: {e}", success=False),
            )

    def action_explain_all(self) -> None:
        """Browse all metric explanations (Shift+E)."""
        self.push_screen(MetricListModal(), self._on_explain_result)

    def _on_explain_result(self, key: str) -> None:
        if key:
            self.push_screen(ExplainModal(key, kind="metric"))

    def action_explain_context(self) -> None:
        """Context-aware explain (e): explains the focused metric, section, or conclusion item."""
        focused = self.focused

        # If on a DataTable, try to explain the selected metric row
        if isinstance(focused, DataTable):
            try:
                row_key = focused.coordinate_to_cell_key(focused.cursor_coordinate).row_key
                key_str = str(row_key.value) if row_key.value else ""
                if key_str:
                    self.push_screen(ExplainModal(key_str, kind="metric"))
                    return
            except Exception:
                pass

            # Check if the DataTable is inside a conclusion section
            section = self._find_parent_section(focused)
            if section == "conclusion":
                # Try to explain the specific conclusion category
                try:
                    row_idx = focused.cursor_coordinate.row
                    row_data = focused.get_row_at(row_idx)
                    cell_text = str(row_data[0]) if row_data else ""
                    # Category rows like "Valuation (65)"
                    for cat in ("valuation", "profitability", "solvency", "growth", "moat"):
                        if cat in cell_text.lower():
                            self.push_screen(ExplainModal(cat, kind="conclusion"))
                            return
                    # Verdict / Summary / Strength / Risk / Tier Note
                    self.push_screen(ExplainModal("overall", kind="conclusion"))
                    return
                except Exception:
                    self.push_screen(ExplainModal("overall", kind="conclusion"))
                    return

            # If the DataTable row has no metric key, explain the parent section
            if section:
                self.push_screen(ExplainModal(section, kind="section"))
                return

        # If on a Collapsible or any widget, try to explain the parent section
        if focused is not None:
            section = self._find_parent_section(focused)
            if section:
                if section == "conclusion":
                    self.push_screen(ExplainModal("overall", kind="conclusion"))
                else:
                    self.push_screen(ExplainModal(section, kind="section"))
                return

        self.notify("Nothing to explain here. Select a metric or section.", timeout=3)

    def _find_parent_section(self, widget) -> str:
        """Walk up the widget tree to find which analysis section a widget belongs to."""
        _SECTION_MAP = {
            "sec-profile": "profile",
            "sec-filings": "filings",
            "sec-news": "news",
        }
        _TITLE_MAP = {
            "company profile": "profile",
            "valuation": "valuation",
            "profitability": "profitability",
            "solvency": "solvency",
            "growth": "growth",
            "moat": "moat",
            "intrinsic value": "intrinsic_value",
            "financials": "financials",
            "filings": "filings",
            "news": "news",
            "conclusion": "conclusion",
        }
        for ancestor in widget.ancestors_with_self:
            if isinstance(ancestor, Collapsible):
                # Check by ID first
                if ancestor.id and ancestor.id in _SECTION_MAP:
                    return _SECTION_MAP[ancestor.id]
                # Check by title
                title = str(getattr(ancestor, "title", "")).lower()
                for key, section in _TITLE_MAP.items():
                    if key in title:
                        return section
        return ""

    def action_info_metric(self) -> None:
        """Show explanation for the currently selected metric row (I key)."""
        self.action_explain_context()

    def action_analyze(self) -> None:
        self.push_screen(SearchModal(), self._on_search_result)

    def action_cycle_theme(self) -> None:
        from lynx.tui.themes import THEME_NAMES
        self._theme_index = (self._theme_index + 1) % len(THEME_NAMES)
        self.theme = THEME_NAMES[self._theme_index]
        self.notify(f"Theme: {self.theme}", timeout=2)

    def action__ee_lynx(self) -> None:
        from lynx.easter import LYNX_ASCII, WOLF_ASCII, BULL_ASCII
        import random
        art = random.choice([LYNX_ASCII, WOLF_ASCII, BULL_ASCII])
        self.notify(art.strip(), timeout=5)

    def action__ee_fortune(self) -> None:
        from lynx.easter import FORTUNE_QUOTES
        import random
        quote = random.choice(FORTUNE_QUOTES)
        self.notify(f"\u2728 {quote}", timeout=8)

    def action__ee_matrix(self) -> None:
        from lynx.tui.themes import THEME_NAMES
        import random
        for i in range(14):
            self._theme_index = (self._theme_index + 1) % len(THEME_NAMES)
            self.theme = THEME_NAMES[self._theme_index]
            self.set_timer(0.2 * i, lambda idx=self._theme_index: None)
        self.notify("\U0001f9e0 You found the Matrix!", timeout=3)

    def action_refresh(self) -> None:
        if self._last_identifier:
            self._start_analysis(self._last_identifier, force_refresh=True)

    def _on_search_result(self, identifier: str) -> None:
        if identifier:
            self._start_analysis(identifier)

    def _start_analysis(self, identifier: str, force_refresh: bool = False) -> None:
        self._last_identifier = identifier
        # Prepare an empty ReportView that will receive sections progressively
        self._remove_reports()
        try:
            self.query_one("#status-area", Static).display = False
        except Exception:
            pass
        self._report_view = ReportView()
        self.mount(self._report_view, before=self.query_one(Footer))
        self._do_analysis(identifier, force_refresh)

    @work(thread=True, exclusive=True)
    def _do_analysis(self, identifier: str, force_refresh: bool = False) -> None:
        from lynx.core.analyzer import run_progressive_analysis
        from lynx.core.storage import is_testing

        def on_progress(stage: str, report) -> None:
            """Forward each stage to the main thread for rendering."""
            self.report = report
            self.call_from_thread(self._render_stage, stage, report)

        try:
            refresh = force_refresh or is_testing()
            report = run_progressive_analysis(
                identifier,
                download_reports=True,
                download_news=True,
                refresh=refresh,
                on_progress=on_progress,
            )
            self.report = report
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
        self._report_view = None
        try:
            for w in list(self.query(ReportView)):
                w.remove()
        except Exception:
            pass

    def _render_stage(self, stage: str, report: AnalysisReport) -> None:
        """Mount a single section into the live ReportView."""
        try:
            view = self._report_view
            if view is None:
                return
            view.add_stage(stage, report)
        except Exception as e:
            # Don't destroy the report view on a single-section error.
            self.notify(
                f"Render error ({stage}): {type(e).__name__}: {e}",
                severity="error",
                timeout=8,
            )

    # --- DataTable row selection handlers ---

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Handle Enter on a selected row in Filings or News tables."""
        if not self.report:
            return

        # Determine which section the table is in by checking parent Collapsible
        table = event.data_table
        section_id = ""
        for ancestor in table.ancestors_with_self:
            if isinstance(ancestor, Collapsible) and ancestor.id:
                section_id = ancestor.id
                break

        row_idx = event.cursor_row

        if section_id == "sec-filings":
            self._download_filing(row_idx)
        elif section_id == "sec-news":
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
        report = self.report
        if not report:
            return
        try:
            path = download_filing(report.profile.ticker, filing)
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

        if safe_webbrowser_open(article.url):
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

def _build_profile_table(r: AnalysisReport) -> DataTable:
    """Build the company profile key-value table (left side of split)."""
    p = r.profile
    t = DataTable(zebra_stripes=True, show_cursor=False)
    t.add_columns("Field", "Value")
    _r2(t, "Company", _s(p.name))
    _r2(t, "Ticker", _s(p.ticker))
    if p.isin:
        _r2(t, "ISIN", p.isin)
    _r2(t, "Tier", _safe_tier(p.tier))
    _r2(t, "Sector", _s(p.sector))
    _r2(t, "Industry", _s(p.industry))
    _r2(t, "Country", _s(p.country))
    _r2(t, "Exchange", _s(p.exchange))
    _r2(t, "Market Cap", _money(p.market_cap))
    _r2(t, "Employees", f"{p.employees:,}" if p.employees else "N/A")
    if p.website:
        _r2(t, "Website", p.website)
    return t


def _build_valuation(r: AnalysisReport) -> DataTable:
    v = r.valuation
    t = DataTable(zebra_stripes=True, cursor_type="row")
    t.add_columns("Metric", "Value", "Assessment", "?")
    if v is None:
        return t
    _rm(t, "P/E (Trailing)", _num(v.pe_trailing), _ape(v.pe_trailing), "pe_trailing")
    _rm(t, "P/E (Forward)", _num(v.pe_forward), _ape(v.pe_forward), "pe_forward")
    _rm(t, "P/B Ratio", _num(v.pb_ratio), _thr(v.pb_ratio, [(1, "Below Book"), (1.5, "Cheap"), (3, "Fair")], "Premium"), "pb_ratio")
    _rm(t, "P/S Ratio", _num(v.ps_ratio), "", "ps_ratio")
    _rm(t, "P/FCF", _num(v.p_fcf), _thr(v.p_fcf, [(10, "Cheap"), (20, "Fair")], "Expensive"), "p_fcf")
    _rm(t, "EV/EBITDA", _num(v.ev_ebitda), _thr(v.ev_ebitda, [(8, "Cheap"), (12, "Fair"), (18, "Expensive")], "Very Expensive"), "ev_ebitda")
    _rm(t, "EV/Revenue", _num(v.ev_revenue), _thr(v.ev_revenue, [(1, "Very cheap"), (3, "Cheap"), (5, "Fair"), (8, "Expensive")], "Very expensive"), "ev_revenue")
    _rm(t, "PEG Ratio", _num(v.peg_ratio), _thr(v.peg_ratio, [(1, "Undervalued"), (2, "Fair")], "Overvalued"), "peg_ratio")
    _rm(t, "Earnings Yield", _pct(v.earnings_yield), _yield_assess(v.earnings_yield), "earnings_yield")
    _rm(t, "Dividend Yield", _pct(v.dividend_yield), _div_assess(v.dividend_yield), "dividend_yield")
    _rm(t, "P/Tangible Book", _num(v.price_to_tangible_book), _thr(v.price_to_tangible_book, [(0.67, "Deep Value"), (1, "Below Book"), (1.5, "Near Book")], "Premium"), "price_to_tangible_book")
    _rm(t, "P/NCAV (Net-Net)", _num(v.price_to_ncav), _thr(v.price_to_ncav, [(0.67, "Classic Net-Net"), (1, "Below NCAV"), (1.5, "Near NCAV")], "Above NCAV"), "price_to_ncav")
    _rm(t, "Enterprise Value", _money(v.enterprise_value), "")
    _rm(t, "Market Cap", _money(v.market_cap), "")
    return t


def _build_profitability(r: AnalysisReport) -> DataTable:
    p = r.profitability
    t = DataTable(zebra_stripes=True, cursor_type="row")
    t.add_columns("Metric", "Value", "Assessment", "?")
    if p is None:
        return t
    _rm(t, "ROE", _pct(p.roe), _thr(p.roe, [(0, "Negative"), (0.10, "Below Avg"), (0.15, "Good"), (0.20, "Excellent")], "Outstanding"), "roe")
    _rm(t, "ROA", _pct(p.roa), _thr(p.roa, [(0, "Negative"), (0.05, "Low"), (0.10, "Good")], "Excellent"), "roa")
    _rm(t, "ROIC", _pct(p.roic), _thr(p.roic, [(0, "Negative"), (0.07, "Below WACC"), (0.10, "Good"), (0.15, "Wide Moat")], "Exceptional"), "roic")
    _rm(t, "Gross Margin", _pct(p.gross_margin), "", "gross_margin")
    _rm(t, "Operating Margin", _pct(p.operating_margin), _margin_assess(p.operating_margin, 0.25, 0.15, 0.05), "operating_margin")
    _rm(t, "Net Margin", _pct(p.net_margin), _margin_assess(p.net_margin, 0.20, 0.10, 0.05), "net_margin")
    _rm(t, "FCF Margin", _pct(p.fcf_margin), _margin_assess(p.fcf_margin, 0.20, 0.10, 0.05), "fcf_margin")
    _rm(t, "EBITDA Margin", _pct(p.ebitda_margin), _margin_assess(p.ebitda_margin, 0.30, 0.15, 0.05), "ebitda_margin")
    return t


def _build_solvency(r: AnalysisReport) -> DataTable:
    s = r.solvency
    t = DataTable(zebra_stripes=True, cursor_type="row")
    t.add_columns("Metric", "Value", "Assessment", "?")
    if s is None:
        return t
    _rm(t, "Debt/Equity", _num(s.debt_to_equity), _thr(s.debt_to_equity, [(0.3, "Very Conservative"), (0.5, "Conservative"), (1.0, "Moderate"), (2.0, "High")], "Very High"), "debt_to_equity")
    _rm(t, "Debt/EBITDA", _num(s.debt_to_ebitda), _thr(s.debt_to_ebitda, [(1, "Very Low"), (2, "Manageable"), (3, "Moderate")], "Heavy"), "debt_to_ebitda")
    _rm(t, "Current Ratio", _num(s.current_ratio), _thr(s.current_ratio, [(1.0, "Liquidity Risk"), (1.5, "Adequate"), (2.0, "Good")], "Strong"), "current_ratio")
    _rm(t, "Quick Ratio", _num(s.quick_ratio), "", "quick_ratio")
    _rm(t, "Interest Coverage", _num(s.interest_coverage, 1), _thr(s.interest_coverage, [(1, "Cannot cover"), (2, "Tight"), (4, "Adequate"), (8, "Strong")], "Very strong"), "interest_coverage")
    _rm(t, "Altman Z-Score", _num(s.altman_z_score), _thr(s.altman_z_score, [(1.81, "Distress"), (2.99, "Grey Zone")], "Safe"), "altman_z_score")
    _rm(t, "Cash Burn Rate (/yr)", _money(s.cash_burn_rate), _burn(s.cash_burn_rate), "cash_burn_rate")
    _rm(t, "Cash Runway", f"{s.cash_runway_years:.1f} yrs" if s.cash_runway_years is not None else "N/A", "", "cash_runway_years")
    _rm(t, "Working Capital", _money(s.working_capital), "")
    _rm(t, "Cash Per Share", f"${s.cash_per_share:.2f}" if s.cash_per_share is not None else "N/A", "")
    _rm(t, "NCAV Per Share", f"${s.ncav_per_share:.4f}" if s.ncav_per_share is not None else "N/A", "", "ncav_per_share")
    _rm(t, "Total Debt", _money(s.total_debt), "")
    _rm(t, "Total Cash", _money(s.total_cash), "")
    _rm(t, "Net Debt", _money(s.net_debt), "")
    return t


def _build_growth(r: AnalysisReport) -> DataTable:
    g = r.growth
    t = DataTable(zebra_stripes=True, cursor_type="row")
    t.add_columns("Metric", "Value", "Assessment", "?")
    if g is None:
        return t
    _rm(t, "Revenue Growth (YoY)", _pct(g.revenue_growth_yoy), _growth_assess(g.revenue_growth_yoy), "revenue_growth_yoy")
    _rm(t, "Revenue CAGR (3Y)", _pct(g.revenue_cagr_3y), _cagr_assess(g.revenue_cagr_3y), "revenue_cagr_3y")
    _rm(t, "Revenue CAGR (5Y)", _pct(g.revenue_cagr_5y), _cagr_assess(g.revenue_cagr_5y), "revenue_cagr_5y")
    _rm(t, "Earnings Growth (YoY)", _pct(g.earnings_growth_yoy), _growth_assess(g.earnings_growth_yoy), "earnings_growth_yoy")
    _rm(t, "Earnings CAGR (3Y)", _pct(g.earnings_cagr_3y), _cagr_assess(g.earnings_cagr_3y), "earnings_cagr_3y")
    _rm(t, "Earnings CAGR (5Y)", _pct(g.earnings_cagr_5y), _cagr_assess(g.earnings_cagr_5y), "earnings_cagr_5y")
    _rm(t, "FCF Growth (YoY)", _pct(g.fcf_growth_yoy), _growth_assess(g.fcf_growth_yoy))
    _rm(t, "Book Value Growth (YoY)", _pct(g.book_value_growth_yoy), _growth_assess(g.book_value_growth_yoy))
    _rm(t, "Share Dilution (YoY)", _pct(g.shares_growth_yoy), _dilution_assess(g.shares_growth_yoy), "shares_growth_yoy")
    return t


def _build_moat(r: AnalysisReport) -> DataTable:
    m = r.moat
    tier = _get_tier(r)
    t = DataTable(zebra_stripes=True)
    t.add_columns("Indicator", "Assessment")
    if m is None:
        return t
    _r2(t, "Score", f"{m.moat_score:.1f}/100" if m.moat_score is not None else "N/A")
    _r2(t, "Position", _s(m.competitive_position))
    if tier in (CompanyTier.MEGA, CompanyTier.LARGE, CompanyTier.MID):
        _r2(t, "ROIC Consistency", _s(m.roic_consistency))
        _r2(t, "Margin Stability", _s(m.margin_stability))
        _r2(t, "Revenue Predictability", _s(m.revenue_predictability))
        _r2(t, "Scale", _s(m.efficient_scale))
        _r2(t, "Switching Costs", _s(m.switching_costs or "Review needed"))
        _r2(t, "Network Effects", _s(m.network_effects or "Review needed"))
        _r2(t, "Cost Advantages", _s(m.cost_advantages or "Not detected"))
        _r2(t, "Intangible Assets", _s(m.intangible_assets or "Not detected"))
    else:
        _r2(t, "Asset Backing", _s(m.asset_backing))
        _r2(t, "Revenue Status", _s(m.revenue_predictability))
        _r2(t, "Niche Position", _s(m.niche_position))
        _r2(t, "Dilution/Insider", _s(m.insider_alignment))
        if m.intangible_assets:
            _r2(t, "Intangible Assets", _s(m.intangible_assets))
        if m.cost_advantages:
            _r2(t, "Cost Advantages", _s(m.cost_advantages))
    roic_vals = [v for v in m.roic_history if v is not None]
    if roic_vals:
        _r2(t, "ROIC Trend", " -> ".join(_pctplain(x) for x in reversed(roic_vals)))
    gm_vals = [v for v in m.gross_margin_history if v is not None]
    if gm_vals:
        _r2(t, "GM Trend", " -> ".join(_pctplain(x) for x in reversed(gm_vals)))
    return t


def _build_insight_table(info) -> DataTable:
    """Build a DataTable for a SectorInsight or IndustryInsight."""
    t = DataTable(zebra_stripes=True)
    t.add_columns("Aspect", "Details")
    _r2(t, "Overview", info.overview)
    _r2(t, "Critical Metrics", ", ".join(info.critical_metrics))
    _r2(t, "Key Risks", ", ".join(info.key_risks))
    _r2(t, "What to Watch", ", ".join(info.what_to_watch))
    _r2(t, "Typical Valuation", info.typical_valuation)
    return t


def _build_iv(r: AnalysisReport) -> DataTable:
    iv = r.intrinsic_value
    t = DataTable(zebra_stripes=True)
    t.add_columns("Method", "Value", "Margin of Safety")
    if iv is None:
        return t
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

def _rm(t: DataTable, c1: str, c2: str, c3: str, key: str = "") -> None:
    """Add a metric row with an info marker if a key is available."""
    t.add_row(str(c1), str(c2), str(c3), "\u2139" if key else "", key=key if key else None)

def _r2(t: DataTable, c1: str, c2: str) -> None:
    t.add_row(str(c1), str(c2))

def _s(val) -> str:
    return str(val) if val is not None else "N/A"

def _num(val, digits: int = 2) -> str:
    if val is None: return "N/A"
    try:
        v = float(val)
        if v != v: return "N/A"  # NaN check
        return f"{v:,.{digits}f}"
    except Exception: return "N/A"

def _pct(val) -> str:
    if val is None: return "N/A"
    try:
        v = float(val)
        if v != v: return "N/A"  # NaN check
        return f"{v * 100:.2f}%"
    except Exception: return "N/A"

def _pctplain(val) -> str:
    if val is None: return "N/A"
    try:
        v = float(val)
        if v != v: return "N/A"  # NaN check
        return f"{v * 100:.1f}%"
    except Exception: return "N/A"

def _money(val) -> str:
    if val is None: return "N/A"
    try:
        v = float(val)
        if v != v: return "N/A"  # NaN check
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
