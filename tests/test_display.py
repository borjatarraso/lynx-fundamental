"""Tests for display formatters and assessment functions."""

import pytest
from lynx.display import (
    _assess_burn,
    _assess_current,
    _assess_de,
    _assess_dilution,
    _assess_ev_ebitda,
    _assess_gross_margin,
    _assess_ncav_vs_price,
    _assess_pb,
    _assess_pe,
    _assess_peg,
    _assess_pfcf,
    _assess_ps,
    _assess_quick,
    _assess_roa,
    _assess_roe,
    _assess_roic,
    _assess_runway,
    _assess_wc,
    _assess_zscore,
    fmt_money,
    fmt_num,
    fmt_pct,
    fmt_score,
)
from lynx.models import CompanyTier


# ---------------------------------------------------------------------------
# Formatters
# ---------------------------------------------------------------------------

class TestFmtPct:
    def test_none(self):
        assert "N/A" in fmt_pct(None)

    def test_zero(self):
        assert "0.00%" in fmt_pct(0.0)

    def test_positive(self):
        assert "25.00%" in fmt_pct(0.25)

    def test_negative(self):
        assert "-10.00%" in fmt_pct(-0.10)

    def test_precision(self):
        result = fmt_pct(0.1234, digits=1)
        assert "12.3%" in result


class TestFmtNum:
    def test_none(self):
        assert "N/A" in fmt_num(None)

    def test_zero(self):
        assert "0.00" in fmt_num(0.0)

    def test_large_number(self):
        result = fmt_num(1234567.89)
        assert "1,234,567.89" in result


class TestFmtMoney:
    def test_none(self):
        assert "N/A" in fmt_money(None)

    def test_trillions(self):
        assert "T" in fmt_money(1_500_000_000_000)

    def test_billions(self):
        assert "B" in fmt_money(5_000_000_000)

    def test_millions(self):
        assert "M" in fmt_money(50_000_000)

    def test_thousands(self):
        result = fmt_money(5000)
        assert "$" in result

    def test_negative_billions(self):
        result = fmt_money(-2_000_000_000)
        assert "B" in result


class TestFmtScore:
    def test_none(self):
        assert "N/A" in fmt_score(None)

    def test_high_score(self):
        result = fmt_score(85.0)
        assert "green" in result
        assert "85.0" in result

    def test_medium_score(self):
        result = fmt_score(55.0)
        assert "yellow" in result

    def test_low_score(self):
        result = fmt_score(15.0)
        assert "red" in result


# ---------------------------------------------------------------------------
# Assessment functions — PE
# ---------------------------------------------------------------------------

class TestAssessPe:
    def test_none(self):
        assert _assess_pe(None, CompanyTier.MEGA) == ""

    def test_negative(self):
        assert "Negative" in _assess_pe(-5, CompanyTier.MEGA)

    def test_cheap_mega(self):
        assert "cheap" in _assess_pe(8, CompanyTier.MEGA).lower()

    def test_expensive_mega(self):
        assert "expensive" in _assess_pe(35, CompanyTier.MEGA).lower()

    def test_micro_lower_thresholds(self):
        # 12 is "Cheap" for micro but "Fair" is not reached until 18
        result_micro = _assess_pe(12, CompanyTier.MICRO)
        result_mega = _assess_pe(12, CompanyTier.MEGA)
        # Both should have valid assessments
        assert result_micro != ""
        assert result_mega != ""


# ---------------------------------------------------------------------------
# Assessment functions — other
# ---------------------------------------------------------------------------

class TestAssessPb:
    def test_none(self):
        assert _assess_pb(None, CompanyTier.MEGA) == ""

    def test_below_book_micro(self):
        assert "book" in _assess_pb(0.5, CompanyTier.MICRO).lower()


class TestAssessRoe:
    def test_negative(self):
        assert "Negative" in _assess_roe(-0.1, CompanyTier.MEGA)

    def test_excellent(self):
        assert "Excellent" in _assess_roe(0.25, CompanyTier.MEGA)

    def test_micro_positive(self):
        assert "Positive" in _assess_roe(0.12, CompanyTier.MICRO)


class TestAssessDe:
    def test_net_cash(self):
        assert "cash" in _assess_de(-0.5, CompanyTier.MEGA).lower()

    def test_micro_high_debt(self):
        assert "risky" in _assess_de(0.8, CompanyTier.MICRO).lower()


class TestAssessZscore:
    def test_safe(self):
        assert "Safe" in _assess_zscore(3.5)

    def test_grey(self):
        assert "Grey" in _assess_zscore(2.5)

    def test_distress(self):
        assert "Distress" in _assess_zscore(1.0)


class TestAssessBurn:
    def test_not_burning(self):
        assert "Not burning" in _assess_burn(0)

    def test_burning(self):
        result = _assess_burn(-1_000_000)
        assert "Burning" in result


class TestAssessRunway:
    def test_ample(self):
        assert "Ample" in _assess_runway(10.0)

    def test_critical(self):
        assert "Critical" in _assess_runway(0.3)


class TestAssessDilution:
    def test_buybacks(self):
        assert "Buyback" in _assess_dilution(-0.05, CompanyTier.MICRO)

    def test_heavy(self):
        assert "Heavy" in _assess_dilution(0.15, CompanyTier.MICRO)

    def test_none(self):
        assert _assess_dilution(None, CompanyTier.MICRO) == ""
