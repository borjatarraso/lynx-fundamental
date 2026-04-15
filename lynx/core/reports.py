"""SEC EDGAR and regulatory report fetching via yfinance and direct EDGAR API."""

from __future__ import annotations

import time
from typing import Optional

import requests
import yfinance as yf

from lynx.core.storage import get_reports_dir, save_binary, save_json, save_text
from lynx.models import Filing

DOWNLOAD_HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; LynxFA/0.1)",
    "Accept-Encoding": "gzip, deflate",
}

# SEC EDGAR requires a User-Agent with contact email
EDGAR_HEADERS = {
    "User-Agent": "LynxFA/0.1 lynx-fundamental-research@example.com",
    "Accept-Encoding": "gzip, deflate",
}

EDGAR_BASE = "https://data.sec.gov"

TARGET_FORMS = {"10-K", "10-Q", "20-F", "6-K", "8-K", "10-K/A", "10-Q/A"}


def fetch_sec_filings(ticker: str) -> list[Filing]:
    """Fetch SEC filing metadata using yfinance (primary) and EDGAR (fallback)."""
    filings = _fetch_via_yfinance(ticker)

    if not filings:
        filings = _fetch_via_edgar(ticker)

    # Save metadata
    if filings:
        rdir = get_reports_dir(ticker)
        save_json(rdir / "filings_index.json", [
            {"form": f.form_type, "date": f.filing_date, "period": f.period, "url": f.url}
            for f in filings
        ])

    return filings


def _fetch_via_yfinance(ticker: str) -> list[Filing]:
    """Fetch filings from yfinance sec_filings property."""
    filings: list[Filing] = []
    try:
        t = yf.Ticker(ticker)
        sec_filings = t.sec_filings
        if not sec_filings:
            return filings

        for item in sec_filings:
            form_type = item.get("type", "")
            if form_type not in TARGET_FORMS:
                continue

            filing_date = ""
            date_obj = item.get("date")
            if date_obj:
                filing_date = str(date_obj)

            # Get the primary document URL from exhibits
            url = ""
            exhibits = item.get("exhibits", {})
            # Prefer the main filing document
            for key in [form_type, form_type.replace("/", ""), "htm", "html"]:
                if key in exhibits:
                    url = exhibits[key]
                    break
            if not url and exhibits:
                # Take the first exhibit
                url = next(iter(exhibits.values()), "")
            if not url:
                edgar_url = item.get("edgarUrl", "")
                if edgar_url:
                    url = edgar_url

            filings.append(Filing(
                form_type=form_type,
                filing_date=filing_date,
                period=filing_date,  # yfinance doesn't separate period
                url=url,
                description=item.get("title", f"{form_type} filed {filing_date}"),
            ))

    except Exception:
        pass

    return filings


def _fetch_via_edgar(ticker: str) -> list[Filing]:
    """Fallback: fetch filings directly from SEC EDGAR API."""
    cik = _resolve_cik(ticker)
    if not cik:
        return []

    cik_padded = cik.zfill(10)
    url = f"{EDGAR_BASE}/submissions/CIK{cik_padded}.json"

    try:
        resp = requests.get(url, headers=EDGAR_HEADERS, timeout=30)
        resp.raise_for_status()
        data = resp.json()
    except Exception:
        return []

    filings: list[Filing] = []
    recent = data.get("filings", {}).get("recent", {})
    if not recent:
        return filings

    forms = recent.get("form", [])
    dates = recent.get("filingDate", [])
    accessions = recent.get("accessionNumber", [])
    primary_docs = recent.get("primaryDocument", [])
    periods = recent.get("reportDate", [])

    for i, form in enumerate(forms):
        if form not in TARGET_FORMS:
            continue
        if i >= len(accessions):
            continue
        accession = accessions[i].replace("-", "")
        doc = primary_docs[i] if i < len(primary_docs) else ""
        filing_url = f"https://www.sec.gov/Archives/edgar/data/{cik}/{accession}/{doc}"

        filings.append(Filing(
            form_type=form,
            filing_date=dates[i] if i < len(dates) else "",
            period=periods[i] if i < len(periods) else "",
            url=filing_url,
            description=f"{form} filed {dates[i] if i < len(dates) else 'N/A'}",
        ))

    return filings


def download_filing(ticker: str, filing: Filing, max_size_mb: int = 20) -> Optional[str]:
    """Download a single filing document."""
    if not filing.url:
        return None

    rdir = get_reports_dir(ticker)
    safe_date = (filing.filing_date or "unknown").replace("-", "")
    filename = f"{filing.form_type.replace('/', '_')}_{safe_date}"

    try:
        resp = requests.get(filing.url, headers=DOWNLOAD_HEADERS, timeout=60)
        resp.raise_for_status()

        content_type = resp.headers.get("content-type", "")
        content = resp.content

        if len(content) > max_size_mb * 1024 * 1024:
            return None

        if "pdf" in content_type or filing.url.endswith(".pdf"):
            path = rdir / f"{filename}.pdf"
            save_binary(path, content)
        else:
            path = rdir / f"{filename}.html"
            save_text(path, content.decode("utf-8", errors="replace"))

        filing.local_path = str(path)
        return str(path)

    except Exception:
        return None


def download_top_filings(ticker: str, filings: list[Filing], max_count: int = 10) -> list[Filing]:
    """Download the most recent filings, respecting rate limits."""
    downloaded = []
    for filing in filings[:max_count]:
        path = download_filing(ticker, filing)
        if path:
            filing.local_path = path
            downloaded.append(filing)
        time.sleep(0.15)
    return downloaded


def _resolve_cik(ticker: str) -> Optional[str]:
    """Resolve ticker to CIK number."""
    # Try the company tickers JSON
    try:
        resp = requests.get(
            "https://www.sec.gov/files/company_tickers.json",
            headers=EDGAR_HEADERS,
            timeout=15,
        )
        if resp.status_code == 200:
            data = resp.json()
            for entry in data.values():
                if entry.get("ticker", "").upper() == ticker.upper():
                    return str(entry["cik_str"])
    except Exception:
        pass

    # Fallback: direct EDGAR
    url = f"{EDGAR_BASE}/submissions/CIK{ticker.upper()}.json"
    try:
        resp = requests.get(url, headers=EDGAR_HEADERS, timeout=15)
        if resp.status_code == 200:
            return resp.json().get("cik", "")
    except Exception:
        pass

    return None
