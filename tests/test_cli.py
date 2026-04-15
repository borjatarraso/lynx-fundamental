"""Tests for CLI argument parsing and dispatch."""

import pytest
from lynx.cli import build_parser


class TestBuildParser:
    def test_production_mode(self):
        parser = build_parser()
        args = parser.parse_args(["-p", "AAPL"])
        assert args.run_mode == "production"
        assert args.identifier == "AAPL"

    def test_testing_mode(self):
        parser = build_parser()
        args = parser.parse_args(["-t", "AAPL"])
        assert args.run_mode == "testing"

    def test_mode_required(self):
        parser = build_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(["AAPL"])

    def test_interactive_flag(self):
        parser = build_parser()
        args = parser.parse_args(["-p", "-i"])
        assert args.interactive is True
        assert args.tui is False

    def test_tui_flag(self):
        parser = build_parser()
        args = parser.parse_args(["-t", "-tui"])
        assert args.tui is True
        assert args.interactive is False

    def test_gui_flag(self):
        parser = build_parser()
        args = parser.parse_args(["-p", "-x"])
        assert args.gui is True

    def test_search_flag(self):
        parser = build_parser()
        args = parser.parse_args(["-p", "-s", "Apple"])
        assert args.search is True
        assert args.identifier == "Apple"

    def test_mutually_exclusive_ui(self):
        parser = build_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(["-p", "-i", "-tui"])

    def test_refresh_flag(self):
        parser = build_parser()
        args = parser.parse_args(["-p", "--refresh", "AAPL"])
        assert args.refresh is True

    def test_no_reports(self):
        parser = build_parser()
        args = parser.parse_args(["-p", "--no-reports", "AAPL"])
        assert args.no_reports is True

    def test_no_news(self):
        parser = build_parser()
        args = parser.parse_args(["-p", "--no-news", "AAPL"])
        assert args.no_news is True

    def test_max_filings_default(self):
        parser = build_parser()
        args = parser.parse_args(["-p", "AAPL"])
        assert args.max_filings == 10

    def test_max_filings_custom(self):
        parser = build_parser()
        args = parser.parse_args(["-p", "--max-filings", "5", "AAPL"])
        assert args.max_filings == 5

    def test_max_filings_negative_rejected(self):
        parser = build_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(["-p", "--max-filings", "-1", "AAPL"])

    def test_max_filings_zero_rejected(self):
        parser = build_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(["-p", "--max-filings", "0", "AAPL"])

    def test_verbose_flag(self):
        parser = build_parser()
        args = parser.parse_args(["-p", "-v", "AAPL"])
        assert args.verbose is True

    def test_list_cache(self):
        parser = build_parser()
        args = parser.parse_args(["-p", "--list-cache"])
        assert args.list_cache is True

    def test_drop_cache_with_ticker(self):
        parser = build_parser()
        args = parser.parse_args(["-p", "--drop-cache", "AAPL"])
        assert args.drop_cache == "AAPL"

    def test_drop_cache_without_ticker(self):
        parser = build_parser()
        args = parser.parse_args(["-p", "--drop-cache"])
        assert args.drop_cache == "__prompt__"

    def test_about_flag(self):
        parser = build_parser()
        args = parser.parse_args(["-p", "--about"])
        assert args.about is True

    def test_defaults(self):
        parser = build_parser()
        args = parser.parse_args(["-p", "AAPL"])
        assert args.interactive is False
        assert args.tui is False
        assert args.gui is False
        assert args.search is False
        assert args.refresh is False
        assert args.no_reports is False
        assert args.no_news is False
        assert args.verbose is False
        assert args.list_cache is False
        assert args.about is False
