"""Tests for storage module — mode management, cache, serialization."""

import json
import pytest
from pathlib import Path

from lynx.core.storage import (
    _MODE,
    drop_cache_all,
    drop_cache_ticker,
    get_cache_age_hours,
    get_company_dir,
    get_data_root,
    get_mode,
    has_cache,
    is_testing,
    list_cached_tickers,
    load_cached_report,
    load_json,
    save_analysis_report,
    save_json,
    set_mode,
)


@pytest.fixture(autouse=True)
def use_testing_mode():
    """Ensure all tests use testing mode to avoid touching production data."""
    set_mode("testing")
    yield
    set_mode("testing")


class TestModeManagement:
    def test_set_production(self):
        set_mode("production")
        assert get_mode() == "production"
        assert not is_testing()
        set_mode("testing")  # restore

    def test_set_testing(self):
        set_mode("testing")
        assert get_mode() == "testing"
        assert is_testing()

    def test_invalid_mode_raises(self):
        with pytest.raises(ValueError, match="Unknown mode"):
            set_mode("invalid")

    def test_data_root_testing(self):
        root = get_data_root()
        assert root.name == "data_test"

    def test_data_root_production(self):
        set_mode("production")
        root = get_data_root()
        assert root.name == "data"
        set_mode("testing")


class TestCacheBehavior:
    def test_has_cache_always_false_in_testing(self):
        assert not has_cache("AAPL")

    def test_load_cached_report_always_none_in_testing(self):
        assert load_cached_report("AAPL") is None


class TestPathHelpers:
    def test_company_dir_creates(self):
        d = get_company_dir("TEST_TICKER")
        assert d.exists()
        assert d.name == "TEST_TICKER"

    def test_company_dir_uppercased(self):
        d = get_company_dir("test_lower")
        assert d.name == "TEST_LOWER"


class TestSerialization:
    def test_save_and_load_json(self, tmp_path):
        data = {"key": "value", "number": 42}
        path = tmp_path / "test.json"
        save_json(path, data)
        loaded = load_json(path)
        assert loaded == data

    def test_save_analysis_report(self):
        report_dict = {
            "profile": {"ticker": "TEST", "name": "Test Co"},
            "fetched_at": "2026-01-01T00:00:00",
        }
        path = save_analysis_report("TEST", report_dict)
        assert path.exists()
        assert "analysis_" in path.name

        # Verify latest link
        latest = get_company_dir("TEST") / "analysis_latest.json"
        assert latest.exists()
        loaded = load_json(latest)
        assert loaded["profile"]["ticker"] == "TEST"


class TestCacheManagement:
    def test_drop_cache_ticker(self):
        # Create some data
        d = get_company_dir("DROP_TEST")
        save_json(d / "test.json", {"data": True})
        assert d.exists()

        result = drop_cache_ticker("DROP_TEST")
        assert result is True
        assert not d.exists()

    def test_drop_nonexistent_ticker(self):
        assert drop_cache_ticker("NONEXISTENT_XYZ") is False

    def test_drop_cache_all(self):
        # Create some data
        for ticker in ["DA1", "DA2", "DA3"]:
            d = get_company_dir(ticker)
            save_json(d / "test.json", {"data": True})

        count = drop_cache_all()
        assert count >= 3

    def test_list_cached_tickers(self):
        # Create a cached ticker
        report_dict = {
            "profile": {"ticker": "LIST_TEST", "name": "List Test"},
            "fetched_at": "2026-01-01T00:00:00",
        }
        save_analysis_report("LIST_TEST", report_dict)

        tickers = list_cached_tickers()
        names = [t["ticker"] for t in tickers]
        assert "LIST_TEST" in names


class TestCacheAgeHours:
    def test_no_cache(self):
        assert get_cache_age_hours("NO_CACHE_TICKER") is None

    def test_with_cache(self):
        report_dict = {"fetched_at": "2026-01-01T00:00:00"}
        save_analysis_report("AGE_TEST", report_dict)
        age = get_cache_age_hours("AGE_TEST")
        assert age is not None
        assert age >= 0
