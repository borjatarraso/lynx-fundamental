"""Tests for GUI app module — importability and helper functions."""

import pytest
from lynx.gui.app import (
    TIER_COLORS,
    _ape,
    _assessment_color,
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
)
from lynx.models import (
    AnalysisReport,
    CompanyProfile,
    CompanyTier,
    EfficiencyMetrics,
    GrowthMetrics,
    IntrinsicValue,
    MoatIndicators,
    ProfitabilityMetrics,
    SolvencyMetrics,
    ValuationMetrics,
)


class TestGuiFormatters:
    def test_s_none(self):
        assert _s(None) == "N/A"

    def test_s_value(self):
        assert _s(42) == "42"

    def test_num_none(self):
        assert _num(None) == "N/A"

    def test_num_value(self):
        assert _num(1234.5) == "1,234.50"

    def test_pct_none(self):
        assert _pct(None) == "N/A"

    def test_pct_value(self):
        assert _pct(0.123) == "12.30%"

    def test_money_none(self):
        assert _money(None) == "N/A"

    def test_money_trillions(self):
        assert "T" in _money(2e12)

    def test_money_billions(self):
        assert "B" in _money(5e9)

    def test_money_millions(self):
        assert "M" in _money(50e6)

    def test_mos_undervalued(self):
        assert "Undervalued" in _mos(0.5)

    def test_mos_overvalued(self):
        assert "Overvalued" in _mos(-0.3)


class TestAssessmentColor:
    def test_green_for_cheap(self):
        from lynx.gui.app import GREEN
        assert _assessment_color("Very cheap") == GREEN

    def test_red_for_expensive(self):
        from lynx.gui.app import RED
        assert _assessment_color("Very expensive") == RED

    def test_yellow_for_fair(self):
        from lynx.gui.app import YELLOW
        assert _assessment_color("Fair") == YELLOW


class TestTierColors:
    def test_all_tiers_have_colors(self):
        for tier in CompanyTier:
            assert tier in TIER_COLORS
            fg, bg = TIER_COLORS[tier]
            assert fg.startswith("#")
            assert bg.startswith("#")


class TestGetTier:
    def test_with_valid_tier(self):
        r = AnalysisReport(
            profile=CompanyProfile(ticker="T", name="T", tier=CompanyTier.MEGA),
            valuation=ValuationMetrics(),
            profitability=ProfitabilityMetrics(),
            solvency=SolvencyMetrics(),
            growth=GrowthMetrics(),
            efficiency=EfficiencyMetrics(),
            moat=MoatIndicators(),
            intrinsic_value=IntrinsicValue(),
        )
        assert _get_tier(r) == CompanyTier.MEGA

    def test_default_nano(self):
        r = AnalysisReport(
            profile=CompanyProfile(ticker="T", name="T"),
            valuation=ValuationMetrics(),
            profitability=ProfitabilityMetrics(),
            solvency=SolvencyMetrics(),
            growth=GrowthMetrics(),
            efficiency=EfficiencyMetrics(),
            moat=MoatIndicators(),
            intrinsic_value=IntrinsicValue(),
        )
        assert _get_tier(r) == CompanyTier.NANO


class TestNaNHandling:
    def test_num_nan(self):
        assert _num(float("nan")) == "N/A"

    def test_pct_nan(self):
        assert _pct(float("nan")) == "N/A"

    def test_pctplain_nan(self):
        assert _pctplain(float("nan")) == "N/A"

    def test_money_nan(self):
        assert _money(float("nan")) == "N/A"


class TestCollapsibleCard:
    def test_expanded_parameter_exists(self):
        from lynx.gui.app import CollapsibleCard
        import inspect
        sig = inspect.signature(CollapsibleCard.__init__)
        assert "expanded" in sig.parameters

    def test_expanded_default_is_true(self):
        from lynx.gui.app import CollapsibleCard
        import inspect
        sig = inspect.signature(CollapsibleCard.__init__)
        assert sig.parameters["expanded"].default is True


class TestLogoImages:
    def test_logo_sm_green_exists(self):
        from pathlib import Path
        logo = Path(__file__).resolve().parent.parent / "img" / "logo_sm_green.png"
        assert logo.exists(), f"Missing logo: {logo}"

    def test_logo_sm_quarter_green_exists(self):
        from pathlib import Path
        logo = Path(__file__).resolve().parent.parent / "img" / "logo_sm_quarter_green.png"
        assert logo.exists(), f"Missing logo: {logo}"

    def test_logo_path_from_gui_module(self):
        """Verify the path resolution used in gui/app.py works."""
        from pathlib import Path
        import lynx.gui.app as gui_mod
        gui_file = Path(gui_mod.__file__).resolve()
        logo = gui_file.parent.parent.parent / "img" / "logo_sm_quarter_green.png"
        assert logo.exists(), f"GUI logo path resolution failed: {logo}"


class TestGuiHasRenderConclusion:
    def test_render_conclusion_exists(self):
        from lynx.gui.app import LynxFAGUI
        assert hasattr(LynxFAGUI, "_render_conclusion")

    def test_render_conclusion_callable(self):
        from lynx.gui.app import LynxFAGUI
        assert callable(getattr(LynxFAGUI, "_render_conclusion"))


class TestMetricInfo:
    def test_show_metric_info_method_exists(self):
        from lynx.gui.app import LynxFAGUI
        assert hasattr(LynxFAGUI, "_show_metric_info")

    def test_add_metric_row_has_key_param(self):
        from lynx.gui.app import LynxFAGUI
        import inspect
        sig = inspect.signature(LynxFAGUI._add_metric_row)
        assert "metric_key" in sig.parameters


class TestRunScript:
    def test_entry_point_exists(self):
        from pathlib import Path
        entry = Path(__file__).resolve().parent.parent / "lynx-fundamental.py"
        assert entry.exists()

    def test_entry_point_executable(self):
        import os
        from pathlib import Path
        entry = Path(__file__).resolve().parent.parent / "lynx-fundamental.py"
        assert os.access(entry, os.X_OK)


