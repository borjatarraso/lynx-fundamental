# Lynx FA — Fundamental Analysis for Value Investing

A command-line tool for fundamental analysis focused on **value investing** and **economic moat** detection. Fetches, calculates, and displays 40+ financial metrics, SEC filings, and news for any publicly traded company — from mega-caps like Apple to micro-caps on TSXV or OTC Pink Sheets.

## Features

- **40+ value investing metrics** — valuation, profitability, solvency, growth, efficiency, moat scoring, intrinsic value
- **Tier-aware analysis** — automatically classifies companies (Mega/Large/Mid/Small/Micro/Nano Cap) and adjusts metrics, thresholds, and valuation methods accordingly
- **Moat detection** — traditional moat analysis for large caps (ROIC consistency, margin stability, pricing power); survival-focused analysis for micro/small caps (cash burn, NCAV, dilution)
- **Intrinsic value** — DCF, Graham Number, NCAV net-net, Peter Lynch fair value, asset-based valuation — each method ranked by reliability per company tier
- **SEC filings** — fetches and downloads 10-K, 10-Q, 8-K, 20-F filings via yfinance/EDGAR
- **News aggregation** — Yahoo Finance + Google News RSS, deduplicated
- **Multi-exchange support** — US (NYSE, NASDAQ, OTC), Canada (TSXV, TSX), Europe (XETRA, LSE, Euronext), Asia-Pacific, and 30+ exchange suffixes
- **ISIN and company name resolution** — search by ISIN, ticker, or free-text company name
- **Local data cache** — production data under `data/`, test data under `data_test/` (fully isolated); cached analyses reused automatically in production mode, with `--refresh` to force update and `--drop-cache` to clean up
- **Four interfaces** — direct CLI (console), interactive prompt mode (`-i`), Textual terminal UI (`-tui`), and graphical interface (`-x`)

## Installation

```bash
pip install -e .
```

### Dependencies

- Python >= 3.10
- yfinance, requests, beautifulsoup4, rich, textual, feedparser, pandas, numpy

## Execution Modes

The tool requires one of two execution modes:

| Mode | Flag | Data Directory | Cache Behavior |
|------|------|---------------|----------------|
| **Production** | `-p` / `--production-mode` | `data/` | Cache-first (reuses saved data) |
| **Testing** | `-t` / `--testing-mode` | `data_test/` | Always fresh (never reads cache) |

**Production mode** stores and reuses data under `data/`. Subsequent analyses of the same ticker load instantly from cache. Use `--refresh` to force a fresh download.

**Testing mode** uses a completely isolated `data_test/` directory. It always fetches fresh data from the network — production data is never read from or written to. Ideal for testing, development, and running automated tests without risk to production data.

## Quick Start

```bash
# Production: analyze (uses cache if available)
lynx-fa -p AAPL

# Production: force fresh data download
lynx-fa -p AAPL --refresh

# Testing: always fetches fresh, writes to data_test/
lynx-fa -t AAPL

# Analyze TSXV / OTC / international stocks
lynx-fa -p OCO.V                 # TSXV (Oroco Resource)
lynx-fa -p AT1.DE                # XETRA (Aroundtown)
lynx-fa -p ORRCF                 # OTC Pink
lynx-fa -p "F3 Uranium"          # Search by company name

# Search for a company across exchanges
lynx-fa -p -s "Aroundtown"

# Launch interactive mode
lynx-fa -p -i                    # Production interactive
lynx-fa -t -i                    # Testing interactive

# Launch terminal UI
lynx-fa -p -tui

# Cache management (mode-specific)
lynx-fa -p --list-cache          # Show production cached tickers
lynx-fa -t --list-cache          # Show test cached tickers
lynx-fa -p --drop-cache AAPL     # Remove production data for AAPL
lynx-fa -t --drop-cache ALL      # Clear all test data

# Skip reports or news
lynx-fa -p GOOG --no-reports --no-news
```

## CLI Reference

```
usage: lynx-fa [-h] (-p | -t) [-i | -tui | -s | -x] [--refresh]
               [--drop-cache [TICKER]] [--list-cache] [--no-reports]
               [--no-news] [--max-filings N] [--verbose] [--version]
               [--about] [identifier]
```

| Flag | Description |
|------|-------------|
| `-p`, `--production-mode` | **Required.** Production mode (data/, cache-first) |
| `-t`, `--testing-mode` | **Required.** Testing mode (data_test/, always fresh) |
| `identifier` | Ticker symbol, ISIN, or company name |
| `-i`, `--interactive-mode` | Launch interactive prompt mode |
| `-tui`, `--textual-ui` | Launch Textual terminal UI |
| `-x`, `--gui` | Launch graphical user interface (Tkinter) |
| `-s`, `--search` | Search for a company across exchanges |
| `--refresh` | Force fresh data download (production mode only) |
| `--drop-cache TICKER` | Remove cached data for a ticker (or `ALL`) |
| `--list-cache` | Show all cached tickers with metadata |
| `--no-reports` | Skip SEC filing download |
| `--no-news` | Skip news fetching |
| `--max-filings N` | Limit filing downloads (default: 10) |
| `-v`, `--verbose` | Verbose output |
| `--about` | Show about information, author, and license |

## Company Tier System

The tool automatically classifies companies by market capitalization and adapts the entire analysis:

| Tier | Market Cap | Analysis Focus |
|------|-----------|----------------|
| **Mega Cap** | > $200B | Full traditional value investing, DCF primary |
| **Large Cap** | $10B–$200B | Full traditional analysis |
| **Mid Cap** | $2B–$10B | Blended (traditional + growth focus) |
| **Small Cap** | $300M–$2B | Balance sheet strength, Graham Number primary |
| **Micro Cap** | $50M–$300M | Survival metrics, NCAV/net-net primary |
| **Nano Cap** | < $50M | Speculative, asset-based only |

### What changes per tier

- **Critical metrics shift**: P/E and ROIC are critical for mega caps but contextual for micro caps; cash burn and NCAV are critical for micro caps but irrelevant for mega caps
- **Moat scoring adapts**: Large caps scored on ROIC consistency, margin stability, and scale; micro caps scored on asset backing, cash runway, dilution risk, and niche position
- **Valuation methods ranked**: DCF is primary for large caps (reliable cash flows) but unreliable for micro caps; NCAV (net-net) is primary for micro caps
- **Thresholds adjust**: P/B < 0.67 is "deep value" for micro caps (Graham's 2/3 rule); D/E > 0.5 is "risky for micro cap" but "conservative" for large caps
- **Display adapts**: Critical metrics marked with `*`, irrelevant metrics hidden, section titles change (e.g., "Survival & Financial Health" for micro caps)

## Metrics Reference

### Valuation (12 metrics)
P/E Trailing, P/E Forward, P/B, P/S, P/FCF, EV/EBITDA, EV/Revenue, PEG, Dividend Yield, Earnings Yield, P/Tangible Book, P/NCAV

### Profitability (8 metrics)
ROE, ROA, ROIC, Gross Margin, Operating Margin, Net Margin, FCF Margin, EBITDA Margin

### Solvency & Survival (11 metrics)
Debt/Equity, Debt/EBITDA, Current Ratio, Quick Ratio, Interest Coverage, Altman Z-Score, Cash Burn Rate, Cash Runway, Working Capital, Cash Per Share, NCAV Per Share

### Growth (10 metrics)
Revenue Growth YoY, Revenue CAGR 3Y/5Y, Earnings Growth YoY, Earnings CAGR 3Y/5Y, FCF Growth, Book Value Growth, Dividend Growth, Share Dilution YoY

### Moat Indicators
**Large caps**: ROIC Consistency, Margin Stability, Revenue Predictability, Financial Strength, Growth Quality, Switching Costs, Network Effects, Cost Advantages, Intangible Assets, Efficient Scale

**Micro/Small caps**: Asset Backing (NCAV), Cash Position & Survival, Revenue Viability, Niche Position, Insider Alignment / Dilution Risk

### Intrinsic Value (5 methods)
DCF (10-year), Graham Number, NCAV Net-Net (Benjamin Graham), Peter Lynch Fair Value, Asset-Based (Tangible Book)

## Data Storage

Data is stored locally. Production mode uses `data/`, testing mode uses `data_test/`:

```
data/
  AAPL/
    analysis_latest.json        # Full computed analysis (cache)
    analysis_20260412_232156.json  # Timestamped snapshots
    financials/
      income_annual.json
      balance_annual.json
      cashflow_annual.json
      ...
    reports/
      10-K_20251031.html
      10-Q_20260130.html
      filings_index.json
    news/
      news_index.json
```

In production mode, subsequent runs reuse cached data automatically. Use `--refresh` to force a fresh download or `--drop-cache` to remove stale data. In testing mode, every run fetches fresh data and the test directory can be safely wiped at any time.

## Interactive Mode Commands

Launch with `lynx-fa -i`:

| Command | Description |
|---------|-------------|
| `analyze <TICKER>` | Analyze (uses cache) |
| `refresh <TICKER>` | Force fresh download |
| `search <query>` | Search for companies |
| `metrics` | Redisplay last analysis |
| `filings` | List SEC filings |
| `download-filing <N>` | Download a filing |
| `news` | Show news articles |
| `download-news <N>` | Download an article |
| `summary` | Show moat + intrinsic value |
| `cache` | List cached tickers |
| `drop-cache <TICKER>` | Remove cached data |
| `export` | Show data directory path |
| `about` | Show about, author, and license |

## Project Structure

```
lynx-fa-analysis/
├── pyproject.toml
├── lynx/
│   ├── __main__.py          # Entry point
│   ├── cli.py               # CLI argument parser
│   ├── interactive.py       # Interactive prompt mode
│   ├── display.py           # Rich console output (tier-aware)
│   ├── models.py            # Data models, tier classification
│   ├── core/
│   │   ├── analyzer.py      # Main orchestrator (cache-aware)
│   │   ├── fetcher.py       # Financial data via yfinance
│   │   ├── reports.py       # SEC filings via yfinance + EDGAR
│   │   ├── news.py          # News from Yahoo Finance + Google RSS
│   │   ├── storage.py       # Local data persistence + cache
│   │   └── ticker.py        # ISIN/ticker/name resolution
│   ├── metrics/
│   │   ├── calculator.py    # All metric calculations (tier-aware)
│   │   └── relevance.py     # Metric relevance per company tier
│   ├── tui/
│   │   └── app.py           # Textual terminal UI
│   └── gui/
│       └── app.py           # Tkinter graphical interface
├── data/                    # Production data storage (gitignored)
└── data_test/               # Testing data storage (gitignored)
```

## Interfaces

### Console Mode (default)
Direct CLI analysis: `lynx-fa -p AAPL`

### Interactive Mode (`-i`)
REPL with commands: analyze, search, filings, news, summary, about, etc.

### Textual UI (`-tui`)
Full terminal UI with tabs, search modal, and keyboard navigation. Press **F1** for About.

### Graphical Interface (`-x`)
Tkinter-based GUI with collapsible sections, moat score bar, and About dialog.

## About

Use `lynx-fa --about` (console), `about` (interactive), **F1** (TUI), or the **About** button (GUI) to view author and license information.

## License

BSD 3-Clause License. Copyright (c) 2026, Borja Tarraso <borja.tarraso@member.fsf.org>.

See [LICENSE](LICENSE) for the full text.
