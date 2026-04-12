"""Metrics calculation engine for value investing analysis.

All calculations are tier-aware: micro/nano-cap companies get survival-focused
metrics (NCAV, cash burn, dilution) while large/mega-caps get full traditional
value investing metrics (DCF, ROIC consistency, moat scoring).
"""

from __future__ import annotations

import math
from typing import Optional

from lynx.models import (
    CompanyTier,
    EfficiencyMetrics,
    FinancialStatement,
    GrowthMetrics,
    IntrinsicValue,
    MoatIndicators,
    ProfitabilityMetrics,
    SolvencyMetrics,
    ValuationMetrics,
    classify_tier,
)


# ---------------------------------------------------------------------------
# Valuation
# ---------------------------------------------------------------------------

def calc_valuation(
    info: dict, statements: list[FinancialStatement], tier: CompanyTier,
) -> ValuationMetrics:
    v = ValuationMetrics()
    v.pe_trailing = info.get("trailingPE")
    v.pe_forward = info.get("forwardPE")
    v.pb_ratio = info.get("priceToBook")
    v.ps_ratio = info.get("priceToSalesTrailing12Months")
    v.peg_ratio = info.get("pegRatio")
    v.ev_ebitda = info.get("enterpriseToEbitda")
    v.ev_revenue = info.get("enterpriseToRevenue")
    v.dividend_yield = info.get("trailingAnnualDividendYield") or info.get("dividendYield")
    v.enterprise_value = info.get("enterpriseValue")
    v.market_cap = info.get("marketCap")

    if v.pe_trailing and v.pe_trailing > 0:
        v.earnings_yield = 1.0 / v.pe_trailing

    price = info.get("currentPrice") or info.get("regularMarketPrice")
    shares = info.get("sharesOutstanding")

    # P/FCF
    if price and shares and statements:
        latest = statements[0]
        if latest.free_cash_flow and latest.free_cash_flow > 0:
            v.p_fcf = (price * shares) / latest.free_cash_flow

    # --- Micro/small-cap specific valuations ---
    if tier in (CompanyTier.MICRO, CompanyTier.NANO, CompanyTier.SMALL) and statements:
        latest = statements[0]
        # Tangible book = equity - intangible assets (approximated)
        if latest.total_equity and latest.total_assets and price and shares:
            # Rough tangible book: use total_equity as proxy
            # (yfinance doesn't always give intangibles separately)
            tbv = latest.total_equity
            if shares > 0:
                tbv_per_share = tbv / shares
                if tbv_per_share > 0:
                    v.price_to_tangible_book = price / tbv_per_share

        # NCAV = Current Assets - Total Liabilities
        if latest.current_assets and latest.total_liabilities and shares and shares > 0:
            ncav = latest.current_assets - latest.total_liabilities
            ncav_ps = ncav / shares
            if ncav_ps > 0 and price:
                v.price_to_ncav = price / ncav_ps

    return v


# ---------------------------------------------------------------------------
# Profitability
# ---------------------------------------------------------------------------

def calc_profitability(
    info: dict, statements: list[FinancialStatement], tier: CompanyTier,
) -> ProfitabilityMetrics:
    p = ProfitabilityMetrics()
    p.roe = info.get("returnOnEquity")
    p.roa = info.get("returnOnAssets")
    p.gross_margin = info.get("grossMargins")
    p.operating_margin = info.get("operatingMargins")
    p.net_margin = info.get("profitMargins")

    if statements:
        s = statements[0]
        # ROIC
        if s.operating_income and s.total_assets and s.total_cash is not None:
            nopat = s.operating_income * 0.75
            invested_capital = s.total_assets - (s.total_cash or 0)
            if invested_capital > 0:
                p.roic = nopat / invested_capital

        if s.free_cash_flow and s.revenue and s.revenue > 0:
            p.fcf_margin = s.free_cash_flow / s.revenue

        if s.ebitda and s.revenue and s.revenue > 0:
            p.ebitda_margin = s.ebitda / s.revenue

    return p


# ---------------------------------------------------------------------------
# Solvency — tier-aware with survival metrics for small/micro
# ---------------------------------------------------------------------------

def calc_solvency(
    info: dict, statements: list[FinancialStatement], tier: CompanyTier,
) -> SolvencyMetrics:
    s = SolvencyMetrics()
    s.debt_to_equity = info.get("debtToEquity")
    if s.debt_to_equity:
        s.debt_to_equity /= 100
    s.current_ratio = info.get("currentRatio")
    s.quick_ratio = info.get("quickRatio")
    s.total_debt = info.get("totalDebt")
    s.total_cash = info.get("totalCash")

    if s.total_debt is not None and s.total_cash is not None:
        s.net_debt = s.total_debt - s.total_cash

    shares = info.get("sharesOutstanding")

    if statements:
        st = statements[0]

        # Debt/EBITDA
        if st.ebitda and st.ebitda > 0 and s.total_debt:
            s.debt_to_ebitda = s.total_debt / st.ebitda

        # Interest coverage
        if st.operating_income and s.total_debt:
            interest_expense = s.total_debt * 0.05
            if interest_expense > 0:
                s.interest_coverage = st.operating_income / interest_expense

        # Altman Z-Score (meaningful mainly for mid+ caps with revenue)
        if st.total_assets and st.total_assets > 0 and st.revenue and st.revenue > 0:
            ta = st.total_assets
            wc = 0
            if s.current_ratio and st.current_liabilities:
                wc = (st.current_assets or 0) - (st.current_liabilities or 0)
            elif s.current_ratio:
                current_liab = ta / s.current_ratio if s.current_ratio > 0 else 0
                wc = (s.current_ratio * current_liab) - current_liab if current_liab else 0

            re = (st.total_equity or 0) * 0.5
            ebit = st.operating_income or 0
            mcap = info.get("marketCap", 0)
            tl = st.total_liabilities or 1
            rev = st.revenue or 0

            z = (1.2 * wc / ta + 1.4 * re / ta + 3.3 * ebit / ta +
                 0.6 * mcap / tl + 1.0 * rev / ta)
            s.altman_z_score = round(z, 2)

        # --- Micro/small-cap survival metrics ---
        # Working capital
        if st.current_assets is not None and st.current_liabilities is not None:
            s.working_capital = st.current_assets - st.current_liabilities
        elif s.current_ratio and st.total_assets:
            # Approximate
            est_cl = st.total_assets / 3  # rough
            s.working_capital = (s.current_ratio * est_cl) - est_cl

        # Cash per share
        if s.total_cash and shares and shares > 0:
            s.cash_per_share = s.total_cash / shares

        # Tangible book value
        if st.total_equity:
            s.tangible_book_value = st.total_equity  # Proxy (no intangibles breakdown)

        # NCAV = Current Assets - Total Liabilities (Ben Graham's net-net)
        if st.current_assets is not None and st.total_liabilities is not None:
            s.ncav = st.current_assets - st.total_liabilities
            if shares and shares > 0:
                s.ncav_per_share = s.ncav / shares

        # Cash burn rate & runway (critical for pre-revenue or loss-making)
        if len(statements) >= 2 and st.operating_cash_flow is not None:
            ocf = st.operating_cash_flow
            if ocf < 0:  # Burning cash
                s.cash_burn_rate = ocf  # Negative number = annual burn
                if s.total_cash and s.total_cash > 0:
                    s.cash_runway_years = s.total_cash / abs(ocf)
            else:
                s.cash_burn_rate = 0  # Not burning

    return s


# ---------------------------------------------------------------------------
# Growth — with dilution tracking
# ---------------------------------------------------------------------------

def calc_growth(
    statements: list[FinancialStatement], tier: CompanyTier,
) -> GrowthMetrics:
    g = GrowthMetrics()
    if len(statements) < 2:
        return g

    stmts = statements

    # YoY growth
    if stmts[0].revenue and stmts[1].revenue and stmts[1].revenue != 0:
        g.revenue_growth_yoy = (stmts[0].revenue - stmts[1].revenue) / abs(stmts[1].revenue)

    if stmts[0].net_income and stmts[1].net_income and stmts[1].net_income != 0:
        g.earnings_growth_yoy = (stmts[0].net_income - stmts[1].net_income) / abs(stmts[1].net_income)

    if stmts[0].free_cash_flow and stmts[1].free_cash_flow and stmts[1].free_cash_flow != 0:
        g.fcf_growth_yoy = (stmts[0].free_cash_flow - stmts[1].free_cash_flow) / abs(stmts[1].free_cash_flow)

    if stmts[0].book_value_per_share and stmts[1].book_value_per_share and stmts[1].book_value_per_share != 0:
        g.book_value_growth_yoy = (
            (stmts[0].book_value_per_share - stmts[1].book_value_per_share)
            / abs(stmts[1].book_value_per_share)
        )

    # Share dilution (critical for micro/small caps)
    if stmts[0].shares_outstanding and stmts[1].shares_outstanding and stmts[1].shares_outstanding > 0:
        g.shares_growth_yoy = (
            (stmts[0].shares_outstanding - stmts[1].shares_outstanding)
            / stmts[1].shares_outstanding
        )

    # 3-year CAGR
    if len(stmts) >= 4:
        g.revenue_cagr_3y = _cagr(stmts[3].revenue, stmts[0].revenue, 3)
        g.earnings_cagr_3y = _cagr(stmts[3].net_income, stmts[0].net_income, 3)

    # 5-year CAGR
    if len(stmts) >= 5:
        g.revenue_cagr_5y = _cagr(stmts[-1].revenue, stmts[0].revenue, len(stmts) - 1)
        g.earnings_cagr_5y = _cagr(stmts[-1].net_income, stmts[0].net_income, len(stmts) - 1)

    return g


# ---------------------------------------------------------------------------
# Efficiency
# ---------------------------------------------------------------------------

def calc_efficiency(
    info: dict, statements: list[FinancialStatement], tier: CompanyTier,
) -> EfficiencyMetrics:
    e = EfficiencyMetrics()
    if not statements:
        return e
    s = statements[0]
    if s.revenue and s.total_assets and s.total_assets > 0:
        e.asset_turnover = s.revenue / s.total_assets
    return e


# ---------------------------------------------------------------------------
# Moat — completely tier-aware scoring
# ---------------------------------------------------------------------------

def calc_moat(
    profitability: ProfitabilityMetrics,
    growth: GrowthMetrics,
    solvency: SolvencyMetrics,
    statements: list[FinancialStatement],
    info: dict,
    tier: CompanyTier,
) -> MoatIndicators:
    """Evaluate economic moat using tier-appropriate criteria.

    Large/mega caps: traditional Morningstar-style moat (ROIC, margins, scale).
    Small caps: balance sheet strength + growth quality + niche position.
    Micro/nano caps: asset backing + cash position + insider alignment signals.
    """
    m = MoatIndicators()

    if tier in (CompanyTier.MEGA, CompanyTier.LARGE, CompanyTier.MID):
        _score_moat_traditional(m, profitability, growth, solvency, statements, info, tier)
    else:
        _score_moat_small_micro(m, profitability, growth, solvency, statements, info, tier)

    return m


def _score_moat_traditional(
    m: MoatIndicators,
    profitability: ProfitabilityMetrics,
    growth: GrowthMetrics,
    solvency: SolvencyMetrics,
    statements: list[FinancialStatement],
    info: dict,
    tier: CompanyTier,
) -> None:
    """Traditional moat scoring for mid+ caps."""
    score = 0.0
    max_score = 0.0

    # --- ROIC Consistency (30 points) ---
    max_score += 30
    roic_values = _calc_roic_history(statements)
    m.roic_history = roic_values

    if roic_values:
        avg_roic = sum(roic_values) / len(roic_values)
        all_above_10 = all(r > 0.10 for r in roic_values)
        if all_above_10 and avg_roic > 0.15:
            m.roic_consistency = "Strong"
            score += 30
        elif avg_roic > 0.10:
            m.roic_consistency = "Moderate"
            score += 18
        elif avg_roic > 0.05:
            m.roic_consistency = "Weak"
            score += 6
        else:
            m.roic_consistency = "None"

    # --- Margin Stability (25 points) ---
    max_score += 25
    margins = _calc_margin_history(statements)
    m.gross_margin_history = margins

    if len(margins) >= 3:
        margin_std = _std(margins)
        avg_margin = sum(margins) / len(margins)
        if margin_std < 0.03 and avg_margin > 0.40:
            m.margin_stability = "Very Stable (High)"
            score += 25
        elif margin_std < 0.05 and avg_margin > 0.30:
            m.margin_stability = "Stable"
            score += 18
        elif margin_std < 0.08:
            m.margin_stability = "Moderate"
            score += 10
        else:
            m.margin_stability = "Volatile"

    # --- Revenue Predictability (20 points) ---
    max_score += 20
    revenues = [s.revenue for s in statements if s.revenue and s.revenue > 0]
    if len(revenues) >= 3:
        growing = all(revenues[i] >= revenues[i + 1] for i in range(len(revenues) - 1))
        if growing:
            m.revenue_predictability = "Consistent Growth"
            score += 20
        elif all(r > 0 for r in revenues):
            m.revenue_predictability = "Positive but Variable"
            score += 10
        else:
            m.revenue_predictability = "Unpredictable"

    # --- Financial Strength (15 points) ---
    max_score += 15
    if solvency.debt_to_equity is not None:
        if solvency.debt_to_equity < 0.5:
            score += 10
        elif solvency.debt_to_equity < 1.0:
            score += 5
    if solvency.current_ratio and solvency.current_ratio > 1.5:
        score += 5

    # --- Growth Quality (10 points) ---
    max_score += 10
    if growth.revenue_cagr_3y and growth.revenue_cagr_3y > 0.10:
        score += 5
    elif growth.revenue_cagr_3y and growth.revenue_cagr_3y > 0.05:
        score += 2
    if growth.earnings_cagr_3y and growth.earnings_cagr_3y > 0.10:
        score += 5
    elif growth.earnings_cagr_3y and growth.earnings_cagr_3y > 0.05:
        score += 2

    # Qualitative moat source hints
    gm = profitability.gross_margin
    if gm and gm > 0.60:
        m.intangible_assets = "Likely — high gross margins suggest brand/IP pricing power"
    if gm and gm > 0.70:
        m.switching_costs = "Possible — very high margins may indicate customer lock-in"
    if profitability.net_margin and profitability.net_margin > 0.20:
        m.cost_advantages = "Possible — high net margins suggest cost efficiency or pricing power"

    # Scale assessment (not scored — just informational)
    mcap = info.get("marketCap", 0)
    if mcap > 200_000_000_000:
        m.efficient_scale = "Mega Cap — dominant market position"
    elif mcap > 10_000_000_000:
        m.efficient_scale = "Large Cap — established market presence"
    else:
        m.efficient_scale = "Mid Cap — growing market position"

    # Composite
    m.moat_score = round((score / max_score) * 100, 1) if max_score > 0 else 0
    if m.moat_score >= 75:
        m.competitive_position = "Wide Moat"
    elif m.moat_score >= 50:
        m.competitive_position = "Narrow Moat"
    elif m.moat_score >= 25:
        m.competitive_position = "Weak Moat"
    else:
        m.competitive_position = "No Moat Detected"


def _score_moat_small_micro(
    m: MoatIndicators,
    profitability: ProfitabilityMetrics,
    growth: GrowthMetrics,
    solvency: SolvencyMetrics,
    statements: list[FinancialStatement],
    info: dict,
    tier: CompanyTier,
) -> None:
    """Moat scoring adapted for small/micro/nano caps.

    Traditional moat analysis doesn't work well for early-stage or small
    companies. Instead, focus on:
      - Asset backing (net-net, tangible book)
      - Cash position and burn rate
      - Revenue existence and trajectory
      - Niche market signals (high gross margins in a small company)
      - Insider alignment (no dilution)
    """
    score = 0.0
    max_score = 0.0

    is_micro = tier in (CompanyTier.MICRO, CompanyTier.NANO)

    # --- Asset Backing (25 points) ---
    max_score += 25
    if solvency.ncav and solvency.ncav > 0:
        price = info.get("currentPrice") or info.get("regularMarketPrice", 0)
        shares = info.get("sharesOutstanding", 0)
        if price and shares and shares > 0:
            ncav_ps = solvency.ncav / shares
            if price < ncav_ps:
                m.asset_backing = "Net-net: trading below NCAV (strong Graham signal)"
                score += 25
            elif price < ncav_ps * 1.5:
                m.asset_backing = "Near net-net territory"
                score += 15
            else:
                m.asset_backing = "Above NCAV but asset-backed"
                score += 5
    elif solvency.tangible_book_value and solvency.tangible_book_value > 0:
        shares = info.get("sharesOutstanding", 0)
        price = info.get("currentPrice") or info.get("regularMarketPrice", 0)
        if price and shares and shares > 0:
            tbv_ps = solvency.tangible_book_value / shares
            if price < tbv_ps:
                m.asset_backing = "Below tangible book value"
                score += 15
            elif price < tbv_ps * 1.5:
                m.asset_backing = "Near tangible book value"
                score += 8
            else:
                m.asset_backing = "Above tangible book"
                score += 2
    else:
        m.asset_backing = "Insufficient asset data"

    # --- Cash Position & Survival (25 points) ---
    max_score += 25
    if solvency.cash_runway_years is not None:
        if solvency.cash_runway_years > 5:
            score += 25
        elif solvency.cash_runway_years > 3:
            score += 18
        elif solvency.cash_runway_years > 1.5:
            score += 10
        elif solvency.cash_runway_years > 0.5:
            score += 3
        # else 0 — critical risk
    elif solvency.cash_burn_rate is not None and solvency.cash_burn_rate >= 0:
        # Not burning cash — either profitable or break-even
        score += 25

    if solvency.current_ratio and solvency.current_ratio > 2.0:
        score += 0  # Already captured in cash position
    if solvency.working_capital and solvency.working_capital > 0:
        pass  # Positive signal, but not scored separately

    # --- Revenue & Business Viability (20 points) ---
    max_score += 20
    revenues = [s.revenue for s in statements if s.revenue and s.revenue > 0]
    if revenues:
        has_revenue = True
        if len(revenues) >= 2:
            growing = revenues[0] > revenues[1]
            if growing and growth.revenue_growth_yoy and growth.revenue_growth_yoy > 0.15:
                m.revenue_predictability = "Strong revenue growth"
                score += 20
            elif growing:
                m.revenue_predictability = "Revenue growing"
                score += 12
            else:
                m.revenue_predictability = "Revenue declining"
                score += 4
        else:
            m.revenue_predictability = "Limited revenue history"
            score += 6
    else:
        m.revenue_predictability = "Pre-revenue (exploration/development stage)"
        score += 0

    # --- Niche Position (15 points) ---
    max_score += 15
    gm = profitability.gross_margin
    if gm and gm > 0.50:
        m.niche_position = "High gross margins — possible niche/IP advantage"
        score += 15
    elif gm and gm > 0.30:
        m.niche_position = "Moderate margins — some competitive advantage"
        score += 8
    elif revenues:
        m.niche_position = "Low margins — commodity-like positioning"
        score += 2
    else:
        m.niche_position = "Cannot assess — no revenue"

    # --- Dilution Risk / Insider Alignment (15 points) ---
    max_score += 15
    if growth.shares_growth_yoy is not None:
        if growth.shares_growth_yoy < 0.01:
            m.insider_alignment = "Minimal dilution — management aligned"
            score += 15
        elif growth.shares_growth_yoy < 0.05:
            m.insider_alignment = "Modest dilution (<5%/yr)"
            score += 10
        elif growth.shares_growth_yoy < 0.10:
            m.insider_alignment = "Moderate dilution (5-10%/yr) — caution"
            score += 4
        else:
            m.insider_alignment = "Heavy dilution (>10%/yr) — warning"
            score += 0
    else:
        m.insider_alignment = "Dilution data unavailable"
        score += 5  # Neutral

    # Populate ROIC/margin history for display
    m.roic_history = _calc_roic_history(statements)
    m.gross_margin_history = _calc_margin_history(statements)

    # Traditional fields that aren't meaningful for this tier
    m.switching_costs = "N/A for this company size"
    m.network_effects = "N/A for this company size"
    m.efficient_scale = tier.value

    if is_micro:
        m.intangible_assets = "Assess manually: patents, licenses, mineral rights"
        m.cost_advantages = "Assess manually: proprietary technology, location"

    # Composite
    m.moat_score = round((score / max_score) * 100, 1) if max_score > 0 else 0
    if m.moat_score >= 70:
        m.competitive_position = "Strong Position" if is_micro else "Narrow Moat"
    elif m.moat_score >= 45:
        m.competitive_position = "Viable Position" if is_micro else "Weak Moat"
    elif m.moat_score >= 20:
        m.competitive_position = "Speculative" if is_micro else "No Moat"
    else:
        m.competitive_position = "High Risk — survival uncertain"


# ---------------------------------------------------------------------------
# Intrinsic Value — tier-appropriate methods
# ---------------------------------------------------------------------------

def calc_intrinsic_value(
    info: dict,
    statements: list[FinancialStatement],
    growth: GrowthMetrics,
    solvency: SolvencyMetrics,
    tier: CompanyTier,
    discount_rate: float = 0.10,
    terminal_growth: float = 0.03,
) -> IntrinsicValue:
    iv = IntrinsicValue()
    iv.current_price = info.get("currentPrice") or info.get("regularMarketPrice")
    shares = info.get("sharesOutstanding")

    if not statements:
        return iv

    latest = statements[0]

    # --- Select primary/secondary methods based on tier ---
    if tier in (CompanyTier.MEGA, CompanyTier.LARGE):
        iv.primary_method = "DCF"
        iv.secondary_method = "Graham Number"
    elif tier == CompanyTier.MID:
        iv.primary_method = "DCF"
        iv.secondary_method = "Graham Number"
    elif tier == CompanyTier.SMALL:
        iv.primary_method = "Graham Number"
        iv.secondary_method = "Asset-Based (Tangible Book)"
    elif tier == CompanyTier.MICRO:
        iv.primary_method = "NCAV (Net-Net)"
        iv.secondary_method = "Asset-Based (Tangible Book)"
    else:  # NANO
        iv.primary_method = "NCAV (Net-Net)"
        iv.secondary_method = "Asset-Based (Tangible Book)"

    # --- DCF (reliable for mid+ caps with positive FCF) ---
    if tier in (CompanyTier.MEGA, CompanyTier.LARGE, CompanyTier.MID):
        if latest.free_cash_flow and latest.free_cash_flow > 0 and shares:
            fcf = latest.free_cash_flow
            growth_rate = min(growth.revenue_cagr_3y or 0.05, 0.20)

            # Higher discount for smaller companies
            dr = discount_rate
            if tier == CompanyTier.MID:
                dr = 0.12

            total_pv = 0.0
            projected_fcf = fcf
            for year in range(1, 11):
                yr_growth = growth_rate - (growth_rate - terminal_growth) * (year / 10)
                projected_fcf *= (1 + yr_growth)
                total_pv += projected_fcf / ((1 + dr) ** year)

            terminal_fcf = projected_fcf * (1 + terminal_growth)
            terminal_value = terminal_fcf / (dr - terminal_growth)
            pv_terminal = terminal_value / ((1 + dr) ** 10)

            total_equity_value = total_pv + pv_terminal
            iv.dcf_value = round(total_equity_value / shares, 2)

    # --- Graham Number (reliable for small+ caps with positive earnings) ---
    eps = latest.eps or (latest.net_income / shares if latest.net_income and shares else None)
    bvps = latest.book_value_per_share or info.get("bookValue")
    if eps and eps > 0 and bvps and bvps > 0:
        iv.graham_number = round(math.sqrt(22.5 * eps * bvps), 2)

    # --- Peter Lynch Fair Value (for companies with positive earnings growth) ---
    if eps and eps > 0 and growth.earnings_cagr_3y and growth.earnings_cagr_3y > 0:
        eg = growth.earnings_cagr_3y * 100
        if eg > 0:
            iv.lynch_fair_value = round(eps * eg, 2)

    # --- NCAV / Net-Net value (critical for micro/nano) ---
    if solvency.ncav_per_share is not None:
        iv.ncav_value = round(solvency.ncav_per_share, 4)

    # --- Asset-Based value (tangible book per share) ---
    if latest.total_equity and shares and shares > 0:
        iv.asset_based_value = round(latest.total_equity / shares, 4)

    # --- Margins of Safety ---
    if iv.current_price and iv.current_price > 0:
        if iv.dcf_value:
            iv.margin_of_safety_dcf = round(
                (iv.dcf_value - iv.current_price) / iv.dcf_value, 4
            )
        if iv.graham_number:
            iv.margin_of_safety_graham = round(
                (iv.graham_number - iv.current_price) / iv.graham_number, 4
            )
        if iv.ncav_value and iv.ncav_value > 0:
            iv.margin_of_safety_ncav = round(
                (iv.ncav_value - iv.current_price) / iv.ncav_value, 4
            )
        if iv.asset_based_value and iv.asset_based_value > 0:
            iv.margin_of_safety_asset = round(
                (iv.asset_based_value - iv.current_price) / iv.asset_based_value, 4
            )

    return iv


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _calc_roic_history(statements: list[FinancialStatement]) -> list[Optional[float]]:
    roic_values = []
    for s in statements:
        if s.operating_income and s.total_assets and s.total_cash is not None:
            nopat = s.operating_income * 0.75
            ic = s.total_assets - (s.total_cash or 0)
            if ic > 0:
                roic_values.append(nopat / ic)
    return roic_values


def _calc_margin_history(statements: list[FinancialStatement]) -> list[Optional[float]]:
    margins = []
    for s in statements:
        if s.gross_profit and s.revenue and s.revenue > 0:
            margins.append(s.gross_profit / s.revenue)
    return margins


def _cagr(start: Optional[float], end: Optional[float], years: int) -> Optional[float]:
    if not start or not end or start <= 0 or end <= 0 or years <= 0:
        return None
    return (end / start) ** (1 / years) - 1


def _std(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    mean = sum(values) / len(values)
    variance = sum((x - mean) ** 2 for x in values) / (len(values) - 1)
    return math.sqrt(variance)
