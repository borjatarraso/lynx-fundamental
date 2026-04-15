"""Command-line interface for Lynx FA."""

from __future__ import annotations

import argparse
import sys

from lynx import __author__, __author_email__, __license__, __version__, __year__


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="lynx-fa",
        description=(
            "Lynx Fundamental Analysis — Value investing research tool.\n"
            "Fetch, calculate, and display fundamental metrics, SEC filings,\n"
            "and news for any publicly traded company by ticker or ISIN.\n\n"
            "One of --production-mode (-p) or --testing-mode (-t) is required."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  lynx-fa -p AAPL                       Production analysis (uses cache)\n"
            "  lynx-fa -p AAPL --refresh              Force fresh data download\n"
            "  lynx-fa -t AAPL                        Testing analysis (fresh, isolated)\n"
            "  lynx-fa -p OCO.V                       Analyze TSXV stock\n"
            '  lynx-fa -p "Oroco Resource"            Search by company name\n'
            "  lynx-fa -p -s AT1                      Search for AT1 across exchanges\n"
            "  lynx-fa -p --list-cache                Show cached tickers\n"
            "  lynx-fa -p --drop-cache AAPL           Remove cached data for AAPL\n"
            "  lynx-fa -p --drop-cache ALL            Remove all cached data\n"
            "  lynx-fa -t --drop-cache ALL            Remove all test data\n"
            "  lynx-fa -p -i                          Interactive mode (production)\n"
            "  lynx-fa -t -i                          Interactive mode (testing)\n"
            "  lynx-fa -p -tui                        Textual UI (production)\n"
            "  lynx-fa -p -x                          Graphical UI (production)\n"
            "  lynx-fa -p -x AAPL                     Graphical UI with pre-filled ticker\n"
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

    parser.add_argument(
        "identifier",
        nargs="?",
        help="Ticker symbol (e.g. AAPL) or ISIN (e.g. US0378331005)",
    )

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
        "--version",
        action="version",
        version=f"%(prog)s {__version__} ({__year__}) by {__author__}",
    )
    parser.add_argument(
        "--about",
        action="store_true",
        help="Show about information, author, and license",
    )

    return parser


def run_cli() -> None:
    """Parse arguments and dispatch to the appropriate mode."""
    parser = build_parser()

    # Allow --about and --version without requiring -p/-t
    if "--about" in sys.argv:
        from rich.console import Console
        _cmd_about(Console(stderr=True))
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

    from lynx.core.analyzer import run_full_analysis
    from lynx.display import display_full_report

    try:
        report = run_full_analysis(
            identifier=args.identifier,
            download_reports=not args.no_reports,
            download_news=not args.no_news,
            max_filings=args.max_filings,
            verbose=args.verbose,
            refresh=refresh,
        )
        display_full_report(report)
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


def _cmd_about(con) -> None:
    from rich.panel import Panel
    from lynx import get_about_text

    about = get_about_text()
    con.print()
    con.print(Panel(
        f"[bold blue]{about['name']}[/]\n"
        f"[dim]Version {about['version']} ({about['year']})[/]\n\n"
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
