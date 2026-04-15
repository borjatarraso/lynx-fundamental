"""Tests for metrics calculator — edge cases, math guards, tier-awareness."""

import math
import pytest
from lynx.models import (
    CompanyTier,
    FinancialStatement,
    GrowthMetrics,
    ProfitabilityMetrics,
    SolvencyMetrics,
)
from lynx.metrics.calculator import (
    _cagr,
    _calc_margin_history,
    _calc_roic_history,
    _std,
    calc_efficiency,
    calc_growth,
    calc_intrinsic_value,
    calc_moat,
    calc_profitability,
    calc_solvency,
    calc_valuation,
)


# ---------------------------------------------------------------------------
# _cagr helper
# ---------------------------------------------------------------------------

class TestCagr:
    def test_basic_growth(self):
        result = _cagr(100, 200, 3)
        assert result is not None
        assert abs(result - (2 ** (1 / 3) - 1)) < 1e-10

    def test_no_growth(self):
        result = _cagr(100, 100, 3)
        assert result is not None
        assert abs(result) < 1e-10

    def test_decline(self):
        result = _cagr(200, 100, 3)
        assert result is not None
        assert result < 0

    def test_none_start(self):
        assert _cagr(None, 100, 3) is None

    def test_none_end(self):
        assert _cagr(100, None, 3) is None

    def test_zero_start(self):
        assert _cagr(0, 100, 3) is None

    def test_zero_end(self):
        assert _cagr(100, 0, 3) is None

    def test_negative_start(self):
        assert _cagr(-100, 200, 3) is None

    def test_negative_end(self):
        assert _cagr(100, -200, 3) is None

    def test_zero_years(self):
        assert _cagr(100, 200, 0) is None

    def test_negative_years(self):
        assert _cagr(100, 200, -1) is None

    def test_one_year(self):
        result = _cagr(100, 150, 1)
        assert result is not None
        assert abs(result - 0.5) < 1e-10

    def test_very_large_growth(self):
        result = _cagr(1, 1_000_000, 5)
        assert result is not None
        assert not math.isnan(result)
        assert not math.isinf(result)


# ---------------------------------------------------------------------------
# _std helper
# ---------------------------------------------------------------------------

class TestStd:
    def test_single_value(self):
        assert _std([5.0]) == 0.0

    def test_empty(self):
        assert _std([]) == 0.0

    def test_identical_values(self):
        assert _std([3.0, 3.0, 3.0]) == 0.0

    def test_known_std(self):
        result = _std([2.0, 4.0, 4.0, 4.0, 5.0, 5.0, 7.0, 9.0])
        assert result > 0


# ---------------------------------------------------------------------------
# calc_valuation
# ---------------------------------------------------------------------------

class TestCalcValuation:
    def test_empty_info(self):
        v = calc_valuation({}, [], CompanyTier.MEGA)
        assert v.pe_trailing is None
        assert v.pe_forward is None

    def test_pe_and_earnings_yield(self):
        info = {"trailingPE": 20.0}
        v = calc_valuation(info, [], CompanyTier.MEGA)
        assert v.pe_trailing == 20.0
        assert v.earnings_yield is not None
        assert abs(v.earnings_yield - 0.05) < 1e-10

    def test_negative_pe_no_earnings_yield(self):
        info = {"trailingPE": -5.0}
        v = calc_valuation(info, [], CompanyTier.MEGA)
        assert v.pe_trailing == -5.0
        assert v.earnings_yield is None

    def test_p_fcf_calculation(self):
        info = {"currentPrice": 100, "sharesOutstanding": 1_000_000}
        stmts = [FinancialStatement(period="2025", free_cash_flow=10_000_000)]
        v = calc_valuation(info, stmts, CompanyTier.MEGA)
        assert v.p_fcf is not None
        assert abs(v.p_fcf - 10.0) < 1e-6

    def test_p_fcf_negative_fcf(self):
        info = {"currentPrice": 100, "sharesOutstanding": 1_000_000}
        stmts = [FinancialStatement(period="2025", free_cash_flow=-5_000_000)]
        v = calc_valuation(info, stmts, CompanyTier.MEGA)
        assert v.p_fcf is None

    def test_ncav_for_micro(self):
        info = {"currentPrice": 1.0, "sharesOutstanding": 1_000_000}
        stmts = [FinancialStatement(
            period="2025",
            current_assets=5_000_000,
            total_liabilities=2_000_000,
            total_equity=3_000_000,
            total_assets=6_000_000,
        )]
        v = calc_valuation(info, stmts, CompanyTier.MICRO)
        assert v.price_to_ncav is not None


# ---------------------------------------------------------------------------
# calc_profitability
# ---------------------------------------------------------------------------

class TestCalcProfitability:
    def test_empty(self):
        p = calc_profitability({}, [], CompanyTier.MEGA)
        assert p.roic is None

    def test_roic_calculation(self):
        info = {}
        stmts = [FinancialStatement(
            period="2025",
            operating_income=1_000_000,
            total_assets=10_000_000,
            total_cash=2_000_000,
        )]
        p = calc_profitability(info, stmts, CompanyTier.MEGA)
        assert p.roic is not None
        # NOPAT = 1M * 0.75 = 750K; IC = 10M - 2M = 8M; ROIC = 750K/8M
        assert abs(p.roic - 0.09375) < 1e-6

    def test_fcf_margin(self):
        stmts = [FinancialStatement(
            period="2025", free_cash_flow=500_000, revenue=2_000_000,
        )]
        p = calc_profitability({}, stmts, CompanyTier.MEGA)
        assert abs(p.fcf_margin - 0.25) < 1e-6


# ---------------------------------------------------------------------------
# calc_solvency
# ---------------------------------------------------------------------------

class TestCalcSolvency:
    def test_empty(self):
        s = calc_solvency({}, [], CompanyTier.MEGA)
        assert s.altman_z_score is None

    def test_cash_burn(self):
        stmts = [
            FinancialStatement(period="2025", operating_cash_flow=-500_000),
            FinancialStatement(period="2024", operating_cash_flow=-400_000),
        ]
        info = {"totalCash": 1_000_000}
        s = calc_solvency(info, stmts, CompanyTier.MICRO)
        assert s.cash_burn_rate == -500_000
        assert s.cash_runway_years is not None
        assert abs(s.cash_runway_years - 2.0) < 1e-6

    def test_not_burning_cash(self):
        stmts = [
            FinancialStatement(period="2025", operating_cash_flow=500_000),
            FinancialStatement(period="2024", operating_cash_flow=400_000),
        ]
        s = calc_solvency({}, stmts, CompanyTier.MICRO)
        assert s.cash_burn_rate == 0

    def test_ncav_calculation(self):
        stmts = [FinancialStatement(
            period="2025", current_assets=10_000_000, total_liabilities=3_000_000,
        )]
        info = {"sharesOutstanding": 1_000_000}
        s = calc_solvency(info, stmts, CompanyTier.MICRO)
        assert s.ncav == 7_000_000
        assert abs(s.ncav_per_share - 7.0) < 1e-6

    def test_debt_to_equity_divided_by_100(self):
        info = {"debtToEquity": 150.0}  # yfinance gives percentage
        s = calc_solvency(info, [], CompanyTier.MEGA)
        assert abs(s.debt_to_equity - 1.5) < 1e-6


# ---------------------------------------------------------------------------
# calc_growth
# ---------------------------------------------------------------------------

class TestCalcGrowth:
    def test_empty(self):
        g = calc_growth([], CompanyTier.MEGA)
        assert g.revenue_growth_yoy is None

    def test_single_statement(self):
        g = calc_growth([FinancialStatement(period="2025")], CompanyTier.MEGA)
        assert g.revenue_growth_yoy is None

    def test_yoy_growth(self):
        stmts = [
            FinancialStatement(period="2025", revenue=200),
            FinancialStatement(period="2024", revenue=100),
        ]
        g = calc_growth(stmts, CompanyTier.MEGA)
        assert abs(g.revenue_growth_yoy - 1.0) < 1e-6

    def test_yoy_decline(self):
        stmts = [
            FinancialStatement(period="2025", revenue=80),
            FinancialStatement(period="2024", revenue=100),
        ]
        g = calc_growth(stmts, CompanyTier.MEGA)
        assert abs(g.revenue_growth_yoy - (-0.2)) < 1e-6

    def test_division_by_zero_revenue(self):
        stmts = [
            FinancialStatement(period="2025", revenue=100),
            FinancialStatement(period="2024", revenue=0),
        ]
        g = calc_growth(stmts, CompanyTier.MEGA)
        assert g.revenue_growth_yoy is None

    def test_share_dilution(self):
        stmts = [
            FinancialStatement(period="2025", shares_outstanding=110),
            FinancialStatement(period="2024", shares_outstanding=100),
        ]
        g = calc_growth(stmts, CompanyTier.MICRO)
        assert abs(g.shares_growth_yoy - 0.1) < 1e-6

    def test_3y_cagr(self):
        stmts = [
            FinancialStatement(period="2025", revenue=200),
            FinancialStatement(period="2024", revenue=170),
            FinancialStatement(period="2023", revenue=140),
            FinancialStatement(period="2022", revenue=100),
        ]
        g = calc_growth(stmts, CompanyTier.MEGA)
        assert g.revenue_cagr_3y is not None
        expected = (200 / 100) ** (1 / 3) - 1
        assert abs(g.revenue_cagr_3y - expected) < 1e-6


# ---------------------------------------------------------------------------
# calc_intrinsic_value
# ---------------------------------------------------------------------------

class TestCalcIntrinsicValue:
    def test_empty(self):
        iv = calc_intrinsic_value({}, [], GrowthMetrics(), SolvencyMetrics(), CompanyTier.MEGA)
        assert iv.dcf_value is None
        assert iv.graham_number is None

    def test_graham_number(self):
        stmts = [FinancialStatement(period="2025", eps=5.0, book_value_per_share=20.0)]
        iv = calc_intrinsic_value({}, stmts, GrowthMetrics(), SolvencyMetrics(), CompanyTier.SMALL)
        assert iv.graham_number is not None
        expected = math.sqrt(22.5 * 5.0 * 20.0)
        assert abs(iv.graham_number - round(expected, 2)) < 0.01

    def test_graham_negative_eps(self):
        stmts = [FinancialStatement(period="2025", eps=-2.0, book_value_per_share=20.0)]
        iv = calc_intrinsic_value({}, stmts, GrowthMetrics(), SolvencyMetrics(), CompanyTier.SMALL)
        assert iv.graham_number is None

    def test_lynch_fair_value_capped(self):
        stmts = [FinancialStatement(period="2025", eps=2.0)]
        growth = GrowthMetrics(earnings_cagr_3y=5.0)  # 500% growth
        iv = calc_intrinsic_value({}, stmts, growth, SolvencyMetrics(), CompanyTier.SMALL)
        # eg should be capped at 100
        assert iv.lynch_fair_value is not None
        assert iv.lynch_fair_value == round(2.0 * 100, 2)  # 200.0

    def test_dcf_for_mega(self):
        info = {"currentPrice": 100, "sharesOutstanding": 1_000_000}
        stmts = [FinancialStatement(period="2025", free_cash_flow=10_000_000)]
        growth = GrowthMetrics(revenue_cagr_3y=0.10)
        iv = calc_intrinsic_value(info, stmts, growth, SolvencyMetrics(), CompanyTier.MEGA)
        assert iv.dcf_value is not None
        assert iv.dcf_value > 0

    def test_dcf_not_computed_for_micro(self):
        info = {"currentPrice": 1, "sharesOutstanding": 1_000_000}
        stmts = [FinancialStatement(period="2025", free_cash_flow=100_000)]
        iv = calc_intrinsic_value(info, stmts, GrowthMetrics(), SolvencyMetrics(), CompanyTier.MICRO)
        assert iv.dcf_value is None  # Not computed for MICRO tier

    def test_margin_of_safety(self):
        info = {"currentPrice": 50}
        stmts = [FinancialStatement(period="2025", eps=5.0, book_value_per_share=20.0)]
        iv = calc_intrinsic_value(info, stmts, GrowthMetrics(), SolvencyMetrics(), CompanyTier.SMALL)
        if iv.graham_number:
            assert iv.margin_of_safety_graham is not None

    def test_primary_method_by_tier(self):
        stmts = [FinancialStatement(period="2025")]
        iv_mega = calc_intrinsic_value({}, stmts, GrowthMetrics(), SolvencyMetrics(), CompanyTier.MEGA)
        assert iv_mega.primary_method == "DCF"

        iv_micro = calc_intrinsic_value({}, stmts, GrowthMetrics(), SolvencyMetrics(), CompanyTier.MICRO)
        assert iv_micro.primary_method == "NCAV (Net-Net)"


# ---------------------------------------------------------------------------
# calc_moat
# ---------------------------------------------------------------------------

class TestCalcMoat:
    def test_empty_mega(self):
        m = calc_moat(
            ProfitabilityMetrics(), GrowthMetrics(), SolvencyMetrics(),
            [], {}, CompanyTier.MEGA,
        )
        assert m.moat_score is not None
        assert m.competitive_position is not None

    def test_empty_micro(self):
        m = calc_moat(
            ProfitabilityMetrics(), GrowthMetrics(), SolvencyMetrics(),
            [], {}, CompanyTier.MICRO,
        )
        assert m.moat_score is not None
        assert m.competitive_position is not None

    def test_wide_moat_conditions(self):
        stmts = [
            FinancialStatement(
                period=str(2025 - i),
                operating_income=2_000_000,
                total_assets=10_000_000,
                total_cash=1_000_000,
                gross_profit=6_000_000,
                revenue=10_000_000,
            )
            for i in range(4)
        ]
        prof = ProfitabilityMetrics(gross_margin=0.65, net_margin=0.25)
        growth = GrowthMetrics(revenue_cagr_3y=0.12, earnings_cagr_3y=0.12)
        solv = SolvencyMetrics(debt_to_equity=0.3, current_ratio=2.0)
        m = calc_moat(prof, growth, solv, stmts, {"marketCap": 50_000_000_000}, CompanyTier.LARGE)
        assert m.moat_score >= 50


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

class TestCalcRoicHistory:
    def test_empty(self):
        assert _calc_roic_history([]) == []

    def test_with_data(self):
        stmts = [FinancialStatement(
            period="2025",
            operating_income=1_000_000,
            total_assets=10_000_000,
            total_cash=2_000_000,
        )]
        result = _calc_roic_history(stmts)
        assert len(result) == 1
        assert result[0] is not None

    def test_missing_data_skipped(self):
        stmts = [
            FinancialStatement(period="2025", operating_income=None),
            FinancialStatement(
                period="2024",
                operating_income=500_000,
                total_assets=5_000_000,
                total_cash=1_000_000,
            ),
        ]
        result = _calc_roic_history(stmts)
        assert len(result) == 1


class TestCalcMarginHistory:
    def test_empty(self):
        assert _calc_margin_history([]) == []

    def test_with_data(self):
        stmts = [FinancialStatement(
            period="2025", gross_profit=600_000, revenue=1_000_000,
        )]
        result = _calc_margin_history(stmts)
        assert len(result) == 1
        assert abs(result[0] - 0.6) < 1e-6

    def test_zero_revenue_skipped(self):
        stmts = [FinancialStatement(
            period="2025", gross_profit=600_000, revenue=0,
        )]
        assert _calc_margin_history(stmts) == []
