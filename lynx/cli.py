"""Command-line interface for lynx-fundamental."""

from __future__ import annotations

import argparse
import sys

from lynx import __author__, __author_email__, __license__, __version__, __year__, SUITE_LABEL


def _ticker_completer(prefix, **kw):
    """Dynamic completer that returns cached tickers for this agent's mode."""
    try:
        from lynx_investor_core.storage import list_cached_tickers
        items = list_cached_tickers() or []
        return [t["ticker"] for t in items if t["ticker"].startswith(prefix.upper())]
    except Exception:
        return []


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="lynx-fundamental",
        description=(
            "Lynx Fundamental Analysis — Value investing research tool.\n"
            "Fetch, calculate, and display fundamental metrics, SEC filings,\n"
            "and news for any publicly traded company by ticker or ISIN.\n\n"
            "One of --production-mode (-p) or --testing-mode (-t) is required."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  lynx-fundamental -p AAPL                       Production analysis (uses cache)\n"
            "  lynx-fundamental -p AAPL --refresh              Force fresh data download\n"
            "  lynx-fundamental -t AAPL                        Testing analysis (fresh, isolated)\n"
            "  lynx-fundamental -p OCO.V                       Analyze TSXV stock\n"
            '  lynx-fundamental -p "Oroco Resource"            Search by company name\n'
            "  lynx-fundamental -p -s AT1                      Search for AT1 across exchanges\n"
            "  lynx-fundamental -p --list-cache                Show cached tickers\n"
            "  lynx-fundamental -p --drop-cache AAPL           Remove cached data for AAPL\n"
            "  lynx-fundamental -p --drop-cache ALL            Remove all cached data\n"
            "  lynx-fundamental -t --drop-cache ALL            Remove all test data\n"
            "  lynx-fundamental -p -i                          Interactive mode (production)\n"
            "  lynx-fundamental -t -i                          Interactive mode (testing)\n"
            "  lynx-fundamental -p -tui                        Textual UI (production)\n"
            "  lynx-fundamental -p -x                          Graphical UI (production)\n"
            "  lynx-fundamental -p -x AAPL                     Graphical UI with pre-filled ticker\n"
        ),
    )

    # --- Required: execution mode ---
    run_mode = parser.add_mutually_exclusive_group(required=True)
    run_mode.add_argument(
        "-p", "--production-mode",
        action="store_const",
        const="production",
        dest="run_mode",
        help="Production mode: use data/ for persistent cache and storage",
    )
    run_mode.add_argument(
        "-t", "--testing-mode",
        action="store_const",
        const="testing",
        dest="run_mode",
        help="Testing mode: use data_test/ (isolated, always fresh, never touches production data)",
    )

    ident_arg = parser.add_argument(
        "identifier",
        nargs="?",
        help="Ticker symbol (e.g. AAPL) or ISIN (e.g. US0378331005)",
    )
    ident_arg.completer = _ticker_completer

    # --- Interface mode ---
    ui_mode = parser.add_mutually_exclusive_group()
    ui_mode.add_argument(
        "-i", "--interactive-mode",
        action="store_true",
        dest="interactive",
        help="Launch interactive prompt mode",
    )
    ui_mode.add_argument(
        "-tui", "--textual-ui",
        action="store_true",
        dest="tui",
        help="Launch the Textual terminal UI",
    )
    ui_mode.add_argument(
        "-s", "--search",
        action="store_true",
        help="Search for a company (use with identifier as query)",
    )
    ui_mode.add_argument(
        "-x", "--gui",
        action="store_true",
        help="Launch the graphical user interface (Tkinter)",
    )

    # --- Data / cache options ---
    parser.add_argument(
        "--refresh",
        action="store_true",
        help="Force fresh data download (ignore cache, production mode only)",
    )
    parser.add_argument(
        "--drop-cache",
        metavar="TICKER",
        nargs="?",
        const="__prompt__",
        help="Remove cached data for TICKER, or ALL to clear everything",
    )
    parser.add_argument(
        "--list-cache",
        action="store_true",
        help="List all cached tickers and their data age",
    )

    # --- Analysis options ---
    parser.add_argument(
        "--no-reports",
        action="store_true",
        help="Skip fetching/downloading SEC filings",
    )
    parser.add_argument(
        "--no-news",
        action="store_true",
        help="Skip fetching news articles",
    )
    def _positive_int(value: str) -> int:
        n = int(value)
        if n <= 0:
            raise argparse.ArgumentTypeError(f"{value} is not a positive integer")
        return n

    parser.add_argument(
        "--max-filings",
        type=_positive_int,
        default=10,
        metavar="N",
        help="Maximum number of filings to download (default: 10)",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output",
    )
    parser.add_argument(
        "--export",
        choices=["txt", "html", "pdf"],
        metavar="FORMAT",
        help="Export report to file (txt, html, or pdf)",
    )
    parser.add_argument(
        "--output",
        metavar="PATH",
        help="Output file path for export (default: auto-generated in data dir)",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}  |  {SUITE_LABEL}  ({__year__}) by {__author__}",
    )
    parser.add_argument(
        "--about",
        action="store_true",
        help="Show about information, author, and license",
    )
    parser.add_argument(
        "--explain",
        metavar="METRIC",
        nargs="?",
        const="__list__",
        help="Explain a metric (e.g. --explain pe_trailing). Use without argument to list all.",
    )
    parser.add_argument(
        "--explain-section",
        metavar="SECTION",
        nargs="?",
        const="__list__",
        help="Explain an analysis section (e.g. --explain-section valuation). Use without argument to list all.",
    )
    parser.add_argument(
        "--explain-conclusion",
        metavar="CATEGORY",
        nargs="?",
        const="overall",
        help="Explain conclusion scoring methodology (overall, valuation, profitability, solvency, growth, moat).",
    )

    return parser


def run_cli() -> None:
    """Parse arguments and dispatch to the appropriate mode."""
    parser = build_parser()

    try:
        import argcomplete
        argcomplete.autocomplete(parser)
    except ImportError:
        pass  # argcomplete optional at runtime

    # Hidden features
    if "--b2m" in sys.argv:
        from rich.console import Console
        from lynx.easter import rich_rocket, rich_fortune
        c = Console()
        rich_rocket(c)
        rich_fortune(c)
        return

    # Allow --about, --explain, and --version without requiring -p/-t
    if "--about" in sys.argv:
        from rich.console import Console
        _cmd_about(Console(stderr=True))
        return

    if "--explain-section" in sys.argv:
        from rich.console import Console
        idx = sys.argv.index("--explain-section")
        section = sys.argv[idx + 1] if idx + 1 < len(sys.argv) and not sys.argv[idx + 1].startswith("-") else None
        _cmd_explain_section(Console(stderr=True), section)
        return

    if "--explain-conclusion" in sys.argv:
        from rich.console import Console
        idx = sys.argv.index("--explain-conclusion")
        cat = sys.argv[idx + 1] if idx + 1 < len(sys.argv) and not sys.argv[idx + 1].startswith("-") else "overall"
        _cmd_explain_conclusion(Console(stderr=True), cat)
        return

    if "--explain" in sys.argv:
        from rich.console import Console
        idx = sys.argv.index("--explain")
        metric = sys.argv[idx + 1] if idx + 1 < len(sys.argv) and not sys.argv[idx + 1].startswith("-") else None
        _cmd_explain(Console(stderr=True), metric)
        return

    args = parser.parse_args()

    from rich.console import Console
    errc = Console(stderr=True)

    # --- Activate storage mode FIRST, before any data access ---
    from lynx.core.storage import set_mode, is_testing
    set_mode(args.run_mode)

    mode_label = "[bold green]PRODUCTION[/]" if args.run_mode == "production" else "[bold yellow]TESTING[/]"
    errc.print(f"Mode: {mode_label}")

    # --- Cache management commands ---
    if args.list_cache:
        _cmd_list_cache(errc)
        return

    if args.drop_cache is not None:
        target = args.drop_cache
        if target == "__prompt__":
            target = args.identifier or ""
        if not target:
            errc.print("[bold red]Error:[/] Specify a ticker or ALL. E.g. --drop-cache AAPL")
            sys.exit(1)
        _cmd_drop_cache(errc, target)
        return

    # --- Interface dispatch ---
    if args.interactive:
        from lynx.interactive import run_interactive
        run_interactive()
        return

    if args.tui:
        from lynx.tui.app import run_tui
        run_tui()
        return

    if args.gui:
        from lynx.gui.app import run_gui
        run_gui(args)
        return

    if args.search:
        if not args.identifier:
            errc.print("[bold red]Error:[/] Provide a search query.")
            sys.exit(1)
        from lynx.core.ticker import search_companies, display_search_results
        results = search_companies(args.identifier, max_results=15)
        if results:
            display_search_results(results)
        else:
            errc.print(f"[yellow]No results for '{args.identifier}'.[/]")
        return

    if not args.identifier:
        parser.print_help()
        sys.exit(1)

    # --- Direct CLI analysis ---
    # In testing mode: always fresh (refresh is implicit)
    refresh = args.refresh or is_testing()

    from lynx.core.analyzer import run_progressive_analysis
    from lynx.display import display_report_stage

    try:
        report = run_progressive_analysis(
            identifier=args.identifier,
            download_reports=not args.no_reports,
            download_news=not args.no_news,
            max_filings=args.max_filings,
            verbose=args.verbose,
            refresh=refresh,
            on_progress=display_report_stage,
        )

        if args.export:
            from pathlib import Path
            from lynx.export import ExportFormat, export_report
            fmt = ExportFormat(args.export)
            out = Path(args.output) if args.output else None
            try:
                path = export_report(report, fmt, out)
                errc.print(f"[bold green]Exported to:[/] {path}")
            except RuntimeError as e:
                errc.print(f"[bold red]Export failed:[/] {e}")
    except ValueError as e:
        errc.print(f"[bold red]Error:[/] {e}")
        sys.exit(1)
    except (ConnectionError, TimeoutError, OSError) as e:
        errc.print(f"[bold red]Network error:[/] {e}")
        errc.print("[dim]Check your internet connection and try again.[/]")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nAborted.")
        sys.exit(130)
    except Exception as e:
        errc.print(f"[bold red]Unexpected error:[/] {type(e).__name__}: {e}")
        sys.exit(1)


# ---- Cache CLI helpers ----

def _cmd_list_cache(con) -> None:
    from rich.table import Table
    from lynx.core.storage import list_cached_tickers, get_mode

    tickers = list_cached_tickers()
    if not tickers:
        con.print(f"[yellow]No cached data found ({get_mode()} mode).[/]")
        return

    title = f"Cached Data ({get_mode()} mode)"
    t = Table(title=title, border_style="cyan")
    t.add_column("Ticker", style="bold cyan")
    t.add_column("Company")
    t.add_column("Tier")
    t.add_column("Fetched At")
    t.add_column("Age", justify="right")
    t.add_column("Files", justify="right")
    t.add_column("Size", justify="right")

    for info in tickers:
        age = info.get("age_hours")
        if age is not None:
            if age < 1:
                age_str = f"{age * 60:.0f}m"
            elif age < 24:
                age_str = f"{age:.1f}h"
            else:
                age_str = f"{age / 24:.1f}d"
        else:
            age_str = "?"
        t.add_row(
            info["ticker"],
            info.get("name", ""),
            info.get("tier", ""),
            info.get("fetched_at", "")[:19],
            age_str,
            str(info.get("files", 0)),
            f"{info.get('size_mb', 0):.1f}MB",
        )

    con.print(t)
    con.print(f"[dim]Total: {len(tickers)} tickers cached[/]")


def _cmd_explain(con, metric: str | None) -> None:
    from rich.panel import Panel
    from rich.table import Table
    from lynx.metrics.explanations import get_explanation, list_metrics

    if metric is None or metric == "__list__":
        t = Table(title="Available Metrics", border_style="cyan")
        t.add_column("Key", style="bold cyan", min_width=22)
        t.add_column("Name", min_width=35)
        t.add_column("Category")
        for m in list_metrics():
            t.add_row(m.key, m.full_name, m.category)
        con.print(t)
        con.print("[dim]Use --explain <key> for detailed explanation.[/]")
        return

    key = metric.lower().replace("-", "_").replace(" ", "_")
    exp = get_explanation(key)
    if not exp:
        con.print(f"[red]Unknown metric '{metric}'.[/] Use --explain to list all metrics.")
        return

    con.print(Panel(
        f"[bold]{exp.full_name}[/]\n\n"
        f"{exp.description}\n\n"
        f"[bold cyan]Why it matters:[/]\n{exp.why_used}\n\n"
        f"[bold cyan]Formula:[/]\n[bold]{exp.formula}[/]\n\n"
        f"[dim]Category: {exp.category}[/]",
        title=f"[bold]{exp.key}[/]",
        border_style="cyan",
    ))


def _cmd_about(con) -> None:
    from rich.panel import Panel
    from lynx import get_about_text, get_logo_ascii

    about = get_about_text()
    logo = get_logo_ascii()
    con.print()
    if logo:
        con.print(Panel(
            f"[green]{logo}[/]",
            border_style="green",
        ))
    con.print(Panel(
        f"[bold blue]{about['name']} v{about['version']}[/]\n"
        f"[dim]Part of {about['suite']} v{about['suite_version']}[/]\n"
        f"[dim]Released {about['year']}[/]\n\n"
        f"[bold]Developed by:[/] {about['author']}\n"
        f"[bold]Contact:[/]      {about['email']}\n"
        f"[bold]License:[/]      {about['license']}\n\n"
        f"[dim]{about['description']}[/]",
        title="[bold]About[/]",
        border_style="blue",
    ))
    con.print(Panel(
        about["license_text"],
        title="[bold]BSD 3-Clause License[/]",
        border_style="dim",
    ))
    con.print()


def _cmd_explain_section(con, section: str | None) -> None:
    from rich.panel import Panel
    from rich.table import Table
    from lynx.metrics.explanations import get_section_explanation, SECTION_EXPLANATIONS

    if section is None or section == "__list__":
        t = Table(title="Analysis Sections", border_style="cyan")
        t.add_column("Key", style="bold cyan", min_width=18)
        t.add_column("Title", min_width=30)
        for key, sec in SECTION_EXPLANATIONS.items():
            t.add_row(key, sec["title"])
        con.print(t)
        con.print("[dim]Use --explain-section <key> for details.[/]")
        return

    key = section.lower().replace("-", "_").replace(" ", "_")
    sec = get_section_explanation(key)
    if not sec:
        con.print(f"[red]Unknown section '{section}'.[/] Use --explain-section to list all.")
        return

    con.print(Panel(
        f"[bold]{sec['title']}[/]\n\n{sec['description']}",
        title=f"[bold]{sec['title']}[/]",
        border_style="cyan",
    ))


def _cmd_explain_conclusion(con, category: str) -> None:
    from rich.panel import Panel
    from rich.table import Table
    from lynx.metrics.explanations import get_conclusion_explanation, CONCLUSION_METHODOLOGY

    key = category.lower().replace("-", "_").replace(" ", "_") if category else "overall"
    ce = get_conclusion_explanation(key)
    if ce:
        con.print(Panel(
            f"[bold]{ce['title']}[/]\n\n{ce['description']}",
            title=f"[bold]{ce['title']}[/]",
            border_style="cyan",
        ))
    else:
        t = Table(title="Conclusion Categories", border_style="cyan")
        t.add_column("Key", style="bold cyan", min_width=18)
        t.add_column("Title", min_width=30)
        for k, v in CONCLUSION_METHODOLOGY.items():
            t.add_row(k, v["title"])
        con.print(t)
        con.print("[dim]Use --explain-conclusion <key> for details.[/]")


def _cmd_drop_cache(con, target: str) -> None:
    from lynx.core.storage import drop_cache_all, drop_cache_ticker, get_mode

    label = f"({get_mode()} mode)"
    if target.upper() == "ALL":
        count = drop_cache_all()
        con.print(f"[bold green]Removed all cached data {label} ({count} tickers).[/]")
    else:
        if drop_cache_ticker(target):
            con.print(f"[bold green]Removed cached data for {target.upper()} {label}.[/]")
        else:
            con.print(f"[yellow]No cached data found for '{target.upper()}' {label}.[/]")
