"""Export package — generate analysis reports in TXT, HTML, and PDF formats."""

from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Optional

from lynx.models import AnalysisReport


class ExportFormat(str, Enum):
    TXT = "txt"
    HTML = "html"
    PDF = "pdf"


def export_report(
    report: AnalysisReport,
    fmt: ExportFormat,
    output_path: Optional[Path] = None,
) -> Path:
    """Export an analysis report to the specified format.

    If output_path is not specified, saves to the company's data directory.
    Returns the path to the exported file.
    """
    from lynx.core.storage import get_company_dir
    from datetime import datetime

    if output_path is None:
        d = get_company_dir(report.profile.ticker)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = d / f"report_{ts}.{fmt.value}"

    output_path.parent.mkdir(parents=True, exist_ok=True)

    if fmt == ExportFormat.TXT:
        from lynx.export.txt_export import export_txt
        return export_txt(report, output_path)
    elif fmt == ExportFormat.HTML:
        from lynx.export.html_export import export_html
        return export_html(report, output_path)
    elif fmt == ExportFormat.PDF:
        from lynx.export.pdf_export import export_pdf
        return export_pdf(report, output_path)
    else:
        raise ValueError(f"Unknown format: {fmt}")
