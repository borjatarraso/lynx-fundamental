"""Tests for data models and tier classification."""

import pytest
from lynx.models import (
    AnalysisReport,
    CompanyProfile,
    CompanyTier,
    EfficiencyMetrics,
    Filing,
    FinancialStatement,
    GrowthMetrics,
    IntrinsicValue,
    MoatIndicators,
    NewsArticle,
    ProfitabilityMetrics,
    Relevance,
    SolvencyMetrics,
    ValuationMetrics,
    classify_tier,
)


class TestClassifyTier:
    def test_mega_cap(self):
        assert classify_tier(300_000_000_000) == CompanyTier.MEGA

    def test_large_cap(self):
        assert classify_tier(50_000_000_000) == CompanyTier.LARGE

    def test_mid_cap(self):
        assert classify_tier(5_000_000_000) == CompanyTier.MID

    def test_small_cap(self):
        assert classify_tier(500_000_000) == CompanyTier.SMALL

    def test_micro_cap(self):
        assert classify_tier(100_000_000) == CompanyTier.MICRO

    def test_nano_cap(self):
        assert classify_tier(10_000_000) == CompanyTier.NANO

    def test_none_defaults_to_nano(self):
        assert classify_tier(None) == CompanyTier.NANO

    def test_zero_defaults_to_nano(self):
        assert classify_tier(0) == CompanyTier.NANO

    def test_negative_defaults_to_nano(self):
        assert classify_tier(-1_000_000) == CompanyTier.NANO

    def test_boundary_mega(self):
        assert classify_tier(200_000_000_000) == CompanyTier.MEGA
        assert classify_tier(199_999_999_999) == CompanyTier.LARGE

    def test_boundary_large(self):
        assert classify_tier(10_000_000_000) == CompanyTier.LARGE
        assert classify_tier(9_999_999_999) == CompanyTier.MID

    def test_boundary_mid(self):
        assert classify_tier(2_000_000_000) == CompanyTier.MID
        assert classify_tier(1_999_999_999) == CompanyTier.SMALL

    def test_boundary_small(self):
        assert classify_tier(300_000_000) == CompanyTier.SMALL
        assert classify_tier(299_999_999) == CompanyTier.MICRO

    def test_boundary_micro(self):
        assert classify_tier(50_000_000) == CompanyTier.MICRO
        assert classify_tier(49_999_999) == CompanyTier.NANO


class TestCompanyTierEnum:
    def test_tier_values(self):
        assert CompanyTier.MEGA.value == "Mega Cap"
        assert CompanyTier.NANO.value == "Nano Cap"

    def test_tier_is_str(self):
        assert isinstance(CompanyTier.MEGA, str)
        assert CompanyTier.MEGA.value == "Mega Cap"


class TestRelevanceEnum:
    def test_relevance_values(self):
        assert Relevance.CRITICAL.value == "critical"
        assert Relevance.IRRELEVANT.value == "irrelevant"


class TestDataclassDefaults:
    def test_company_profile_defaults(self):
        p = CompanyProfile(ticker="TEST", name="Test Co")
        assert p.isin is None
        assert p.sector is None
        assert p.tier == CompanyTier.NANO

    def test_valuation_all_none(self):
        v = ValuationMetrics()
        assert v.pe_trailing is None
        assert v.pe_forward is None
        assert v.price_to_ncav is None

    def test_solvency_all_none(self):
        s = SolvencyMetrics()
        assert s.cash_burn_rate is None
        assert s.cash_runway_years is None
        assert s.ncav is None

    def test_moat_list_defaults(self):
        m = MoatIndicators()
        assert m.roic_history == []
        assert m.gross_margin_history == []

    def test_financial_statement_defaults(self):
        fs = FinancialStatement(period="2025")
        assert fs.revenue is None
        assert fs.net_income is None

    def test_filing_creation(self):
        f = Filing(form_type="10-K", filing_date="2025-01-01", period="2024", url="https://example.com")
        assert f.local_path is None

    def test_news_article_creation(self):
        n = NewsArticle(title="Test", url="https://example.com")
        assert n.published is None
        assert n.local_path is None

    def test_analysis_report_defaults(self):
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
        assert r.financials == []
        assert r.filings == []
        assert r.news == []
        assert r.fetched_at  # auto-generated
