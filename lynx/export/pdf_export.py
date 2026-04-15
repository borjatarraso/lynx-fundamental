"""PDF export — converts HTML export to PDF using weasyprint (optional dependency)."""

from __future__ import annotations

from pathlib import Path

from lynx.models import AnalysisReport


def export_pdf(report: AnalysisReport, output_path: Path) -> Path:
    """Export report as a PDF file.

    Requires weasyprint to be installed: pip install weasyprint
    Falls back to a helpful error message if not available.
    """
    # Generate HTML first
    from lynx.export.html_export import export_html

    html_path = output_path.with_suffix(".html")
    export_html(report, html_path)

    try:
        from weasyprint import HTML
    except ImportError:
        # Clean up temp HTML
        html_path.unlink(missing_ok=True)
        raise RuntimeError(
            "PDF export requires weasyprint. Install it with:\n"
            "  pip install weasyprint\n"
            "Or use HTML/TXT export instead."
        )

    HTML(filename=str(html_path)).write_pdf(str(output_path))

    # Clean up intermediate HTML
    html_path.unlink(missing_ok=True)

    return output_path
