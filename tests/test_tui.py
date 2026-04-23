"""Tests for TUI app module — importability and structure."""

import pytest
from lynx.tui.app import (
    AboutModal,
    DownloadResultDialog,
    LynxApp,
    NewsBrowserDialog,
    ReportView,
    SearchModal,
    _ape,
    _build_filings,
    _build_news,
    _build_valuation,
    _burn,
    _get_tier,
    _money,
    _mos,
    _num,
    _pct,
    _pctplain,
    _s,
    _safe_tier,
    _thr,
    run_tui,
)
from lynx.models import (
    AnalysisReport,
    CompanyProfile,
    CompanyTier,
    EfficiencyMetrics,
    Filing,
    GrowthMetrics,
    IntrinsicValue,
    MoatIndicators,
    NewsArticle,
    ProfitabilityMetrics,
    SolvencyMetrics,
    ValuationMetrics,
)


class TestTuiFormatters:
    def test_s_none(self):
        assert _s(None) == "N/A"

    def test_s_value(self):
        assert _s("hello") == "hello"

    def test_num_none(self):
        assert _num(None) == "N/A"

    def test_num_value(self):
        assert _num(1234.5) == "1,234.50"

    def test_pct_none(self):
        assert _pct(None) == "N/A"

    def test_pct_value(self):
        assert _pct(0.25) == "25.00%"

    def test_money_none(self):
        assert _money(None) == "N/A"

    def test_money_billions(self):
        assert "B" in _money(5e9)

    def test_mos_none(self):
        assert _mos(None) == "N/A"

    def test_mos_undervalued(self):
        assert "Undervalued" in _mos(0.5)

    def test_mos_overvalued(self):
        assert "Overvalued" in _mos(-0.2)

    def test_safe_tier_enum(self):
        assert _safe_tier(CompanyTier.MEGA) == "Mega Cap"

    def test_safe_tier_none(self):
        assert _safe_tier(None) == "N/A"


class TestBuildFunctions:
    """Verify build functions are importable and callable signatures are correct.
    Note: DataTable instantiation requires an active Textual app context,
    so we test function existence and structure rather than calling them."""

    def test_build_functions_exist(self):
        assert callable(_build_valuation)
        assert callable(_build_filings)
        assert callable(_build_news)


class TestLynxAppStructure:
    def test_bindings_include_tab(self):
        binding_keys = [b.key for b in LynxApp.BINDINGS]
        assert "tab" in binding_keys
        assert "shift+tab" in binding_keys

    def test_bindings_include_about(self):
        binding_keys = [b.key for b in LynxApp.BINDINGS]
        assert "f1" in binding_keys

    def test_bindings_include_theme(self):
        binding_keys = [b.key for b in LynxApp.BINDINGS]
        assert "t" in binding_keys

    def test_suppress_flag_default(self):
        # Check class attribute default
        assert LynxApp._suppress_news_dialog is False

    def test_theme_index_default(self):
        assert LynxApp._theme_index == 0


class TestNaNHandling:
    def test_num_nan(self):
        assert _num(float("nan")) == "N/A"

    def test_pct_nan(self):
        assert _pct(float("nan")) == "N/A"

    def test_pctplain_nan(self):
        assert _pctplain(float("nan")) == "N/A"

    def test_money_nan(self):
        assert _money(float("nan")) == "N/A"


class TestThemes:
    def test_theme_names_nonempty(self):
        from lynx.tui.themes import THEME_NAMES
        assert len(THEME_NAMES) >= 5

    def test_theme_names_includes_customs(self):
        from lynx.tui.themes import THEME_NAMES
        assert "lynx-dark" in THEME_NAMES
        assert "lynx-light" in THEME_NAMES
        # Suite-wide gallery themes
        assert "dracula" in THEME_NAMES
        assert "matrix" in THEME_NAMES
        assert "solarized-dark" in THEME_NAMES

    def test_theme_names_includes_builtins(self):
        from lynx.tui.themes import THEME_NAMES
        assert "textual-dark" in THEME_NAMES
        assert "textual-light" in THEME_NAMES

    def test_custom_themes_valid(self):
        from lynx.tui.themes import CUSTOM_THEMES
        for theme in CUSTOM_THEMES:
            assert theme.name
            assert theme.primary
            assert theme.background
            assert theme.surface

    def test_custom_themes_have_dark_flag(self):
        from lynx.tui.themes import CUSTOM_THEMES
        dark_themes = [t for t in CUSTOM_THEMES if t.dark]
        light_themes = [t for t in CUSTOM_THEMES if not t.dark]
        assert len(dark_themes) >= 4
        assert len(light_themes) >= 1

    def test_register_function_exists(self):
        from lynx.tui.themes import register_all_themes
        assert callable(register_all_themes)

    def test_profile_table_builder(self):
        from lynx.tui.app import _build_profile_table
        assert callable(_build_profile_table)

    def test_metric_info_binding(self):
        binding_keys = [b.key for b in LynxApp.BINDINGS]
        assert "i" in binding_keys

    def test_rm_helper_exists(self):
        from lynx.tui.app import _rm
        assert callable(_rm)
