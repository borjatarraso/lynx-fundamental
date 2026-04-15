"""Financial data fetching via yfinance."""

from __future__ import annotations

from typing import Optional

import pandas as pd
import yfinance as yf

from lynx.core.storage import get_financials_dir, save_json
from lynx.models import (
    CompanyProfile,
    FinancialStatement,
)


def fetch_company_profile(ticker: str, info: dict | None = None) -> CompanyProfile:
    """Fetch company profile information.

    If *info* is provided, uses it directly instead of making an API call.
    """
    if info is None:
        info = fetch_info(ticker)
    return CompanyProfile(
        ticker=ticker.upper(),
        name=info.get("longName") or info.get("shortName", ticker),
        sector=info.get("sector"),
        industry=info.get("industry"),
        country=info.get("country"),
        exchange=info.get("exchange"),
        currency=info.get("currency", "USD"),
        market_cap=info.get("marketCap"),
        description=info.get("longBusinessSummary"),
        website=info.get("website"),
        employees=info.get("fullTimeEmployees"),
    )


def fetch_info(ticker: str) -> dict:
    """Fetch raw yfinance info dict for a ticker."""
    try:
        t = yf.Ticker(ticker)
        return t.info or {}
    except Exception:
        return {}


def fetch_financial_statements(ticker: str) -> list[FinancialStatement]:
    """Fetch income statement, balance sheet, and cash flow data."""
    try:
        t = yf.Ticker(ticker)
    except Exception:
        return []
    statements: list[FinancialStatement] = []

    try:
        income = _safe_df(t.financials)
    except Exception:
        income = None
    try:
        quarterly_income = _safe_df(t.quarterly_financials)
    except Exception:
        quarterly_income = None
    try:
        balance = _safe_df(t.balance_sheet)
    except Exception:
        balance = None
    try:
        quarterly_balance = _safe_df(t.quarterly_balance_sheet)
    except Exception:
        quarterly_balance = None
    try:
        cashflow = _safe_df(t.cashflow)
    except Exception:
        cashflow = None
    try:
        quarterly_cashflow = _safe_df(t.quarterly_cashflow)
    except Exception:
        quarterly_cashflow = None

    # Save raw data
    fdir = get_financials_dir(ticker)
    for name, df in [
        ("income_annual", income),
        ("income_quarterly", quarterly_income),
        ("balance_annual", balance),
        ("balance_quarterly", quarterly_balance),
        ("cashflow_annual", cashflow),
        ("cashflow_quarterly", quarterly_cashflow),
    ]:
        if df is not None and not df.empty:
            save_json(fdir / f"{name}.json", _df_to_dict(df))

    # Build annual statements
    if income is not None and not income.empty:
        for col in income.columns:
            period = col.strftime("%Y") if hasattr(col, "strftime") else str(col)
            stmt = FinancialStatement(period=period)
            stmt.revenue = _get(income, col, "Total Revenue")
            stmt.cost_of_revenue = _get(income, col, "Cost Of Revenue")
            stmt.gross_profit = _get(income, col, "Gross Profit")
            stmt.operating_income = _get(income, col, "Operating Income")
            stmt.net_income = _get(income, col, "Net Income")
            stmt.ebitda = _get(income, col, "EBITDA")
            stmt.interest_expense = _get(income, col, "Interest Expense", "Interest Expense Non Operating")
            stmt.eps = _get(income, col, "Basic EPS")

            # Merge balance sheet
            if balance is not None and col in balance.columns:
                stmt.total_assets = _get(balance, col, "Total Assets")
                stmt.total_liabilities = _get(
                    balance, col, "Total Liabilities Net Minority Interest"
                )
                stmt.total_equity = _get(
                    balance, col, "Stockholders Equity", "Total Equity Gross Minority Interest"
                )
                stmt.total_debt = _get(balance, col, "Total Debt")
                stmt.total_cash = _get(
                    balance, col, "Cash And Cash Equivalents", "Cash Cash Equivalents And Short Term Investments"
                )
                stmt.current_assets = _get(
                    balance, col, "Current Assets",
                )
                stmt.current_liabilities = _get(
                    balance, col, "Current Liabilities",
                )
                stmt.shares_outstanding = _get(balance, col, "Ordinary Shares Number", "Share Issued")
                equity = stmt.total_equity
                shares = stmt.shares_outstanding
                if equity is not None and shares and shares > 0:
                    stmt.book_value_per_share = equity / shares

            # Merge cash flow
            if cashflow is not None and col in cashflow.columns:
                stmt.operating_cash_flow = _get(cashflow, col, "Operating Cash Flow")
                stmt.capital_expenditure = _get(cashflow, col, "Capital Expenditure")
                stmt.free_cash_flow = _get(cashflow, col, "Free Cash Flow")
                stmt.dividends_paid = _get(cashflow, col, "Common Stock Dividend Paid")

                if stmt.free_cash_flow is None and stmt.operating_cash_flow is not None:
                    capex = stmt.capital_expenditure or 0
                    stmt.free_cash_flow = stmt.operating_cash_flow + capex  # capex is negative

            statements.append(stmt)

    return statements


def fetch_historical_prices(ticker: str, period: str = "5y") -> Optional[pd.DataFrame]:
    """Fetch historical price data."""
    try:
        t = yf.Ticker(ticker)
        hist = t.history(period=period)
    except Exception:
        return None
    if hist is not None and not hist.empty:
        fdir = get_financials_dir(ticker)
        save_json(fdir / "price_history.json", {
            "dates": [d.isoformat() for d in hist.index],
            "close": hist["Close"].tolist(),
        })
    return hist


def _safe_df(df) -> Optional[pd.DataFrame]:
    """Return df if it's a valid non-empty DataFrame, else None."""
    if df is None:
        return None
    if isinstance(df, pd.DataFrame) and not df.empty:
        return df
    return None


def _get(df: pd.DataFrame, col, *row_names) -> Optional[float]:
    """Safely get a value from a DataFrame by trying multiple row names."""
    for name in row_names:
        if name in df.index:
            val = df.loc[name, col]
            if pd.notna(val):
                return float(val)
    return None


def _df_to_dict(df: pd.DataFrame) -> dict:
    """Convert DataFrame to a JSON-serializable dict."""
    result = {}
    for col in df.columns:
        key = col.isoformat() if hasattr(col, "isoformat") else str(col)
        result[key] = {}
        for idx in df.index:
            val = df.loc[idx, col]
            result[key][str(idx)] = None if pd.isna(val) else float(val)
    return result
