# lynx-fundamental — Development Guide

## Project

Value investing fundamental analysis CLI tool. Fetches financial data via yfinance, calculates 40+ metrics, and displays tier-aware reports.

## Build & Run

```bash
pip install -r requirements.txt          # Install dependencies
pip install weasyprint                   # Optional: PDF export support

python3 lynx-fundamental.py -p AAPL                 # Production mode analysis
python3 lynx-fundamental.py -t AAPL                 # Testing mode analysis
python3 lynx-fundamental.py -p -i                   # Production interactive mode
python3 lynx-fundamental.py -t -i                   # Testing interactive mode
python3 lynx-fundamental.py -p -tui                 # Production Textual UI
python3 lynx-fundamental.py -p -x                   # Production graphical UI (Tkinter)
python3 lynx-fundamental.py -p -x AAPL              # Graphical UI with pre-filled ticker
```

## Execution Modes

The app has two mandatory modes that control data isolation:

- **Production** (`-p`): Uses `data/` directory, cache-enabled. This is the user-facing mode.
- **Testing** (`-t`): Uses `data_test/` directory, always fetches fresh. Never reads or writes to `data/`. Use this for development, debugging, and automated tests.

In code, `set_mode("testing")` must be called before any storage operation. The CLI handles this automatically from the `-p`/`-t` flags.

## Architecture

- `lynx/core/storage.py` — Mode-aware storage. Global `_MODE` controls data root (`data/` vs `data_test/`). All path functions, cache reads, and writes route through the current mode.
- `lynx/core/analyzer.py` — Main orchestrator. `run_progressive_analysis()` emits stage callbacks for progressive display; `run_full_analysis()` is a non-progressive wrapper. Cache-first in production: loads cached report if available. Filings and news are fetched in parallel via `ThreadPoolExecutor`.
- `lynx/core/conclusion.py` — Report synthesis engine with tier-weighted scoring. All scoring functions handle `None` metric sections gracefully.
- `lynx/core/fetcher.py` — yfinance data fetching (profile, financials, prices)
- `lynx/core/reports.py` — SEC filings via yfinance `sec_filings` property (EDGAR as fallback)
- `lynx/core/news.py` — Yahoo Finance + Google News RSS aggregation
- `lynx/core/ticker.py` — Multi-layer ticker/ISIN/name resolution (supports OTC, TSXV, international exchanges)
- `lynx/models.py` — Dataclass models, `CompanyTier` enum, `Relevance` enum. `AnalysisReport` metric fields are `Optional` to support progressive building.
- `lynx/metrics/calculator.py` — All metric calculations. Every function takes `tier` parameter.
- `lynx/metrics/relevance.py` — Defines metric relevance (critical/relevant/contextual/irrelevant) per company tier
- `lynx/display.py` — Rich terminal output. `display_report_stage()` renders individual sections progressively; `display_full_report()` renders everything at once. Tier-aware: highlights critical metrics, dims irrelevant ones, adjusts thresholds. All display functions handle `None` metric sections gracefully.
- `lynx/cli.py` — argparse CLI with `-p`/`-t` mode selection, `--refresh`, `--drop-cache`, `--list-cache`
- `lynx/interactive.py` — Prompt-based interactive shell (mode-aware prompt and behavior)
- `lynx/tui/app.py` — Textual terminal UI with progressive rendering (sections mount dynamically as data arrives), collapsible sections, About modal (F1), theme cycling (T)
- `lynx/tui/themes.py` — Custom Textual themes: lynx-dark, hacker, dracula, solarized, lynx-light
- `lynx/gui/app.py` — Tkinter graphical interface with progressive rendering (sections rendered via `root.after()` callbacks), collapsible sections, split Company Profile, logo branding, About dialog with logo

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
- Progressive analysis: All UIs use `run_progressive_analysis()` with callbacks. Display/render functions must handle `None` metric sections. The analyzer always sets a metric field before emitting its stage callback, but defensive `None` guards are required throughout.
- License: BSD 3-Clause. See `LICENSE` file and `lynx/__init__.py:LICENSE_TEXT`

## TUI Themes

The Textual UI supports multiple color themes. Press `T` to cycle through them:

- **lynx-dark** (default) — Catppuccin Mocha inspired, blue accents on dark background
- **hacker** — Classic green-on-black terminal aesthetic
- **dracula** — Purple/pink accents on dark background
- **solarized** — Solarized Dark color palette
- **lynx-light** — Light theme with blue accents
- **textual-dark** — Textual's built-in dark theme
- **textual-light** — Textual's built-in light theme

Custom themes are defined in `lynx/tui/themes.py`. To add a new theme, create a `Theme` object and add it to `CUSTOM_THEMES` and `THEME_NAMES`.

## TUI Keybindings

| Key | Action |
|-----|--------|
| `A` | Analyze a stock |
| `R` | Refresh current analysis |
| `T` | Cycle color theme |
| `e` | Context-aware explain: metric at cursor, section header, or conclusion methodology |
| `E` (Shift) | Browse all metric explanations |
| `I` | Same as `e` (explain focused item) |
| `X` | Export report (TXT/HTML/PDF) |
| `F1` | About dialog |
| `Q` | Quit |
| `Enter` | Download filing / open news article (in Filings/News sections) |
| `Escape` | Close modal / go back |

## GUI Layout

The graphical interface (Tkinter) uses collapsible sections:

- **Company Profile** is expanded by default with a split layout: key-value metrics on the left, business description on the right
- **Sector & Industry Insights** appear after the profile with contextual analysis guidance
- All other sections (Valuation, Profitability, etc.) start collapsed — click the header to expand
- Each section header has a `?` button that explains what the section covers
- **Financial Statements** P&L values are colored green (positive) / red (negative); currency is highlighted in yellow
- Use **Expand All** / **Collapse All** buttons in the toolbar to toggle all sections
- The **Keybindings** button (or **Ctrl+P**) shows keyboard shortcuts and controls
- Toolbar right side order: Collapse All, Expand All, About, Quit
- The Lynx logo (`img/logo_sm_quarter_green.png`) is shown in the toolbar
- The About dialog is centered on screen and includes a scrollable license text area
- Export success dialog shows a clickable file path with Open File / Open Folder buttons

## PDF Export

PDF export requires `weasyprint` as an optional dependency:

```bash
pip install weasyprint
```

If weasyprint is not installed, the CLI and all UIs show a clear error message with installation instructions. HTML and TXT exports always work without additional dependencies.

All exports (HTML, PDF) use a white background with dark text for maximum readability and print-friendliness, regardless of the application theme being used.

## Metric Explanations

Every metric in the report (P/E, ROE, Debt/Equity, etc.) has a detailed explanation accessible from all modes:

- **Console CLI**: `python3 lynx-fundamental.py --explain pe_trailing` or `python3 lynx-fundamental.py --explain` to list all
- **Interactive**: `explain pe_trailing` or `explain-all`
- **TUI**: Select a metric row and press `I`, or press `E` to browse all metrics
- **GUI**: Click the `?` button next to any metric

Each explanation includes: what it measures, the formula, why it matters in fundamental analysis, and general guidance on interpretation.

### Section Explanations

Each analysis section (Valuation, Profitability, Solvency, etc.) has an explanation of what it covers and why. Access via:

- **Console CLI**: `python3 lynx-fundamental.py --explain-section valuation`
- **Interactive**: `explain-section valuation`
- **TUI**: Press `e` while focused on a section header
- **GUI**: Click the `?` button on any section header

### Conclusion Methodology

The conclusion scoring methodology (how weights work per tier, how category scores are computed) is accessible:

- **Console CLI**: `python3 lynx-fundamental.py --explain-conclusion` or `--explain-conclusion valuation`
- **Interactive**: `explain-conclusion` or `explain-conclusion valuation`
- **TUI**: Press `e` while focused on a conclusion row
- **GUI**: Click the `?` button on the Assessment Conclusion section header

## Running the Program

Run directly from the project root:

```bash
python3 lynx-fundamental.py -p AAPL       # Production analysis
python3 lynx-fundamental.py -t AAPL       # Testing analysis
python3 lynx-fundamental.py -p -tui       # TUI mode
python3 lynx-fundamental.py -p -x         # GUI mode
python3 lynx-fundamental.py -p -i         # Interactive mode
```
