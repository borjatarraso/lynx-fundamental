"""Plaintext export — captures Rich console output to a file."""

from __future__ import annotations

from pathlib import Path

from rich.console import Console

from lynx.models import AnalysisReport


def export_txt(report: AnalysisReport, output_path: Path) -> Path:
    """Export report as plain text using Rich console capture."""
    from lynx.display import display_full_report
    import lynx.display as disp

    f = open(output_path, "w", encoding="utf-8")
    try:
        console = Console(file=f, force_terminal=False, width=90, no_color=True)
        original_console = disp.console
        disp.console = console
        try:
            display_full_report(report)
        finally:
            disp.console = original_console

        # Author / signature footer (every Suite export carries it).
        try:
            from lynx_investor_core.author_footer import text_footer
            from lynx import SUITE_LABEL
            f.write(text_footer(SUITE_LABEL))
        except ImportError:
            pass
    finally:
        f.close()

    return output_path
