"""Metric relevance by company tier.

Defines which metrics are critical, relevant, contextual, or irrelevant
for each company size tier. This drives both display highlighting and
assessment threshold selection.
"""

from __future__ import annotations

from lynx.models import CompanyTier, Relevance

# Shorthand
C = Relevance.CRITICAL
R = Relevance.RELEVANT
X = Relevance.CONTEXTUAL
I = Relevance.IRRELEVANT

# fmt: off
# Each entry: metric_key -> {tier: relevance}
# Tiers: MEGA, LARGE, MID, SMALL, MICRO, NANO

VALUATION_RELEVANCE: dict[str, dict[CompanyTier, Relevance]] = {
    #                          MEGA  LARGE  MID    SMALL  MICRO  NANO
    "pe_trailing":           {CompanyTier.MEGA: C, CompanyTier.LARGE: C, CompanyTier.MID: C, CompanyTier.SMALL: R, CompanyTier.MICRO: X, CompanyTier.NANO: I},
    "pe_forward":            {CompanyTier.MEGA: R, CompanyTier.LARGE: R, CompanyTier.MID: R, CompanyTier.SMALL: X, CompanyTier.MICRO: I, CompanyTier.NANO: I},
    "pb_ratio":              {CompanyTier.MEGA: R, CompanyTier.LARGE: R, CompanyTier.MID: C, CompanyTier.SMALL: C, CompanyTier.MICRO: C, CompanyTier.NANO: C},
    "ps_ratio":              {CompanyTier.MEGA: R, CompanyTier.LARGE: R, CompanyTier.MID: R, CompanyTier.SMALL: R, CompanyTier.MICRO: X, CompanyTier.NANO: I},
    "p_fcf":                 {CompanyTier.MEGA: C, CompanyTier.LARGE: C, CompanyTier.MID: C, CompanyTier.SMALL: R, CompanyTier.MICRO: X, CompanyTier.NANO: I},
    "ev_ebitda":             {CompanyTier.MEGA: C, CompanyTier.LARGE: C, CompanyTier.MID: C, CompanyTier.SMALL: R, CompanyTier.MICRO: X, CompanyTier.NANO: I},
    "ev_revenue":            {CompanyTier.MEGA: R, CompanyTier.LARGE: R, CompanyTier.MID: R, CompanyTier.SMALL: X, CompanyTier.MICRO: I, CompanyTier.NANO: I},
    "peg_ratio":             {CompanyTier.MEGA: R, CompanyTier.LARGE: R, CompanyTier.MID: R, CompanyTier.SMALL: X, CompanyTier.MICRO: I, CompanyTier.NANO: I},
    "dividend_yield":        {CompanyTier.MEGA: R, CompanyTier.LARGE: R, CompanyTier.MID: R, CompanyTier.SMALL: X, CompanyTier.MICRO: I, CompanyTier.NANO: I},
    "earnings_yield":        {CompanyTier.MEGA: C, CompanyTier.LARGE: C, CompanyTier.MID: R, CompanyTier.SMALL: R, CompanyTier.MICRO: X, CompanyTier.NANO: I},
    "price_to_tangible_book":{CompanyTier.MEGA: X, CompanyTier.LARGE: X, CompanyTier.MID: R, CompanyTier.SMALL: C, CompanyTier.MICRO: C, CompanyTier.NANO: C},
    "price_to_ncav":         {CompanyTier.MEGA: I, CompanyTier.LARGE: I, CompanyTier.MID: X, CompanyTier.SMALL: R, CompanyTier.MICRO: C, CompanyTier.NANO: C},
}

PROFITABILITY_RELEVANCE: dict[str, dict[CompanyTier, Relevance]] = {
    "roe":              {CompanyTier.MEGA: C, CompanyTier.LARGE: C, CompanyTier.MID: C, CompanyTier.SMALL: R, CompanyTier.MICRO: X, CompanyTier.NANO: I},
    "roa":              {CompanyTier.MEGA: R, CompanyTier.LARGE: R, CompanyTier.MID: R, CompanyTier.SMALL: R, CompanyTier.MICRO: R, CompanyTier.NANO: X},
    "roic":             {CompanyTier.MEGA: C, CompanyTier.LARGE: C, CompanyTier.MID: C, CompanyTier.SMALL: R, CompanyTier.MICRO: X, CompanyTier.NANO: I},
    "gross_margin":     {CompanyTier.MEGA: C, CompanyTier.LARGE: C, CompanyTier.MID: C, CompanyTier.SMALL: C, CompanyTier.MICRO: R, CompanyTier.NANO: X},
    "operating_margin": {CompanyTier.MEGA: C, CompanyTier.LARGE: C, CompanyTier.MID: R, CompanyTier.SMALL: R, CompanyTier.MICRO: X, CompanyTier.NANO: I},
    "net_margin":       {CompanyTier.MEGA: R, CompanyTier.LARGE: R, CompanyTier.MID: R, CompanyTier.SMALL: R, CompanyTier.MICRO: X, CompanyTier.NANO: I},
    "fcf_margin":       {CompanyTier.MEGA: C, CompanyTier.LARGE: C, CompanyTier.MID: R, CompanyTier.SMALL: R, CompanyTier.MICRO: X, CompanyTier.NANO: I},
    "ebitda_margin":    {CompanyTier.MEGA: R, CompanyTier.LARGE: R, CompanyTier.MID: R, CompanyTier.SMALL: X, CompanyTier.MICRO: I, CompanyTier.NANO: I},
}

SOLVENCY_RELEVANCE: dict[str, dict[CompanyTier, Relevance]] = {
    "debt_to_equity":    {CompanyTier.MEGA: C, CompanyTier.LARGE: C, CompanyTier.MID: C, CompanyTier.SMALL: C, CompanyTier.MICRO: C, CompanyTier.NANO: C},
    "debt_to_ebitda":    {CompanyTier.MEGA: C, CompanyTier.LARGE: C, CompanyTier.MID: R, CompanyTier.SMALL: R, CompanyTier.MICRO: X, CompanyTier.NANO: I},
    "current_ratio":     {CompanyTier.MEGA: R, CompanyTier.LARGE: R, CompanyTier.MID: R, CompanyTier.SMALL: C, CompanyTier.MICRO: C, CompanyTier.NANO: C},
    "quick_ratio":       {CompanyTier.MEGA: X, CompanyTier.LARGE: X, CompanyTier.MID: R, CompanyTier.SMALL: C, CompanyTier.MICRO: C, CompanyTier.NANO: C},
    "interest_coverage":  {CompanyTier.MEGA: R, CompanyTier.LARGE: R, CompanyTier.MID: R, CompanyTier.SMALL: R, CompanyTier.MICRO: X, CompanyTier.NANO: I},
    "altman_z_score":    {CompanyTier.MEGA: R, CompanyTier.LARGE: R, CompanyTier.MID: R, CompanyTier.SMALL: R, CompanyTier.MICRO: X, CompanyTier.NANO: I},
    "cash_burn_rate":    {CompanyTier.MEGA: I, CompanyTier.LARGE: I, CompanyTier.MID: X, CompanyTier.SMALL: R, CompanyTier.MICRO: C, CompanyTier.NANO: C},
    "cash_runway_years": {CompanyTier.MEGA: I, CompanyTier.LARGE: I, CompanyTier.MID: X, CompanyTier.SMALL: R, CompanyTier.MICRO: C, CompanyTier.NANO: C},
    "working_capital":   {CompanyTier.MEGA: X, CompanyTier.LARGE: X, CompanyTier.MID: R, CompanyTier.SMALL: C, CompanyTier.MICRO: C, CompanyTier.NANO: C},
    "cash_per_share":    {CompanyTier.MEGA: X, CompanyTier.LARGE: X, CompanyTier.MID: R, CompanyTier.SMALL: C, CompanyTier.MICRO: C, CompanyTier.NANO: C},
    "ncav_per_share":    {CompanyTier.MEGA: I, CompanyTier.LARGE: I, CompanyTier.MID: X, CompanyTier.SMALL: R, CompanyTier.MICRO: C, CompanyTier.NANO: C},
}

GROWTH_RELEVANCE: dict[str, dict[CompanyTier, Relevance]] = {
    "revenue_growth_yoy":     {CompanyTier.MEGA: R, CompanyTier.LARGE: R, CompanyTier.MID: C, CompanyTier.SMALL: C, CompanyTier.MICRO: C, CompanyTier.NANO: C},
    "revenue_cagr_3y":        {CompanyTier.MEGA: C, CompanyTier.LARGE: C, CompanyTier.MID: C, CompanyTier.SMALL: R, CompanyTier.MICRO: X, CompanyTier.NANO: I},
    "revenue_cagr_5y":        {CompanyTier.MEGA: C, CompanyTier.LARGE: C, CompanyTier.MID: R, CompanyTier.SMALL: X, CompanyTier.MICRO: I, CompanyTier.NANO: I},
    "earnings_growth_yoy":    {CompanyTier.MEGA: R, CompanyTier.LARGE: R, CompanyTier.MID: R, CompanyTier.SMALL: R, CompanyTier.MICRO: X, CompanyTier.NANO: I},
    "earnings_cagr_3y":       {CompanyTier.MEGA: C, CompanyTier.LARGE: C, CompanyTier.MID: R, CompanyTier.SMALL: X, CompanyTier.MICRO: I, CompanyTier.NANO: I},
    "earnings_cagr_5y":       {CompanyTier.MEGA: C, CompanyTier.LARGE: C, CompanyTier.MID: R, CompanyTier.SMALL: X, CompanyTier.MICRO: I, CompanyTier.NANO: I},
    "shares_growth_yoy":      {CompanyTier.MEGA: X, CompanyTier.LARGE: X, CompanyTier.MID: R, CompanyTier.SMALL: C, CompanyTier.MICRO: C, CompanyTier.NANO: C},
}

# fmt: on


def get_relevance(
    metric_key: str,
    tier: CompanyTier,
    category: str = "valuation",
) -> Relevance:
    """Look up relevance for a metric/tier. Falls back to RELEVANT."""
    table = {
        "valuation": VALUATION_RELEVANCE,
        "profitability": PROFITABILITY_RELEVANCE,
        "solvency": SOLVENCY_RELEVANCE,
        "growth": GROWTH_RELEVANCE,
    }.get(category, {})
    entry = table.get(metric_key, {})
    return entry.get(tier, Relevance.RELEVANT)
