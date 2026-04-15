"""Ticker and ISIN resolution utilities.

Supports standard US tickers, OTC/Pink Sheets, TSXV (.V), TSX (.TO),
European exchanges (.DE, .L, .PA, .AS, .MI, .SW, .VI), ASX (.AX),
and company-name lookups via yfinance Search.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional

import yfinance as yf
from rich.console import Console
from rich.table import Table

console = Console(stderr=True)

# Exchange suffixes to try when a bare ticker doesn't resolve.
# Ordered by commonality for the OTC/venture/international use-case.
EXCHANGE_SUFFIXES = [
    "",       # US major exchanges (NYSE, NASDAQ)
    ".V",     # TSX Venture Exchange
    ".TO",    # Toronto Stock Exchange
    ".DE",    # XETRA (Germany)
    ".L",     # London Stock Exchange
    ".PA",    # Euronext Paris
    ".AS",    # Euronext Amsterdam
    ".MI",    # Borsa Italiana (Milan)
    ".SW",    # SIX Swiss Exchange
    ".VI",    # Vienna Stock Exchange
    ".AX",    # Australian Securities Exchange
    ".HK",    # Hong Kong Stock Exchange
    ".SI",    # Singapore Exchange
    ".F",     # Frankfurt Stock Exchange
    ".BR",    # Euronext Brussels
    ".ST",    # Nasdaq Stockholm
    ".CO",    # Nasdaq Copenhagen
    ".OL",    # Oslo Børs
    ".HE",    # Nasdaq Helsinki
    ".MC",    # Bolsa de Madrid
    ".LS",    # Euronext Lisbon
    ".WA",    # Warsaw Stock Exchange
    ".JK",    # Jakarta Stock Exchange
    ".NS",    # National Stock Exchange of India
    ".BO",    # Bombay Stock Exchange
    ".TW",    # Taiwan Stock Exchange
    ".KS",    # Korea Stock Exchange
    ".T",     # Tokyo Stock Exchange
    ".MX",    # Bolsa Mexicana de Valores
    ".SA",    # B3 (Brazil)
]


@dataclass
class SearchResult:
    """A single search result for display / selection."""
    symbol: str
    name: str
    exchange: str
    quote_type: str
    score: float = 0.0


def is_isin(code: str) -> bool:
    """Check if a string looks like an ISIN (2-letter country + 9 alphanum + 1 check)."""
    return bool(re.match(r"^[A-Z]{2}[A-Z0-9]{9}[0-9]$", code.strip().upper()))


def resolve_identifier(identifier: str) -> tuple[str, str | None]:
    """Resolve an identifier (ticker, ISIN, or company name) to (ticker, isin).

    Resolution strategy (multi-layer):
      1. If ISIN  -> search via yfinance Search
      2. Try exact ticker (as-is) -> direct yfinance Ticker lookup
      3. Try ticker + exchange suffixes -> brute-force common exchanges
      4. Fuzzy search via yfinance Search -> pick best equity match
      5. If multiple results, pick the best one (highest score, equity preferred)

    Raises ValueError if nothing can be found.
    """
    raw = identifier.strip()
    upper = raw.upper()

    # Detect if this looks like a company name (has spaces or is very long)
    looks_like_name = " " in raw or len(raw) > 12

    # --- 1. ISIN resolution ---
    if is_isin(upper):
        result = _search_best_equity(upper)
        if result:
            console.print(
                f"[dim]ISIN resolved to:[/] {result.symbol} "
                f"({result.name}) on {result.exchange}"
            )
            return result.symbol, upper
        raise ValueError(
            f"Could not resolve ISIN '{upper}' to any ticker. "
            "Try providing the ticker symbol directly (e.g. OCO.V, AT1.DE)."
        )

    # --- 1b. Company name -> go straight to search (skip slow suffix scan) ---
    if looks_like_name:
        result = _search_best_equity(raw)
        if result:
            console.print(
                f"[dim]Search resolved '{raw}' -> {result.symbol} "
                f"({result.name}) on {result.exchange}[/]"
            )
            return result.symbol, None
        raise ValueError(
            f"Could not find any company matching '{raw}'.\n"
            "Try a different name or provide the ticker directly."
        )

    # --- 2. Direct ticker lookup (exact match, including dot-suffixed like OCO.V) ---
    ticker_candidate = _try_direct_ticker(upper)
    if ticker_candidate:
        return ticker_candidate, None

    # --- 3. yfinance Search (fast: single API call) ---
    # Try search BEFORE brute-force suffix iteration — this is much faster
    # and handles company names, ambiguous tickers (AT1), and OTC names.
    result = _search_best_equity(raw)
    if result:
        console.print(
            f"[dim]Search resolved '{raw}' -> {result.symbol} "
            f"({result.name}) on {result.exchange}[/]"
        )
        return result.symbol, None

    # --- 4. Brute-force exchange suffixes (fallback for rare cases) ---
    # Only if search returned nothing and the identifier has no dot suffix.
    if "." not in upper:
        for suffix in EXCHANGE_SUFFIXES:
            if not suffix:
                continue
            candidate = upper + suffix
            found = _try_direct_ticker(candidate)
            if found:
                console.print(
                    f"[dim]Resolved {raw} -> {found} (via suffix {suffix})[/]"
                )
                return found, None

    # --- 5. Broader search as last resort ---
    for extra_query in [f"{raw} stock", f"{raw} corp"]:
        result = _search_best_equity(extra_query)
        if result:
            console.print(
                f"[dim]Search resolved '{raw}' -> {result.symbol} "
                f"({result.name}) on {result.exchange}[/]"
            )
            return result.symbol, None

    raise ValueError(
        f"Could not find any company matching '{raw}'.\n"
        "Tips:\n"
        "  - For TSXV stocks, try: OCO.V, FUU.V\n"
        "  - For TSX stocks, try: RY.TO, SU.TO\n"
        "  - For German stocks, try: AT1.DE, SAP.DE\n"
        "  - For OTC/Pink Sheets, try the US OTC ticker (e.g. ORRCF, FUUFF)\n"
        "  - You can also type the full company name: 'Oroco Resource Corp'"
    )


def search_companies(query: str, max_results: int = 10) -> list[SearchResult]:
    """Search for companies by name, ticker, or ISIN.

    Returns a list of SearchResult objects sorted by relevance.
    """
    try:
        s = yf.Search(query)
        quotes = s.quotes or []
    except Exception:
        return []

    results: list[SearchResult] = []
    for q in quotes[:max_results]:
        qt = q.get("quoteType", "")
        results.append(SearchResult(
            symbol=q.get("symbol", ""),
            name=q.get("longname") or q.get("shortname", ""),
            exchange=q.get("exchDisp") or q.get("exchange", ""),
            quote_type=qt,
            score=q.get("score", 0),
        ))

    return results


def display_search_results(results: list[SearchResult]) -> None:
    """Pretty-print search results to the console."""
    t = Table(title="Search Results", border_style="cyan")
    t.add_column("#", style="dim", width=3)
    t.add_column("Symbol", style="bold cyan", min_width=12)
    t.add_column("Name", min_width=30)
    t.add_column("Exchange", min_width=15)
    t.add_column("Type", min_width=8)

    for i, r in enumerate(results, 1):
        t.add_row(str(i), r.symbol, r.name, r.exchange, r.quote_type)

    console.print(t)


def validate_ticker(ticker: str) -> dict:
    """Validate a ticker and return basic info. Raises ValueError if invalid."""
    t = yf.Ticker(ticker)
    info = t.info or {}
    name = info.get("longName") or info.get("shortName")
    if not name:
        raise ValueError(f"Could not find company data for ticker '{ticker}'.")
    return info


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _try_direct_ticker(symbol: str) -> Optional[str]:
    """Try to look up a symbol directly via yfinance Ticker.

    Returns the symbol if it has valid data (price or name), else None.
    Suppresses stderr noise from yfinance HTTP 404s using per-logger
    level adjustment (thread-safe) instead of global logging.disable().
    """
    import logging
    import io
    import os

    # Suppress yfinance/urllib3 loggers at the logger level (thread-safe)
    _loggers_to_suppress = ["yfinance", "peewee", "urllib3", "urllib3.connectionpool"]
    saved_levels = {}
    for name in _loggers_to_suppress:
        logger = logging.getLogger(name)
        saved_levels[name] = logger.level
        logger.setLevel(logging.CRITICAL + 1)

    # Redirect stderr at the fd level to suppress C-extension noise
    old_stderr_fd = os.dup(2)
    devnull = os.open(os.devnull, os.O_WRONLY)
    os.dup2(devnull, 2)
    os.close(devnull)
    try:
        t = yf.Ticker(symbol)
        info = t.info
        if not info:
            return None

        # Check for clear signals that this is a real, active ticker
        has_price = (
            info.get("regularMarketPrice") is not None
            or info.get("currentPrice") is not None
        )
        has_name = bool(info.get("longName") or info.get("shortName"))

        if has_price and has_name:
            return symbol

        # Some OTC/micro-cap might not have currentPrice but have other data
        if has_name and info.get("marketCap"):
            return symbol

    except Exception:
        pass
    finally:
        os.dup2(old_stderr_fd, 2)
        os.close(old_stderr_fd)
        for name, level in saved_levels.items():
            logging.getLogger(name).setLevel(level)

    return None


def _search_best_equity(query: str) -> Optional[SearchResult]:
    """Search yfinance and return the best equity match.

    Ranking logic:
      1. Exact symbol match (query == symbol base, ignoring exchange suffix)
      2. Equities on primary exchanges
      3. Equities on any exchange
      4. Non-fund results
    """
    results = search_companies(query, max_results=15)
    if not results:
        return None

    query_upper = query.strip().upper()

    # Filter to equities only
    equities = [r for r in results if r.quote_type == "EQUITY"]

    if equities:
        # Check for exact symbol match first (e.g. query "FUU" -> symbol "FUU.V")
        # The symbol base is the part before the dot suffix
        exact_matches = [
            r for r in equities
            if r.symbol.upper().split(".")[0] == query_upper
            or r.symbol.upper() == query_upper
        ]
        if exact_matches:
            # Among exact matches, prefer primary exchanges
            primary = _filter_primary(exact_matches)
            return primary[0] if primary else exact_matches[0]

        # No exact match — prefer primary exchanges
        primary = _filter_primary(equities)
        if primary:
            return primary[0]
        return equities[0]

    # No equities — return the best non-fund result
    non_fund = [r for r in results if r.quote_type not in ("MUTUALFUND",)]
    if non_fund:
        return non_fund[0]

    return results[0]


# Exchanges considered "primary" for ranking search results.
_PRIMARY_EXCHANGES = {
    # North America
    "NMS", "NYQ", "NYSE", "NASDAQ", "NGM", "NCM", "NIM",
    "CDNX", "VAN", "TOR", "Toronto",
    "OTC Markets", "OQB", "OQX", "PNK",
    # Europe
    "GER", "XETRA", "LSE", "London", "PAR", "Paris",
    "AMS", "Amsterdam", "MIL", "Milan", "EBS", "SIX",
    "VIE", "Vienna", "MCE", "Madrid",
    # Asia-Pacific
    "ASX", "Australian", "HKG", "Hong Kong",
    "TYO", "Tokyo", "KSC", "Korea",
    "NSE", "BSE",
}


def _filter_primary(results: list[SearchResult]) -> list[SearchResult]:
    """Filter results to those on primary exchanges."""
    return [r for r in results if r.exchange in _PRIMARY_EXCHANGES]
