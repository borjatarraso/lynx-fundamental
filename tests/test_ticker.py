"""Tests for ticker resolution utilities."""

import pytest
from lynx.core.ticker import SearchResult, is_isin, _filter_primary


class TestIsIsin:
    def test_valid_us_isin(self):
        assert is_isin("US0378331005") is True

    def test_valid_de_isin(self):
        assert is_isin("DE000A14KRD3") is True

    def test_lowercase_converted(self):
        assert is_isin("us0378331005") is True

    def test_too_short(self):
        assert is_isin("US037833100") is False

    def test_too_long(self):
        assert is_isin("US03783310050") is False

    def test_invalid_country(self):
        assert is_isin("123456789012") is False

    def test_ticker_not_isin(self):
        assert is_isin("AAPL") is False

    def test_empty(self):
        assert is_isin("") is False

    def test_spaces(self):
        assert is_isin("  US0378331005  ") is True


class TestFilterPrimary:
    def test_empty(self):
        assert _filter_primary([]) == []

    def test_primary_exchange(self):
        results = [
            SearchResult(symbol="AAPL", name="Apple", exchange="NMS", quote_type="EQUITY"),
            SearchResult(symbol="AAPL.MX", name="Apple", exchange="MEX", quote_type="EQUITY"),
        ]
        filtered = _filter_primary(results)
        assert len(filtered) == 1
        assert filtered[0].exchange == "NMS"

    def test_no_primary(self):
        results = [
            SearchResult(symbol="TEST", name="Test", exchange="UNKNOWN", quote_type="EQUITY"),
        ]
        filtered = _filter_primary(results)
        assert len(filtered) == 0


class TestSearchResult:
    def test_creation(self):
        r = SearchResult(symbol="AAPL", name="Apple Inc.", exchange="NASDAQ", quote_type="EQUITY")
        assert r.symbol == "AAPL"
        assert r.score == 0.0  # default

    def test_with_score(self):
        r = SearchResult(symbol="AAPL", name="Apple", exchange="NMS", quote_type="EQUITY", score=0.95)
        assert r.score == 0.95
