# Lynx FA — Development Guide

## Project

Value investing fundamental analysis CLI tool. Fetches financial data via yfinance, calculates 40+ metrics, and displays tier-aware reports.

## Build & Run

```bash
pip install -e .                # Install in editable mode
lynx-fa -p AAPL                 # Production mode analysis
lynx-fa -t AAPL                 # Testing mode analysis
lynx-fa -p -i                   # Production interactive mode
lynx-fa -t -i                   # Testing interactive mode
lynx-fa -p -tui                 # Production Textual UI
```

## Execution Modes

The app has two mandatory modes that control data isolation:

- **Production** (`-p`): Uses `data/` directory, cache-enabled. This is the user-facing mode.
- **Testing** (`-t`): Uses `data_test/` directory, always fetches fresh. Never reads or writes to `data/`. Use this for development, debugging, and automated tests.

In code, `set_mode("testing")` must be called before any storage operation. The CLI handles this automatically from the `-p`/`-t` flags.

## Architecture

- `lynx/core/storage.py` — Mode-aware storage. Global `_MODE` controls data root (`data/` vs `data_test/`). All path functions, cache reads, and writes route through the current mode.
- `lynx/core/analyzer.py` — Main orchestrator. Cache-first in production: loads `analysis_latest.json` if available. Always fresh in testing mode.
- `lynx/core/fetcher.py` — yfinance data fetching (profile, financials, prices)
- `lynx/core/reports.py` — SEC filings via yfinance `sec_filings` property (EDGAR as fallback)
- `lynx/core/news.py` — Yahoo Finance + Google News RSS aggregation
- `lynx/core/ticker.py` — Multi-layer ticker/ISIN/name resolution (supports OTC, TSXV, international exchanges)
- `lynx/models.py` — Dataclass models, `CompanyTier` enum, `Relevance` enum
- `lynx/metrics/calculator.py` — All metric calculations. Every function takes `tier` parameter.
- `lynx/metrics/relevance.py` — Defines metric relevance (critical/relevant/contextual/irrelevant) per company tier
- `lynx/display.py` — Rich terminal output. Tier-aware: highlights critical metrics, dims irrelevant ones, adjusts thresholds.
- `lynx/cli.py` — argparse CLI with `-p`/`-t` mode selection, `--refresh`, `--drop-cache`, `--list-cache`
- `lynx/interactive.py` — Prompt-based interactive shell (mode-aware prompt and behavior)
- `lynx/tui/app.py` — Textual terminal UI with About modal (F1)
- `lynx/gui/app.py` — Tkinter graphical interface with About dialog

## Key Conventions

- `-p` or `-t` is required on every CLI invocation — there is no implicit default mode
- All metric calculators accept a `CompanyTier` parameter — never assume large-cap behavior
- `data/` and `data_test/` are gitignored — cache is local only
- Tier classification is in `models.py:classify_tier()` — market cap boundaries are defined there
- The relevance tables in `metrics/relevance.py` drive display behavior — add new metrics there
- SEC EDGAR direct access may be blocked by IP/environment — yfinance `sec_filings` is the primary source
- yfinance `Ticker.info` HTTP 404 noise is suppressed in `ticker.py:_try_direct_ticker()` using thread-safe per-logger level adjustment
- When writing tests, always call `set_mode("testing")` at the start to avoid touching production data
- About information is centralized in `lynx/__init__.py:get_about_text()` — all modes (console, interactive, TUI, GUI) use this single source
- License: BSD 3-Clause. See `LICENSE` file and `lynx/__init__.py:LICENSE_TEXT`
