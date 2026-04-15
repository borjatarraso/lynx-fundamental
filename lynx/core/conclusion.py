"""Report synthesis engine — generates narrative conclusions from analysis data.

Produces a tier-aware assessment with weighted scoring across categories,
key strengths/risks identification, and an investment verdict.
"""

from __future__ import annotations

from lynx.models import AnalysisConclusion, AnalysisReport, CompanyTier


# Category weights by tier (valuation, profitability, solvency, growth, moat)
_WEIGHTS = {
    CompanyTier.MEGA:  (0.25, 0.25, 0.15, 0.15, 0.20),
    CompanyTier.LARGE: (0.25, 0.25, 0.15, 0.15, 0.20),
    CompanyTier.MID:   (0.25, 0.20, 0.20, 0.20, 0.15),
    CompanyTier.SMALL: (0.20, 0.20, 0.25, 0.20, 0.15),
    CompanyTier.MICRO: (0.15, 0.15, 0.35, 0.20, 0.15),
    CompanyTier.NANO:  (0.10, 0.10, 0.40, 0.20, 0.20),
}


def generate_conclusion(report: AnalysisReport) -> AnalysisConclusion:
    """Generate a synthesis conclusion from the full analysis report."""
    c = AnalysisConclusion()
    tier = report.profile.tier

    val_score = _score_valuation(report)
    prof_score = _score_profitability(report)
    solv_score = _score_solvency(report)
    grow_score = _score_growth(report)
    moat_score = report.moat.moat_score or 0

    c.category_scores = {
        "valuation": round(val_score, 1),
        "profitability": round(prof_score, 1),
        "solvency": round(solv_score, 1),
        "growth": round(grow_score, 1),
        "moat": round(moat_score, 1),
    }

    w = _WEIGHTS.get(tier, _WEIGHTS[CompanyTier.MID])
    c.overall_score = round(
        val_score * w[0] + prof_score * w[1] + solv_score * w[2] +
        grow_score * w[3] + moat_score * w[4], 1
    )

    c.verdict = _verdict(c.overall_score)
    c.category_summaries = _build_summaries(report)
    c.strengths = _find_strengths(report)
    c.risks = _find_risks(report)
    c.summary = _build_narrative(report, c)
    c.tier_note = _tier_note(tier)

    return c


def _verdict(score: float) -> str:
    if score >= 75: return "Strong Buy"
    if score >= 60: return "Buy"
    if score >= 45: return "Hold"
    if score >= 30: return "Caution"
    return "Avoid"


def _score_valuation(r: AnalysisReport) -> float:
    v = r.valuation
    score = 50.0  # neutral baseline
    signals = 0

    if v.pe_trailing is not None:
        signals += 1
        if v.pe_trailing < 0: score += 0
        elif v.pe_trailing < 10: score += 25
        elif v.pe_trailing < 15: score += 15
        elif v.pe_trailing < 20: score += 5
        elif v.pe_trailing < 30: score -= 5
        else: score -= 15

    if v.pb_ratio is not None:
        signals += 1
        if v.pb_ratio < 1: score += 20
        elif v.pb_ratio < 1.5: score += 10
        elif v.pb_ratio < 3: score += 0
        else: score -= 10

    if v.p_fcf is not None:
        signals += 1
        if v.p_fcf < 10: score += 15
        elif v.p_fcf < 20: score += 5
        else: score -= 10

    if v.ev_ebitda is not None:
        signals += 1
        if v.ev_ebitda < 8: score += 15
        elif v.ev_ebitda < 12: score += 5
        else: score -= 10

    return max(0, min(100, score))


def _score_profitability(r: AnalysisReport) -> float:
    p = r.profitability
    score = 50.0
    if p.roe is not None:
        if p.roe > 0.20: score += 15
        elif p.roe > 0.10: score += 5
        elif p.roe < 0: score -= 15
    if p.roic is not None:
        if p.roic > 0.15: score += 15
        elif p.roic > 0.10: score += 5
        elif p.roic < 0: score -= 15
    if p.gross_margin is not None:
        if p.gross_margin > 0.50: score += 10
        elif p.gross_margin > 0.30: score += 5
        elif p.gross_margin < 0.10: score -= 10
    if p.net_margin is not None:
        if p.net_margin > 0.15: score += 10
        elif p.net_margin > 0.05: score += 5
        elif p.net_margin < 0: score -= 15
    return max(0, min(100, score))


def _score_solvency(r: AnalysisReport) -> float:
    s = r.solvency
    score = 50.0
    if s.debt_to_equity is not None:
        if s.debt_to_equity < 0: score += 15  # net cash
        elif s.debt_to_equity < 0.5: score += 10
        elif s.debt_to_equity > 2: score -= 15
    if s.current_ratio is not None:
        if s.current_ratio > 2: score += 10
        elif s.current_ratio > 1.5: score += 5
        elif s.current_ratio < 1: score -= 15
    if s.altman_z_score is not None:
        if s.altman_z_score > 3: score += 10
        elif s.altman_z_score < 1.8: score -= 20
    if s.cash_burn_rate is not None and s.cash_burn_rate < 0:
        if s.cash_runway_years is not None:
            if s.cash_runway_years < 1: score -= 25
            elif s.cash_runway_years < 2: score -= 10
    return max(0, min(100, score))


def _score_growth(r: AnalysisReport) -> float:
    g = r.growth
    score = 50.0
    if g.revenue_growth_yoy is not None:
        if g.revenue_growth_yoy > 0.20: score += 15
        elif g.revenue_growth_yoy > 0.05: score += 5
        elif g.revenue_growth_yoy < -0.10: score -= 15
    if g.earnings_growth_yoy is not None:
        if g.earnings_growth_yoy > 0.20: score += 10
        elif g.earnings_growth_yoy > 0: score += 5
        elif g.earnings_growth_yoy < -0.20: score -= 10
    if g.revenue_cagr_3y is not None:
        if g.revenue_cagr_3y > 0.10: score += 10
        elif g.revenue_cagr_3y > 0: score += 5
        elif g.revenue_cagr_3y < 0: score -= 10
    if g.shares_growth_yoy is not None:
        if g.shares_growth_yoy < -0.02: score += 5  # buybacks
        elif g.shares_growth_yoy > 0.10: score -= 10  # heavy dilution
    return max(0, min(100, score))


def _build_summaries(r: AnalysisReport) -> dict[str, str]:
    summaries = {}
    v = r.valuation
    if v.pe_trailing is not None:
        pe_word = "cheap" if v.pe_trailing < 15 else "fair" if v.pe_trailing < 25 else "expensive"
        summaries["valuation"] = f"Valuation appears {pe_word} with P/E of {v.pe_trailing:.1f}"
        if v.pb_ratio is not None:
            summaries["valuation"] += f" and P/B of {v.pb_ratio:.1f}"
    else:
        summaries["valuation"] = "Limited valuation data available"

    p = r.profitability
    if p.net_margin is not None:
        if p.net_margin > 0:
            summaries["profitability"] = f"Profitable with {p.net_margin*100:.1f}% net margin"
        else:
            summaries["profitability"] = f"Currently unprofitable ({p.net_margin*100:.1f}% net margin)"
    else:
        summaries["profitability"] = "Limited profitability data available"

    s = r.solvency
    if s.debt_to_equity is not None:
        if s.debt_to_equity < 0.5:
            summaries["solvency"] = "Conservative balance sheet with low leverage"
        elif s.debt_to_equity < 1.5:
            summaries["solvency"] = "Moderate leverage, appears manageable"
        else:
            summaries["solvency"] = "Highly leveraged — elevated financial risk"
    else:
        summaries["solvency"] = "Limited solvency data available"

    g = r.growth
    if g.revenue_growth_yoy is not None:
        if g.revenue_growth_yoy > 0.10:
            summaries["growth"] = f"Strong revenue growth at {g.revenue_growth_yoy*100:.1f}% YoY"
        elif g.revenue_growth_yoy > 0:
            summaries["growth"] = f"Modest revenue growth at {g.revenue_growth_yoy*100:.1f}% YoY"
        else:
            summaries["growth"] = f"Revenue declining at {g.revenue_growth_yoy*100:.1f}% YoY"
    else:
        summaries["growth"] = "Limited growth data available"

    m = r.moat
    summaries["moat"] = m.competitive_position or "Moat assessment unavailable"

    return summaries


def _find_strengths(r: AnalysisReport) -> list[str]:
    strengths = []
    v = r.valuation
    if v.pe_trailing and 0 < v.pe_trailing < 15:
        strengths.append(f"Attractive P/E of {v.pe_trailing:.1f}")
    if v.pb_ratio and v.pb_ratio < 1:
        strengths.append(f"Trading below book value (P/B {v.pb_ratio:.2f})")

    p = r.profitability
    if p.roic and p.roic > 0.15:
        strengths.append(f"Excellent ROIC of {p.roic*100:.1f}% — wide moat signal")
    if p.gross_margin and p.gross_margin > 0.50:
        strengths.append(f"High gross margins ({p.gross_margin*100:.1f}%) indicate pricing power")
    if p.fcf_margin and p.fcf_margin > 0.15:
        strengths.append(f"Strong cash generation ({p.fcf_margin*100:.1f}% FCF margin)")

    s = r.solvency
    if s.debt_to_equity is not None and s.debt_to_equity < 0.3:
        strengths.append("Very conservative balance sheet")
    if s.current_ratio and s.current_ratio > 2:
        strengths.append("Strong liquidity position")

    g = r.growth
    if g.revenue_cagr_3y and g.revenue_cagr_3y > 0.10:
        strengths.append(f"Consistent revenue growth ({g.revenue_cagr_3y*100:.1f}% 3Y CAGR)")
    if g.shares_growth_yoy is not None and g.shares_growth_yoy < -0.02:
        strengths.append("Share buybacks — returning capital to shareholders")

    m = r.moat
    if m.moat_score and m.moat_score > 60:
        strengths.append(f"Strong competitive position (moat score: {m.moat_score:.0f}/100)")

    return strengths[:5]


def _find_risks(r: AnalysisReport) -> list[str]:
    risks = []
    v = r.valuation
    if v.pe_trailing and v.pe_trailing > 30:
        risks.append(f"Expensive valuation (P/E {v.pe_trailing:.1f})")
    if v.pe_trailing and v.pe_trailing < 0:
        risks.append("Negative earnings")

    p = r.profitability
    if p.net_margin is not None and p.net_margin < 0:
        risks.append(f"Currently unprofitable ({p.net_margin*100:.1f}% net margin)")
    if p.roic is not None and 0 < p.roic < 0.07:
        risks.append(f"Low returns on capital (ROIC {p.roic*100:.1f}%)")

    s = r.solvency
    if s.debt_to_equity is not None and s.debt_to_equity > 2:
        risks.append(f"High leverage (D/E {s.debt_to_equity:.1f})")
    if s.altman_z_score is not None and s.altman_z_score < 1.81:
        risks.append(f"Bankruptcy risk (Z-Score {s.altman_z_score:.2f})")
    if s.cash_runway_years is not None and s.cash_runway_years < 2:
        risks.append(f"Limited cash runway ({s.cash_runway_years:.1f} years)")

    g = r.growth
    if g.revenue_growth_yoy is not None and g.revenue_growth_yoy < -0.10:
        risks.append(f"Revenue declining ({g.revenue_growth_yoy*100:.1f}% YoY)")
    if g.shares_growth_yoy is not None and g.shares_growth_yoy > 0.10:
        risks.append(f"Heavy share dilution ({g.shares_growth_yoy*100:.1f}%/yr)")

    m = r.moat
    if m.moat_score is not None and m.moat_score < 25:
        risks.append("No economic moat detected")

    return risks[:5]


def _build_narrative(r: AnalysisReport, c: AnalysisConclusion) -> str:
    name = r.profile.name
    tier = r.profile.tier.value

    parts = [f"{name} ({tier}) receives an overall score of {c.overall_score:.0f}/100, resulting in a '{c.verdict}' assessment."]

    if c.strengths:
        parts.append(f"Key strengths include: {c.strengths[0].lower()}")
        if len(c.strengths) > 1:
            parts[-1] += f" and {c.strengths[1].lower()}"
        parts[-1] += "."

    if c.risks:
        parts.append(f"Primary risks: {c.risks[0].lower()}")
        if len(c.risks) > 1:
            parts[-1] += f" and {c.risks[1].lower()}"
        parts[-1] += "."

    return " ".join(parts)


def _tier_note(tier: CompanyTier) -> str:
    notes = {
        CompanyTier.MEGA: "Full traditional value investing analysis applies. DCF and ROIC are the primary valuation and quality metrics.",
        CompanyTier.LARGE: "Full traditional analysis applies. All metrics are reliable with sufficient data.",
        CompanyTier.MID: "Blended analysis: traditional metrics are reliable but growth trajectory is weighted more heavily.",
        CompanyTier.SMALL: "Balance sheet strength is critical. Graham Number is preferred over DCF for valuation.",
        CompanyTier.MICRO: "Survival metrics dominate. NCAV/net-net and cash runway are more reliable than DCF. High uncertainty.",
        CompanyTier.NANO: "Speculative territory. Asset-based valuation only. High risk of capital loss. Limited data availability.",
    }
    return notes.get(tier, "")
