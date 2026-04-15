"""Tests for the report synthesis / conclusion engine."""

import pytest
from lynx.core.conclusion import generate_conclusion, _verdict
from lynx.models import (
    AnalysisReport,
    CompanyProfile,
    CompanyTier,
    EfficiencyMetrics,
    FinancialStatement,
    GrowthMetrics,
    IntrinsicValue,
    MoatIndicators,
    ProfitabilityMetrics,
    SolvencyMetrics,
    ValuationMetrics,
)


def _make_report(**overrides):
    defaults = dict(
        profile=CompanyProfile(ticker="TEST", name="Test Co", tier=CompanyTier.MEGA, market_cap=500e9),
        valuation=ValuationMetrics(pe_trailing=18.0, pb_ratio=2.5, p_fcf=15.0, ev_ebitda=12.0),
        profitability=ProfitabilityMetrics(roe=0.18, roic=0.14, gross_margin=0.45, net_margin=0.12),
        solvency=SolvencyMetrics(debt_to_equity=0.6, current_ratio=1.8, altman_z_score=3.5),
        growth=GrowthMetrics(revenue_growth_yoy=0.08, revenue_cagr_3y=0.10, earnings_growth_yoy=0.12),
        efficiency=EfficiencyMetrics(),
        moat=MoatIndicators(moat_score=55.0, competitive_position="Narrow Moat"),
        intrinsic_value=IntrinsicValue(),
    )
    defaults.update(overrides)
    return AnalysisReport(**defaults)


class TestVerdict:
    def test_strong_buy(self):
        assert _verdict(80) == "Strong Buy"

    def test_buy(self):
        assert _verdict(65) == "Buy"

    def test_hold(self):
        assert _verdict(50) == "Hold"

    def test_caution(self):
        assert _verdict(35) == "Caution"

    def test_avoid(self):
        assert _verdict(20) == "Avoid"


class TestGenerateConclusion:
    def test_returns_conclusion(self):
        r = _make_report()
        c = generate_conclusion(r)
        assert c.overall_score > 0
        assert c.verdict in ("Strong Buy", "Buy", "Hold", "Caution", "Avoid")
        assert c.summary
        assert len(c.category_scores) == 5

    def test_score_bounded(self):
        r = _make_report()
        c = generate_conclusion(r)
        assert 0 <= c.overall_score <= 100

    def test_category_scores_present(self):
        r = _make_report()
        c = generate_conclusion(r)
        for cat in ("valuation", "profitability", "solvency", "growth", "moat"):
            assert cat in c.category_scores
            assert 0 <= c.category_scores[cat] <= 100

    def test_category_summaries(self):
        r = _make_report()
        c = generate_conclusion(r)
        assert "valuation" in c.category_summaries
        assert "profitability" in c.category_summaries

    def test_strengths_and_risks(self):
        r = _make_report()
        c = generate_conclusion(r)
        assert isinstance(c.strengths, list)
        assert isinstance(c.risks, list)
        assert len(c.strengths) <= 5
        assert len(c.risks) <= 5

    def test_tier_note(self):
        r = _make_report()
        c = generate_conclusion(r)
        assert c.tier_note  # non-empty for all tiers

    def test_micro_cap_higher_solvency_weight(self):
        r = _make_report(
            profile=CompanyProfile(ticker="T", name="T", tier=CompanyTier.MICRO),
            solvency=SolvencyMetrics(cash_burn_rate=-500_000, cash_runway_years=0.5),
        )
        c = generate_conclusion(r)
        # Micro cap with bad solvency should score poorly
        assert c.category_scores["solvency"] < 50

    def test_empty_data(self):
        r = _make_report(
            valuation=ValuationMetrics(),
            profitability=ProfitabilityMetrics(),
            solvency=SolvencyMetrics(),
            growth=GrowthMetrics(),
            moat=MoatIndicators(),
        )
        c = generate_conclusion(r)
        assert c.verdict  # should still produce a verdict
        assert c.overall_score >= 0

    def test_excellent_company(self):
        r = _make_report(
            valuation=ValuationMetrics(pe_trailing=12.0, pb_ratio=0.8, p_fcf=8.0, ev_ebitda=6.0),
            profitability=ProfitabilityMetrics(roe=0.25, roic=0.20, gross_margin=0.65, net_margin=0.22),
            solvency=SolvencyMetrics(debt_to_equity=0.2, current_ratio=3.0, altman_z_score=4.0),
            growth=GrowthMetrics(revenue_growth_yoy=0.25, revenue_cagr_3y=0.18),
            moat=MoatIndicators(moat_score=80.0),
        )
        c = generate_conclusion(r)
        assert c.verdict in ("Strong Buy", "Buy")
        assert len(c.strengths) > 0

    def test_distressed_company(self):
        r = _make_report(
            valuation=ValuationMetrics(pe_trailing=-5.0),
            profitability=ProfitabilityMetrics(net_margin=-0.15, roic=-0.05),
            solvency=SolvencyMetrics(debt_to_equity=3.0, altman_z_score=1.2, cash_burn_rate=-1e6, cash_runway_years=0.8),
            growth=GrowthMetrics(revenue_growth_yoy=-0.20, shares_growth_yoy=0.15),
            moat=MoatIndicators(moat_score=10.0),
        )
        c = generate_conclusion(r)
        assert c.verdict in ("Caution", "Avoid")
        assert len(c.risks) > 0
