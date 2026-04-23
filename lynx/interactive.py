"""Interactive prompt-based mode for lynx-fundamental."""

from __future__ import annotations

try:
    import readline as _readline  # noqa: F401 — enables arrow-key history
except ImportError:
    pass  # readline unavailable on Windows; arrow keys won't navigate history

from rich.console import Console
from rich.panel import Panel
from rich.prompt import IntPrompt, Prompt
from rich.table import Table

from lynx_investor_core.pager import console_pager, paged_print
from lynx.core.analyzer import run_progressive_analysis
from lynx.core.news import download_article
from lynx.core.reports import download_filing
from lynx.display import display_full_report, display_report_stage
from lynx.models import AnalysisReport

console = Console()

BANNER = """
[bold blue]  L Y N X   Fundamental Analysis[/]
[dim]    Value Investing & Moat Analysis[/]
"""

MENU = """
[bold cyan]Analysis:[/]
  [bold]analyze[/] <TICKER|ISIN|NAME>   Analyze (uses cache in production mode)
  [bold]refresh[/] <TICKER|ISIN|NAME>   Force fresh data download
  [bold]search[/] <query>               Search for a company

[bold cyan]View data:[/]
  [bold]metrics[/]                      Show last analysis metrics
  [bold]filings[/]                      List SEC filings
  [bold]download-filing[/] <N>          Download filing #N
  [bold]news[/]                         Show recent news
  [bold]download-news[/] <N>            Download news article #N
  [bold]open-news[/] <N>                Open news article #N in browser
  [bold]summary[/]                      Show moat + intrinsic value summary
  [bold]export[/] <txt|html|pdf>        Export report to file

[bold cyan]Cache:[/]
  [bold]cache[/]                        List all cached tickers
  [bold]drop-cache[/] <TICKER>          Remove cached data for a ticker
  [bold]drop-cache all[/]               Remove all cached data

[bold cyan]Learn:[/]
  [bold]explain[/] <metric>             Explain a metric (e.g. explain pe_trailing)
  [bold]explain-all[/]                  List all metric explanations
  [bold]explain-section[/] <section>    Explain an analysis section
  [bold]explain-conclusion[/] \[category]  Explain conclusion methodology

[bold cyan]Other:[/]
  [bold]about[/]                        Show about, author, and license
  [bold]help[/]                         Show this menu
  [bold]quit[/]                         Exit
"""


def run_interactive() -> None:
    """Run the interactive prompt loop."""
    from lynx.core.storage import get_mode, is_testing

    console.print(BANNER)

    mode = get_mode()
    if is_testing():
        console.print(Panel(
            "[bold yellow]TESTING MODE[/]\n"
            "Data is stored in [bold]data_test/[/] — production data is never touched.\n"
            "All fetches are fresh (cache is not used).",
            border_style="yellow",
        ))
    else:
        console.print(Panel(
            "[bold green]PRODUCTION MODE[/]\n"
            "Data is stored in [bold]data/[/] — cached analyses are reused automatically.\n"
            "Use [bold]refresh[/] to force a fresh download.",
            border_style="green",
        ))

    console.print(Panel(MENU, border_style="cyan", title="[bold]Interactive Mode[/]"))

    current_report: AnalysisReport | None = None

    while True:
        prompt_color = "yellow" if is_testing() else "cyan"
        prompt_suffix = " [test]" if is_testing() else ""
        try:
            # Use input() instead of Rich Prompt.ask() so that the
            # readline module provides arrow-key command history.
            console.print(f"\n[bold {prompt_color}]lynx-fundamental{prompt_suffix}[/] ", end="")
            raw = input().strip()
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

        elif cmd == "explain":
            from lynx.metrics.explanations import get_explanation, list_metrics
            if not arg:
                console.print("[yellow]Usage: explain <metric_key>  (e.g. explain pe_trailing)[/]")
                console.print("[dim]Use 'explain-all' to see all available metrics.[/]")
                continue
            exp = get_explanation(arg.lower().replace("-", "_").replace(" ", "_"))
            if exp:
                console.print(Panel(
                    f"[bold]{exp.full_name}[/]\n\n"
                    f"{exp.description}\n\n"
                    f"[bold cyan]Why it matters:[/]\n{exp.why_used}\n\n"
                    f"[bold cyan]Formula:[/]\n[bold]{exp.formula}[/]\n\n"
                    f"[dim]Category: {exp.category}[/]",
                    title=f"[bold]{exp.key}[/]",
                    border_style="cyan",
                ))
            else:
                console.print(f"[red]Unknown metric '{arg}'.[/] Use 'explain-all' to see available metrics.")

        elif cmd == "explain-all":
            from lynx.metrics.explanations import list_metrics
            t = Table(title="Available Metrics", border_style="cyan")
            t.add_column("Key", style="bold cyan", min_width=22)
            t.add_column("Name", min_width=35)
            t.add_column("Category")
            for m in list_metrics():
                t.add_row(m.key, m.full_name, m.category)
            paged_print(console, t)
            console.print("[dim]Use 'explain <key>' for detailed explanation.[/]")

        elif cmd == "explain-section":
            from lynx.metrics.explanations import get_section_explanation, SECTION_EXPLANATIONS
            if not arg:
                # List available sections
                console.print("[bold]Available sections:[/]")
                for key, sec in SECTION_EXPLANATIONS.items():
                    console.print(f"  [bold cyan]{key:20s}[/] {sec['title']}")
                console.print("\n[dim]Use 'explain-section <key>' for details.[/]")
            else:
                sec = get_section_explanation(arg.lower().replace(" ", "_").replace("-", "_"))
                if sec:
                    console.print(Panel(
                        f"[bold]{sec['title']}[/]\n\n{sec['description']}",
                        title=f"[bold]{sec['title']}[/]",
                        border_style="cyan",
                    ))
                else:
                    console.print(f"[red]Unknown section '{arg}'.[/] Use 'explain-section' to list all.")

        elif cmd == "explain-conclusion":
            from lynx.metrics.explanations import get_conclusion_explanation, CONCLUSION_METHODOLOGY
            key = arg.lower().replace(" ", "_").replace("-", "_") if arg else "overall"
            ce = get_conclusion_explanation(key)
            if ce:
                console.print(Panel(
                    f"[bold]{ce['title']}[/]\n\n{ce['description']}",
                    title=f"[bold]{ce['title']}[/]",
                    border_style="cyan",
                ))
            else:
                console.print("[bold]Available conclusion categories:[/]")
                for k, v in CONCLUSION_METHODOLOGY.items():
                    console.print(f"  [bold cyan]{k:20s}[/] {v['title']}")
                console.print("\n[dim]Use 'explain-conclusion <category>' for details.[/]")

        elif cmd == "about":
            _show_about()

        elif cmd == "search":
            try:
                if not arg:
                    arg = Prompt.ask("[bold]Search query (company name, ticker, ISIN)[/]")
            except (EOFError, KeyboardInterrupt):
                console.print("[dim]Cancelled.[/]")
                continue
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
            force_refresh = (cmd == "refresh") or is_testing()
            try:
                if not arg:
                    arg = Prompt.ask("[bold]Enter ticker, ISIN, or company name[/]")
            except (EOFError, KeyboardInterrupt):
                console.print("[dim]Cancelled.[/]")
                continue
            if not arg:
                console.print("[red]No identifier provided.[/]")
                continue
            try:
                current_report = run_progressive_analysis(
                    identifier=arg,
                    download_reports=True,
                    download_news=True,
                    refresh=force_refresh,
                    on_progress=display_report_stage,
                )
            except ValueError as e:
                console.print(f"[bold red]Error:[/] {e}")
            except (ConnectionError, TimeoutError, OSError) as e:
                console.print(f"[bold red]Network error:[/] {e}")
                console.print("[dim]Check your connection and try again.[/]")
            except KeyboardInterrupt:
                console.print("[dim]Analysis cancelled.[/]")
            except Exception as e:
                console.print(f"[bold red]Unexpected error:[/] {type(e).__name__}: {e}")

        elif cmd == "metrics":
            if not current_report:
                console.print("[yellow]No analysis loaded. Run 'analyze <TICKER>' first.[/]")
            else:
                with console_pager(console):
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
            except (ValueError, TypeError):
                console.print("[red]Provide a valid number.[/]")
            except (EOFError, KeyboardInterrupt):
                console.print("[dim]Cancelled.[/]")

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
            except (ValueError, TypeError):
                console.print("[red]Provide a valid number.[/]")
            except (EOFError, KeyboardInterrupt):
                console.print("[dim]Cancelled.[/]")

        elif cmd == "open-news":
            if not current_report or not current_report.news:
                console.print("[yellow]No news available.[/]")
                continue
            try:
                idx = int(arg) - 1 if arg else IntPrompt.ask("Article number") - 1
                if 0 <= idx < len(current_report.news):
                    art = current_report.news[idx]
                    if art.url:
                        from lynx_investor_core.urlsafe import safe_webbrowser_open
                        if safe_webbrowser_open(art.url):
                            console.print(
                                f"[green]Opened in browser:[/] {art.title[:60]}"
                            )
                        else:
                            console.print("[red]Refused: unsafe URL[/]")
                    else:
                        console.print("[red]No URL available for this article.[/]")
                else:
                    console.print(f"[red]Invalid index. Choose 1-{len(current_report.news)}[/]")
            except (ValueError, TypeError):
                console.print("[red]Provide a valid number.[/]")
            except (EOFError, KeyboardInterrupt):
                console.print("[dim]Cancelled.[/]")

        elif cmd == "summary":
            if not current_report:
                console.print("[yellow]No analysis loaded.[/]")
            else:
                from lynx.display import _display_moat, _display_intrinsic_value
                _display_moat(current_report)
                _display_intrinsic_value(current_report)

        elif cmd == "export":
            if not current_report:
                console.print("[yellow]No analysis loaded. Run 'analyze <TICKER>' first.[/]")
                continue
            fmt = arg.lower() if arg else ""
            if fmt not in ("txt", "html", "pdf"):
                console.print("[yellow]Usage: export <txt|html|pdf>[/]")
                continue
            try:
                from lynx.export import ExportFormat, export_report
                path = export_report(current_report, ExportFormat(fmt))
                console.print(f"[bold green]Exported to:[/] {path}")
            except RuntimeError as e:
                console.print(f"[bold red]Export failed:[/] {e}")
            except Exception as e:
                console.print(f"[bold red]Error:[/] {type(e).__name__}: {e}")

        elif cmd == "cache":
            _show_cache()

        elif cmd == "drop-cache":
            try:
                if not arg:
                    arg = Prompt.ask("[bold]Ticker to drop (or 'all')[/]")
            except (EOFError, KeyboardInterrupt):
                console.print("[dim]Cancelled.[/]")
                continue
            if not arg:
                console.print("[red]No ticker provided.[/]")
                continue
            _drop_cache(arg)

        elif cmd == "matrix":
            from lynx.easter import rich_matrix
            rich_matrix(console)

        elif cmd == "fortune":
            from lynx.easter import rich_fortune
            rich_fortune(console)

        elif cmd == "rocket":
            from lynx.easter import rich_rocket
            rich_rocket(console)

        elif cmd == "lynx":
            from lynx.easter import rich_lynx
            rich_lynx(console)

        else:
            console.print(f"[dim]Unknown command '{cmd}'. Trying as ticker...[/]")
            try:
                force = is_testing()
                current_report = run_progressive_analysis(
                    identifier=raw, refresh=force,
                    on_progress=display_report_stage,
                )
            except ValueError as e:
                console.print(f"[red]Could not resolve '{raw}':[/] {e}")
                console.print("[dim]Type 'help' for available commands.[/]")
            except (ConnectionError, TimeoutError, OSError) as e:
                console.print(f"[bold red]Network error:[/] {e}")
            except KeyboardInterrupt:
                console.print("[dim]Cancelled.[/]")
            except Exception as e:
                console.print(f"[red]Error:[/] {type(e).__name__}: {e}")
                console.print("[dim]Type 'help' for available commands.[/]")


def _show_cache() -> None:
    from lynx.core.storage import list_cached_tickers, get_mode

    tickers = list_cached_tickers()
    if not tickers:
        console.print(f"[yellow]No cached data ({get_mode()} mode).[/]")
        return

    t = Table(title=f"Cached Data ({get_mode()} mode)", border_style="cyan")
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


def _show_about() -> None:
    from lynx import get_about_text, get_logo_ascii

    about = get_about_text()
    logo = get_logo_ascii()
    console.print()
    if logo:
        console.print(Panel(
            f"[green]{logo}[/]",
            border_style="green",
        ))
    console.print(Panel(
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
    console.print(Panel(
        about["license_text"],
        title="[bold]BSD 3-Clause License[/]",
        border_style="dim",
    ))


def _drop_cache(target: str) -> None:
    from lynx.core.storage import drop_cache_all, drop_cache_ticker, get_mode

    label = f"({get_mode()} mode)"
    if target.lower() == "all":
        count = drop_cache_all()
        console.print(f"[bold green]Removed all cached data {label} ({count} tickers).[/]")
    else:
        if drop_cache_ticker(target):
            console.print(f"[bold green]Removed cached data for {target.upper()} {label}.[/]")
        else:
            console.print(f"[yellow]No cached data found for '{target.upper()}' {label}.[/]")
