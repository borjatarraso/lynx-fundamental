"""Data models for Lynx Fundamental Analysis."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


# ---------------------------------------------------------------------------
# Company tier classification
# ---------------------------------------------------------------------------

class CompanyTier(str, Enum):
    """Market-cap based company classification.

    Each tier has distinct analytical requirements:
      MEGA/LARGE  — full traditional value investing, DCF meaningful
      MID         — transitional; most metrics apply, growth matters more
      SMALL       — balance sheet focus, management/insider signals, Graham
      MICRO       — survival metrics dominate; NCAV/net-net, cash runway
      NANO        — speculative; asset-based valuation only
    """
    MEGA = "Mega Cap"     # >$200B
    LARGE = "Large Cap"   # $10B–$200B
    MID = "Mid Cap"       # $2B–$10B
    SMALL = "Small Cap"   # $300M–$2B
    MICRO = "Micro Cap"   # $50M–$300M
    NANO = "Nano Cap"     # <$50M


def classify_tier(market_cap: Optional[float]) -> CompanyTier:
    """Classify company by market cap."""
    if market_cap is None or market_cap <= 0:
        return CompanyTier.NANO
    if market_cap >= 200_000_000_000:
        return CompanyTier.MEGA
    if market_cap >= 10_000_000_000:
        return CompanyTier.LARGE
    if market_cap >= 2_000_000_000:
        return CompanyTier.MID
    if market_cap >= 300_000_000:
        return CompanyTier.SMALL
    if market_cap >= 50_000_000:
        return CompanyTier.MICRO
    return CompanyTier.NANO


class Relevance(str, Enum):
    """How relevant a metric is for the company's tier."""
    CRITICAL = "critical"       # Must-check for this tier, highlighted
    RELEVANT = "relevant"       # Standard importance, displayed normally
    CONTEXTUAL = "contextual"   # Shown dimmed — informational only
    IRRELEVANT = "irrelevant"   # Not meaningful for this tier, hidden/dimmed


# ---------------------------------------------------------------------------
# Core data models
# ---------------------------------------------------------------------------

@dataclass
class CompanyProfile:
    ticker: str
    name: str
    isin: Optional[str] = None
    sector: Optional[str] = None
    industry: Optional[str] = None
    country: Optional[str] = None
    exchange: Optional[str] = None
    currency: Optional[str] = None
    market_cap: Optional[float] = None
    description: Optional[str] = None
    website: Optional[str] = None
    employees: Optional[int] = None
    tier: CompanyTier = CompanyTier.NANO


@dataclass
class ValuationMetrics:
    """Price-based valuation ratios."""
    pe_trailing: Optional[float] = None
    pe_forward: Optional[float] = None
    pb_ratio: Optional[float] = None
    ps_ratio: Optional[float] = None
    p_fcf: Optional[float] = None
    ev_ebitda: Optional[float] = None
    ev_revenue: Optional[float] = None
    peg_ratio: Optional[float] = None
    dividend_yield: Optional[float] = None
    earnings_yield: Optional[float] = None
    enterprise_value: Optional[float] = None
    market_cap: Optional[float] = None
    # Microcap-specific
    price_to_tangible_book: Optional[float] = None
    price_to_ncav: Optional[float] = None  # Price / Net Current Asset Value


@dataclass
class ProfitabilityMetrics:
    """Margins and returns on capital."""
    roe: Optional[float] = None
    roa: Optional[float] = None
    roic: Optional[float] = None
    gross_margin: Optional[float] = None
    operating_margin: Optional[float] = None
    net_margin: Optional[float] = None
    fcf_margin: Optional[float] = None
    ebitda_margin: Optional[float] = None


@dataclass
class SolvencyMetrics:
    """Financial health and leverage."""
    debt_to_equity: Optional[float] = None
    debt_to_ebitda: Optional[float] = None
    current_ratio: Optional[float] = None
    quick_ratio: Optional[float] = None
    interest_coverage: Optional[float] = None
    altman_z_score: Optional[float] = None
    net_debt: Optional[float] = None
    total_debt: Optional[float] = None
    total_cash: Optional[float] = None
    # Microcap/smallcap survival metrics
    cash_burn_rate: Optional[float] = None      # Annual cash burn (negative = burning)
    cash_runway_years: Optional[float] = None   # Years of cash left at current burn
    working_capital: Optional[float] = None
    cash_per_share: Optional[float] = None
    tangible_book_value: Optional[float] = None
    ncav: Optional[float] = None                # Net Current Asset Value
    ncav_per_share: Optional[float] = None      # NCAV / shares outstanding


@dataclass
class GrowthMetrics:
    """Year-over-year and compound growth rates."""
    revenue_growth_yoy: Optional[float] = None
    revenue_cagr_3y: Optional[float] = None
    revenue_cagr_5y: Optional[float] = None
    earnings_growth_yoy: Optional[float] = None
    earnings_cagr_3y: Optional[float] = None
    earnings_cagr_5y: Optional[float] = None
    fcf_growth_yoy: Optional[float] = None
    book_value_growth_yoy: Optional[float] = None
    dividend_growth_5y: Optional[float] = None
    # Share dilution tracking (critical for micro/small)
    shares_growth_yoy: Optional[float] = None   # Positive = dilution


@dataclass
class EfficiencyMetrics:
    """Operational efficiency ratios."""
    asset_turnover: Optional[float] = None
    inventory_turnover: Optional[float] = None
    receivables_turnover: Optional[float] = None
    days_sales_outstanding: Optional[float] = None
    days_inventory: Optional[float] = None
    cash_conversion_cycle: Optional[float] = None


@dataclass
class MoatIndicators:
    """Qualitative and quantitative moat signals."""
    moat_score: Optional[float] = None  # 0-100 composite
    roic_consistency: Optional[str] = None
    margin_stability: Optional[str] = None
    revenue_predictability: Optional[str] = None
    competitive_position: Optional[str] = None
    switching_costs: Optional[str] = None
    network_effects: Optional[str] = None
    cost_advantages: Optional[str] = None
    intangible_assets: Optional[str] = None
    efficient_scale: Optional[str] = None
    # Micro/small-cap moat sources
    niche_position: Optional[str] = None
    insider_alignment: Optional[str] = None
    asset_backing: Optional[str] = None
    # Historical trends
    roic_history: list[Optional[float]] = field(default_factory=list)
    gross_margin_history: list[Optional[float]] = field(default_factory=list)


@dataclass
class IntrinsicValue:
    """Intrinsic value estimates."""
    dcf_value: Optional[float] = None
    graham_number: Optional[float] = None
    ncav_value: Optional[float] = None           # Net-net value (Benjamin Graham)
    lynch_fair_value: Optional[float] = None
    asset_based_value: Optional[float] = None     # Tangible book per share
    current_price: Optional[float] = None
    margin_of_safety_dcf: Optional[float] = None
    margin_of_safety_graham: Optional[float] = None
    margin_of_safety_ncav: Optional[float] = None
    margin_of_safety_asset: Optional[float] = None
    # Which methods are considered reliable for this tier
    primary_method: Optional[str] = None
    secondary_method: Optional[str] = None


@dataclass
class FinancialStatement:
    """A single period's financial statement data."""
    period: str
    revenue: Optional[float] = None
    cost_of_revenue: Optional[float] = None
    gross_profit: Optional[float] = None
    operating_income: Optional[float] = None
    net_income: Optional[float] = None
    ebitda: Optional[float] = None
    total_assets: Optional[float] = None
    total_liabilities: Optional[float] = None
    total_equity: Optional[float] = None
    total_debt: Optional[float] = None
    total_cash: Optional[float] = None
    current_assets: Optional[float] = None
    current_liabilities: Optional[float] = None
    operating_cash_flow: Optional[float] = None
    capital_expenditure: Optional[float] = None
    free_cash_flow: Optional[float] = None
    dividends_paid: Optional[float] = None
    shares_outstanding: Optional[float] = None
    eps: Optional[float] = None
    book_value_per_share: Optional[float] = None


@dataclass
class MetricExplanation:
    """Explanation of a financial metric."""
    key: str
    full_name: str
    description: str
    why_used: str
    formula: str
    category: str  # valuation, profitability, solvency, growth, efficiency


@dataclass
class Filing:
    """SEC or regulatory filing metadata."""
    form_type: str
    filing_date: str
    period: str
    url: str
    description: Optional[str] = None
    local_path: Optional[str] = None


@dataclass
class NewsArticle:
    title: str
    url: str
    published: Optional[str] = None
    source: Optional[str] = None
    summary: Optional[str] = None
    local_path: Optional[str] = None


@dataclass
class AnalysisReport:
    """Complete fundamental analysis for a company."""
    profile: CompanyProfile
    valuation: ValuationMetrics
    profitability: ProfitabilityMetrics
    solvency: SolvencyMetrics
    growth: GrowthMetrics
    efficiency: EfficiencyMetrics
    moat: MoatIndicators
    intrinsic_value: IntrinsicValue
    financials: list[FinancialStatement] = field(default_factory=list)
    filings: list[Filing] = field(default_factory=list)
    news: list[NewsArticle] = field(default_factory=list)
    fetched_at: str = field(default_factory=lambda: datetime.now().isoformat())
