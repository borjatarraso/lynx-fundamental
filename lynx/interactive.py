"""Interactive prompt-based mode for Lynx FA."""

from __future__ import annotations

import sys

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, IntPrompt
from rich.table import Table

from lynx.core.analyzer import run_full_analysis
from lynx.core.news import download_article
from lynx.core.reports import download_filing
from lynx.display import display_full_report
from lynx.models import AnalysisReport

console = Console()

BANNER = """
[bold blue]
  ╦  ╦ ╔╗╔ ╦ ╦  ═╗═╗
  ║  ╚╦╝║║║  ╠╣  ╠╣╠╣
  ╩═╝ ╩ ╝╚╝ ╩ ╩ ╩ ╩ ╩
[/]
[bold]Fundamental Analysis Tool[/]
[dim]Value Investing & Moat Analysis[/]
"""

MENU = """
[bold cyan]Analysis:[/]
  [bold]analyze[/] <TICKER|ISIN|NAME>  Analyze (uses cached data if available)
  [bold]refresh[/] <TICKER|ISIN|NAME>  Force fresh data download
  [bold]search[/] <query>              Search for a company

[bold cyan]View data:[/]
  [bold]metrics[/]                     Show last analysis metrics
  [bold]filings[/]                     List SEC filings
  [bold]download-filing[/] <N>         Download filing #N
  [bold]news[/]                        Show recent news
  [bold]download-news[/] <N>           Download news article #N
  [bold]summary[/]                     Show moat + intrinsic value summary
  [bold]export[/]                      Show data export path

[bold cyan]Cache:[/]
  [bold]cache[/]                       List all cached tickers
  [bold]drop-cache[/] <TICKER>         Remove cached data for a ticker
  [bold]drop-cache all[/]              Remove all cached data

[bold cyan]Other:[/]
  [bold]help[/]                        Show this menu
  [bold]quit[/]                        Exit

[dim]Tip: You can use tickers like OCO.V (TSXV), AT1.DE (XETRA), ORRCF (OTC),
     or just type a company name like 'Oroco Resource Corp'.[/]
"""


def run_interactive() -> None:
    """Run the interactive prompt loop."""
    console.print(BANNER)
    console.print(Panel(MENU, border_style="cyan", title="[bold]Interactive Mode[/]"))

    current_report: AnalysisReport | None = None

    while True:
        try:
            raw = Prompt.ask("\n[bold cyan]lynx-fa[/]").strip()
        except (EOFError, KeyboardInterrupt):
            console.print("\n[dim]Goodbye![/]")
            break

        if not raw:
            continue

        parts = raw.split(maxsplit=1)
        cmd = parts[0].lower()
        arg = parts[1].strip() if len(parts) > 1 else ""

        if cmd in ("quit", "exit", "q"):
            console.print("[dim]Goodbye![/]")
            break

        elif cmd == "help":
            console.print(MENU)

        elif cmd == "search":
            if not arg:
                arg = Prompt.ask("[bold]Search query (company name, ticker, ISIN)[/]")
            if not arg:
                console.print("[red]No query provided.[/]")
                continue
            from lynx.core.ticker import search_companies, display_search_results
            results = search_companies(arg, max_results=10)
            if results:
                display_search_results(results)
                console.print("[dim]Use 'analyze <SYMBOL>' with a symbol from above.[/]")
            else:
                console.print(f"[yellow]No results for '{arg}'.[/]")

        elif cmd in ("analyze", "refresh"):
            force_refresh = cmd == "refresh"
            if not arg:
                arg = Prompt.ask("[bold]Enter ticker, ISIN, or company name[/]")
            if not arg:
                console.print("[red]No identifier provided.[/]")
                continue
            try:
                current_report = run_full_analysis(
                    identifier=arg,
                    download_reports=True,
                    download_news=True,
                    refresh=force_refresh,
                )
                display_full_report(current_report)
            except ValueError as e:
                console.print(f"[bold red]Error:[/] {e}")
            except Exception as e:
                console.print(f"[bold red]Unexpected error:[/] {e}")

        elif cmd == "metrics":
            if not current_report:
                console.print("[yellow]No analysis loaded. Run 'analyze <TICKER>' first.[/]")
            else:
                display_full_report(current_report)

        elif cmd == "filings":
            if not current_report or not current_report.filings:
                console.print("[yellow]No filings available. Run 'analyze <TICKER>' first.[/]")
            else:
                from lynx.display import _display_filings
                _display_filings(current_report)

        elif cmd == "download-filing":
            if not current_report or not current_report.filings:
                console.print("[yellow]No filings available.[/]")
                continue
            try:
                idx = int(arg) - 1 if arg else IntPrompt.ask("Filing number") - 1
                if 0 <= idx < len(current_report.filings):
                    f = current_report.filings[idx]
                    console.print(f"[cyan]Downloading {f.form_type} ({f.filing_date})...[/]")
                    path = download_filing(current_report.profile.ticker, f)
                    if path:
                        console.print(f"[green]Saved to:[/] {path}")
                    else:
                        console.print("[red]Download failed.[/]")
                else:
                    console.print(f"[red]Invalid index. Choose 1-{len(current_report.filings)}[/]")
            except ValueError:
                console.print("[red]Provide a valid number.[/]")

        elif cmd == "news":
            if not current_report or not current_report.news:
                console.print("[yellow]No news available. Run 'analyze <TICKER>' first.[/]")
            else:
                from lynx.display import _display_news
                _display_news(current_report)

        elif cmd == "download-news":
            if not current_report or not current_report.news:
                console.print("[yellow]No news available.[/]")
                continue
            try:
                idx = int(arg) - 1 if arg else IntPrompt.ask("Article number") - 1
                if 0 <= idx < len(current_report.news):
                    art = current_report.news[idx]
                    console.print(f"[cyan]Downloading: {art.title[:60]}...[/]")
                    path = download_article(current_report.profile.ticker, art)
                    if path:
                        console.print(f"[green]Saved to:[/] {path}")
                    else:
                        console.print("[red]Download failed.[/]")
                else:
                    console.print(f"[red]Invalid index. Choose 1-{len(current_report.news)}[/]")
            except ValueError:
                console.print("[red]Provide a valid number.[/]")

        elif cmd == "summary":
            if not current_report:
                console.print("[yellow]No analysis loaded.[/]")
            else:
                from lynx.display import _display_moat, _display_intrinsic_value
                _display_moat(current_report)
                _display_intrinsic_value(current_report)

        elif cmd == "export":
            if not current_report:
                console.print("[yellow]No analysis loaded.[/]")
            else:
                from lynx.core.storage import get_company_dir
                d = get_company_dir(current_report.profile.ticker)
                console.print(f"[green]Data directory:[/] {d}")

        elif cmd == "cache":
            _show_cache()

        elif cmd == "drop-cache":
            if not arg:
                arg = Prompt.ask("[bold]Ticker to drop (or 'all')[/]")
            if not arg:
                console.print("[red]No ticker provided.[/]")
                continue
            _drop_cache(arg)

        else:
            # Try treating the entire input as a ticker
            console.print(f"[dim]Unknown command '{cmd}'. Trying as ticker...[/]")
            try:
                current_report = run_full_analysis(identifier=raw)
                display_full_report(current_report)
            except Exception:
                console.print("[red]Unknown command. Type 'help' for available commands.[/]")


def _show_cache() -> None:
    from lynx.core.storage import list_cached_tickers

    tickers = list_cached_tickers()
    if not tickers:
        console.print("[yellow]No cached data.[/]")
        return

    t = Table(title="Cached Data", border_style="cyan")
    t.add_column("Ticker", style="bold cyan")
    t.add_column("Company")
    t.add_column("Tier")
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
            age_str,
            str(info.get("files", 0)),
            f"{info.get('size_mb', 0):.1f}MB",
        )

    console.print(t)


def _drop_cache(target: str) -> None:
    from lynx.core.storage import drop_cache_all, drop_cache_ticker

    if target.lower() == "all":
        count = drop_cache_all()
        console.print(f"[bold green]Removed all cached data ({count} tickers).[/]")
    else:
        if drop_cache_ticker(target):
            console.print(f"[bold green]Removed cached data for {target.upper()}.[/]")
        else:
            console.print(f"[yellow]No cached data found for '{target.upper()}'.[/]")
