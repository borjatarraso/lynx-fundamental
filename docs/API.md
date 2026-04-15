# lynx-fundamental — Python API Reference

lynx-fundamental can be used as a Python library in addition to the CLI. This document covers the public API.

## Quick Example

```python
from lynx.core.storage import set_mode
from lynx.core.analyzer import run_full_analysis
from lynx.display import display_full_report

# IMPORTANT: set mode before any data operations
set_mode("production")  # uses data/ with cache
# or
set_mode("testing")     # uses data_test/, always fresh

# Run analysis (production: uses cache if available)
report = run_full_analysis("AAPL")

# Force fresh data (or use testing mode which is always fresh)
report = run_full_analysis("AAPL", refresh=True)

# Display in terminal
display_full_report(report)

# Access individual metrics
print(report.profile.name)              # "Apple Inc."
print(report.profile.tier)              # CompanyTier.MEGA
print(report.valuation.pe_trailing)     # 33.01
print(report.profitability.roic)        # 0.3086
print(report.moat.moat_score)           # 63.0
print(report.intrinsic_value.dcf_value) # 94.72
```

---

## Core API

### `lynx.core.analyzer`

#### `run_full_analysis(identifier, ...) -> AnalysisReport`

Main entry point. Resolves a ticker/ISIN/company name, fetches data, calculates all metrics, and returns a complete analysis report.

```python
def run_full_analysis(
    identifier: str,              # Ticker, ISIN, or company name
    download_reports: bool = True, # Fetch SEC filings
    download_news: bool = True,    # Fetch news articles
    max_filings: int = 10,         # Max filings to download
    verbose: bool = False,
    refresh: bool = False,         # True = ignore cache, re-fetch everything
) -> AnalysisReport
```

**Cache behavior:**
- `refresh=False` (default): If `data/<TICKER>/analysis_latest.json` exists, it is loaded directly. No network calls are made.
- `refresh=True`: Ignores any cached data. Fetches everything fresh from the network. Overwrites the cache.

**Raises:** `ValueError` if the identifier cannot be resolved.

#### `run_progressive_analysis(identifier, ..., on_progress) -> AnalysisReport`

Progressive variant that calls `on_progress(stage, report)` after each stage completes, allowing UIs to render sections as data arrives.

```python
from lynx.core.analyzer import run_progressive_analysis

def on_progress(stage: str, report):
    print(f"Stage complete: {stage}")

report = run_progressive_analysis("AAPL", on_progress=on_progress)
```

**Stages emitted** (in order): `profile`, `financials`, `valuation`, `profitability`, `solvency`, `growth`, `moat`, `intrinsic_value`, `filings`, `news`, `conclusion`, `complete`.

The report is built incrementally — metric sections are `None` until their stage completes. Filings and news are fetched in parallel via `ThreadPoolExecutor`.

**ISIN auto-retrieval:** During analysis, the ISIN is automatically fetched from yfinance when not already known from the identifier resolution step.

If `on_progress` is `None`, behaves identically to `run_full_analysis`.

---

### `lynx.core.ticker`

#### `resolve_identifier(identifier) -> tuple[str, str | None]`

Resolves a ticker, ISIN, or company name to a `(ticker, isin)` tuple. Multi-layer resolution:

1. ISIN detection and search
2. Company name detection (spaces / long strings) — direct to yfinance Search
3. Direct yfinance Ticker lookup
4. yfinance Search (fuzzy, single API call)
5. Exchange suffix brute-force (30+ suffixes as last resort)

```python
from lynx.core.ticker import resolve_identifier

resolve_identifier("AAPL")                # ("AAPL", None)
resolve_identifier("OCO")                 # ("OCO.V", None)   — TSXV
resolve_identifier("AT1")                 # ("AT1.DE", None)  — XETRA
resolve_identifier("Oroco Resource Corp") # ("OCO.V", None)
resolve_identifier("US0378331005")        # ("AAPL", "US0378331005")
```

#### `search_companies(query, max_results=10) -> list[SearchResult]`

Search for companies by name, ticker, or ISIN. Returns `SearchResult` objects with `symbol`, `name`, `exchange`, `quote_type`, `score`.

```python
from lynx.core.ticker import search_companies

results = search_companies("F3 Uranium", max_results=5)
for r in results:
    print(f"{r.symbol:12s} {r.name:40s} {r.exchange}")
```

---

### `lynx.core.fetcher`

#### `fetch_company_profile(ticker) -> CompanyProfile`

Fetches basic company information from yfinance.

#### `fetch_info(ticker) -> dict`

Returns the raw yfinance `Ticker.info` dictionary. Used internally by metric calculators.

#### `fetch_financial_statements(ticker) -> list[FinancialStatement]`

Fetches income statement, balance sheet, and cash flow data. Returns a list of `FinancialStatement` objects sorted by recency (most recent first). Also saves raw JSON to `data/<TICKER>/financials/`.

#### `fetch_historical_prices(ticker, period="5y") -> pd.DataFrame | None`

Fetches historical price data from yfinance.

---

### `lynx.core.reports`

#### `fetch_sec_filings(ticker) -> list[Filing]`

Fetches SEC filing metadata using yfinance (primary) and EDGAR API (fallback). Returns `Filing` objects with `form_type`, `filing_date`, `period`, `url`.

#### `download_filing(ticker, filing) -> str | None`

Downloads a single filing document (HTML or PDF). Returns the local path, or None on failure.

#### `download_top_filings(ticker, filings, max_count=10) -> list[Filing]`

Downloads the most recent filings, respecting rate limits.

---

### `lynx.core.news`

#### `fetch_all_news(ticker, company_name=None) -> list[NewsArticle]`

Aggregates news from Yahoo Finance and Google News RSS, deduplicates by title.

#### `download_article(ticker, article) -> str | None`

Downloads and extracts text content from a news article URL.

---

### `lynx.core.storage`

#### Mode Management

```python
from lynx.core.storage import set_mode, get_mode, is_testing

set_mode("production")  # All paths route to data/
set_mode("testing")     # All paths route to data_test/

get_mode()              # -> "production" or "testing"
is_testing()            # -> bool
```

**Important:** Call `set_mode()` before any other storage operation. All path functions, cache reads, and cache writes are routed through the current mode. In testing mode, `has_cache()` and `load_cached_report()` always return `False`/`None` to guarantee fresh fetches.

#### Cache Management

```python
from lynx.core.storage import (
    has_cache,           # has_cache("AAPL") -> bool (always False in testing)
    load_cached_report,  # load_cached_report("AAPL") -> dict | None (always None in testing)
    get_cache_age_hours, # get_cache_age_hours("AAPL") -> float | None
    drop_cache_ticker,   # drop_cache_ticker("AAPL") -> bool
    drop_cache_all,      # drop_cache_all() -> int (count removed)
    list_cached_tickers, # list_cached_tickers() -> list[dict]
)
```

#### File Paths

All paths are mode-dependent. In production mode they resolve under `data/`, in testing mode under `data_test/`.

```python
from lynx.core.storage import (
    get_data_root,      # -> Path("data/") or Path("data_test/")
    get_company_dir,    # get_company_dir("AAPL") -> Path("data/AAPL/") or Path("data_test/AAPL/")
    get_reports_dir,    # -> Path("data/AAPL/reports/")
    get_news_dir,       # -> Path("data/AAPL/news/")
    get_financials_dir, # -> Path("data/AAPL/financials/")
)
```

#### Serialization

```python
from lynx.core.storage import save_json, load_json, save_text, save_binary
```

---

## Metrics API

### `lynx.metrics.calculator`

All calculators accept a `tier: CompanyTier` parameter that controls which metrics are computed.

```python
from lynx.metrics.calculator import (
    calc_valuation,       # (info, statements, tier) -> ValuationMetrics
    calc_profitability,   # (info, statements, tier) -> ProfitabilityMetrics
    calc_solvency,        # (info, statements, tier) -> SolvencyMetrics
    calc_growth,          # (statements, tier)       -> GrowthMetrics
    calc_efficiency,      # (info, statements, tier) -> EfficiencyMetrics
    calc_moat,            # (prof, growth, solv, stmts, info, tier) -> MoatIndicators
    calc_intrinsic_value, # (info, stmts, growth, solv, tier) -> IntrinsicValue
)
```

### `lynx.metrics.relevance`

Defines which metrics are critical, relevant, contextual, or irrelevant for each company tier.

```python
from lynx.metrics.relevance import get_relevance
from lynx.models import CompanyTier, Relevance

rel = get_relevance("pe_trailing", CompanyTier.MEGA, "valuation")
# -> Relevance.CRITICAL

rel = get_relevance("cash_burn_rate", CompanyTier.MEGA, "solvency")
# -> Relevance.IRRELEVANT

rel = get_relevance("cash_burn_rate", CompanyTier.MICRO, "solvency")
# -> Relevance.CRITICAL
```

### `lynx.metrics.sector_insights`

Provides sector and industry-specific analysis guidance: critical metrics, key risks, what to watch, and typical valuation ranges.

```python
from lynx.metrics.sector_insights import (
    get_sector_insight,    # (sector: str) -> SectorInsight | None
    get_industry_insight,  # (industry: str) -> IndustryInsight | None
    list_sectors,          # () -> list[str]
    list_industries,       # () -> list[str]
)

s = get_sector_insight("Technology")
# -> SectorInsight(sector="Technology", overview="...", critical_metrics=[...], ...)

i = get_industry_insight("Consumer Electronics")
# -> IndustryInsight(industry="Consumer Electronics", ...)
```

**Coverage:** 11 sectors, 16 industries. Lookups are case-insensitive. Returns `None` for unrecognized sectors/industries.

---

## Data Models

### `lynx.models`

All models are Python dataclasses.

#### `CompanyTier` (Enum)

```python
class CompanyTier(str, Enum):
    MEGA  = "Mega Cap"   # > $200B
    LARGE = "Large Cap"  # $10B–$200B
    MID   = "Mid Cap"    # $2B–$10B
    SMALL = "Small Cap"  # $300M–$2B
    MICRO = "Micro Cap"  # $50M–$300M
    NANO  = "Nano Cap"   # < $50M
```

#### `classify_tier(market_cap) -> CompanyTier`

```python
from lynx.models import classify_tier
classify_tier(3_800_000_000_000)  # CompanyTier.MEGA (Apple)
classify_tier(128_000_000)        # CompanyTier.MICRO (Oroco Resource)
```

#### `Relevance` (Enum)

```python
class Relevance(str, Enum):
    CRITICAL    = "critical"    # Must-check, highlighted with *
    RELEVANT    = "relevant"    # Standard importance
    CONTEXTUAL  = "contextual"  # Shown dimmed
    IRRELEVANT  = "irrelevant"  # Hidden
```

#### `AnalysisReport`

Top-level container returned by `run_full_analysis()` / `run_progressive_analysis()`.

Metric sections default to `None` so the report can be built incrementally during progressive analysis. After a complete analysis, all fields are populated.

```python
@dataclass
class AnalysisReport:
    profile: CompanyProfile                        # always present
    valuation: Optional[ValuationMetrics] = None
    profitability: Optional[ProfitabilityMetrics] = None
    solvency: Optional[SolvencyMetrics] = None
    growth: Optional[GrowthMetrics] = None
    efficiency: Optional[EfficiencyMetrics] = None
    moat: Optional[MoatIndicators] = None
    intrinsic_value: Optional[IntrinsicValue] = None
    financials: list[FinancialStatement]            # default: []
    filings: list[Filing]                           # default: []
    news: list[NewsArticle]                         # default: []
    fetched_at: str                                 # ISO timestamp
```

#### Key Metric Models

| Model | Fields |
|-------|--------|
| `CompanyProfile` | ticker, name, isin, sector, industry, country, exchange, currency, market_cap, description, website, employees, tier |
| `ValuationMetrics` | pe_trailing, pe_forward, pb_ratio, ps_ratio, p_fcf, ev_ebitda, ev_revenue, peg_ratio, dividend_yield, earnings_yield, enterprise_value, market_cap, price_to_tangible_book, price_to_ncav |
| `ProfitabilityMetrics` | roe, roa, roic, gross_margin, operating_margin, net_margin, fcf_margin, ebitda_margin |
| `SolvencyMetrics` | debt_to_equity, debt_to_ebitda, current_ratio, quick_ratio, interest_coverage, altman_z_score, net_debt, total_debt, total_cash, cash_burn_rate, cash_runway_years, working_capital, cash_per_share, tangible_book_value, ncav, ncav_per_share |
| `GrowthMetrics` | revenue_growth_yoy, revenue_cagr_3y, revenue_cagr_5y, earnings_growth_yoy, earnings_cagr_3y, earnings_cagr_5y, fcf_growth_yoy, book_value_growth_yoy, dividend_growth_5y, shares_growth_yoy |
| `MoatIndicators` | moat_score, roic_consistency, margin_stability, revenue_predictability, competitive_position, switching_costs, network_effects, cost_advantages, intangible_assets, efficient_scale, niche_position, insider_alignment, asset_backing, roic_history, gross_margin_history |
| `IntrinsicValue` | dcf_value, graham_number, ncav_value, lynch_fair_value, asset_based_value, current_price, margin_of_safety_dcf, margin_of_safety_graham, margin_of_safety_ncav, margin_of_safety_asset, primary_method, secondary_method |
| `FinancialStatement` | period, revenue, cost_of_revenue, gross_profit, operating_income, net_income, ebitda, total_assets, total_liabilities, total_equity, total_debt, total_cash, current_assets, current_liabilities, operating_cash_flow, capital_expenditure, free_cash_flow, dividends_paid, shares_outstanding, eps, book_value_per_share |
| `Filing` | form_type, filing_date, period, url, description, local_path |
| `NewsArticle` | title, url, published, source, summary, local_path |

---

## Display API

### `lynx.display`

#### `display_full_report(report: AnalysisReport) -> None`

Renders the complete analysis to the terminal using Rich. Output is tier-aware: critical metrics are highlighted with `*`, irrelevant metrics are hidden, thresholds shift by tier. Handles partial reports gracefully — sections with `None` metrics are skipped.

#### `display_report_stage(stage: str, report: AnalysisReport) -> None`

Renders a single stage of the report (progressive mode). Use as the `on_progress` callback for `run_progressive_analysis`:

```python
from lynx.core.analyzer import run_progressive_analysis
from lynx.display import display_report_stage

report = run_progressive_analysis("AAPL", on_progress=display_report_stage)
```

Individual sections can be called directly:

```python
from lynx.display import (
    display_full_report,
    display_report_stage,
    _display_header,
    _display_profile,
    _display_valuation,
    _display_profitability,
    _display_solvency,
    _display_growth,
    _display_moat,
    _display_intrinsic_value,
    _display_financials,
    _display_filings,
    _display_news,
)
```

---

## About API

### `lynx.get_about_text() -> dict`

Returns structured about information including author, license, and description. Used by all interfaces (console, interactive, TUI, GUI) to display consistent about/license information.

```python
from lynx import get_about_text, LICENSE_TEXT, __author__, __author_email__, __license__

about = get_about_text()
# Returns:
# {
#     "name": "Lynx Fundamental Analysis",
#     "version": "0.1.0",
#     "author": "Borja Tarraso",
#     "email": "borja.tarraso@member.fsf.org",
#     "year": "2026",
#     "license": "BSD-3-Clause",
#     "license_text": "BSD 3-Clause License\n\nCopyright (c) ...",
#     "description": "Value investing research tool ...",
# }
```

### Accessing About from each mode

| Mode | How to access |
|------|---------------|
| Console (CLI) | `lynx-fundamental --about` |
| Interactive | Type `about` at the prompt |
| Textual UI | Press **F1** |
| Graphical UI | Click **About** button in toolbar |

### Filing Downloads

| Mode | How to download |
|------|-----------------|
| Console (CLI) | Automatic during analysis (top N filings) |
| Interactive | `download-filing <N>` |
| Textual UI | Select filing row, press **Enter** |
| Graphical UI | Click **Download** button on filing row |

### News: Open in Browser

| Mode | How to open |
|------|-------------|
| Interactive | `open-news <N>` |
| Textual UI | Select news row, press **Enter** |
| Graphical UI | Click **Open** button on news row |

The TUI and GUI show a confirmation dialog after opening news in the browser. The dialog includes a "Do not show again" option that suppresses it for the rest of the session. The flag resets when the application is restarted.

---

## TUI Themes

The Textual UI supports 7 color themes, cycled with the `T` key:

| Theme | Style |
|-------|-------|
| `lynx-dark` | Default dark theme (Catppuccin Mocha) |
| `hacker` | Green-on-black terminal aesthetic |
| `dracula` | Purple/pink Dracula color palette |
| `solarized` | Solarized Dark |
| `lynx-light` | Light theme with blue accents |
| `textual-dark` | Textual built-in dark |
| `textual-light` | Textual built-in light |

### Programmatic Theme Registration

```python
from lynx.tui.themes import CUSTOM_THEMES, THEME_NAMES, register_all_themes

# THEME_NAMES lists all theme names in cycle order
print(THEME_NAMES)

# register_all_themes(app) registers custom themes on a Textual App
```

---

## Collapsible Layout

Both the TUI and GUI use collapsible sections for the analysis report:

- **Company Profile** is expanded by default with a split layout (metrics left, description right)
- All other sections (Valuation, Profitability, Solvency, Growth, Moat, Intrinsic Value, Conclusion, Financials, Filings, News) start collapsed
- Click or toggle to expand/collapse individual sections

### Metric Explanations

Both TUI and GUI provide inline access to metric explanations:

| Mode | How to access |
|------|---------------|
| TUI | Select a metric row, press `I` to see explanation |
| GUI | Click the `?` button on any metric row |
| Interactive | Type `explain <metric_key>` |
| Console CLI | `lynx-fundamental --explain <metric_key>` |

Explanation data is stored in `lynx/metrics/explanations.py` and includes: full name, description, formula, why it matters, and category.

### GUI Branding

The GUI displays the Lynx logo in two locations:
- `img/logo_sm_quarter_green.png` in the top-left toolbar
- `img/logo_sm_green.png` in the About dialog
```
