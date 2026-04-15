"""Tests for metric relevance per company tier."""

import pytest
from lynx.metrics.relevance import get_relevance
from lynx.models import CompanyTier, Relevance


class TestGetRelevance:
    def test_pe_critical_for_mega(self):
        assert get_relevance("pe_trailing", CompanyTier.MEGA, "valuation") == Relevance.CRITICAL

    def test_cash_burn_irrelevant_for_mega(self):
        assert get_relevance("cash_burn_rate", CompanyTier.MEGA, "solvency") == Relevance.IRRELEVANT

    def test_cash_burn_critical_for_micro(self):
        assert get_relevance("cash_burn_rate", CompanyTier.MICRO, "solvency") == Relevance.CRITICAL

    def test_ncav_critical_for_nano(self):
        result = get_relevance("price_to_ncav", CompanyTier.NANO, "valuation")
        assert result in (Relevance.CRITICAL, Relevance.RELEVANT)

    def test_unknown_metric_defaults(self):
        result = get_relevance("nonexistent_metric", CompanyTier.MEGA, "valuation")
        assert result == Relevance.RELEVANT  # default

    def test_unknown_category_defaults(self):
        result = get_relevance("pe_trailing", CompanyTier.MEGA, "nonexistent")
        assert result == Relevance.RELEVANT  # default

    def test_shares_growth_critical_for_micro(self):
        result = get_relevance("shares_growth_yoy", CompanyTier.MICRO, "growth")
        assert result == Relevance.CRITICAL

    def test_shares_growth_contextual_for_mega(self):
        result = get_relevance("shares_growth_yoy", CompanyTier.MEGA, "growth")
        assert result in (Relevance.CONTEXTUAL, Relevance.RELEVANT)
