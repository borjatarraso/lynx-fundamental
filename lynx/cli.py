"""Command-line interface for Lynx FA."""

from __future__ import annotations

import argparse
import sys

from lynx import __author__, __version__, __year__


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="lynx-fa",
        description=(
            "Lynx Fundamental Analysis — Value investing research tool.\n"
            "Fetch, calculate, and display fundamental metrics, SEC filings,\n"
            "and news for any publicly traded company by ticker or ISIN."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  lynx-fa AAPL                         Analyze (uses cache if available)\n"
            "  lynx-fa AAPL --refresh                Force fresh data download\n"
            "  lynx-fa MSFT --no-reports             Skip downloading SEC filings\n"
            "  lynx-fa OCO.V                         Analyze TSXV stock\n"
            '  lynx-fa "Oroco Resource"              Search by company name\n'
            "  lynx-fa -s AT1                        Search for AT1 across exchanges\n"
            "  lynx-fa --list-cache                  Show all cached tickers\n"
            "  lynx-fa --drop-cache AAPL             Remove cached data for AAPL\n"
            "  lynx-fa --drop-cache ALL              Remove all cached data\n"
            "  lynx-fa -i                            Launch interactive mode\n"
            "  lynx-fa -tui                          Launch Textual UI\n"
        ),
    )

    parser.add_argument(
        "identifier",
        nargs="?",
        help="Ticker symbol (e.g. AAPL) or ISIN (e.g. US0378331005)",
    )

    # Mode flags
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "-i", "--interactive-mode",
        action="store_true",
        dest="interactive",
        help="Launch interactive prompt mode",
    )
    mode.add_argument(
        "-tui", "--textual-ui",
        action="store_true",
        dest="tui",
        help="Launch the Textual terminal UI",
    )
    mode.add_argument(
        "-s", "--search",
        action="store_true",
        help="Search for a company (use with identifier as query)",
    )

    # Data / cache options
    parser.add_argument(
        "--refresh",
        action="store_true",
        help="Force fresh data download (ignore cache)",
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

    # Analysis options
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
    parser.add_argument(
        "--max-filings",
        type=int,
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

    return parser


def run_cli() -> None:
    """Parse arguments and dispatch to the appropriate mode."""
    parser = build_parser()
    args = parser.parse_args()

    from rich.console import Console
    errc = Console(stderr=True)

    # --- Cache management commands ---
    if args.list_cache:
        _cmd_list_cache(errc)
        return

    if args.drop_cache is not None:
        target = args.drop_cache
        if target == "__prompt__":
            # --drop-cache was used without a value; use identifier if provided
            target = args.identifier or ""
        if not target:
            errc.print("[bold red]Error:[/] Specify a ticker or ALL. E.g. --drop-cache AAPL")
            sys.exit(1)
        _cmd_drop_cache(errc, target)
        return

    # --- Mode dispatch ---
    if args.interactive:
        from lynx.interactive import run_interactive
        run_interactive()
        return

    if args.tui:
        from lynx.tui.app import run_tui
        run_tui()
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
    from lynx.core.analyzer import run_full_analysis
    from lynx.display import display_full_report

    try:
        report = run_full_analysis(
            identifier=args.identifier,
            download_reports=not args.no_reports,
            download_news=not args.no_news,
            max_filings=args.max_filings,
            verbose=args.verbose,
            refresh=args.refresh,
        )
        display_full_report(report)
    except ValueError as e:
        errc.print(f"[bold red]Error:[/] {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nAborted.")
        sys.exit(130)


# ---- Cache CLI helpers ----

def _cmd_list_cache(con) -> None:
    from rich.table import Table
    from lynx.core.storage import list_cached_tickers

    tickers = list_cached_tickers()
    if not tickers:
        con.print("[yellow]No cached data found.[/]")
        return

    t = Table(title="Cached Data", border_style="cyan")
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


def _cmd_drop_cache(con, target: str) -> None:
    from lynx.core.storage import drop_cache_all, drop_cache_ticker

    if target.upper() == "ALL":
        count = drop_cache_all()
        con.print(f"[bold green]Removed all cached data ({count} tickers).[/]")
    else:
        if drop_cache_ticker(target):
            con.print(f"[bold green]Removed cached data for {target.upper()}.[/]")
        else:
            con.print(f"[yellow]No cached data found for '{target.upper()}'.[/]")
