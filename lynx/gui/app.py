"""Tkinter graphical user interface for Lynx Fundamental Analysis."""

from __future__ import annotations

import threading
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path
from typing import Optional

from lynx.models import AnalysisReport, CompanyTier
from lynx_investor_core.gui_themes import ThemeCycler, apply_theme
from lynx_investor_core.urlsafe import safe_webbrowser_open

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
        from lynx import __version__, __year__, __author__, SUITE_LABEL
        self.version = tk.Label(
            center, text=f"v{__version__}  {BULLET}  {__year__}  {BULLET}  {__author__}",
            font=FONT_SPLASH_VER, bg=BG, fg=FG_SUBTLE,
        )
        self.version.pack(pady=(0, 4))

        self.suite_label = tk.Label(
            center, text=SUITE_LABEL,
            font=FONT_SPLASH_VER, bg=BG, fg=FG_SUBTLE,
        )
        self.suite_label.pack(pady=(0, 40))

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
                 accent: str = ACCENT, expanded: bool = True,
                 info_command=None) -> None:
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

        # Section info button (right side of header)
        self._info_btn = None
        if info_command:
            self._info_btn = tk.Button(
                self.header, text=" ? ", font=(_FAMILY, 9, "bold"),
                bg=BORDER, fg=ACCENT, activebackground=BG_HOVER,
                activeforeground=FG, relief=tk.FLAT, padx=2, pady=0,
                cursor="hand2", command=info_command,
            )
            self._info_btn.pack(side=tk.RIGHT, padx=(0, 8))

        # Content area
        self.content = tk.Frame(
            self.outer, bg=BG_CARD,
            highlightbackground=BORDER, highlightthickness=1,
        )
        if expanded:
            self.content.pack(fill=tk.X, pady=(0, 0))

        # Bind click on entire header — but skip the info button so its
        # command fires without also toggling the section.
        for widget in (self.header, self.arrow_label):
            widget.bind("<Button-1>", self._toggle)
        for child in self.header.winfo_children():
            if child is not self._info_btn:
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
        self.root.title("Lynx Fundamental Analysis")
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

        # Suite-wide theme cycling (Ctrl+T / Ctrl+Shift+T)
        self._theme_cycler = ThemeCycler(self.root)
        self._theme_cycler.apply_current()
        self.root.bind_all("<Control-t>", lambda _: self._theme_cycler.next())
        self.root.bind_all("<Control-T>", lambda _: self._theme_cycler.previous())

        # Pre-fill and auto-analyze if ticker given
        identifier = getattr(self.cli_args, "identifier", None)
        if identifier:
            self.entry_ticker.insert(0, identifier)
            self.root.after(100, self._on_analyze)

    # ---- Toolbar ---------------------------------------------------------

    def _build_toolbar(self) -> None:
        toolbar = tk.Frame(self.root, bg=BG_SURFACE, pady=8, padx=16)
        toolbar.pack(fill=tk.X)

        # Left side: branding with logo
        brand = tk.Frame(toolbar, bg=BG_SURFACE)
        brand.pack(side=tk.LEFT, padx=(0, 20))

        # Toolbar logo
        self._toolbar_logo = None
        logo_path = Path(__file__).resolve().parent.parent.parent / "img" / "logo_sm_quarter_green.png"
        if logo_path.exists():
            try:
                self._toolbar_logo = tk.PhotoImage(file=str(logo_path))
                tk.Label(
                    brand, image=self._toolbar_logo, bg=BG_SURFACE,
                ).pack(side=tk.LEFT, padx=(0, 6))
            except tk.TclError:
                pass

        tk.Label(
            brand, text="Lynx Fundamental", font=(_FAMILY, 14, "bold"),
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

        # Export button (left group, after checkboxes)
        self.btn_export = tk.Button(
            toolbar, text="  Export  ", font=FONT_BTN,
            bg=BTN_SECONDARY_BG, fg=BTN_SECONDARY_FG,
            activebackground=BG_HOVER, activeforeground=FG,
            relief=tk.FLAT, padx=6, pady=3, cursor="hand2",
            command=self._on_export,
        )
        self.btn_export.pack(side=tk.LEFT, padx=(0, 6))

        # Keybindings button
        self.btn_keys = tk.Button(
            toolbar, text="  Keybindings  ", font=FONT_BTN,
            bg=BTN_SECONDARY_BG, fg=BTN_SECONDARY_FG,
            activebackground=BG_HOVER, activeforeground=FG,
            relief=tk.FLAT, padx=6, pady=3, cursor="hand2",
            command=self._show_controls,
        )
        self.btn_keys.pack(side=tk.LEFT, padx=(0, 6))

        # Status bar — shows progress during analysis
        self.status_var = tk.StringVar(value="")
        self.status_label = tk.Label(
            toolbar, textvariable=self.status_var, font=FONT_SMALL,
            bg=BG_SURFACE, fg=FG_DIM, anchor=tk.W,
        )
        self.status_label.pack(side=tk.LEFT, padx=(8, 0))

        # ── Right side buttons (packed right-to-left) ──

        # Quit (rightmost)
        self.btn_quit = tk.Button(
            toolbar, text="  Quit  ", font=FONT_BTN,
            bg=BTN_DANGER_BG, fg=BTN_FG,
            activebackground="#e06080", activeforeground=BTN_FG,
            relief=tk.FLAT, padx=8, pady=3, cursor="hand2",
            command=self.root.destroy,
        )
        self.btn_quit.pack(side=tk.RIGHT, padx=(4, 0))

        # About (before Quit)
        self.btn_about = tk.Button(
            toolbar, text="  About  ", font=FONT_BTN,
            bg=BTN_SECONDARY_BG, fg=BTN_SECONDARY_FG,
            activebackground=BG_HOVER, activeforeground=FG,
            relief=tk.FLAT, padx=6, pady=3, cursor="hand2",
            command=self._on_about,
        )
        self.btn_about.pack(side=tk.RIGHT, padx=(4, 0))

        # Expand all / Collapse all (before About)
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

        # Bind Enter key
        self.entry_ticker.bind("<Return>", lambda _: self._on_analyze())
        # Bind Escape to clear
        self.root.bind("<Escape>", lambda _: self._on_clear())
        # Ctrl+P: show keyboard shortcuts / controls
        self.root.bind("<Control-p>", lambda _: self._show_controls())
        # Hidden keybindings (F-keys bypass Entry widget interception)
        self.root.bind("<F9>", lambda _: self._ee_shake())
        self.root.bind("<F10>", lambda _: self._ee_rainbow())
        self.root.bind("<F11>", lambda _: self._ee_fortune())

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
        # PageUp / PageDown (Ctrl+Home/End) — shared across every suite app.
        from lynx_investor_core.pager import bind_tk_paging
        bind_tk_paging(self.root, self.canvas)

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

    def _on_export(self) -> None:
        if not self._current_report:
            self.status_var.set(f"{WARN_ICON}  Analyze a stock first")
            return

        from tkinter import filedialog
        fmt = tk.StringVar(value="html")
        win = tk.Toplevel(self.root)
        win.title("Export Report")
        win.configure(bg=BG)
        win.geometry("360x200")
        win.resizable(False, False)
        win.transient(self.root)
        win.grab_set()

        tk.Label(win, text="Export Format", font=FONT_BOLD, bg=BG, fg=ACCENT).pack(pady=(16, 8))
        for text, val in [("TXT (Plain Text)", "txt"), ("HTML", "html"), ("PDF (requires weasyprint)", "pdf")]:
            tk.Radiobutton(
                win, text=text, variable=fmt, value=val,
                font=FONT, bg=BG, fg=FG, selectcolor=BG_INPUT,
                activebackground=BG, activeforeground=FG,
            ).pack(anchor=tk.W, padx=40)

        def _do_export():
            win.destroy()
            report = self._current_report
            chosen = fmt.get()

            def _run():
                from lynx.export import ExportFormat, export_report
                try:
                    path = export_report(report, ExportFormat(chosen))
                    self.root.after(0, lambda p=str(path): self._show_export_success(p))
                except Exception as e:
                    self.root.after(0, lambda msg=str(e): self._show_export_error(msg))

            thread = threading.Thread(target=_run, daemon=True)
            thread.start()

        tk.Button(
            win, text="  Export  ", font=FONT_BTN,
            bg=BTN_BG, fg=BTN_FG, activebackground=BTN_ACTIVE,
            relief=tk.FLAT, padx=14, pady=4, cursor="hand2",
            command=_do_export,
        ).pack(pady=(12, 0))
        win.bind("<Escape>", lambda _: win.destroy())

    def _show_export_success(self, file_path: str) -> None:
        """Show a styled export success dialog with a clickable file link."""
        import subprocess
        import platform

        win = tk.Toplevel(self.root)
        win.title("Export Complete")
        win.configure(bg=BG)
        win.resizable(False, False)
        win.transient(self.root)
        win.grab_set()

        # Success icon and title
        tk.Label(
            win, text=CHECK, font=(_FAMILY, 32),
            bg=BG, fg=GREEN,
        ).pack(pady=(20, 4))

        tk.Label(
            win, text="Report exported successfully", font=(_FAMILY, 13, "bold"),
            bg=BG, fg=FG,
        ).pack(pady=(0, 12))

        # File path card
        path_card = tk.Frame(win, bg=BG_CARD, padx=16, pady=10)
        path_card.pack(fill=tk.X, padx=24, pady=(0, 4))

        tk.Label(
            path_card, text="Saved to:", font=FONT_SMALL_BOLD,
            bg=BG_CARD, fg=FG_DIM, anchor=tk.W,
        ).pack(fill=tk.X)

        # Clickable file path
        path_label = tk.Label(
            path_card, text=file_path, font=FONT_MONO,
            bg=BG_CARD, fg=ACCENT, anchor=tk.W, cursor="hand2",
            wraplength=500, justify=tk.LEFT,
        )
        path_label.pack(fill=tk.X, pady=(2, 0))

        def _open_file():
            try:
                sys = platform.system()
                if sys == "Darwin":
                    subprocess.Popen(["open", file_path])
                elif sys == "Windows":
                    subprocess.Popen(["start", "", file_path], shell=True)
                else:
                    subprocess.Popen(["xdg-open", file_path])
            except Exception:
                pass

        def _open_folder():
            try:
                folder = str(Path(file_path).parent)
                sys = platform.system()
                if sys == "Darwin":
                    subprocess.Popen(["open", folder])
                elif sys == "Windows":
                    subprocess.Popen(["explorer", folder])
                else:
                    subprocess.Popen(["xdg-open", folder])
            except Exception:
                pass

        path_label.bind("<Button-1>", lambda _: _open_file())

        # Hover effect on the path label
        path_label.bind("<Enter>", lambda _: path_label.configure(fg=BTN_ACTIVE))
        path_label.bind("<Leave>", lambda _: path_label.configure(fg=ACCENT))

        # Hint
        tk.Label(
            win, text="Click the path to open the file",
            font=FONT_SMALL, bg=BG, fg=FG_SUBTLE,
        ).pack(pady=(2, 8))

        # Buttons row
        btn_row = tk.Frame(win, bg=BG)
        btn_row.pack(pady=(0, 16))

        tk.Button(
            btn_row, text="  Open File  ", font=FONT_BTN,
            bg=BTN_BG, fg=BTN_FG, activebackground=BTN_ACTIVE,
            relief=tk.FLAT, padx=12, pady=4, cursor="hand2",
            command=_open_file,
        ).pack(side=tk.LEFT, padx=(0, 6))

        tk.Button(
            btn_row, text="  Open Folder  ", font=FONT_BTN,
            bg=BTN_SECONDARY_BG, fg=BTN_SECONDARY_FG,
            activebackground=BG_HOVER, activeforeground=FG,
            relief=tk.FLAT, padx=12, pady=4, cursor="hand2",
            command=_open_folder,
        ).pack(side=tk.LEFT, padx=(0, 6))

        tk.Button(
            btn_row, text="  Close  ", font=FONT_BTN,
            bg=BTN_SECONDARY_BG, fg=BTN_SECONDARY_FG,
            activebackground=BG_HOVER, activeforeground=FG,
            relief=tk.FLAT, padx=12, pady=4, cursor="hand2",
            command=win.destroy,
        ).pack(side=tk.LEFT)

        win.bind("<Escape>", lambda _: win.destroy())

        # Center on screen
        win.update_idletasks()
        w, h = win.winfo_reqwidth(), win.winfo_reqheight()
        sx = (win.winfo_screenwidth() - w) // 2
        sy = (win.winfo_screenheight() - h) // 2
        win.geometry(f"{w}x{h}+{sx}+{sy}")

    def _show_export_error(self, msg: str) -> None:
        """Show a styled export error dialog."""
        win = tk.Toplevel(self.root)
        win.title("Export Failed")
        win.configure(bg=BG)
        win.resizable(False, False)
        win.transient(self.root)
        win.grab_set()

        tk.Label(
            win, text=CROSS, font=(_FAMILY, 32),
            bg=BG, fg=RED,
        ).pack(pady=(20, 4))

        tk.Label(
            win, text="Export failed", font=(_FAMILY, 13, "bold"),
            bg=BG, fg=RED,
        ).pack(pady=(0, 12))

        error_card = tk.Frame(win, bg=BG_CARD, padx=16, pady=10)
        error_card.pack(fill=tk.X, padx=24, pady=(0, 12))

        tk.Label(
            error_card, text=msg, font=FONT,
            bg=BG_CARD, fg=FG, wraplength=450, justify=tk.LEFT,
        ).pack(fill=tk.X)

        btn_frame = tk.Frame(win, bg=BG)
        btn_frame.pack(pady=(0, 16))
        tk.Button(
            btn_frame, text="  Close  ", font=FONT_BTN,
            bg=BTN_BG, fg=BTN_FG, activebackground=BTN_ACTIVE,
            relief=tk.FLAT, padx=14, pady=4, cursor="hand2",
            command=win.destroy,
        ).pack(anchor=tk.CENTER)

        win.bind("<Escape>", lambda _: win.destroy())

        win.update_idletasks()
        w, h = win.winfo_reqwidth(), win.winfo_reqheight()
        sx = (win.winfo_screenwidth() - w) // 2
        sy = (win.winfo_screenheight() - h) // 2
        win.geometry(f"{w}x{h}+{sx}+{sy}")

    def _show_controls(self) -> None:
        """Show keyboard shortcuts and controls dialog (Ctrl+P)."""
        shortcuts = [
            ("Enter", "Analyze ticker"),
            ("Escape", "Clear / Reset"),
            ("Ctrl+P", "Show this controls dialog"),
            ("Ctrl+T", "Cycle theme"),
            ("Scroll", "Navigate results"),
            ("Click section header", "Expand / Collapse section"),
            ("Click ?", "Explain section or metric"),
        ]
        sections = []
        for key, action in shortcuts:
            sections.append((key, action))
        self._show_info_popup(
            "Keyboard Shortcuts & Controls",
            "lynx-fundamental — Graphical Interface",
            sections,
        )

    def _on_about(self) -> None:
        from lynx import get_about_text
        about = get_about_text()

        win = tk.Toplevel(self.root)
        win.title("About lynx-fundamental")
        win.configure(bg=BG)
        win.configure(width=620, height=700)
        win.resizable(False, False)
        win.transient(self.root)
        win.grab_set()

        # Logo
        logo_path = Path(__file__).resolve().parent.parent.parent / "img" / "logo_sm_green.png"
        if logo_path.exists():
            try:
                win._about_logo = tk.PhotoImage(file=str(logo_path))
                tk.Label(
                    win, image=win._about_logo, bg=BG,
                ).pack(pady=(16, 8))
            except tk.TclError:
                pass

        # Title
        tk.Label(
            win, text=about['name'],
            font=(_FAMILY, 18, "bold"), bg=BG, fg=ACCENT,
        ).pack(pady=(4, 4))

        tk.Label(
            win, text=f"Version {about['version']}",
            font=FONT_SMALL, bg=BG, fg=FG_DIM,
        ).pack(pady=(0, 2))

        tk.Label(
            win, text=f"Part of {about['suite']} v{about['suite_version']}",
            font=FONT_SMALL, bg=BG, fg=ACCENT_DIM,
        ).pack(pady=(0, 2))

        tk.Label(
            win, text=f"Released {about['year']}",
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

        license_inner = tk.Frame(license_frame, bg=BG_CARD)
        license_inner.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0, 8))

        license_scroll = ttk.Scrollbar(license_inner, orient=tk.VERTICAL)
        license_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        license_text = tk.Text(
            license_inner, font=FONT_SMALL, bg=BG_CARD, fg=FG_DIM,
            wrap=tk.WORD, relief=tk.FLAT, height=14,
            highlightthickness=0, padx=12, pady=4,
            yscrollcommand=license_scroll.set,
        )
        license_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        license_scroll.configure(command=license_text.yview)
        license_text.insert("1.0", about["license_text"])
        license_text.configure(state=tk.DISABLED)

        # Close button (centered)
        close_frame = tk.Frame(win, bg=BG)
        close_frame.pack(fill=tk.X, pady=(8, 16))
        tk.Button(
            close_frame, text="  Close  ", font=(_FAMILY, 11, "bold"),
            bg=BTN_BG, fg=BTN_FG,
            activebackground=BTN_ACTIVE, activeforeground=BTN_FG,
            relief=tk.FLAT, padx=20, pady=6, cursor="hand2",
            command=win.destroy,
        ).pack(anchor=tk.CENTER)

        win.bind("<Escape>", lambda _: win.destroy())

        # Center on screen after all widgets are packed
        win.update_idletasks()
        w = win.winfo_reqwidth()
        h = win.winfo_reqheight()
        sx = (win.winfo_screenwidth() - w) // 2
        sy = (win.winfo_screenheight() - h) // 2
        win.geometry(f"{w}x{h}+{sx}+{sy}")

    def _toggle_all(self, expand: bool) -> None:
        for card in self._sections:
            if expand and not card.expanded:
                card._toggle()
            elif not expand and card.expanded:
                card._toggle()

    # ---- Hidden features -------------------------------------------------

    def _ee_shake(self) -> None:
        from lynx.easter import tk_fireworks
        tk_fireworks(self.root)

    def _ee_rainbow(self) -> None:
        from lynx.easter import tk_rainbow_title
        tk_rainbow_title(self.root)

    def _ee_fortune(self) -> None:
        from lynx.easter import FORTUNE_QUOTES
        import random
        quote = random.choice(FORTUNE_QUOTES)
        messagebox.showinfo("\u2728 Fortune Cookie \u2728", quote)

    # ---- Analysis -------------------------------------------------------

    def _run_analysis(self, identifier: str) -> None:
        try:
            from lynx.core.analyzer import run_progressive_analysis
            from lynx.core.storage import is_testing

            refresh = self.var_refresh.get() or is_testing()

            # Prepare the scroll area for progressive rendering
            self.root.after(0, self._prepare_progressive)

            def on_progress(stage: str, report: AnalysisReport) -> None:
                """Dispatch each stage to the UI thread."""
                try:
                    self.root.after(0, self._render_stage, stage, report)
                except tk.TclError:
                    pass  # Root destroyed

            report = run_progressive_analysis(
                identifier=identifier,
                download_reports=not self.var_no_reports.get(),
                download_news=not self.var_no_news.get(),
                max_filings=getattr(self.cli_args, "max_filings", 10),
                verbose=getattr(self.cli_args, "verbose", False),
                refresh=refresh,
                on_progress=on_progress,
            )

            self._current_report = report
            try:
                self.root.after(0, self._finalize_report, report)
            except tk.TclError:
                pass

        except Exception as e:
            msg = str(e) or type(e).__name__
            try:
                self.root.after(0, self._show_analysis_error, msg)
            except tk.TclError:
                pass  # Root window was destroyed

    def _prepare_progressive(self) -> None:
        """Clear the scroll area and prepare for progressive section mounting."""
        for child in self.scroll_frame.winfo_children():
            child.destroy()
        self._sections.clear()
        self.status_var.set("Fetching data...")

    def _render_stage(self, stage: str, report: AnalysisReport) -> None:
        """Render a single analysis stage into the scroll area."""
        self._current_report = report
        try:
            if stage == "profile":
                self._render_tier_banner(report)
                self._render_profile(report)
                self._render_sector_industry(report)
                p = report.profile
                self.status_var.set(
                    f"Analyzing {_s(p.name)} ({_s(p.ticker)})..."
                )
            elif stage == "financials":
                self._render_financials(report)
            elif stage == "valuation":
                self._render_valuation(report)
            elif stage == "profitability":
                self._render_profitability(report)
            elif stage == "solvency":
                self._render_solvency(report)
            elif stage == "growth":
                self._render_growth(report)
            elif stage == "moat":
                self._render_moat(report)
            elif stage == "intrinsic_value":
                self._render_intrinsic_value(report)
            elif stage == "filings":
                self._render_filings(report)
            elif stage == "news":
                self._render_news(report)
            elif stage == "conclusion":
                self._render_conclusion(report)
            elif stage == "complete":
                # If no sections rendered yet (cached report), render all now.
                if not self._sections:
                    self._render_all_sections(report)

            # Update scroll region after each section
            self.scroll_frame.update_idletasks()
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        except Exception:
            pass  # Silently ignore render errors for individual sections

    def _render_all_sections(self, report: AnalysisReport) -> None:
        """Render all sections at once (used for cached reports)."""
        self._render_tier_banner(report)
        self._render_profile(report)
        self._render_sector_industry(report)
        self._render_valuation(report)
        self._render_profitability(report)
        self._render_solvency(report)
        self._render_growth(report)
        self._render_moat(report)
        self._render_intrinsic_value(report)
        self._render_financials(report)
        self._render_filings(report)
        self._render_news(report)
        self._render_conclusion(report)

    def _finalize_report(self, report: AnalysisReport) -> None:
        """Called after the full analysis completes."""
        self.status_var.set(f"{CHECK}  Analysis complete")
        self.btn_analyze.configure(state=tk.NORMAL)
        self.btn_clear.configure(state=tk.NORMAL)
        # Bottom padding
        tk.Frame(self.scroll_frame, bg=BG, height=24).pack(fill=tk.X)
        self.scroll_frame.update_idletasks()
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _show_analysis_error(self, msg: str) -> None:
        self.status_var.set(f"{WARN_ICON}  Error")
        self.btn_analyze.configure(state=tk.NORMAL)
        self.btn_clear.configure(state=tk.NORMAL)
        messagebox.showerror("Analysis Error", msg)

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
            icon=ICON_PROFILE, accent=ACCENT, expanded=True,
            info_command=lambda: self._show_section_info("profile"),
        )
        self._sections.append(card)
        frame = card.frame

        # Split layout: metrics left (1/3), description right (2/3)
        split = tk.Frame(frame, bg=BG_CARD)
        split.pack(fill=tk.X)
        split.columnconfigure(0, weight=1)
        split.columnconfigure(1, weight=2)

        # Left side: key-value metrics (1/3)
        left = tk.Frame(split, bg=BG_CARD)
        left.grid(row=0, column=0, sticky="nsew")

        # (label, value, optional fg override)
        rows: list[tuple[str, str, str]] = [
            ("Company", _s(p.name), FG),
            ("Ticker", _s(p.ticker), FG),
            ("ISIN", _s(p.isin), FG),
            ("Tier", _safe_tier(p.tier), FG),
            ("Sector", _s(p.sector), FG),
            ("Industry", _s(p.industry), FG),
            ("Country", _s(p.country), FG),
            ("Exchange", _s(p.exchange), FG),
            ("Currency", _s(p.currency), YELLOW),
            ("Market Cap", _money(p.market_cap), FG),
            ("Employees", f"{p.employees:,}" if p.employees else "N/A", FG),
        ]
        if p.website:
            rows.append(("Website", p.website, FG))

        for i, (label, value, fg_color) in enumerate(rows):
            bg = BG_INPUT if i % 2 == 0 else BG_CARD
            row = tk.Frame(left, bg=bg)
            row.pack(fill=tk.X)
            tk.Label(
                row, text=label, font=FONT_BOLD, bg=bg, fg=ACCENT,
                width=14, anchor=tk.E, pady=3,
            ).pack(side=tk.LEFT, padx=(12, 6))
            tk.Label(
                row, text=value, font=FONT, bg=bg, fg=fg_color,
                anchor=tk.W, pady=3,
            ).pack(side=tk.LEFT, padx=(6, 12))

        # Right side: business description (2/3)
        right = tk.Frame(split, bg=BG_CARD, padx=12, pady=8)
        right.grid(row=0, column=1, sticky="nsew")

        # Vertical separator
        tk.Frame(right, bg=BORDER, width=1).pack(side=tk.LEFT, fill=tk.Y, padx=(0, 12))

        desc_area = tk.Frame(right, bg=BG_CARD)
        desc_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        tk.Label(
            desc_area, text="Business Description", font=FONT_SMALL_BOLD,
            bg=BG_CARD, fg=ACCENT_DIM, anchor=tk.W,
        ).pack(fill=tk.X, pady=(0, 6))

        desc = p.description or "No description available."
        tk.Label(
            desc_area, text=desc, font=FONT,
            bg=BG_CARD, fg=FG_DIM, wraplength=600,
            justify=tk.LEFT, anchor=tk.NW,
        ).pack(fill=tk.BOTH, expand=True)

    # ---- Sector & Industry Insights ----------------------------------------

    def _render_sector_industry(self, r: AnalysisReport) -> None:
        from lynx.metrics.sector_insights import get_sector_insight, get_industry_insight

        p = r.profile
        items = []
        if p.sector:
            si = get_sector_insight(p.sector)
            if si:
                items.append((f"Sector: {si.sector}", si))
        if p.industry:
            ii = get_industry_insight(p.industry)
            if ii:
                items.append((f"Industry: {ii.industry}", ii))

        for label, info in items:
            card = CollapsibleCard(
                self.scroll_frame, label,
                icon="\U0001f4d6", accent=LAVENDER, expanded=False,
            )
            self._sections.append(card)
            frame = card.frame
            rows = [
                ("Overview", info.overview),
                ("Critical Metrics", ", ".join(info.critical_metrics)),
                ("Key Risks", ", ".join(info.key_risks)),
                ("What to Watch", ", ".join(info.what_to_watch)),
                ("Typical Valuation", info.typical_valuation),
            ]
            for i, (lbl, value) in enumerate(rows):
                bg = BG_INPUT if i % 2 == 0 else BG_CARD
                row_frame = tk.Frame(frame, bg=bg)
                row_frame.pack(fill=tk.X)
                tk.Label(
                    row_frame, text=lbl, font=FONT_BOLD, bg=bg, fg=ACCENT,
                    width=22, anchor=tk.E, pady=3,
                ).pack(side=tk.LEFT, padx=(12, 6))
                tk.Label(
                    row_frame, text=value, font=FONT, bg=bg, fg=FG,
                    anchor=tk.W, pady=3, wraplength=700, justify=tk.LEFT,
                ).pack(side=tk.LEFT, padx=(6, 12))

    # ---- Valuation -------------------------------------------------------

    def _render_valuation(self, r: AnalysisReport) -> None:
        v = r.valuation
        if v is None:
            return
        card = CollapsibleCard(
            self.scroll_frame, "Valuation",
            icon=ICON_VALUATION, accent=YELLOW, expanded=False,
            info_command=lambda: self._show_section_info("valuation"),
        )
        self._sections.append(card)
        frame = card.frame
        rows = [
            ("P/E (Trailing)", _num(v.pe_trailing), _ape(v.pe_trailing), "pe_trailing"),
            ("P/E (Forward)", _num(v.pe_forward), _ape(v.pe_forward), "pe_forward"),
            ("P/B Ratio", _num(v.pb_ratio), _thr(v.pb_ratio, [(1, "Below Book"), (1.5, "Cheap"), (3, "Fair")], "Premium"), "pb_ratio"),
            ("P/S Ratio", _num(v.ps_ratio), "", "ps_ratio"),
            ("P/FCF", _num(v.p_fcf), _thr(v.p_fcf, [(10, "Cheap"), (20, "Fair")], "Expensive"), "p_fcf"),
            ("EV/EBITDA", _num(v.ev_ebitda), _thr(v.ev_ebitda, [(8, "Cheap"), (12, "Fair"), (18, "Expensive")], "Very Expensive"), "ev_ebitda"),
            ("EV/Revenue", _num(v.ev_revenue), _thr(v.ev_revenue, [(1, "Very cheap"), (3, "Cheap"), (5, "Fair"), (8, "Expensive")], "Very expensive"), "ev_revenue"),
            ("PEG Ratio", _num(v.peg_ratio), _thr(v.peg_ratio, [(1, "Undervalued"), (2, "Fair")], "Overvalued"), "peg_ratio"),
            ("Earnings Yield", _pct(v.earnings_yield), _thr(v.earnings_yield, [(0, "Negative"), (0.05, "Low"), (0.07, "Fair"), (0.10, "Good")], "Excellent"), "earnings_yield"),
            ("Dividend Yield", _pct(v.dividend_yield), _thr(v.dividend_yield, [(0, "No dividend"), (0.02, "Low"), (0.04, "Moderate"), (0.06, "High")], "Very high"), "dividend_yield"),
            ("P/Tangible Book", _num(v.price_to_tangible_book), _thr(v.price_to_tangible_book, [(0.67, "Deep Value"), (1, "Below Book"), (1.5, "Near Book")], "Premium"), "price_to_tangible_book"),
            ("P/NCAV (Net-Net)", _num(v.price_to_ncav), _thr(v.price_to_ncav, [(0.67, "Classic Net-Net"), (1, "Below NCAV"), (1.5, "Near NCAV")], "Above NCAV"), "price_to_ncav"),
            ("Enterprise Value", _money(v.enterprise_value), "", ""),
            ("Market Cap", _money(v.market_cap), "", ""),
        ]
        for i, (label, value, assessment, key) in enumerate(rows):
            self._add_metric_row(frame, i, label, value, assessment, metric_key=key)

    # ---- Profitability ---------------------------------------------------

    def _render_profitability(self, r: AnalysisReport) -> None:
        p = r.profitability
        if p is None:
            return
        card = CollapsibleCard(
            self.scroll_frame, "Profitability",
            icon=ICON_PROFIT, accent=GREEN, expanded=False,
            info_command=lambda: self._show_section_info("profitability"),
        )
        self._sections.append(card)
        frame = card.frame
        rows = [
            ("ROE", _pct(p.roe), _thr(p.roe, [(0, "Negative"), (0.10, "Below Avg"), (0.15, "Good"), (0.20, "Excellent")], "Outstanding"), "roe"),
            ("ROA", _pct(p.roa), _thr(p.roa, [(0, "Negative"), (0.05, "Low"), (0.10, "Good")], "Excellent"), "roa"),
            ("ROIC", _pct(p.roic), _thr(p.roic, [(0, "Negative"), (0.07, "Below WACC"), (0.10, "Good"), (0.15, "Wide Moat")], "Exceptional"), "roic"),
            ("Gross Margin", _pct(p.gross_margin), _thr(p.gross_margin, [(0, "Negative"), (0.20, "Thin"), (0.40, "Good"), (0.60, "Strong")], "Very strong"), "gross_margin"),
            ("Operating Margin", _pct(p.operating_margin), _thr(p.operating_margin, [(0, "Loss"), (0.05, "Thin"), (0.15, "Good"), (0.25, "Excellent")], "Outstanding"), "operating_margin"),
            ("Net Margin", _pct(p.net_margin), _thr(p.net_margin, [(0, "Loss"), (0.05, "Thin"), (0.10, "Good"), (0.20, "Excellent")], "Outstanding"), "net_margin"),
            ("FCF Margin", _pct(p.fcf_margin), _thr(p.fcf_margin, [(0, "Negative"), (0.05, "Weak"), (0.10, "Good"), (0.20, "Strong")], "Excellent"), "fcf_margin"),
            ("EBITDA Margin", _pct(p.ebitda_margin), _thr(p.ebitda_margin, [(0, "Negative"), (0.05, "Thin"), (0.15, "Good"), (0.30, "Excellent")], "Outstanding"), "ebitda_margin"),
        ]
        for i, (label, value, assessment, key) in enumerate(rows):
            self._add_metric_row(frame, i, label, value, assessment, metric_key=key)

    # ---- Solvency --------------------------------------------------------

    def _render_solvency(self, r: AnalysisReport) -> None:
        s = r.solvency
        if s is None:
            return
        card = CollapsibleCard(
            self.scroll_frame, "Solvency & Financial Health",
            icon=ICON_SOLVENCY, accent=RED, expanded=False,
            info_command=lambda: self._show_section_info("solvency"),
        )
        self._sections.append(card)
        frame = card.frame
        rows = [
            ("Debt/Equity", _num(s.debt_to_equity), _thr(s.debt_to_equity, [(0.3, "Very Conservative"), (0.5, "Conservative"), (1.0, "Moderate"), (2.0, "High")], "Very High"), "debt_to_equity"),
            ("Debt/EBITDA", _num(s.debt_to_ebitda), _thr(s.debt_to_ebitda, [(1, "Very Low"), (2, "Manageable"), (3, "Moderate")], "Heavy"), "debt_to_ebitda"),
            ("Current Ratio", _num(s.current_ratio), _thr(s.current_ratio, [(1.0, "Liquidity Risk"), (1.5, "Adequate"), (2.0, "Good")], "Strong"), "current_ratio"),
            ("Quick Ratio", _num(s.quick_ratio), "", "quick_ratio"),
            ("Interest Coverage", _num(s.interest_coverage, 1), _thr(s.interest_coverage, [(1, "Cannot cover"), (2, "Tight"), (4, "Adequate"), (8, "Strong")], "Very strong"), "interest_coverage"),
            ("Altman Z-Score", _num(s.altman_z_score), _thr(s.altman_z_score, [(1.81, "Distress"), (2.99, "Grey Zone")], "Safe"), "altman_z_score"),
            ("Cash Burn Rate (/yr)", _money(s.cash_burn_rate), _burn(s.cash_burn_rate), "cash_burn_rate"),
            ("Cash Runway", f"{s.cash_runway_years:.1f} yrs" if s.cash_runway_years is not None else "N/A", "", "cash_runway_years"),
            ("Working Capital", _money(s.working_capital), "", ""),
            ("Cash Per Share", f"${s.cash_per_share:.2f}" if s.cash_per_share is not None else "N/A", "", ""),
            ("NCAV Per Share", f"${s.ncav_per_share:.4f}" if s.ncav_per_share is not None else "N/A", "", "ncav_per_share"),
            ("Total Debt", _money(s.total_debt), "", ""),
            ("Total Cash", _money(s.total_cash), "", ""),
            ("Net Debt", _money(s.net_debt), "", ""),
        ]
        for i, (label, value, assessment, key) in enumerate(rows):
            self._add_metric_row(frame, i, label, value, assessment, metric_key=key)

    # ---- Growth ----------------------------------------------------------

    def _render_growth(self, r: AnalysisReport) -> None:
        g = r.growth
        if g is None:
            return
        card = CollapsibleCard(
            self.scroll_frame, "Growth",
            icon=ICON_GROWTH, accent=MAUVE, expanded=False,
            info_command=lambda: self._show_section_info("growth"),
        )
        self._sections.append(card)
        frame = card.frame

        def _ga(val):
            return _thr(val, [(0, "Declining"), (0.10, "Positive"), (0.25, "Good")], "Very strong") if val is not None else ""
        def _ca(val):
            return _thr(val, [(0, "Declining"), (0.08, "Positive"), (0.15, "Good")], "Excellent") if val is not None else ""
        def _da(val):
            if val is None: return ""
            try:
                v = float(val)
                if v < -0.02: return "Buybacks"
                if v < 0.01: return "Minimal"
                if v < 0.05: return "Modest"
                if v < 0.10: return "Significant"
                return "Heavy dilution"
            except Exception: return ""

        rows = [
            ("Revenue Growth (YoY)", _pct(g.revenue_growth_yoy), _ga(g.revenue_growth_yoy), "revenue_growth_yoy"),
            ("Revenue CAGR (3Y)", _pct(g.revenue_cagr_3y), _ca(g.revenue_cagr_3y), "revenue_cagr_3y"),
            ("Revenue CAGR (5Y)", _pct(g.revenue_cagr_5y), _ca(g.revenue_cagr_5y), "revenue_cagr_5y"),
            ("Earnings Growth (YoY)", _pct(g.earnings_growth_yoy), _ga(g.earnings_growth_yoy), "earnings_growth_yoy"),
            ("Earnings CAGR (3Y)", _pct(g.earnings_cagr_3y), _ca(g.earnings_cagr_3y), "earnings_cagr_3y"),
            ("Earnings CAGR (5Y)", _pct(g.earnings_cagr_5y), _ca(g.earnings_cagr_5y), "earnings_cagr_5y"),
            ("FCF Growth (YoY)", _pct(g.fcf_growth_yoy), _ga(g.fcf_growth_yoy), ""),
            ("Book Value Growth (YoY)", _pct(g.book_value_growth_yoy), _ga(g.book_value_growth_yoy), ""),
            ("Share Dilution (YoY)", _pct(g.shares_growth_yoy), _da(g.shares_growth_yoy), "shares_growth_yoy"),
        ]
        for i, (label, value, assessment, key) in enumerate(rows):
            self._add_metric_row(frame, i, label, value, assessment, metric_key=key)

    # ---- Moat ------------------------------------------------------------

    def _render_moat(self, r: AnalysisReport) -> None:
        m = r.moat
        if m is None:
            return
        tier = _get_tier(r)
        card = CollapsibleCard(
            self.scroll_frame, "Moat Indicators",
            icon=ICON_MOAT, accent=YELLOW, expanded=False,
            info_command=lambda: self._show_section_info("moat"),
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
                ("Switching Costs", _s(m.switching_costs or "Review needed")),
                ("Network Effects", _s(m.network_effects or "Review needed")),
                ("Cost Advantages", _s(m.cost_advantages or "Not detected")),
                ("Intangible Assets", _s(m.intangible_assets or "Not detected")),
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
        if iv is None:
            return
        card = CollapsibleCard(
            self.scroll_frame, "Intrinsic Value",
            icon=ICON_VALUE, accent=TEAL, expanded=False,
            info_command=lambda: self._show_section_info("intrinsic_value"),
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

    # ---- Conclusion -----------------------------------------------------

    def _render_conclusion(self, r: AnalysisReport) -> None:
        from lynx.core.conclusion import generate_conclusion
        c = generate_conclusion(r)

        # Verdict colour
        verdict_colors = {
            "Strong Buy": GREEN, "Buy": GREEN_DIM,
            "Hold": YELLOW, "Caution": ORANGE, "Avoid": RED,
        }
        vc = verdict_colors.get(c.verdict, FG)

        card = CollapsibleCard(
            self.scroll_frame, "Assessment Conclusion",
            icon="\U0001f4dd", accent=vc, expanded=False,
            info_command=lambda: self._show_conclusion_info("overall"),
        )
        self._sections.append(card)
        frame = card.frame

        # Verdict + score bar
        verdict_frame = tk.Frame(frame, bg=BG_CARD, pady=8, padx=16)
        verdict_frame.pack(fill=tk.X)
        tk.Label(
            verdict_frame, text=f"{c.verdict}  ({c.overall_score:.0f}/100)",
            font=(_FAMILY, 14, "bold"), bg=BG_CARD, fg=vc,
        ).pack(anchor=tk.W)
        tk.Label(
            verdict_frame, text=c.summary, font=FONT_SMALL,
            bg=BG_CARD, fg=FG_DIM, wraplength=900, justify=tk.LEFT,
        ).pack(anchor=tk.W, pady=(4, 0))

        # Category scores
        sep = tk.Frame(frame, bg=BORDER, height=1)
        sep.pack(fill=tk.X, padx=12, pady=6)
        for i, cat in enumerate(("valuation", "profitability", "solvency", "growth", "moat")):
            score = c.category_scores.get(cat, 0)
            summary = c.category_summaries.get(cat, "")
            self._add_metric_row(frame, i, cat.title(), f"{score:.0f}/100", summary)

        # Strengths & risks
        if c.strengths or c.risks:
            sep2 = tk.Frame(frame, bg=BORDER, height=1)
            sep2.pack(fill=tk.X, padx=12, pady=6)
            idx = 0
            for s in c.strengths:
                bg = BG_INPUT if idx % 2 == 0 else BG_CARD
                row = tk.Frame(frame, bg=bg)
                row.pack(fill=tk.X)
                tk.Label(
                    row, text=f"{CHECK} Strength", font=FONT_BOLD, bg=bg, fg=GREEN,
                    width=22, anchor=tk.E, pady=3,
                ).pack(side=tk.LEFT, padx=(12, 6))
                tk.Label(
                    row, text=s, font=FONT, bg=bg, fg=FG,
                    anchor=tk.W, pady=3,
                ).pack(side=tk.LEFT, padx=(6, 12))
                idx += 1
            for risk in c.risks:
                bg = BG_INPUT if idx % 2 == 0 else BG_CARD
                row = tk.Frame(frame, bg=bg)
                row.pack(fill=tk.X)
                tk.Label(
                    row, text=f"{WARN_ICON} Risk", font=FONT_BOLD, bg=bg, fg=RED,
                    width=22, anchor=tk.E, pady=3,
                ).pack(side=tk.LEFT, padx=(12, 6))
                tk.Label(
                    row, text=risk, font=FONT, bg=bg, fg=FG,
                    anchor=tk.W, pady=3,
                ).pack(side=tk.LEFT, padx=(6, 12))
                idx += 1

        # Tier note
        if c.tier_note:
            tk.Label(
                frame, text=c.tier_note, font=FONT_SMALL,
                bg=BG_CARD, fg=FG_SUBTLE, wraplength=900,
                justify=tk.LEFT, anchor=tk.NW, padx=16, pady=6,
            ).pack(fill=tk.X)

    # ---- Financials ------------------------------------------------------

    def _render_financials(self, r: AnalysisReport) -> None:
        if not r.financials:
            return
        card = CollapsibleCard(
            self.scroll_frame, f"Financial Statements ({len(r.financials[:5])}Y)",
            icon=ICON_FINANCE, accent=SKY, expanded=False,
            info_command=lambda: self._show_section_info("financials"),
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
            # (value_text, raw_number) — raw used for red/green coloring
            cells = [
                (_s(st.period), None),
                (_money(st.revenue), st.revenue),
                (_money(st.gross_profit), st.gross_profit),
                (_money(st.operating_income), st.operating_income),
                (_money(st.net_income), st.net_income),
                (_money(st.free_cash_flow), st.free_cash_flow),
                (_money(st.total_equity), st.total_equity),
                (_money(st.total_debt), None),  # debt is not P&L
            ]
            for val_text, raw in cells:
                fg_color = FG
                if raw is not None:
                    try:
                        v = float(raw)
                        if v > 0:
                            fg_color = GREEN
                        elif v < 0:
                            fg_color = RED
                    except (TypeError, ValueError):
                        pass
                tk.Label(
                    row, text=val_text, font=FONT_SMALL, bg=bg, fg=fg_color,
                    width=14, anchor=tk.CENTER, pady=3,
                ).pack(side=tk.LEFT, padx=1)

    # ---- Filings ---------------------------------------------------------

    def _render_filings(self, r: AnalysisReport) -> None:
        if not r.filings:
            return
        card = CollapsibleCard(
            self.scroll_frame, f"SEC Filings ({len(r.filings)})",
            icon=ICON_FILING, accent=PEACH, expanded=False,
            info_command=lambda: self._show_section_info("filings"),
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
            icon=ICON_NEWS, accent=PINK, expanded=False,
            info_command=lambda: self._show_section_info("news"),
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
        report = self._current_report
        if not report:
            return

        def _do():
            from lynx.core.reports import download_filing
            try:
                path = download_filing(report.profile.ticker, filing)
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
        if not article.url:
            return
        if not safe_webbrowser_open(article.url):
            messagebox.showerror("Unsafe URL", "Refused: unsafe URL")
            return

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
                        label: str, value: str, assessment: str,
                        metric_key: str = "") -> None:
        """Add a metric row with label, value, assessment badge, and info button."""
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
        # Metric explanation "?" button
        if metric_key:
            btn = tk.Button(
                r, text=" ? ", font=(_FAMILY, 9, "bold"),
                bg=BORDER, fg=ACCENT, activebackground=BG_HOVER,
                activeforeground=FG, relief=tk.FLAT, padx=2, pady=0,
                cursor="hand2",
                command=lambda k=metric_key: self._show_metric_info(k),
            )
            btn.pack(side=tk.RIGHT, padx=(0, 8))

    # ---- Explanation popups ------------------------------------------------

    def _show_info_popup(self, title: str, subtitle: str, sections: list) -> None:
        """Generic info popup with title, subtitle, and content sections."""
        win = tk.Toplevel(self.root)
        win.title(title)
        win.configure(bg=BG)
        win.resizable(False, False)
        win.transient(self.root)
        win.grab_set()

        tk.Label(
            win, text=title, font=(_FAMILY, 14, "bold"),
            bg=BG, fg=ACCENT, wraplength=560,
        ).pack(padx=24, pady=(16, 4))

        if subtitle:
            tk.Label(
                win, text=subtitle, font=FONT_SMALL,
                bg=BG, fg=FG_SUBTLE,
            ).pack(padx=24, pady=(0, 12))

        card = tk.Frame(win, bg=BG_CARD, padx=16, pady=12)
        card.pack(fill=tk.X, padx=20, pady=(0, 8))

        for i, (heading, text) in enumerate(sections):
            if i > 0:
                tk.Frame(card, bg=BORDER, height=1).pack(fill=tk.X, pady=8)
            tk.Label(
                card, text=heading, font=FONT_SMALL_BOLD,
                bg=BG_CARD, fg=ACCENT, anchor=tk.W,
            ).pack(fill=tk.X)
            tk.Label(
                card, text=text, font=FONT, bg=BG_CARD, fg=FG,
                wraplength=520, justify=tk.LEFT, anchor=tk.NW,
            ).pack(fill=tk.X, pady=(2, 0))

        btn_frame = tk.Frame(win, bg=BG)
        btn_frame.pack(fill=tk.X, pady=(8, 16))
        tk.Button(
            btn_frame, text="  Close  ", font=FONT_BTN,
            bg=BTN_BG, fg=BTN_FG, activebackground=BTN_ACTIVE,
            relief=tk.FLAT, padx=14, pady=4, cursor="hand2",
            command=win.destroy,
        ).pack(anchor=tk.CENTER)

        win.bind("<Escape>", lambda _: win.destroy())
        win.update_idletasks()
        w, h = win.winfo_reqwidth(), win.winfo_reqheight()
        sx = (win.winfo_screenwidth() - w) // 2
        sy = (win.winfo_screenheight() - h) // 2
        win.geometry(f"{w}x{h}+{sx}+{sy}")

    def _show_metric_info(self, key: str) -> None:
        from lynx.metrics.explanations import get_explanation
        exp = get_explanation(key)
        if not exp:
            return
        self._show_info_popup(
            exp.full_name,
            f"Category: {exp.category.title()}",
            [
                ("What it measures", exp.description),
                ("Formula", exp.formula),
                ("Why it matters", exp.why_used),
            ],
        )

    def _show_section_info(self, section_key: str) -> None:
        from lynx.metrics.explanations import get_section_explanation
        sec = get_section_explanation(section_key)
        if not sec:
            return
        self._show_info_popup(
            sec["title"],
            "",
            [("Description", sec["description"])],
        )

    def _show_conclusion_info(self, category: str = "overall") -> None:
        from lynx.metrics.explanations import get_conclusion_explanation
        ce = get_conclusion_explanation(category)
        if not ce:
            return
        self._show_info_popup(
            ce["title"],
            "Conclusion Methodology",
            [("How it works", ce["description"])],
        )


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
        v = float(val)
        if v != v: return "N/A"  # NaN check
        return f"{v:,.{digits}f}"
    except Exception:
        return "N/A"


def _pct(val) -> str:
    if val is None:
        return "N/A"
    try:
        v = float(val)
        if v != v: return "N/A"  # NaN check
        return f"{v * 100:.2f}%"
    except Exception:
        return "N/A"


def _pctplain(val) -> str:
    if val is None:
        return "N/A"
    try:
        v = float(val)
        if v != v: return "N/A"  # NaN check
        return f"{v * 100:.1f}%"
    except Exception:
        return "N/A"


def _money(val) -> str:
    if val is None:
        return "N/A"
    try:
        v = float(val)
        if v != v: return "N/A"  # NaN check
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
