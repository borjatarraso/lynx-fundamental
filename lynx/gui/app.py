"""Tkinter graphical user interface for Lynx Fundamental Analysis."""

from __future__ import annotations

import threading
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional

from lynx.models import AnalysisReport, CompanyTier

# ---------------------------------------------------------------------------
# Colour palette (Catppuccin Mocha)
# ---------------------------------------------------------------------------
BG = "#1e1e2e"
BG_SURFACE = "#232336"
BG_CARD = "#2a2a3d"
BG_INPUT = "#313147"
BG_HOVER = "#3b3b54"
FG = "#cdd6f4"
FG_DIM = "#6c7086"
FG_SUBTLE = "#585b70"
ACCENT = "#89b4fa"
ACCENT_DIM = "#5a7ec2"
LAVENDER = "#b4befe"
BORDER = "#45475a"
BORDER_LIGHT = "#585b70"
BTN_BG = "#89b4fa"
BTN_FG = "#1e1e2e"
BTN_ACTIVE = "#74c7ec"
BTN_SECONDARY_BG = "#45475a"
BTN_SECONDARY_FG = "#cdd6f4"
BTN_DANGER_BG = "#f38ba8"
GREEN = "#a6e3a1"
GREEN_DIM = "#5a8a5a"
RED = "#f38ba8"
RED_DIM = "#8a4a5a"
YELLOW = "#f9e2af"
ORANGE = "#fab387"
TEAL = "#94e2d5"
MAUVE = "#cba6f7"
PINK = "#f5c2e7"
SKY = "#89dceb"
PEACH = "#fab387"

# Unicode glyphs
DIAMOND = "\u25c6"
CHECK = "\u2714"
CROSS = "\u2718"
WARN_ICON = "\u26a0"
ARROW_DOWN = "\u25bc"
ARROW_RIGHT = "\u25b6"
BULLET = "\u2022"
STAR = "\u2605"
CIRCLE = "\u25cf"
CHART = "\u2587"

# Section icons
ICON_PROFILE = "\U0001f3e2"    # office building
ICON_VALUATION = "\U0001f4b0"  # money bag
ICON_PROFIT = "\U0001f4c8"     # chart increasing
ICON_SOLVENCY = "\U0001f3e6"   # bank
ICON_GROWTH = "\U0001f680"     # rocket
ICON_MOAT = "\U0001f3f0"       # castle
ICON_VALUE = "\U0001f4a1"      # light bulb
ICON_FINANCE = "\U0001f4ca"    # bar chart
ICON_FILING = "\U0001f4c4"     # page facing up
ICON_NEWS = "\U0001f4f0"       # newspaper

# Fonts — use platform-appropriate defaults.
# Tkinter does NOT support comma-separated fallback lists; each tuple
# must contain a single family name.  We pick a good cross-platform
# default and Tk handles missing fonts gracefully (falls back to its
# built-in default).
import platform as _plat
if _plat.system() == "Windows":
    _FAMILY = "Segoe UI"
    _MONO = "Consolas"
elif _plat.system() == "Darwin":
    _FAMILY = "Helvetica"
    _MONO = "Menlo"
else:
    _FAMILY = "Noto Sans"
    _MONO = "Noto Sans Mono"

FONT = (_FAMILY, 11)
FONT_BOLD = (_FAMILY, 11, "bold")
FONT_SMALL = (_FAMILY, 10)
FONT_SMALL_BOLD = (_FAMILY, 10, "bold")
FONT_TITLE = (_FAMILY, 22, "bold")
FONT_SUBTITLE = (_FAMILY, 12)
FONT_SECTION = (_FAMILY, 13, "bold")
FONT_MONO = (_MONO, 10)
FONT_SPLASH_TITLE = (_FAMILY, 36, "bold")
FONT_SPLASH_SUB = (_FAMILY, 14)
FONT_SPLASH_VER = (_FAMILY, 11)
FONT_TIER = (_FAMILY, 12, "bold")
FONT_BTN = (_FAMILY, 10, "bold")

# Tier colour mapping
TIER_COLORS = {
    CompanyTier.MEGA:  ("#a6e3a1", "#1a3a1a"),  # green badge
    CompanyTier.LARGE: ("#94e2d5", "#1a3535"),   # teal badge
    CompanyTier.MID:   ("#89b4fa", "#1a2a45"),   # blue badge
    CompanyTier.SMALL: ("#f9e2af", "#3a351a"),   # yellow badge
    CompanyTier.MICRO: ("#fab387", "#3a2a1a"),   # orange badge
    CompanyTier.NANO:  ("#f38ba8", "#3a1a25"),   # red badge
}


# ---------------------------------------------------------------------------
# Splash screen
# ---------------------------------------------------------------------------

class SplashScreen:
    """Animated splash screen shown at startup."""

    def __init__(self, root: tk.Tk, on_done: callable) -> None:
        self.root = root
        self.on_done = on_done
        self.frame = tk.Frame(root, bg=BG)
        self.frame.place(relx=0, rely=0, relwidth=1, relheight=1)
        self.frame.lift()

        # Center content
        center = tk.Frame(self.frame, bg=BG)
        center.place(relx=0.5, rely=0.4, anchor=tk.CENTER)

        # Logo diamond pattern
        logo_text = f"{DIAMOND}  {DIAMOND}  {DIAMOND}"
        self.logo = tk.Label(
            center, text=logo_text, font=(_FAMILY, 28),
            bg=BG, fg=ACCENT,
        )
        self.logo.pack(pady=(0, 12))

        # Title
        self.title = tk.Label(
            center, text="LYNX", font=FONT_SPLASH_TITLE,
            bg=BG, fg=FG,
        )
        self.title.pack(pady=(0, 2))

        # Subtitle
        self.subtitle = tk.Label(
            center, text="Fundamental Analysis", font=FONT_SPLASH_SUB,
            bg=BG, fg=ACCENT,
        )
        self.subtitle.pack(pady=(0, 20))

        # Tagline
        self.tagline = tk.Label(
            center, text="Value Investing  &  Moat Analysis", font=FONT_SMALL,
            bg=BG, fg=FG_DIM,
        )
        self.tagline.pack(pady=(0, 30))

        # Version
        from lynx import __version__, __year__, __author__
        self.version = tk.Label(
            center, text=f"v{__version__}  {BULLET}  {__year__}  {BULLET}  {__author__}",
            font=FONT_SPLASH_VER, bg=BG, fg=FG_SUBTLE,
        )
        self.version.pack(pady=(0, 40))

        # Loading bar
        self.bar_frame = tk.Frame(center, bg=BORDER, height=3, width=260)
        self.bar_frame.pack(pady=(0, 8))
        self.bar_frame.pack_propagate(False)
        self.bar_fill = tk.Frame(self.bar_frame, bg=ACCENT, height=3, width=0)
        self.bar_fill.place(x=0, y=0, relheight=1)

        self.loading_label = tk.Label(
            center, text="Loading...", font=FONT_SMALL,
            bg=BG, fg=FG_DIM,
        )
        self.loading_label.pack()

        self._progress = 0
        self._animate()

    def _animate(self) -> None:
        self._progress += 8
        if self._progress > 100:
            self._progress = 100
        bar_width = int(260 * self._progress / 100)
        self.bar_fill.place(x=0, y=0, relheight=1, width=bar_width)

        if self._progress >= 100:
            self.root.after(200, self._fade_out)
        else:
            self.root.after(40, self._animate)

    def _fade_out(self) -> None:
        self.frame.destroy()
        self.on_done()


# ---------------------------------------------------------------------------
# Collapsible section
# ---------------------------------------------------------------------------

class CollapsibleCard:
    """A card with a clickable header that expands/collapses the content."""

    def __init__(self, parent: tk.Frame, title: str, icon: str = "",
                 accent: str = ACCENT, expanded: bool = True) -> None:
        self.expanded = expanded
        self.accent = accent

        self.outer = tk.Frame(parent, bg=BG)
        self.outer.pack(fill=tk.X, padx=16, pady=(10, 0))

        # Header bar — clickable
        self.header = tk.Frame(self.outer, bg=BG_CARD, cursor="hand2")
        self.header.pack(fill=tk.X)

        # Expand/collapse indicator
        arrow = ARROW_DOWN if expanded else ARROW_RIGHT
        self.arrow_label = tk.Label(
            self.header, text=arrow, font=FONT_SMALL,
            bg=BG_CARD, fg=FG_DIM, padx=8,
        )
        self.arrow_label.pack(side=tk.LEFT)

        # Icon
        if icon:
            tk.Label(
                self.header, text=icon, font=(_FAMILY, 13),
                bg=BG_CARD, fg=accent, padx=(0,),
            ).pack(side=tk.LEFT)

        # Title
        tk.Label(
            self.header, text=f"  {title}", font=FONT_SECTION,
            bg=BG_CARD, fg=accent, anchor=tk.W,
        ).pack(side=tk.LEFT, fill=tk.X)

        # Content area
        self.content = tk.Frame(
            self.outer, bg=BG_CARD,
            highlightbackground=BORDER, highlightthickness=1,
        )
        if expanded:
            self.content.pack(fill=tk.X, pady=(0, 0))

        # Bind click on entire header
        for widget in (self.header, self.arrow_label):
            widget.bind("<Button-1>", self._toggle)
        for child in self.header.winfo_children():
            child.bind("<Button-1>", self._toggle)

    def _toggle(self, event=None) -> None:
        self.expanded = not self.expanded
        if self.expanded:
            self.content.pack(fill=tk.X, pady=(0, 0))
            self.arrow_label.configure(text=ARROW_DOWN)
        else:
            self.content.pack_forget()
            self.arrow_label.configure(text=ARROW_RIGHT)

    @property
    def frame(self) -> tk.Frame:
        return self.content


# ---------------------------------------------------------------------------
# Main application
# ---------------------------------------------------------------------------

class LynxFAGUI:
    """Tkinter GUI application for Lynx Fundamental Analysis."""

    def __init__(self, cli_args) -> None:
        self.cli_args = cli_args
        self._current_report: AnalysisReport | None = None
        self._sections: list[CollapsibleCard] = []
        self._suppress_news_dialog: bool = False

        self.root = tk.Tk()
        self.root.title(f"{DIAMOND} Lynx Fundamental Analysis {DIAMOND}")
        self.root.configure(bg=BG)
        self.root.geometry("1150x900")
        self.root.minsize(960, 640)

        # Configure ttk scrollbar style
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Vertical.TScrollbar",
                        background=BORDER, troughcolor=BG,
                        arrowcolor=FG_DIM, borderwidth=0)

        # Show splash, then build UI
        self._splash = SplashScreen(self.root, self._after_splash)

    def _after_splash(self) -> None:
        self._build_toolbar()
        self._build_result_area()
        self._show_welcome()

        # Pre-fill and auto-analyze if ticker given
        identifier = getattr(self.cli_args, "identifier", None)
        if identifier:
            self.entry_ticker.insert(0, identifier)
            self.root.after(100, self._on_analyze)

    # ---- Toolbar ---------------------------------------------------------

    def _build_toolbar(self) -> None:
        toolbar = tk.Frame(self.root, bg=BG_SURFACE, pady=8, padx=16)
        toolbar.pack(fill=tk.X)

        # Left side: branding
        brand = tk.Frame(toolbar, bg=BG_SURFACE)
        brand.pack(side=tk.LEFT, padx=(0, 20))

        tk.Label(
            brand, text=f"{DIAMOND} LYNX FA", font=(_FAMILY, 14, "bold"),
            bg=BG_SURFACE, fg=ACCENT,
        ).pack(side=tk.LEFT)

        # Separator
        sep = tk.Frame(toolbar, bg=BORDER, width=1, height=30)
        sep.pack(side=tk.LEFT, padx=(0, 16), fill=tk.Y)

        # Ticker input
        tk.Label(
            toolbar, text="Ticker:", font=FONT_SMALL_BOLD,
            bg=BG_SURFACE, fg=FG_DIM,
        ).pack(side=tk.LEFT, padx=(0, 6))

        self.entry_ticker = tk.Entry(
            toolbar, font=FONT, width=16, bg=BG_INPUT, fg=FG,
            insertbackground=FG, relief=tk.FLAT, highlightthickness=2,
            highlightcolor=ACCENT, highlightbackground=BORDER,
        )
        self.entry_ticker.pack(side=tk.LEFT, padx=(0, 10), ipady=3)

        # Analyze button
        self.btn_analyze = tk.Button(
            toolbar, text=f"  {STAR} Analyze  ", font=FONT_BTN,
            bg=BTN_BG, fg=BTN_FG,
            activebackground=BTN_ACTIVE, activeforeground=BTN_FG,
            relief=tk.FLAT, padx=14, pady=4, cursor="hand2",
            command=self._on_analyze,
        )
        self.btn_analyze.pack(side=tk.LEFT, padx=(0, 6))

        # Clear button
        self.btn_clear = tk.Button(
            toolbar, text="  Clear  ", font=FONT_BTN,
            bg=BTN_SECONDARY_BG, fg=BTN_SECONDARY_FG,
            activebackground=BG_HOVER, activeforeground=FG,
            relief=tk.FLAT, padx=10, pady=4, cursor="hand2",
            command=self._on_clear,
        )
        self.btn_clear.pack(side=tk.LEFT, padx=(0, 12))

        # Options row (checkboxes)
        opts = tk.Frame(toolbar, bg=BG_SURFACE)
        opts.pack(side=tk.LEFT, padx=(0, 8))

        self.var_refresh = tk.BooleanVar(
            value=getattr(self.cli_args, "refresh", False))
        self.var_no_reports = tk.BooleanVar(
            value=getattr(self.cli_args, "no_reports", False))
        self.var_no_news = tk.BooleanVar(
            value=getattr(self.cli_args, "no_news", False))

        for text, var in [("Refresh", self.var_refresh),
                          ("Skip filings", self.var_no_reports),
                          ("Skip news", self.var_no_news)]:
            cb = tk.Checkbutton(
                opts, text=text, variable=var,
                font=FONT_SMALL, bg=BG_SURFACE, fg=FG_DIM,
                selectcolor=BG_INPUT, activebackground=BG_SURFACE,
                activeforeground=FG, highlightthickness=0,
            )
            cb.pack(side=tk.LEFT, padx=(0, 6))

        # Status (right-aligned)
        self.status_var = tk.StringVar(value="")
        self.status_label = tk.Label(
            toolbar, textvariable=self.status_var, font=FONT_SMALL,
            bg=BG_SURFACE, fg=FG_DIM, anchor=tk.E,
        )
        self.status_label.pack(side=tk.RIGHT, padx=(8, 0))

        # Expand all / Collapse all buttons (right side)
        self.btn_expand = tk.Button(
            toolbar, text=" Expand All ", font=FONT_BTN,
            bg=BTN_SECONDARY_BG, fg=BTN_SECONDARY_FG,
            activebackground=BG_HOVER, activeforeground=FG,
            relief=tk.FLAT, padx=6, pady=3, cursor="hand2",
            command=lambda: self._toggle_all(True),
        )
        self.btn_expand.pack(side=tk.RIGHT, padx=(2, 0))

        self.btn_collapse = tk.Button(
            toolbar, text=" Collapse All ", font=FONT_BTN,
            bg=BTN_SECONDARY_BG, fg=BTN_SECONDARY_FG,
            activebackground=BG_HOVER, activeforeground=FG,
            relief=tk.FLAT, padx=6, pady=3, cursor="hand2",
            command=lambda: self._toggle_all(False),
        )
        self.btn_collapse.pack(side=tk.RIGHT, padx=(2, 0))

        # About button (right side, before expand/collapse)
        self.btn_about = tk.Button(
            toolbar, text="  About  ", font=FONT_BTN,
            bg=BTN_SECONDARY_BG, fg=BTN_SECONDARY_FG,
            activebackground=BG_HOVER, activeforeground=FG,
            relief=tk.FLAT, padx=6, pady=3, cursor="hand2",
            command=self._on_about,
        )
        self.btn_about.pack(side=tk.RIGHT, padx=(8, 0))

        # Bind Enter key
        self.entry_ticker.bind("<Return>", lambda _: self._on_analyze())
        # Bind Escape to clear
        self.root.bind("<Escape>", lambda _: self._on_clear())

    # ---- Scrollable result area ------------------------------------------

    def _build_result_area(self) -> None:
        container = tk.Frame(self.root, bg=BG)
        container.pack(fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(container, bg=BG, highlightthickness=0)
        scrollbar = ttk.Scrollbar(
            container, orient=tk.VERTICAL, command=self.canvas.yview,
        )
        self.scroll_frame = tk.Frame(self.canvas, bg=BG)

        self.scroll_frame.bind(
            "<Configure>",
            lambda _: self.canvas.configure(scrollregion=self.canvas.bbox("all")),
        )
        self.canvas_window = self.canvas.create_window(
            (0, 0), window=self.scroll_frame, anchor=tk.NW,
        )
        self.canvas.configure(yscrollcommand=scrollbar.set)

        self.canvas.bind(
            "<Configure>",
            lambda e: self.canvas.itemconfig(self.canvas_window, width=e.width),
        )

        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Mouse wheel scrolling (Linux + Windows)
        self.canvas.bind_all(
            "<MouseWheel>",
            lambda e: self.canvas.yview_scroll(-1 * (e.delta // 120), "units"),
        )
        self.canvas.bind_all(
            "<Button-4>",
            lambda _: self.canvas.yview_scroll(-3, "units"),
        )
        self.canvas.bind_all(
            "<Button-5>",
            lambda _: self.canvas.yview_scroll(3, "units"),
        )

    # ---- Welcome screen --------------------------------------------------

    def _show_welcome(self) -> None:
        """Show an empty-state welcome message."""
        for child in self.scroll_frame.winfo_children():
            child.destroy()
        self._sections.clear()

        center = tk.Frame(self.scroll_frame, bg=BG)
        center.pack(expand=True, fill=tk.BOTH, pady=80)

        tk.Label(
            center, text=DIAMOND, font=(_FAMILY, 48),
            bg=BG, fg=ACCENT_DIM,
        ).pack(pady=(0, 16))

        tk.Label(
            center, text="Enter a ticker symbol and press Analyze",
            font=FONT_SUBTITLE, bg=BG, fg=FG_DIM,
        ).pack(pady=(0, 8))

        tk.Label(
            center, text="e.g. AAPL, MSFT, OCO.V, AT1.DE, or an ISIN",
            font=FONT_SMALL, bg=BG, fg=FG_SUBTLE,
        ).pack(pady=(0, 24))

        # Keyboard hints
        hints = tk.Frame(center, bg=BG)
        hints.pack()
        for key, action in [("Enter", "Analyze"), ("Escape", "Clear"),
                            ("Scroll", "Navigate results")]:
            row = tk.Frame(hints, bg=BG)
            row.pack(anchor=tk.W, pady=1)
            tk.Label(
                row, text=f"  {key}  ", font=FONT_SMALL_BOLD,
                bg=BORDER, fg=FG, padx=4,
            ).pack(side=tk.LEFT, padx=(0, 8))
            tk.Label(
                row, text=action, font=FONT_SMALL,
                bg=BG, fg=FG_DIM,
            ).pack(side=tk.LEFT)

    # ---- Actions ---------------------------------------------------------

    def _on_analyze(self) -> None:
        ticker = self.entry_ticker.get().strip()
        if not ticker:
            self.status_var.set(f"{WARN_ICON}  Enter a ticker or ISIN")
            return

        self.btn_analyze.configure(state=tk.DISABLED)
        self.btn_clear.configure(state=tk.DISABLED)
        self.status_var.set(f"Analysing {ticker}...")

        thread = threading.Thread(
            target=self._run_analysis, args=(ticker,), daemon=True,
        )
        thread.start()

    def _on_clear(self) -> None:
        self.entry_ticker.delete(0, tk.END)
        self._current_report = None
        self.status_var.set("")
        self._show_welcome()
        self.entry_ticker.focus_set()

    def _on_about(self) -> None:
        from lynx import get_about_text
        about = get_about_text()

        win = tk.Toplevel(self.root)
        win.title(f"{DIAMOND} About Lynx FA")
        win.configure(bg=BG)
        win.geometry("620x560")
        win.resizable(False, False)
        win.transient(self.root)
        win.grab_set()

        # Title
        tk.Label(
            win, text=f"{DIAMOND}  {about['name']}  {DIAMOND}",
            font=(_FAMILY, 18, "bold"), bg=BG, fg=ACCENT,
        ).pack(pady=(24, 4))

        tk.Label(
            win, text=f"Version {about['version']} ({about['year']})",
            font=FONT_SMALL, bg=BG, fg=FG_DIM,
        ).pack(pady=(0, 16))

        # Author info
        info_frame = tk.Frame(win, bg=BG_CARD, padx=20, pady=12)
        info_frame.pack(fill=tk.X, padx=24, pady=(0, 12))

        for label, value in [
            ("Developed by", about["author"]),
            ("Contact", about["email"]),
            ("License", about["license"]),
        ]:
            row = tk.Frame(info_frame, bg=BG_CARD)
            row.pack(fill=tk.X, pady=2)
            tk.Label(
                row, text=f"{label}:", font=FONT_BOLD,
                bg=BG_CARD, fg=ACCENT, width=14, anchor=tk.E,
            ).pack(side=tk.LEFT, padx=(0, 8))
            tk.Label(
                row, text=value, font=FONT,
                bg=BG_CARD, fg=FG, anchor=tk.W,
            ).pack(side=tk.LEFT)

        # Description
        tk.Label(
            win, text=about["description"], font=FONT_SMALL,
            bg=BG, fg=FG_DIM, wraplength=560, justify=tk.CENTER,
        ).pack(padx=24, pady=(0, 12))

        # License text in scrollable frame
        license_frame = tk.Frame(win, bg=BG_CARD)
        license_frame.pack(fill=tk.BOTH, expand=True, padx=24, pady=(0, 12))

        tk.Label(
            license_frame, text="BSD 3-Clause License",
            font=FONT_SMALL_BOLD, bg=BG_CARD, fg=ACCENT,
        ).pack(pady=(8, 4))

        license_text = tk.Text(
            license_frame, font=FONT_SMALL, bg=BG_CARD, fg=FG_DIM,
            wrap=tk.WORD, relief=tk.FLAT, height=12,
            highlightthickness=0, padx=12, pady=4,
        )
        license_text.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0, 8))
        license_text.insert("1.0", about["license_text"])
        license_text.configure(state=tk.DISABLED)

        # Close button
        tk.Button(
            win, text="  Close  ", font=FONT_BTN,
            bg=BTN_BG, fg=BTN_FG,
            activebackground=BTN_ACTIVE, activeforeground=BTN_FG,
            relief=tk.FLAT, padx=16, pady=4, cursor="hand2",
            command=win.destroy,
        ).pack(pady=(0, 16))

        win.bind("<Escape>", lambda _: win.destroy())

    def _toggle_all(self, expand: bool) -> None:
        for card in self._sections:
            if expand and not card.expanded:
                card._toggle()
            elif not expand and card.expanded:
                card._toggle()

    def _run_analysis(self, identifier: str) -> None:
        try:
            from lynx.core.analyzer import run_full_analysis
            from lynx.core.storage import is_testing

            refresh = self.var_refresh.get() or is_testing()

            self.root.after(0, self.status_var.set, f"Fetching data for {identifier}...")

            report = run_full_analysis(
                identifier=identifier,
                download_reports=not self.var_no_reports.get(),
                download_news=not self.var_no_news.get(),
                max_filings=getattr(self.cli_args, "max_filings", 10),
                verbose=getattr(self.cli_args, "verbose", False),
                refresh=refresh,
            )

            self.root.after(0, self._display_report, report)

        except Exception as e:
            msg = str(e) or type(e).__name__
            try:
                self.root.after(
                    0, lambda: (
                        self.status_var.set(f"{WARN_ICON}  Error"),
                        self.btn_analyze.configure(state=tk.NORMAL),
                        self.btn_clear.configure(state=tk.NORMAL),
                        messagebox.showerror("Analysis Error", msg),
                    ),
                )
            except tk.TclError:
                pass  # Root window was destroyed

    # ---- Display report --------------------------------------------------

    def _display_report(self, report: AnalysisReport) -> None:
        self._current_report = report
        p = report.profile
        self.status_var.set(
            f"{CHECK}  {_s(p.name)} ({_s(p.ticker)})  {BULLET}  {_safe_tier(p.tier)}"
        )
        self.btn_analyze.configure(state=tk.NORMAL)
        self.btn_clear.configure(state=tk.NORMAL)

        # Clear
        for child in self.scroll_frame.winfo_children():
            child.destroy()
        self._sections.clear()

        # Tier banner
        self._render_tier_banner(report)

        # Sections
        self._render_profile(report)
        self._render_valuation(report)
        self._render_profitability(report)
        self._render_solvency(report)
        self._render_growth(report)
        self._render_moat(report)
        self._render_intrinsic_value(report)
        self._render_financials(report)
        self._render_filings(report)
        self._render_news(report)

        # Bottom padding
        tk.Frame(self.scroll_frame, bg=BG, height=24).pack(fill=tk.X)

        self.canvas.yview_moveto(0)

    # ---- Tier banner -----------------------------------------------------

    def _render_tier_banner(self, r: AnalysisReport) -> None:
        p = r.profile
        tier = p.tier
        fg_col, bg_col = TIER_COLORS.get(tier, (ACCENT, BG_CARD))

        banner = tk.Frame(self.scroll_frame, bg=bg_col, pady=12, padx=20)
        banner.pack(fill=tk.X, padx=16, pady=(12, 0))

        # Company name row
        name_row = tk.Frame(banner, bg=bg_col)
        name_row.pack(fill=tk.X)

        tk.Label(
            name_row, text=_s(p.name), font=(_FAMILY, 18, "bold"),
            bg=bg_col, fg=FG, anchor=tk.W,
        ).pack(side=tk.LEFT)

        tk.Label(
            name_row, text=f"  ({_s(p.ticker)})", font=(_FAMILY, 14),
            bg=bg_col, fg=FG_DIM, anchor=tk.W,
        ).pack(side=tk.LEFT)

        if p.isin:
            tk.Label(
                name_row, text=f"  ISIN: {p.isin}", font=FONT_SMALL,
                bg=bg_col, fg=FG_SUBTLE, anchor=tk.W,
            ).pack(side=tk.LEFT, padx=(12, 0))

        # Info row
        info_row = tk.Frame(banner, bg=bg_col)
        info_row.pack(fill=tk.X, pady=(6, 0))

        # Tier badge
        badge_frame = tk.Frame(info_row, bg=fg_col, padx=8, pady=2)
        badge_frame.pack(side=tk.LEFT, padx=(0, 12))
        tk.Label(
            badge_frame, text=_safe_tier(tier), font=FONT_TIER,
            bg=fg_col, fg=BG,
        ).pack()

        # Quick stats
        parts = []
        if p.sector:
            parts.append(p.sector)
        if p.industry:
            parts.append(p.industry)
        if p.country:
            parts.append(p.country)
        if p.market_cap:
            parts.append(f"MCap: {_money(p.market_cap)}")

        if parts:
            tk.Label(
                info_row, text=f"  {BULLET}  ".join(parts), font=FONT_SMALL,
                bg=bg_col, fg=FG_DIM, anchor=tk.W,
            ).pack(side=tk.LEFT)

    # ---- Profile ---------------------------------------------------------

    def _render_profile(self, r: AnalysisReport) -> None:
        p = r.profile
        card = CollapsibleCard(
            self.scroll_frame, "Company Profile",
            icon=ICON_PROFILE, accent=ACCENT,
        )
        self._sections.append(card)
        frame = card.frame

        rows = [
            ("Company", _s(p.name)),
            ("Ticker", _s(p.ticker)),
            ("ISIN", _s(p.isin)),
            ("Tier", _safe_tier(p.tier)),
            ("Sector", _s(p.sector)),
            ("Industry", _s(p.industry)),
            ("Country", _s(p.country)),
            ("Exchange", _s(p.exchange)),
            ("Currency", _s(p.currency)),
            ("Market Cap", _money(p.market_cap)),
            ("Employees", f"{p.employees:,}" if p.employees else "N/A"),
        ]
        if p.website:
            rows.append(("Website", p.website))

        for i, (label, value) in enumerate(rows):
            self._add_row(frame, i, label, value)

        if p.description:
            sep = tk.Frame(frame, bg=BORDER, height=1)
            sep.pack(fill=tk.X, padx=12, pady=6)
            tk.Label(
                frame, text=p.description, font=FONT_SMALL,
                bg=BG_CARD, fg=FG_DIM, wraplength=900,
                justify=tk.LEFT, anchor=tk.NW, padx=16, pady=6,
            ).pack(fill=tk.X)

    # ---- Valuation -------------------------------------------------------

    def _render_valuation(self, r: AnalysisReport) -> None:
        v = r.valuation
        card = CollapsibleCard(
            self.scroll_frame, "Valuation",
            icon=ICON_VALUATION, accent=YELLOW,
        )
        self._sections.append(card)
        frame = card.frame
        rows = [
            ("P/E (Trailing)", _num(v.pe_trailing), _ape(v.pe_trailing)),
            ("P/E (Forward)", _num(v.pe_forward), _ape(v.pe_forward)),
            ("P/B Ratio", _num(v.pb_ratio), _thr(v.pb_ratio, [(1, "Below Book"), (1.5, "Cheap"), (3, "Fair")], "Premium")),
            ("P/S Ratio", _num(v.ps_ratio), ""),
            ("P/FCF", _num(v.p_fcf), _thr(v.p_fcf, [(10, "Cheap"), (20, "Fair")], "Expensive")),
            ("EV/EBITDA", _num(v.ev_ebitda), _thr(v.ev_ebitda, [(8, "Cheap"), (12, "Fair"), (18, "Expensive")], "Very Expensive")),
            ("EV/Revenue", _num(v.ev_revenue), ""),
            ("PEG Ratio", _num(v.peg_ratio), _thr(v.peg_ratio, [(1, "Undervalued"), (2, "Fair")], "Overvalued")),
            ("Earnings Yield", _pct(v.earnings_yield), ""),
            ("Dividend Yield", _pct(v.dividend_yield), ""),
            ("P/Tangible Book", _num(v.price_to_tangible_book), _thr(v.price_to_tangible_book, [(0.67, "Deep Value"), (1, "Below Book"), (1.5, "Near Book")], "Premium")),
            ("P/NCAV (Net-Net)", _num(v.price_to_ncav), _thr(v.price_to_ncav, [(0.67, "Classic Net-Net"), (1, "Below NCAV"), (1.5, "Near NCAV")], "Above NCAV")),
            ("Enterprise Value", _money(v.enterprise_value), ""),
            ("Market Cap", _money(v.market_cap), ""),
        ]
        for i, (label, value, assessment) in enumerate(rows):
            self._add_metric_row(frame, i, label, value, assessment)

    # ---- Profitability ---------------------------------------------------

    def _render_profitability(self, r: AnalysisReport) -> None:
        p = r.profitability
        card = CollapsibleCard(
            self.scroll_frame, "Profitability",
            icon=ICON_PROFIT, accent=GREEN,
        )
        self._sections.append(card)
        frame = card.frame
        rows = [
            ("ROE", _pct(p.roe), _thr(p.roe, [(0, "Negative"), (0.10, "Below Avg"), (0.15, "Good"), (0.20, "Excellent")], "Outstanding")),
            ("ROA", _pct(p.roa), _thr(p.roa, [(0, "Negative"), (0.05, "Low"), (0.10, "Good")], "Excellent")),
            ("ROIC", _pct(p.roic), _thr(p.roic, [(0, "Negative"), (0.07, "Below WACC"), (0.10, "Good"), (0.15, "Wide Moat")], "Exceptional")),
            ("Gross Margin", _pct(p.gross_margin), ""),
            ("Operating Margin", _pct(p.operating_margin), ""),
            ("Net Margin", _pct(p.net_margin), ""),
            ("FCF Margin", _pct(p.fcf_margin), ""),
            ("EBITDA Margin", _pct(p.ebitda_margin), ""),
        ]
        for i, (label, value, assessment) in enumerate(rows):
            self._add_metric_row(frame, i, label, value, assessment)

    # ---- Solvency --------------------------------------------------------

    def _render_solvency(self, r: AnalysisReport) -> None:
        s = r.solvency
        card = CollapsibleCard(
            self.scroll_frame, "Solvency & Financial Health",
            icon=ICON_SOLVENCY, accent=RED,
        )
        self._sections.append(card)
        frame = card.frame
        rows = [
            ("Debt/Equity", _num(s.debt_to_equity), _thr(s.debt_to_equity, [(0.3, "Very Conservative"), (0.5, "Conservative"), (1.0, "Moderate"), (2.0, "High")], "Very High")),
            ("Debt/EBITDA", _num(s.debt_to_ebitda), _thr(s.debt_to_ebitda, [(1, "Very Low"), (2, "Manageable"), (3, "Moderate")], "Heavy")),
            ("Current Ratio", _num(s.current_ratio), _thr(s.current_ratio, [(1.0, "Liquidity Risk"), (1.5, "Adequate"), (2.0, "Good")], "Strong")),
            ("Quick Ratio", _num(s.quick_ratio), ""),
            ("Interest Coverage", _num(s.interest_coverage, 1), ""),
            ("Altman Z-Score", _num(s.altman_z_score), _thr(s.altman_z_score, [(1.81, "Distress"), (2.99, "Grey Zone")], "Safe")),
            ("Cash Burn Rate (/yr)", _money(s.cash_burn_rate), _burn(s.cash_burn_rate)),
            ("Cash Runway", f"{s.cash_runway_years:.1f} yrs" if s.cash_runway_years is not None else "N/A", ""),
            ("Working Capital", _money(s.working_capital), ""),
            ("Cash Per Share", f"${s.cash_per_share:.2f}" if s.cash_per_share is not None else "N/A", ""),
            ("NCAV Per Share", f"${s.ncav_per_share:.4f}" if s.ncav_per_share is not None else "N/A", ""),
            ("Total Debt", _money(s.total_debt), ""),
            ("Total Cash", _money(s.total_cash), ""),
            ("Net Debt", _money(s.net_debt), ""),
        ]
        for i, (label, value, assessment) in enumerate(rows):
            self._add_metric_row(frame, i, label, value, assessment)

    # ---- Growth ----------------------------------------------------------

    def _render_growth(self, r: AnalysisReport) -> None:
        g = r.growth
        card = CollapsibleCard(
            self.scroll_frame, "Growth",
            icon=ICON_GROWTH, accent=MAUVE,
        )
        self._sections.append(card)
        frame = card.frame
        rows = [
            ("Revenue Growth (YoY)", _pct(g.revenue_growth_yoy)),
            ("Revenue CAGR (3Y)", _pct(g.revenue_cagr_3y)),
            ("Revenue CAGR (5Y)", _pct(g.revenue_cagr_5y)),
            ("Earnings Growth (YoY)", _pct(g.earnings_growth_yoy)),
            ("Earnings CAGR (3Y)", _pct(g.earnings_cagr_3y)),
            ("Earnings CAGR (5Y)", _pct(g.earnings_cagr_5y)),
            ("FCF Growth (YoY)", _pct(g.fcf_growth_yoy)),
            ("Book Value Growth (YoY)", _pct(g.book_value_growth_yoy)),
            ("Share Dilution (YoY)", _pct(g.shares_growth_yoy)),
        ]
        for i, (label, value) in enumerate(rows):
            self._add_row(frame, i, label, value)

    # ---- Moat ------------------------------------------------------------

    def _render_moat(self, r: AnalysisReport) -> None:
        m = r.moat
        tier = _get_tier(r)
        card = CollapsibleCard(
            self.scroll_frame, "Moat Indicators",
            icon=ICON_MOAT, accent=YELLOW,
        )
        self._sections.append(card)
        frame = card.frame

        # Moat score bar
        if m.moat_score is not None:
            self._render_score_bar(frame, m.moat_score)

        rows: list[tuple[str, str]] = [
            ("Competitive Position", _s(m.competitive_position)),
        ]

        if tier in (CompanyTier.MEGA, CompanyTier.LARGE, CompanyTier.MID):
            rows += [
                ("ROIC Consistency", _s(m.roic_consistency)),
                ("Margin Stability", _s(m.margin_stability)),
                ("Revenue Predictability", _s(m.revenue_predictability)),
                ("Scale", _s(m.efficient_scale)),
                ("Switching Costs", _s(m.switching_costs) or "Review needed"),
                ("Network Effects", _s(m.network_effects) or "Review needed"),
                ("Cost Advantages", _s(m.cost_advantages) or "Not detected"),
                ("Intangible Assets", _s(m.intangible_assets) or "Not detected"),
            ]
        else:
            rows += [
                ("Asset Backing", _s(m.asset_backing)),
                ("Revenue Status", _s(m.revenue_predictability)),
                ("Niche Position", _s(m.niche_position)),
                ("Dilution/Insider", _s(m.insider_alignment)),
            ]
            if m.intangible_assets:
                rows.append(("Intangible Assets", _s(m.intangible_assets)))
            if m.cost_advantages:
                rows.append(("Cost Advantages", _s(m.cost_advantages)))

        for i, (label, value) in enumerate(rows):
            self._add_row(frame, i, label, value)

        if m.roic_history:
            sep = tk.Frame(frame, bg=BORDER, height=1)
            sep.pack(fill=tk.X, padx=12, pady=6)
            trend = " \u2192 ".join(_pctplain(x) for x in reversed(m.roic_history))
            tk.Label(
                frame, text=f"  ROIC Trend:  {trend}",
                font=FONT_MONO, bg=BG_CARD, fg=FG_DIM,
                anchor=tk.W, padx=16, pady=2,
            ).pack(fill=tk.X)

        if m.gross_margin_history:
            trend = " \u2192 ".join(_pctplain(x) for x in reversed(m.gross_margin_history))
            tk.Label(
                frame, text=f"  GM Trend:    {trend}",
                font=FONT_MONO, bg=BG_CARD, fg=FG_DIM,
                anchor=tk.W, padx=16, pady=2,
            ).pack(fill=tk.X)

    def _render_score_bar(self, parent: tk.Frame, score: float) -> None:
        """Render a visual moat score bar."""
        bar_row = tk.Frame(parent, bg=BG_CARD, pady=8, padx=16)
        bar_row.pack(fill=tk.X)

        tk.Label(
            bar_row, text="Moat Score", font=FONT_BOLD,
            bg=BG_CARD, fg=ACCENT, anchor=tk.E, width=22,
        ).pack(side=tk.LEFT, padx=(0, 8))

        # Score bar container
        bar_outer = tk.Frame(bar_row, bg=BORDER, height=18, width=200)
        bar_outer.pack(side=tk.LEFT, padx=(0, 8))
        bar_outer.pack_propagate(False)

        # Determine color
        if score >= 70:
            bar_color = GREEN
        elif score >= 45:
            bar_color = YELLOW
        elif score >= 20:
            bar_color = ORANGE
        else:
            bar_color = RED

        fill_width = max(1, int(200 * score / 100))
        bar_fill = tk.Frame(bar_outer, bg=bar_color, height=18)
        bar_fill.place(x=0, y=0, relheight=1, width=fill_width)

        tk.Label(
            bar_row, text=f"{score:.1f}/100", font=FONT_BOLD,
            bg=BG_CARD, fg=bar_color,
        ).pack(side=tk.LEFT)

    # ---- Intrinsic Value -------------------------------------------------

    def _render_intrinsic_value(self, r: AnalysisReport) -> None:
        iv = r.intrinsic_value
        card = CollapsibleCard(
            self.scroll_frame, "Intrinsic Value",
            icon=ICON_VALUE, accent=TEAL,
        )
        self._sections.append(card)
        frame = card.frame

        primary = _s(iv.primary_method)
        secondary = _s(iv.secondary_method)

        def tag(n: str) -> str:
            if n in primary:
                return "(primary) "
            if n in secondary:
                return "(secondary) "
            return ""

        rows = [
            ("Current Price", f"${iv.current_price:.2f}" if iv.current_price else "N/A", ""),
            (f"{tag('DCF')}DCF (10Y)", f"${iv.dcf_value:.2f}" if iv.dcf_value else "N/A", _mos(iv.margin_of_safety_dcf)),
            (f"{tag('Graham')}Graham Number", f"${iv.graham_number:.2f}" if iv.graham_number else "N/A", _mos(iv.margin_of_safety_graham)),
            (f"{tag('NCAV')}NCAV (Net-Net)", f"${iv.ncav_value:.4f}" if iv.ncav_value is not None else "N/A", _mos(iv.margin_of_safety_ncav)),
            (f"{tag('Asset')}Tangible Book", f"${iv.asset_based_value:.4f}" if iv.asset_based_value else "N/A", _mos(iv.margin_of_safety_asset)),
        ]
        if iv.lynch_fair_value:
            rows.append(("Lynch Fair Value", f"${iv.lynch_fair_value:.2f}", ""))

        for i, (label, value, assessment) in enumerate(rows):
            self._add_metric_row(frame, i, label, value, assessment)

    # ---- Financials ------------------------------------------------------

    def _render_financials(self, r: AnalysisReport) -> None:
        if not r.financials:
            return
        card = CollapsibleCard(
            self.scroll_frame, f"Financial Statements ({len(r.financials[:5])}Y)",
            icon=ICON_FINANCE, accent=SKY,
        )
        self._sections.append(card)
        frame = card.frame

        cols = ["Period", "Revenue", "Gross Profit", "Op Income",
                "Net Income", "FCF", "Equity", "Debt"]
        hdr = tk.Frame(frame, bg=BG_SURFACE)
        hdr.pack(fill=tk.X)
        for col in cols:
            tk.Label(
                hdr, text=col, font=FONT_SMALL_BOLD, bg=BG_SURFACE, fg=ACCENT,
                width=14, anchor=tk.CENTER, pady=4,
            ).pack(side=tk.LEFT, padx=1)

        for i, st in enumerate(r.financials[:5]):
            bg = BG_INPUT if i % 2 == 0 else BG_CARD
            row = tk.Frame(frame, bg=bg)
            row.pack(fill=tk.X)
            vals = [
                _s(st.period), _money(st.revenue), _money(st.gross_profit),
                _money(st.operating_income), _money(st.net_income),
                _money(st.free_cash_flow), _money(st.total_equity),
                _money(st.total_debt),
            ]
            for val in vals:
                tk.Label(
                    row, text=val, font=FONT_SMALL, bg=bg, fg=FG,
                    width=14, anchor=tk.CENTER, pady=3,
                ).pack(side=tk.LEFT, padx=1)

    # ---- Filings ---------------------------------------------------------

    def _render_filings(self, r: AnalysisReport) -> None:
        if not r.filings:
            return
        card = CollapsibleCard(
            self.scroll_frame, f"SEC Filings ({len(r.filings)})",
            icon=ICON_FILING, accent=PEACH,
        )
        self._sections.append(card)
        frame = card.frame

        cols = ["Type", "Filed", "Period", "Saved", ""]
        hdr = tk.Frame(frame, bg=BG_SURFACE)
        hdr.pack(fill=tk.X)
        widths = [14, 18, 18, 10, 12]
        for col, w in zip(cols, widths):
            tk.Label(
                hdr, text=col, font=FONT_SMALL_BOLD, bg=BG_SURFACE, fg=ACCENT,
                width=w, anchor=tk.CENTER, pady=4,
            ).pack(side=tk.LEFT, padx=1)

        for i, f in enumerate(r.filings[:20]):
            bg = BG_INPUT if i % 2 == 0 else BG_CARD
            row = tk.Frame(frame, bg=bg)
            row.pack(fill=tk.X)
            vals = [
                (_s(f.form_type), 14),
                (_s(f.filing_date), 18),
                (_s(f.period), 18),
                (f"{CHECK} Yes" if f.local_path else "No", 10),
            ]
            for val, w in vals:
                fg_color = GREEN if val.startswith(CHECK) else FG
                tk.Label(
                    row, text=val, font=FONT_SMALL, bg=bg, fg=fg_color,
                    width=w, anchor=tk.CENTER, pady=3,
                ).pack(side=tk.LEFT, padx=1)
            # Download button
            filing = f
            btn = tk.Button(
                row, text="Download", font=FONT_SMALL,
                bg=BTN_SECONDARY_BG, fg=BTN_SECONDARY_FG,
                activebackground=BG_HOVER, activeforeground=FG,
                relief=tk.FLAT, padx=4, pady=1, cursor="hand2",
                command=lambda fl=filing: self._download_filing_gui(fl),
            )
            btn.pack(side=tk.LEFT, padx=4)

    # ---- News ------------------------------------------------------------

    def _render_news(self, r: AnalysisReport) -> None:
        if not r.news:
            return
        card = CollapsibleCard(
            self.scroll_frame, f"News ({len(r.news)})",
            icon=ICON_NEWS, accent=PINK,
        )
        self._sections.append(card)
        frame = card.frame

        for i, n in enumerate(r.news[:20]):
            bg = BG_INPUT if i % 2 == 0 else BG_CARD
            row = tk.Frame(frame, bg=bg, pady=3)
            row.pack(fill=tk.X)

            title = (n.title or "")[:80] + ("..." if len(n.title or "") > 80 else "")
            meta = f"{_s(n.source)}  {BULLET}  {_s(n.published)}"

            tk.Label(
                row, text=f" {i + 1}.", font=FONT_SMALL_BOLD, bg=bg, fg=FG_DIM,
                anchor=tk.E, width=4,
            ).pack(side=tk.LEFT, padx=(8, 4))
            tk.Label(
                row, text=title, font=FONT, bg=bg, fg=FG,
                anchor=tk.W,
            ).pack(side=tk.LEFT, padx=(0, 8))

            # Open in browser button
            if n.url:
                article = n
                btn = tk.Button(
                    row, text="Open", font=FONT_SMALL,
                    bg=BTN_SECONDARY_BG, fg=BTN_SECONDARY_FG,
                    activebackground=BG_HOVER, activeforeground=FG,
                    relief=tk.FLAT, padx=4, pady=1, cursor="hand2",
                    command=lambda art=article: self._open_news_gui(art),
                )
                btn.pack(side=tk.RIGHT, padx=(4, 12))

            tk.Label(
                row, text=meta, font=FONT_SMALL, bg=bg, fg=FG_SUBTLE,
                anchor=tk.E,
            ).pack(side=tk.RIGHT, padx=(0, 4))

    # ---- Filing download / News open --------------------------------------

    def _download_filing_gui(self, filing) -> None:
        if not self._current_report:
            return

        def _do():
            from lynx.core.reports import download_filing
            try:
                path = download_filing(self._current_report.profile.ticker, filing)
                if path:
                    self.root.after(0, lambda: messagebox.showinfo(
                        "Download Complete",
                        f"Filing {filing.form_type} ({filing.filing_date}) downloaded.\n\n"
                        f"Saved to:\n{path}",
                    ))
                else:
                    self.root.after(0, lambda: messagebox.showerror(
                        "Download Failed",
                        f"Could not download {filing.form_type} ({filing.filing_date}).",
                    ))
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror(
                    "Download Error", str(e),
                ))

        thread = threading.Thread(target=_do, daemon=True)
        thread.start()

    def _open_news_gui(self, article) -> None:
        import webbrowser
        if not article.url:
            return
        try:
            webbrowser.open(article.url)
        except Exception:
            pass

        if not self._suppress_news_dialog:
            result = messagebox.askyesno(
                "News Opened",
                "News article has been opened in your default browser.\n\n"
                "Click 'Yes' to continue showing this message,\n"
                "or 'No' to suppress it for the rest of this session.",
            )
            if not result:
                self._suppress_news_dialog = True

    # ---- Row helpers -----------------------------------------------------

    def _add_row(self, frame: tk.Frame, idx: int, label: str, value: str) -> None:
        """Add a simple label-value row."""
        bg = BG_INPUT if idx % 2 == 0 else BG_CARD
        r = tk.Frame(frame, bg=bg)
        r.pack(fill=tk.X)
        tk.Label(
            r, text=label, font=FONT_BOLD, bg=bg, fg=ACCENT,
            width=26, anchor=tk.E, pady=3,
        ).pack(side=tk.LEFT, padx=(12, 6))
        tk.Label(
            r, text=value, font=FONT, bg=bg, fg=FG,
            anchor=tk.W, pady=3,
        ).pack(side=tk.LEFT, padx=(6, 12))

    def _add_metric_row(self, frame: tk.Frame, idx: int,
                        label: str, value: str, assessment: str) -> None:
        """Add a metric row with label, value, and assessment badge."""
        bg = BG_INPUT if idx % 2 == 0 else BG_CARD
        r = tk.Frame(frame, bg=bg)
        r.pack(fill=tk.X)
        tk.Label(
            r, text=label, font=FONT_BOLD, bg=bg, fg=ACCENT,
            width=22, anchor=tk.E, pady=3,
        ).pack(side=tk.LEFT, padx=(12, 6))
        tk.Label(
            r, text=value, font=FONT, bg=bg, fg=FG,
            width=16, anchor=tk.E, pady=3,
        ).pack(side=tk.LEFT, padx=(6, 8))
        if assessment:
            fg_color = _assessment_color(assessment)
            tk.Label(
                r, text=f" {assessment} ", font=FONT_SMALL,
                bg=bg, fg=fg_color, anchor=tk.W, pady=3,
            ).pack(side=tk.LEFT, padx=(4, 8))

    # ---- Run -------------------------------------------------------------

    def run(self) -> None:
        if hasattr(self, "entry_ticker"):
            self.entry_ticker.focus_set()
        self.root.mainloop()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _s(val) -> str:
    return str(val) if val is not None else "N/A"


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
        p = float(val) * 100
        if p > 25:
            return f"{p:.1f}% (Undervalued)"
        if p > 0:
            return f"{p:.1f}% (Slight Undervalue)"
        return f"{p:.1f}% (Overvalued)"
    except Exception:
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
    except Exception:
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
    except Exception:
        return ""


def _thr(val, thresholds, over_label) -> str:
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


def _get_tier(r: AnalysisReport) -> CompanyTier:
    try:
        tier = r.profile.tier
        if isinstance(tier, CompanyTier):
            return tier
    except Exception:
        pass
    return CompanyTier.NANO


def _assessment_color(text: str) -> str:
    """Pick a colour for assessment text based on sentiment."""
    t = text.lower()

    # Check neutral first — these override broader substring matches.
    neutral = ("slight undervalue", "below avg", "below wacc",
               "near book", "near ncav", "grey zone",
               "fair", "moderate", "manageable", "adequate")
    for word in neutral:
        if word in t:
            return YELLOW

    # Positive — ordered longest-first to avoid substring collisions.
    positive = ("not burning cash", "cash flow positive",
                "very conservative", "classic net-net",
                "below book", "below ncav", "deep value",
                "wide moat", "value range", "very low", "very cheap",
                "undervalue", "cheap", "good", "excellent", "outstanding",
                "exceptional", "strong", "safe", "conservative", "low")
    for word in positive:
        if word in t:
            return GREEN

    # Negative — checked last.
    negative = ("very expensive", "very high", "burning cash",
                "liquidity risk", "above ncav", "negative",
                "expensive", "overvalued", "distress",
                "heavy", "high", "premium")
    for word in negative:
        if word in t:
            return RED

    return FG_DIM


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def run_gui(args) -> None:
    """Launch the tkinter GUI."""
    app = LynxFAGUI(cli_args=args)
    app.run()
