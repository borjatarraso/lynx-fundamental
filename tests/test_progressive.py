"""Tests for progressive analysis, partial report building, and None-safe display."""

import pytest
from io import StringIO

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


def _profile(**overrides):
    defaults = dict(ticker="TEST", name="Test Corp", tier=CompanyTier.LARGE, market_cap=50e9)
    defaults.update(overrides)
    return CompanyProfile(**defaults)


# ---------------------------------------------------------------------------
# AnalysisReport partial construction
# ---------------------------------------------------------------------------

class TestPartialReport:
    """AnalysisReport can be constructed with only a profile."""

    def test_minimal(self):
        r = AnalysisReport(profile=_profile())
        assert r.valuation is None
        assert r.profitability is None
        assert r.solvency is None
        assert r.growth is None
        assert r.efficiency is None
        assert r.moat is None
        assert r.intrinsic_value is None
        assert r.financials == []
        assert r.filings == []
        assert r.news == []

    def test_incremental_build(self):
        r = AnalysisReport(profile=_profile())
        r.valuation = ValuationMetrics(pe_trailing=15.0)
        assert r.valuation.pe_trailing == 15.0
        assert r.profitability is None  # still None

    def test_full_construction_still_works(self):
        r = AnalysisReport(
            profile=_profile(),
            valuation=ValuationMetrics(),
            profitability=ProfitabilityMetrics(),
            solvency=SolvencyMetrics(),
            growth=GrowthMetrics(),
            efficiency=EfficiencyMetrics(),
            moat=MoatIndicators(),
            intrinsic_value=IntrinsicValue(),
        )
        assert r.valuation is not None
        assert r.moat is not None


# ---------------------------------------------------------------------------
# Conclusion with None metric sections
# ---------------------------------------------------------------------------

class TestConclusionNoneSafe:
    """generate_conclusion must not crash when metric sections are None."""

    def test_all_none(self):
        from lynx.core.conclusion import generate_conclusion
        r = AnalysisReport(profile=_profile())
        c = generate_conclusion(r)
        assert c.verdict in ("Strong Buy", "Buy", "Hold", "Caution", "Avoid")
        assert 0 <= c.overall_score <= 100
        assert len(c.category_scores) == 5
        assert len(c.category_summaries) == 5

    def test_partial_metrics(self):
        from lynx.core.conclusion import generate_conclusion
        r = AnalysisReport(
            profile=_profile(),
            valuation=ValuationMetrics(pe_trailing=12.0),
            profitability=None,
            solvency=SolvencyMetrics(debt_to_equity=0.3),
        )
        c = generate_conclusion(r)
        assert c.verdict
        assert c.category_summaries["profitability"] == "Limited profitability data available"

    def test_summaries_fallback(self):
        from lynx.core.conclusion import generate_conclusion
        r = AnalysisReport(profile=_profile())
        c = generate_conclusion(r)
        assert "Limited" in c.category_summaries["valuation"]
        assert "Moat assessment" in c.category_summaries["moat"]


# ---------------------------------------------------------------------------
# Serialization round-trip with None fields
# ---------------------------------------------------------------------------

class TestSerializationNoneSafe:
    """_report_to_dict / _dict_to_report handle None metric sections."""

    def test_round_trip_partial(self):
        from lynx.core.analyzer import _report_to_dict, _dict_to_report
        r = AnalysisReport(
            profile=_profile(),
            valuation=ValuationMetrics(pe_trailing=20.0),
        )
        d = _report_to_dict(r)
        assert d["profitability"] is None
        assert d["valuation"]["pe_trailing"] == 20.0

        r2 = _dict_to_report(d)
        assert r2.profitability is None
        assert r2.valuation is not None
        assert r2.valuation.pe_trailing == 20.0

    def test_round_trip_full(self):
        from lynx.core.analyzer import _report_to_dict, _dict_to_report
        r = AnalysisReport(
            profile=_profile(),
            valuation=ValuationMetrics(pe_trailing=15.0),
            profitability=ProfitabilityMetrics(roe=0.2),
            solvency=SolvencyMetrics(current_ratio=2.0),
            growth=GrowthMetrics(revenue_growth_yoy=0.1),
            efficiency=EfficiencyMetrics(),
            moat=MoatIndicators(moat_score=60.0),
            intrinsic_value=IntrinsicValue(current_price=100.0),
        )
        d = _report_to_dict(r)
        r2 = _dict_to_report(d)
        assert r2.valuation.pe_trailing == 15.0
        assert r2.moat.moat_score == 60.0


# ---------------------------------------------------------------------------
# display_report_stage and display_full_report with partial reports
# ---------------------------------------------------------------------------

class TestDisplayNoneSafe:
    """Display functions must not crash when metric sections are None."""

    def test_display_full_report_partial(self):
        from rich.console import Console
        from lynx.display import display_full_report

        r = AnalysisReport(profile=_profile())
        buf = StringIO()
        # Redirect console output
        import lynx.display as disp
        old_console = disp.console
        disp.console = Console(file=buf, force_terminal=True)
        try:
            display_full_report(r)
        finally:
            disp.console = old_console
        output = buf.getvalue()
        assert "Test Corp" in output

    def test_display_report_stage_profile(self):
        from rich.console import Console
        from lynx.display import display_report_stage

        r = AnalysisReport(profile=_profile())
        buf = StringIO()
        import lynx.display as disp
        old_console = disp.console
        disp.console = Console(file=buf, force_terminal=True)
        try:
            display_report_stage("profile", r)
        finally:
            disp.console = old_console
        output = buf.getvalue()
        assert "Test Corp" in output

    def test_display_report_stage_valuation(self):
        from rich.console import Console
        from lynx.display import display_report_stage

        r = AnalysisReport(
            profile=_profile(),
            valuation=ValuationMetrics(pe_trailing=15.0),
        )
        buf = StringIO()
        import lynx.display as disp
        old_console = disp.console
        disp.console = Console(file=buf, force_terminal=True)
        try:
            display_report_stage("valuation", r)
        finally:
            disp.console = old_console
        output = buf.getvalue()
        assert "15.00" in output

    def test_display_report_stage_conclusion_partial(self):
        from rich.console import Console
        from lynx.display import display_report_stage

        r = AnalysisReport(profile=_profile())
        buf = StringIO()
        import lynx.display as disp
        old_console = disp.console
        disp.console = Console(file=buf, force_terminal=True)
        try:
            display_report_stage("conclusion", r)
        finally:
            disp.console = old_console
        output = buf.getvalue()
        assert "Caution" in output or "Hold" in output or "Avoid" in output

    def test_display_all_stages_sequence(self):
        """Simulate full progressive flow through display_report_stage."""
        from rich.console import Console
        from lynx.display import display_report_stage

        r = AnalysisReport(profile=_profile())
        buf = StringIO()
        import lynx.display as disp
        old_console = disp.console
        disp.console = Console(file=buf, force_terminal=True)
        try:
            display_report_stage("profile", r)
            r.valuation = ValuationMetrics(pe_trailing=10.0)
            display_report_stage("valuation", r)
            r.profitability = ProfitabilityMetrics(roe=0.18)
            display_report_stage("profitability", r)
            r.solvency = SolvencyMetrics(current_ratio=2.5)
            display_report_stage("solvency", r)
            r.growth = GrowthMetrics(revenue_growth_yoy=0.12)
            display_report_stage("growth", r)
            r.moat = MoatIndicators(moat_score=55.0)
            display_report_stage("moat", r)
            r.intrinsic_value = IntrinsicValue(current_price=100.0)
            display_report_stage("intrinsic_value", r)
            display_report_stage("filings", r)
            display_report_stage("news", r)
            display_report_stage("conclusion", r)
            display_report_stage("complete", r)
        finally:
            disp.console = old_console
        output = buf.getvalue()
        assert "Test Corp" in output
        assert "Valuation" in output
        assert "Profitability" in output


# ---------------------------------------------------------------------------
# Progressive analysis callback mechanism
# ---------------------------------------------------------------------------

class TestProgressCallback:
    """run_progressive_analysis on_progress callback receives correct stages."""

    def test_callback_signature(self):
        """Verify ProgressCallback type alias exists and is callable."""
        from lynx.core.analyzer import ProgressCallback
        # Just ensure the type exists
        assert ProgressCallback is not None


# ---------------------------------------------------------------------------
# Sector/industry insights
# ---------------------------------------------------------------------------

class TestSectorInsights:
    """Sector and industry insight data and lookups."""

    def test_get_sector_insight_found(self):
        from lynx.metrics.sector_insights import get_sector_insight
        s = get_sector_insight("Technology")
        assert s is not None
        assert s.sector == "Technology"
        assert len(s.critical_metrics) > 0
        assert len(s.key_risks) > 0

    def test_get_sector_insight_case_insensitive(self):
        from lynx.metrics.sector_insights import get_sector_insight
        assert get_sector_insight("technology") is not None
        assert get_sector_insight("TECHNOLOGY") is not None
        assert get_sector_insight("Technology") is not None

    def test_get_sector_insight_none(self):
        from lynx.metrics.sector_insights import get_sector_insight
        assert get_sector_insight(None) is None
        assert get_sector_insight("") is None
        assert get_sector_insight("Nonexistent Sector") is None

    def test_get_industry_insight_found(self):
        from lynx.metrics.sector_insights import get_industry_insight
        i = get_industry_insight("Consumer Electronics")
        assert i is not None
        assert i.industry == "Consumer Electronics"
        assert len(i.critical_metrics) > 0

    def test_get_industry_insight_none(self):
        from lynx.metrics.sector_insights import get_industry_insight
        assert get_industry_insight(None) is None
        assert get_industry_insight("") is None

    def test_all_sectors_have_data(self):
        from lynx.metrics.sector_insights import list_sectors
        sectors = list_sectors()
        assert len(sectors) >= 10

    def test_all_industries_have_data(self):
        from lynx.metrics.sector_insights import list_industries
        industries = list_industries()
        assert len(industries) >= 10

    def test_sector_insight_fields(self):
        from lynx.metrics.sector_insights import get_sector_insight
        s = get_sector_insight("Financial Services")
        assert s.overview
        assert s.typical_valuation
        assert len(s.what_to_watch) > 0

    def test_display_sector_industry_none_safe(self):
        """_display_sector_industry handles None sector/industry."""
        from rich.console import Console
        from lynx.display import _display_sector_industry
        import lynx.display as disp
        from io import StringIO

        r = AnalysisReport(profile=_profile())
        r.profile.sector = None
        r.profile.industry = None
        buf = StringIO()
        old = disp.console
        disp.console = Console(file=buf, force_terminal=True)
        try:
            _display_sector_industry(r)  # should not crash
        finally:
            disp.console = old


# ---------------------------------------------------------------------------
# HTML escaping in exports
# ---------------------------------------------------------------------------

class TestExportHTMLEscaping:
    """Export functions must escape special chars in company names."""

    def test_html_export_escapes_ampersand(self, tmp_path):
        from lynx.export.html_export import export_html
        r = AnalysisReport(profile=_profile(name="AT&T Inc", ticker="T"))
        r.valuation = ValuationMetrics()
        path = export_html(r, tmp_path / "test.html")
        content = path.read_text()
        assert "AT&amp;T" in content
        assert "AT&T" not in content.split("<style>")[0]  # raw & not in head

    def test_html_export_escapes_angle_brackets(self, tmp_path):
        from lynx.export.html_export import export_html
        r = AnalysisReport(profile=_profile(name="Test <Script> Corp", ticker="TST"))
        r.valuation = ValuationMetrics()
        path = export_html(r, tmp_path / "test.html")
        content = path.read_text()
        assert "&lt;Script&gt;" in content


# ---------------------------------------------------------------------------
# _safe() edge cases
# ---------------------------------------------------------------------------

class TestSafeHelper:
    """The _safe() helper in conclusion.py handles edge cases."""

    def test_safe_none(self):
        from lynx.core.conclusion import _safe
        assert _safe(None) == 0.0
        assert _safe(None, None) is None

    def test_safe_nan(self):
        from lynx.core.conclusion import _safe
        assert _safe(float("nan")) == 0.0

    def test_safe_inf(self):
        from lynx.core.conclusion import _safe
        assert _safe(float("inf")) == 0.0
        assert _safe(float("-inf")) == 0.0

    def test_safe_bool(self):
        from lynx.core.conclusion import _safe
        assert _safe(True) == 0.0
        assert _safe(False) == 0.0

    def test_safe_valid(self):
        from lynx.core.conclusion import _safe
        assert _safe(15.5) == 15.5
        assert _safe(-3.0) == -3.0
        assert _safe(0) == 0.0

    def test_safe_string(self):
        from lynx.core.conclusion import _safe
        assert _safe("not a number") == 0.0
        assert _safe("") == 0.0


# ---------------------------------------------------------------------------
# ISIN retrieval
# ---------------------------------------------------------------------------

class TestISINRetrieval:
    """ISIN field is populated when available."""

    def test_profile_isin_field_exists(self):
        p = _profile()
        assert hasattr(p, "isin")

    def test_report_preserves_isin(self):
        from lynx.core.analyzer import _report_to_dict, _dict_to_report
        r = AnalysisReport(profile=_profile())
        r.profile.isin = "US0378331005"
        d = _report_to_dict(r)
        r2 = _dict_to_report(d)
        assert r2.profile.isin == "US0378331005"

    def test_report_preserves_none_isin(self):
        from lynx.core.analyzer import _report_to_dict, _dict_to_report
        r = AnalysisReport(profile=_profile())
        r.profile.isin = None
        d = _report_to_dict(r)
        r2 = _dict_to_report(d)
        assert r2.profile.isin is None
