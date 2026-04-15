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

    def test_suppress_flag_default(self):
        # Check class attribute default
        assert LynxApp._suppress_news_dialog is False
