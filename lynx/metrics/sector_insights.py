"""Sector and industry-specific fundamental analysis insights.

Provides critical metrics, key risks, and analytical focus areas tailored
to each sector and industry.  Used by all display modes to render
contextual guidance alongside the standard analysis.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class SectorInsight:
    """Analysis guidance specific to a sector."""
    sector: str
    overview: str
    critical_metrics: list[str] = field(default_factory=list)
    key_risks: list[str] = field(default_factory=list)
    what_to_watch: list[str] = field(default_factory=list)
    typical_valuation: str = ""


@dataclass
class IndustryInsight:
    """Analysis guidance specific to an industry within a sector."""
    industry: str
    sector: str
    overview: str
    critical_metrics: list[str] = field(default_factory=list)
    key_risks: list[str] = field(default_factory=list)
    what_to_watch: list[str] = field(default_factory=list)
    typical_valuation: str = ""


# ---------------------------------------------------------------------------
# Sector insights
# ---------------------------------------------------------------------------

_SECTORS: dict[str, SectorInsight] = {}


def _add_sector(sector, overview, critical_metrics, key_risks, what_to_watch,
                typical_valuation):
    _SECTORS[sector.lower()] = SectorInsight(
        sector=sector, overview=overview,
        critical_metrics=critical_metrics, key_risks=key_risks,
        what_to_watch=what_to_watch, typical_valuation=typical_valuation,
    )


_add_sector(
    "Technology",
    "Technology companies are valued primarily on growth, margins, and "
    "scalability.  Software businesses often have near-zero marginal costs, "
    "while hardware companies face inventory and supply chain constraints.  "
    "R&D spending is a critical capital allocation decision.",
    ["Revenue Growth (YoY & CAGR)", "Gross Margin (>60% for software)",
     "R&D as % of Revenue", "FCF Margin", "Customer Retention / Churn"],
    ["Rapid technological obsolescence", "Customer concentration",
     "Regulatory risk (antitrust, data privacy)",
     "High stock-based compensation diluting shareholders"],
    ["TAM (Total Addressable Market) expansion",
     "Net revenue retention rate",
     "Operating leverage — margins expanding with scale",
     "Competitive moat from network effects or switching costs"],
    "Growth-adjusted: PEG ratio and EV/Revenue more relevant than P/E "
    "for high-growth. P/E 20-35 typical for mature tech.",
)

_add_sector(
    "Financial Services",
    "Financial companies (banks, insurance, asset managers) are valued "
    "differently from other sectors.  Book value and return on equity are "
    "the primary metrics.  Balance sheet leverage is inherent to the "
    "business model, so Debt/Equity ratios are not comparable to other sectors.",
    ["ROE (>12% is strong for banks)", "Net Interest Margin",
     "Efficiency Ratio (<55% is excellent)", "Book Value per Share",
     "Tangible Book Value", "Credit Loss Provisions"],
    ["Interest rate sensitivity", "Credit cycle / loan defaults",
     "Regulatory capital requirements (Basel III/IV)",
     "Concentration in loan portfolios"],
    ["Net interest income trends",
     "Non-performing loan ratio",
     "CET1 capital ratio (regulatory minimum ~4.5%)",
     "Dividend payout ratio and share buybacks"],
    "P/B ratio is primary (1.0-2.0 typical). P/E 10-15 for banks. "
    "Avoid using EV/EBITDA (not meaningful for financials).",
)

_add_sector(
    "Healthcare",
    "Healthcare is driven by R&D pipelines, patent cliffs, and regulatory "
    "approvals.  Pharma and biotech have high margins but binary drug "
    "approval risk.  Medical devices and services are more stable but "
    "face pricing pressure from payers.",
    ["R&D Pipeline Value", "Gross Margin (>70% for pharma)",
     "Patent Expiry Timeline", "Revenue Concentration by Drug",
     "FDA Approval Success Rate"],
    ["Patent cliff — revenue loss when key drugs go generic",
     "FDA/EMA regulatory rejection risk",
     "Drug pricing reform and political risk",
     "Clinical trial failures"],
    ["Pipeline depth and phase distribution",
     "Revenue diversification across drugs/therapies",
     "Upcoming patent expirations",
     "M&A activity for pipeline replenishment"],
    "P/E 15-25 for diversified pharma. Biotech often valued on "
    "pipeline (sum-of-parts DCF). EV/EBITDA 12-18 typical.",
)

_add_sector(
    "Energy",
    "Energy companies are highly cyclical, tied to commodity prices.  "
    "Capital intensity is extreme — upstream (E&P) companies must "
    "continuously invest in reserves replacement.  Integrated majors "
    "benefit from diversification across upstream/downstream.",
    ["Reserve Replacement Ratio", "Finding & Development Costs",
     "Debt/EBITDA (critical for survival)", "FCF Yield",
     "Dividend Sustainability"],
    ["Oil/gas price volatility", "Reserve depletion without replacement",
     "Energy transition and stranded asset risk",
     "Geopolitical risk in producing regions"],
    ["Breakeven oil price for profitability",
     "Capital discipline vs. growth spending",
     "Transition strategy (renewables, carbon capture)",
     "Shareholder returns (dividends + buybacks) vs. reinvestment"],
    "EV/EBITDA 4-8 typical. P/E is volatile due to commodity cycles. "
    "FCF yield and dividend yield are more reliable valuation anchors.",
)

_add_sector(
    "Consumer Cyclical",
    "Consumer cyclical (discretionary) companies are sensitive to economic "
    "cycles.  Revenue and margins expand in good times and contract sharply "
    "in recessions.  Brand strength, pricing power, and e-commerce "
    "penetration are key differentiators.",
    ["Same-Store Sales Growth", "Gross Margin Trend",
     "Inventory Turnover", "E-commerce % of Revenue",
     "Consumer Sentiment Indicators"],
    ["Economic recession reducing consumer spending",
     "Inventory buildup and markdowns",
     "Shifting consumer preferences and fashion risk",
     "Supply chain disruptions"],
    ["Consumer confidence and spending trends",
     "Inventory levels relative to sales",
     "Brand strength and pricing power during downturns",
     "Omnichannel strategy execution"],
    "P/E 15-25 at mid-cycle. Use normalized earnings (5Y average) "
    "to smooth cyclicality. EV/EBITDA 8-14 typical.",
)

_add_sector(
    "Consumer Defensive",
    "Consumer staples (defensive) companies sell essential goods with "
    "stable demand regardless of economic conditions.  They offer "
    "predictable cash flows and dividends but limited growth.  Pricing "
    "power and brand loyalty are the primary moat sources.",
    ["Organic Revenue Growth", "Gross Margin Stability",
     "Dividend Yield & Payout Ratio", "FCF Conversion",
     "Brand Portfolio Strength"],
    ["Input cost inflation eroding margins",
     "Private label competition",
     "Currency headwinds (most are multinationals)",
     "Changing consumer preferences (health, sustainability)"],
    ["Volume growth vs. price-driven growth",
     "Margin expansion from premiumization",
     "Dividend growth track record",
     "Market share trends in core categories"],
    "P/E 18-25 (premium for stability). Dividend yield 2-4% typical. "
    "EV/EBITDA 12-16. Rarely cheap — investors pay for predictability.",
)

_add_sector(
    "Industrials",
    "Industrial companies are cyclical, tied to capital expenditure cycles "
    "and economic growth.  Order backlogs provide revenue visibility.  "
    "Operational efficiency and pricing power during inflationary periods "
    "are critical differentiators.",
    ["Order Backlog & Book-to-Bill Ratio", "Operating Margin",
     "ROIC (>12% indicates pricing power)", "FCF Conversion",
     "Organic Revenue Growth"],
    ["Economic downturn reducing capital spending",
     "Raw material cost inflation",
     "Supply chain and logistics disruptions",
     "Geopolitical trade restrictions"],
    ["PMI (Purchasing Managers Index) trends",
     "Backlog growth and order momentum",
     "Pricing power during input cost inflation",
     "Aftermarket / services revenue (higher margins, recurring)"],
    "P/E 15-22 at mid-cycle. EV/EBITDA 10-14. Use normalized "
    "earnings — cyclical peaks/troughs distort single-year P/E.",
)

_add_sector(
    "Utilities",
    "Utilities are regulated monopolies or near-monopolies with "
    "predictable, bond-like cash flows.  They are valued primarily on "
    "dividend yield and rate base growth.  Interest rate sensitivity is "
    "high — utilities compete with bonds for income investors.",
    ["Dividend Yield (3-5% typical)", "Rate Base Growth",
     "Regulatory ROE Allowed", "Payout Ratio (<75% is safe)",
     "Debt/Equity (higher leverage is normal)"],
    ["Interest rate increases (reduces relative attractiveness)",
     "Regulatory risk — rate case denials",
     "Weather events and natural disasters",
     "Clean energy transition capital requirements"],
    ["Rate base growth from infrastructure investment",
     "Regulatory environment (constructive vs. hostile)",
     "Renewable energy transition progress",
     "Dividend growth history and sustainability"],
    "Dividend yield 3-5% is typical. P/E 16-22. EV/EBITDA 10-14. "
    "High Debt/Equity (1.0-1.5) is normal for the sector.",
)

_add_sector(
    "Basic Materials",
    "Basic materials (mining, chemicals, metals, forestry) are commodity-"
    "driven and highly cyclical.  Reserves, production costs, and "
    "commodity price cycles dominate valuation.  Balance sheet strength "
    "is critical to survive downturns.",
    ["All-In Sustaining Cost (AISC) for miners", "Reserve Life",
     "Debt/EBITDA (<2x in cyclical troughs)", "FCF at Current Prices",
     "Production Growth Profile"],
    ["Commodity price collapse", "Reserve depletion",
     "Jurisdictional/political risk (mining permits)",
     "Environmental remediation liabilities"],
    ["Commodity price cycle position (early, mid, late)",
     "Cost curve position (low-cost producers survive downturns)",
     "Reserve replacement and exploration success",
     "ESG and environmental compliance costs"],
    "P/E is unreliable (earnings swing with commodity prices). "
    "EV/EBITDA 4-7 for miners. P/NAV (price to net asset value) "
    "is the primary valuation for mining companies.",
)

_add_sector(
    "Real Estate",
    "REITs and real estate companies are valued on FFO (Funds From "
    "Operations), NAV, and dividend yield.  Traditional P/E is misleading "
    "due to depreciation of property assets.  Interest rate sensitivity "
    "is high given typical leverage levels.",
    ["FFO / AFFO per Share", "NAV (Net Asset Value)",
     "Occupancy Rate", "Debt/EBITDA",
     "Dividend Yield & AFFO Payout Ratio"],
    ["Interest rate increases raising financing costs",
     "Tenant defaults and occupancy declines",
     "Work-from-home reducing office demand",
     "Oversupply in specific property types"],
    ["Same-property NOI growth", "Lease duration and renewal rates",
     "Cap rate trends in target markets",
     "Development pipeline and funding"],
    "P/FFO 12-20. Dividend yield 3-6%. Price/NAV around 1.0 "
    "(discount = potential value, premium = quality).",
)

_add_sector(
    "Communication Services",
    "Telecom and media companies span from regulated utilities (telcos) "
    "to high-growth digital media.  Legacy telecom is valued on dividend "
    "yield and FCF; digital media on user growth and engagement metrics.",
    ["ARPU (Average Revenue Per User)", "Subscriber/User Growth",
     "Content Spending Efficiency", "FCF Margin",
     "Churn Rate"],
    ["Cord-cutting and subscriber losses (traditional media)",
     "Content cost escalation",
     "Regulatory and antitrust intervention",
     "Competitive intensity in streaming/digital ads"],
    ["Subscriber/user growth trajectory",
     "Monetization per user trends",
     "Content ROI and library value",
     "5G and infrastructure capex cycle"],
    "Telcos: P/E 10-14, dividend yield 4-7%. Digital media: "
    "EV/Revenue and user-based metrics. Wide range by sub-sector.",
)


# ---------------------------------------------------------------------------
# Industry insights (selected high-frequency industries)
# ---------------------------------------------------------------------------

_INDUSTRIES: dict[str, IndustryInsight] = {}


def _add_industry(industry, sector, overview, critical_metrics, key_risks,
                  what_to_watch, typical_valuation):
    _INDUSTRIES[industry.lower()] = IndustryInsight(
        industry=industry, sector=sector, overview=overview,
        critical_metrics=critical_metrics, key_risks=key_risks,
        what_to_watch=what_to_watch, typical_valuation=typical_valuation,
    )


# Technology industries
_add_industry(
    "Software - Application", "Technology",
    "Application software companies benefit from recurring revenue (SaaS), "
    "high gross margins (75-90%), and strong operating leverage.  The key "
    "question is whether growth is sustainable and the path to profitability "
    "is clear for unprofitable companies.",
    ["Net Revenue Retention (>120% is excellent)", "ARR Growth",
     "Rule of 40 (Growth % + FCF Margin %)", "Gross Margin (>75%)",
     "CAC Payback Period"],
    ["Customer churn in economic downturns",
     "Competition from platform players (Microsoft, Google)",
     "Long sales cycles in enterprise software",
     "Stock-based compensation dilution"],
    ["NRR trend (expansion vs. contraction)",
     "Large customer concentration",
     "Path to profitability (Rule of 40 benchmark)",
     "Platform vs. point solution positioning"],
    "EV/Revenue 5-15x for growth SaaS. P/E 30-50 for profitable. "
    "Rule of 40 is the key efficiency benchmark.",
)

_add_industry(
    "Software - Infrastructure", "Technology",
    "Infrastructure software (databases, DevOps, security, cloud) benefits "
    "from high switching costs and mission-critical positioning.  These "
    "businesses tend to be stickier than application software with higher "
    "net retention rates.",
    ["Net Revenue Retention (>130% for best-in-class)",
     "Gross Margin (>80%)", "FCF Margin",
     "Dollar-Based Expansion Rate", "RPO Growth"],
    ["Cloud platform competition (AWS, Azure, GCP)",
     "Open-source alternatives", "Security breach liability",
     "Rapid technology shifts"],
    ["Cloud consumption trends", "Multi-cloud adoption",
     "Developer ecosystem and community",
     "Platform expansion beyond core product"],
    "EV/Revenue 8-20x for high-growth. Premium to application "
    "software due to higher switching costs and retention.",
)

_add_industry(
    "Semiconductors", "Technology",
    "Semiconductors are highly cyclical with long capital investment cycles.  "
    "Fabless companies (design only) have higher margins but depend on "
    "foundries.  Integrated device manufacturers (IDMs) have higher capex "
    "but more control.  Inventory cycles drive short-term performance.",
    ["Gross Margin (>50% for fabless)", "R&D as % of Revenue",
     "Inventory Days", "Book-to-Bill Ratio",
     "Design Win Pipeline"],
    ["Cyclical demand swings", "Geopolitical supply chain risk (Taiwan)",
     "Technology node transitions (high R&D cost)",
     "Customer concentration (top 5 often >50% of revenue)"],
    ["Inventory levels across the supply chain",
     "End-market demand (data center, auto, mobile, industrial)",
     "Foundry capacity and pricing trends",
     "AI/ML chip demand trajectory"],
    "P/E 15-25 at mid-cycle. EV/EBITDA 10-18. Use normalized "
    "earnings — semiconductor cycles are pronounced.",
)

_add_industry(
    "Consumer Electronics", "Technology",
    "Consumer electronics companies face intense competition, short product "
    "cycles, and commoditization risk.  Ecosystem lock-in and services "
    "revenue provide defensibility.  Hardware margins are lower than "
    "software, but scale advantages are significant.",
    ["Gross Margin (>35% indicates premium positioning)",
     "Services Revenue Growth", "Installed Base Size",
     "ASP Trends", "Inventory Turnover"],
    ["Product cycle dependency", "Component cost inflation",
     "Trade restrictions and tariffs",
     "Commoditization of hardware features"],
    ["Services/recurring revenue as % of total",
     "Ecosystem stickiness and switching costs",
     "Geographic revenue diversification",
     "Product launch cadence and innovation pipeline"],
    "P/E 20-30 for premium brands. EV/EBITDA 12-18. "
    "Services multiple often higher than hardware.",
)

# Financial Services industries
_add_industry(
    "Banks - Diversified", "Financial Services",
    "Diversified banks generate revenue from net interest income (lending), "
    "fees (wealth management, trading), and investment banking.  Credit "
    "quality and capital adequacy are existential concerns.  Regulatory "
    "compliance costs are substantial.",
    ["Net Interest Margin (NIM)", "Efficiency Ratio",
     "CET1 Capital Ratio (>10% is strong)",
     "Non-Performing Loan Ratio (<1% is clean)",
     "Return on Tangible Common Equity (ROTCE)"],
    ["Credit cycle deterioration", "Interest rate compression",
     "Regulatory capital requirements increasing",
     "Fintech disruption in payments and lending"],
    ["Loan growth by segment", "Deposit costs and beta",
     "Credit loss provisions vs. charge-offs",
     "Fee income diversification"],
    "P/TBV 1.0-2.0. P/E 10-14. Do NOT use EV/EBITDA — it is "
    "not meaningful for banks.",
)

_add_industry(
    "Insurance - Diversified", "Financial Services",
    "Insurance companies earn from underwriting profit (premiums minus "
    "claims) and investment income on float.  Combined ratio below 100% "
    "indicates underwriting profit.  Investment portfolio quality and "
    "duration matching are critical.",
    ["Combined Ratio (<100% = underwriting profit)",
     "Investment Income Yield", "Book Value Growth",
     "Premium Growth", "Reserve Adequacy"],
    ["Catastrophe losses from natural disasters",
     "Low interest rates reducing investment income",
     "Adverse reserve development",
     "Regulatory changes in reserve requirements"],
    ["Loss ratio trends by line of business",
     "Reserve triangle development",
     "Investment portfolio duration and credit quality",
     "Pricing cycle position (hard vs. soft market)"],
    "P/B 1.0-2.0. P/E 10-15. Buffett's preferred metric: "
    "float growth and cost of float.",
)

# Healthcare industries
_add_industry(
    "Drug Manufacturers - General", "Healthcare",
    "Large pharma companies have diversified drug portfolios, strong cash "
    "flows, and dividend programs.  Patent cliffs are the primary risk — "
    "blockbuster drugs losing exclusivity can eliminate billions in revenue.  "
    "Pipeline replenishment through R&D or M&A is essential.",
    ["Revenue Concentration (top drug as % of total)",
     "Patent Expiry Calendar", "Pipeline Phase Distribution",
     "R&D Productivity (revenue per R&D dollar)",
     "Gross Margin (>70% typical)"],
    ["Patent cliff on key drugs", "Generic competition post-expiry",
     "Drug pricing reform legislation",
     "Clinical trial failures in late-stage pipeline"],
    ["Upcoming LOE (Loss of Exclusivity) dates",
     "Phase 3 pipeline depth", "M&A strategy for pipeline gaps",
     "Biosimilar competition timeline"],
    "P/E 12-18 for diversified pharma. Higher for strong pipelines. "
    "Sum-of-parts DCF for pipeline valuation.",
)

_add_industry(
    "Biotechnology", "Healthcare",
    "Biotech companies are often pre-revenue or single-product, making "
    "traditional valuation metrics unreliable.  Binary event risk from "
    "clinical trials dominates.  Cash runway and burn rate are critical "
    "for pre-revenue companies.",
    ["Cash Runway (years at current burn)", "Pipeline Stage & Phase",
     "Clinical Trial Data Readouts", "Cash Burn Rate",
     "Partnered vs. Self-Funded Programs"],
    ["Clinical trial failure (binary risk)",
     "Financing dilution for pre-revenue companies",
     "Regulatory rejection (FDA Complete Response Letter)",
     "Competition from larger pharma companies"],
    ["Upcoming clinical catalysts and data readouts",
     "Cash position vs. burn rate",
     "Partnership and licensing deals",
     "Orphan drug designation or fast-track status"],
    "Traditional P/E usually not applicable. Risk-adjusted NPV "
    "of pipeline is the primary method. P/Cash for pre-revenue.",
)

# Energy industries
_add_industry(
    "Oil & Gas Integrated", "Energy",
    "Integrated oil companies operate across upstream (exploration & "
    "production), midstream (transport), and downstream (refining, "
    "chemicals).  Diversification provides earnings stability.  Capital "
    "discipline and shareholder returns are key investor focus areas.",
    ["Upstream: Reserve Replacement Ratio", "Finding & Development Cost",
     "Downstream: Refining Margins", "FCF Yield (>8% is attractive)",
     "Shareholder Yield (dividends + buybacks)"],
    ["Oil/gas price collapse", "Energy transition / stranded assets",
     "Geopolitical risk in producing regions",
     "Carbon regulation and emission costs"],
    ["Capital allocation: growth vs. returns",
     "Breakeven price for upstream profitability",
     "Renewable / low-carbon strategy",
     "Dividend sustainability through commodity cycles"],
    "EV/EBITDA 4-7. FCF yield is the best valuation anchor. "
    "P/E unreliable due to commodity price swings.",
)

_add_industry(
    "Oil & Gas E&P", "Energy",
    "Exploration & Production companies are pure upstream plays, highly "
    "leveraged to commodity prices.  Reserve quality, production costs, "
    "and balance sheet strength determine survival through downturns.",
    ["All-In Cash Costs per BOE", "Reserve Life Index",
     "Production Growth", "Debt/EBITDA (<2x in downturns)",
     "Netback per BOE"],
    ["Commodity price crash below breakeven",
     "Reserve depletion without replacement",
     "Well productivity decline rates",
     "Permitting and environmental restrictions"],
    ["Hedging book and price protection",
     "Decline rate and maintenance capex",
     "Acreage quality and drilling inventory",
     "Breakeven price floor"],
    "EV/EBITDA 3-6. P/NAV for reserve valuation. "
    "FCF yield at strip pricing.",
)

# Mining industries
_add_industry(
    "Gold", "Basic Materials",
    "Gold miners are leveraged to gold prices.  AISC (All-In Sustaining "
    "Cost) determines profitability.  Reserve grade, mine life, and "
    "jurisdictional risk are critical.  Gold miners often trade at "
    "premium multiples during price upcycles.",
    ["AISC per Ounce", "Reserve Grade (g/t)", "Mine Life (years)",
     "Production Profile", "NAV per Share"],
    ["Gold price decline", "Grade dilution as mines age",
     "Political/jurisdictional risk", "Rising energy/labor costs"],
    ["Gold price cycle position", "AISC trend (rising or falling)",
     "Exploration success and resource growth",
     "M&A discipline (avoiding overpaying for assets)"],
    "P/NAV 0.5-1.5x. EV/EBITDA 5-10. Avoid P/E — gold miner "
    "earnings swing dramatically with gold prices.",
)

_add_industry(
    "Other Industrial Metals & Mining", "Basic Materials",
    "Industrial metals miners (copper, zinc, nickel, lithium) are "
    "driven by industrial demand and supply constraints.  Electrification "
    "and EV demand are structural tailwinds for copper and battery metals.  "
    "Exploration-stage juniors carry high risk but asymmetric upside.",
    ["Cash Cost per Unit", "Resource/Reserve Size", "Mine Life",
     "Grade and Recovery Rate", "Jurisdictional Risk Score"],
    ["Commodity price volatility", "Permitting delays or denials",
     "Capital cost overruns on new projects",
     "Financing dilution for exploration-stage companies"],
    ["Supply-demand balance for the specific metal",
     "Electrification demand growth forecasts",
     "Project economics (NPV/IRR at various price decks)",
     "Insider ownership and skin in the game"],
    "Exploration juniors: P/NAV and EV/Resource. Producers: "
    "EV/EBITDA 4-7. Use DCF at consensus commodity prices.",
)

# Utilities industries
_add_industry(
    "Utilities - Regulated Electric", "Utilities",
    "Regulated electric utilities earn a guaranteed return on their rate "
    "base (invested capital).  Growth comes from rate base expansion "
    "through infrastructure investment.  Regulatory relationships are "
    "the single most important factor.",
    ["Allowed ROE (regulatory)", "Rate Base Growth",
     "Earned ROE vs. Allowed ROE", "Dividend Yield",
     "FFO/Debt Ratio (credit health)"],
    ["Regulatory disallowance of capital spending",
     "Interest rate increases reducing valuation",
     "Wildfire and weather liability",
     "Distributed generation (rooftop solar) reducing demand"],
    ["Rate case outcomes and regulatory tone",
     "Capital investment plan and rate base CAGR",
     "Clean energy transition capex opportunities",
     "Dividend growth vs. earnings growth alignment"],
    "P/E 17-22. Dividend yield 3-4.5%. Premium for constructive "
    "regulatory jurisdictions.",
)

# Consumer industries
_add_industry(
    "Internet Retail", "Consumer Cyclical",
    "Internet retailers compete on convenience, selection, and price.  "
    "Scale economics are powerful — the largest players benefit from "
    "logistics networks, data advantages, and marketplace network effects.  "
    "Profitability often lagged growth by years.",
    ["GMV (Gross Merchandise Value) Growth", "Take Rate",
     "Fulfillment Cost as % of Revenue", "Customer Acquisition Cost",
     "Active Customer Growth"],
    ["Margin pressure from fulfillment costs",
     "Competition from traditional retail going digital",
     "Regulatory scrutiny on market dominance",
     "Returns and fraud costs"],
    ["Marketplace vs. first-party revenue mix",
     "Advertising and services revenue (higher margin)",
     "Logistics and fulfillment efficiency gains",
     "International expansion economics"],
    "EV/Revenue for high-growth. P/E 30-60 for profitable. "
    "EV/EBITDA 15-25. FCF yield gaining importance as sector matures.",
)

_add_industry(
    "Household & Personal Products", "Consumer Defensive",
    "Household and personal products companies sell everyday essentials "
    "with strong brand loyalty.  Organic growth is typically low single "
    "digits, driven by pricing power and premiumization.  Dividend "
    "aristocrats are common in this industry.",
    ["Organic Revenue Growth (volume + price)", "Gross Margin",
     "Advertising Spend as % of Revenue", "Dividend Growth Rate",
     "Market Share in Core Categories"],
    ["Input cost inflation (commodities, packaging)",
     "Private label share gains", "Currency headwinds",
     "Changing consumer preferences"],
    ["Volume vs. price-driven growth",
     "Innovation pipeline (new products)",
     "E-commerce channel development",
     "Emerging market growth contribution"],
    "P/E 22-28 (stability premium). Dividend yield 2-3.5%. "
    "EV/EBITDA 14-18. Rarely cheap — investors pay for consistency.",
)

_add_industry(
    "Farm & Heavy Construction Machinery", "Industrials",
    "Heavy equipment manufacturers are cyclical, tied to agricultural "
    "commodity prices, construction spending, and infrastructure investment.  "
    "Aftermarket parts and services provide higher-margin recurring revenue "
    "that smooths cyclical swings.",
    ["Order Backlog", "Aftermarket Revenue % of Total",
     "Operating Margin Through-Cycle", "ROIC",
     "Dealer Inventory Levels"],
    ["Agricultural downturn reducing farm equipment demand",
     "Construction cycle slowdown",
     "Raw material cost increases (steel, components)",
     "Used equipment inventory overhang"],
    ["Dealer inventory vs. retail sales trends",
     "Precision agriculture and technology adoption",
     "Aftermarket growth and service contracts",
     "Infrastructure spending legislation"],
    "P/E 12-18 at mid-cycle. EV/EBITDA 8-12. Use normalized "
    "earnings to look through the cycle.",
)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_sector_insight(sector: str | None) -> SectorInsight | None:
    """Look up sector-specific analysis insight."""
    if not sector:
        return None
    return _SECTORS.get(sector.lower())


def get_industry_insight(industry: str | None) -> IndustryInsight | None:
    """Look up industry-specific analysis insight."""
    if not industry:
        return None
    return _INDUSTRIES.get(industry.lower())


def list_sectors() -> list[str]:
    """List all sectors with available insights."""
    return sorted(s.sector for s in _SECTORS.values())


def list_industries() -> list[str]:
    """List all industries with available insights."""
    return sorted(i.industry for i in _INDUSTRIES.values())
