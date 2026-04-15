"""Tests for the export module."""

import pytest
from pathlib import Path

from lynx.core.storage import set_mode
from lynx.export import ExportFormat, export_report
from lynx.models import (
    AnalysisReport,
    CompanyProfile,
    CompanyTier,
    EfficiencyMetrics,
    GrowthMetrics,
    IntrinsicValue,
    MoatIndicators,
    ProfitabilityMetrics,
    SolvencyMetrics,
    ValuationMetrics,
)


@pytest.fixture(autouse=True)
def testing_mode():
    set_mode("testing")
    yield
    set_mode("testing")


def _make_report():
    return AnalysisReport(
        profile=CompanyProfile(
            ticker="EXPORT_TEST", name="Export Test Co",
            tier=CompanyTier.MEGA, market_cap=500e9,
            sector="Technology", industry="Software",
        ),
        valuation=ValuationMetrics(pe_trailing=20.0, pb_ratio=5.0),
        profitability=ProfitabilityMetrics(roe=0.20, net_margin=0.15),
        solvency=SolvencyMetrics(debt_to_equity=0.5, current_ratio=1.8),
        growth=GrowthMetrics(revenue_growth_yoy=0.12),
        efficiency=EfficiencyMetrics(),
        moat=MoatIndicators(moat_score=55.0, competitive_position="Narrow Moat"),
        intrinsic_value=IntrinsicValue(current_price=150.0),
    )


class TestExportFormat:
    def test_enum_values(self):
        assert ExportFormat.TXT.value == "txt"
        assert ExportFormat.HTML.value == "html"
        assert ExportFormat.PDF.value == "pdf"


class TestExportTxt:
    def test_export_to_txt(self, tmp_path):
        report = _make_report()
        path = export_report(report, ExportFormat.TXT, tmp_path / "test.txt")
        assert path.exists()
        content = path.read_text()
        assert "Export Test Co" in content
        assert "EXPORT_TEST" in content
        assert len(content) > 100

    def test_export_txt_has_metrics(self, tmp_path):
        report = _make_report()
        path = export_report(report, ExportFormat.TXT, tmp_path / "test.txt")
        content = path.read_text()
        assert "P/E" in content or "Valuation" in content

    def test_export_txt_has_conclusion(self, tmp_path):
        report = _make_report()
        path = export_report(report, ExportFormat.TXT, tmp_path / "test.txt")
        content = path.read_text()
        assert "Conclusion" in content or "Assessment" in content


class TestExportHtml:
    def test_export_to_html(self, tmp_path):
        report = _make_report()
        path = export_report(report, ExportFormat.HTML, tmp_path / "test.html")
        assert path.exists()
        content = path.read_text()
        assert "<!DOCTYPE html>" in content
        assert "Export Test Co" in content

    def test_html_has_styling(self, tmp_path):
        report = _make_report()
        path = export_report(report, ExportFormat.HTML, tmp_path / "test.html")
        content = path.read_text()
        assert "<style>" in content

    def test_html_has_title(self, tmp_path):
        report = _make_report()
        path = export_report(report, ExportFormat.HTML, tmp_path / "test.html")
        content = path.read_text()
        assert "<title>" in content
        assert "Lynx Fundamental Analysis" in content

    def test_html_white_background(self, tmp_path):
        """HTML export must use white background for readability."""
        report = _make_report()
        path = export_report(report, ExportFormat.HTML, tmp_path / "test.html")
        content = path.read_text()
        assert "background: #ffffff" in content


class TestExportPdf:
    def test_pdf_requires_weasyprint(self, tmp_path):
        """PDF export should raise RuntimeError if weasyprint is not installed."""
        report = _make_report()
        try:
            import weasyprint
            pytest.skip("weasyprint is installed — cannot test fallback")
        except ImportError:
            with pytest.raises(RuntimeError, match="weasyprint"):
                export_report(report, ExportFormat.PDF, tmp_path / "test.pdf")

    def test_pdf_creates_valid_file(self, tmp_path):
        """PDF export creates a valid PDF when weasyprint is installed."""
        try:
            import weasyprint
        except ImportError:
            pytest.skip("weasyprint not installed")
        report = _make_report()
        output = tmp_path / "test_output.pdf"
        result = export_report(report, ExportFormat.PDF, output)
        assert result.exists()
        assert result.suffix == ".pdf"
        content = result.read_bytes()
        assert content[:5] == b"%PDF-"
        # Verify intermediate HTML was cleaned up
        assert not output.with_suffix(".html").exists()

    def test_pdf_has_content(self, tmp_path):
        """PDF file has reasonable size (not empty)."""
        try:
            import weasyprint
        except ImportError:
            pytest.skip("weasyprint not installed")
        report = _make_report()
        output = tmp_path / "test_size.pdf"
        export_report(report, ExportFormat.PDF, output)
        assert output.stat().st_size > 1000


class TestExportAutoPath:
    def test_auto_generates_path(self):
        report = _make_report()
        path = export_report(report, ExportFormat.TXT)
        assert path.exists()
        assert "EXPORT_TEST" in str(path)
        assert path.suffix == ".txt"
        # Cleanup
        path.unlink(missing_ok=True)
