"""Plaintext export — captures Rich console output to a file."""

from __future__ import annotations

from pathlib import Path

from rich.console import Console

from lynx.models import AnalysisReport


def export_txt(report: AnalysisReport, output_path: Path) -> Path:
    """Export report as plain text using Rich console capture."""
    from lynx.display import display_full_report

    console = Console(file=open(output_path, "w", encoding="utf-8"),
                      force_terminal=False, width=120, no_color=True)

    # Temporarily replace the display module's console
    import lynx.display as disp
    original_console = disp.console
    disp.console = console

    try:
        display_full_report(report)
    finally:
        disp.console = original_console
        console.file.close()

    return output_path
