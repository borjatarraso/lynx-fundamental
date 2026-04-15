"""Tests for metric explanations dictionary."""

import pytest
from lynx.metrics.explanations import (
    METRIC_EXPLANATIONS,
    get_explanation,
    list_metrics,
)
from lynx.models import MetricExplanation


class TestMetricExplanations:
    def test_dict_not_empty(self):
        assert len(METRIC_EXPLANATIONS) > 30

    def test_all_are_metric_explanation(self):
        for key, exp in METRIC_EXPLANATIONS.items():
            assert isinstance(exp, MetricExplanation)
            assert exp.key == key

    def test_all_have_required_fields(self):
        for key, exp in METRIC_EXPLANATIONS.items():
            assert exp.full_name, f"{key} missing full_name"
            assert exp.description, f"{key} missing description"
            assert exp.why_used, f"{key} missing why_used"
            assert exp.formula, f"{key} missing formula"
            assert exp.category in ("valuation", "profitability", "solvency", "growth", "efficiency"), \
                f"{key} has invalid category: {exp.category}"

    def test_categories_covered(self):
        categories = {exp.category for exp in METRIC_EXPLANATIONS.values()}
        assert "valuation" in categories
        assert "profitability" in categories
        assert "solvency" in categories
        assert "growth" in categories


class TestGetExplanation:
    def test_known_metric(self):
        exp = get_explanation("pe_trailing")
        assert exp is not None
        assert exp.key == "pe_trailing"

    def test_unknown_metric(self):
        assert get_explanation("nonexistent") is None

    def test_all_keys_accessible(self):
        for key in METRIC_EXPLANATIONS:
            assert get_explanation(key) is not None


class TestListMetrics:
    def test_all(self):
        all_metrics = list_metrics()
        assert len(all_metrics) == len(METRIC_EXPLANATIONS)

    def test_filter_valuation(self):
        val_metrics = list_metrics("valuation")
        assert len(val_metrics) > 0
        assert all(m.category == "valuation" for m in val_metrics)

    def test_filter_profitability(self):
        prof_metrics = list_metrics("profitability")
        assert len(prof_metrics) > 0

    def test_filter_nonexistent(self):
        assert list_metrics("nonexistent") == []


class TestKeyMetricsExist:
    """Verify that key metrics used in the display have explanations."""

    @pytest.mark.parametrize("key", [
        "pe_trailing", "pe_forward", "pb_ratio", "ps_ratio", "p_fcf",
        "ev_ebitda", "ev_revenue", "peg_ratio", "dividend_yield", "earnings_yield",
    ])
    def test_valuation_metrics(self, key):
        assert key in METRIC_EXPLANATIONS

    @pytest.mark.parametrize("key", [
        "roe", "roa", "roic", "gross_margin", "operating_margin",
        "net_margin", "fcf_margin", "ebitda_margin",
    ])
    def test_profitability_metrics(self, key):
        assert key in METRIC_EXPLANATIONS

    @pytest.mark.parametrize("key", [
        "debt_to_equity", "debt_to_ebitda", "current_ratio", "quick_ratio",
        "interest_coverage", "altman_z_score", "cash_burn_rate", "cash_runway_years",
    ])
    def test_solvency_metrics(self, key):
        assert key in METRIC_EXPLANATIONS

    @pytest.mark.parametrize("key", [
        "revenue_growth_yoy", "revenue_cagr_3y", "earnings_growth_yoy",
        "earnings_cagr_3y", "shares_growth_yoy",
    ])
    def test_growth_metrics(self, key):
        assert key in METRIC_EXPLANATIONS
