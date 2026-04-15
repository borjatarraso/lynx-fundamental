"""Custom Textual themes for the lynx-fundamental TUI application."""

from __future__ import annotations

from typing import TYPE_CHECKING

from textual.theme import Theme

if TYPE_CHECKING:
    from textual.app import App


# ---------------------------------------------------------------------------
# Theme definitions
# ---------------------------------------------------------------------------

LYNX_DARK = Theme(
    name="lynx-dark",
    primary="#89b4fa",
    secondary="#a6adc8",
    accent="#f9e2af",
    warning="#fab387",
    error="#f38ba8",
    success="#a6e3a1",
    foreground="#cdd6f4",
    background="#1e1e2e",
    surface="#313244",
    panel="#45475a",
    dark=True,
)

HACKER = Theme(
    name="hacker",
    primary="#00ff41",
    secondary="#00cc33",
    accent="#39ff14",
    warning="#ffff00",
    error="#ff0000",
    success="#00ff41",
    foreground="#00ff41",
    background="#0a0a0a",
    surface="#0d1a0d",
    panel="#142814",
    dark=True,
)

DRACULA = Theme(
    name="dracula",
    primary="#bd93f9",
    secondary="#f8f8f2",
    accent="#ff79c6",
    warning="#f1fa8c",
    error="#ff5555",
    success="#50fa7b",
    foreground="#f8f8f2",
    background="#282a36",
    surface="#44475a",
    panel="#6272a4",
    dark=True,
)

SOLARIZED = Theme(
    name="solarized",
    primary="#268bd2",
    secondary="#93a1a1",
    accent="#b58900",
    warning="#cb4b16",
    error="#dc322f",
    success="#859900",
    foreground="#839496",
    background="#002b36",
    surface="#073642",
    panel="#586e75",
    dark=True,
)

LYNX_LIGHT = Theme(
    name="lynx-light",
    primary="#1e66f5",
    secondary="#6c6f85",
    accent="#df8e1d",
    warning="#fe640b",
    error="#d20f39",
    success="#40a02b",
    foreground="#4c4f69",
    background="#eff1f5",
    surface="#e6e9ef",
    panel="#ccd0da",
    dark=False,
)

# ---------------------------------------------------------------------------
# All custom themes in a single collection
# ---------------------------------------------------------------------------

CUSTOM_THEMES: list[Theme] = [
    LYNX_DARK,
    HACKER,
    DRACULA,
    SOLARIZED,
    LYNX_LIGHT,
]

# Cycle order: custom themes first, then the two built-in Textual themes.
THEME_NAMES: list[str] = [
    "lynx-dark",
    "hacker",
    "dracula",
    "solarized",
    "lynx-light",
    "textual-dark",
    "textual-light",
]


# ---------------------------------------------------------------------------
# Registration helper
# ---------------------------------------------------------------------------

def register_all_themes(app: App) -> None:
    """Register every custom Lynx theme on the given Textual *app*."""
    for theme in CUSTOM_THEMES:
        app.register_theme(theme)
