# Lynx FA — Development Guide

## Project

Value investing fundamental analysis CLI tool. Fetches financial data via yfinance, calculates 40+ metrics, and displays tier-aware reports.

## Build & Run

```bash
pip install -e .       # Install in editable mode
lynx-fa AAPL           # Run analysis
lynx-fa -i             # Interactive mode
lynx-fa -tui           # Textual UI
```

## Architecture

- `lynx/core/analyzer.py` — Main orchestrator. Cache-first: loads `analysis_latest.json` if available, otherwise fetches fresh data.
- `lynx/core/fetcher.py` — yfinance data fetching (profile, financials, prices)
- `lynx/core/reports.py` — SEC filings via yfinance `sec_filings` property (EDGAR as fallback)
- `lynx/core/news.py` — Yahoo Finance + Google News RSS aggregation
- `lynx/core/storage.py` — All local file I/O under `data/<TICKER>/`
- `lynx/core/ticker.py` — Multi-layer ticker/ISIN/name resolution (supports OTC, TSXV, international exchanges)
- `lynx/models.py` — Dataclass models, `CompanyTier` enum, `Relevance` enum
- `lynx/metrics/calculator.py` — All metric calculations. Every function takes `tier` parameter.
- `lynx/metrics/relevance.py` — Defines metric relevance (critical/relevant/contextual/irrelevant) per company tier
- `lynx/display.py` — Rich terminal output. Tier-aware: highlights critical metrics, dims irrelevant ones, adjusts thresholds.
- `lynx/cli.py` — argparse CLI with `--refresh`, `--drop-cache`, `--list-cache`
- `lynx/interactive.py` — Prompt-based interactive shell
- `lynx/tui/app.py` — Textual terminal UI

## Key Conventions

- All metric calculators accept a `CompanyTier` parameter — never assume large-cap behavior
- The `data/` folder is gitignored — cache is local only
- Tier classification is in `models.py:classify_tier()` — market cap boundaries are defined there
- The relevance tables in `metrics/relevance.py` drive display behavior — add new metrics there
- SEC EDGAR direct access may be blocked by IP/environment — yfinance `sec_filings` is the primary source
- yfinance `Ticker.info` HTTP 404 noise is suppressed in `ticker.py:_try_direct_ticker()`
