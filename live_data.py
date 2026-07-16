import yfinance as yf

COMPANY_TICKERS = {
    "adani_ar25": "ADANIENT.NS",
    "inf_ar25": "INFY.NS",
    "rel_ar25": "RELIANCE.NS",
    "sbi_ar25": "SBIN.NS",
    "tatamotors_ar25": "TMCV.NS"  # updated post-demerger; was TATAMOTORS.NS
}


def get_live_price(company_key: str) -> dict:
    """Fetch current price and basic market data for a company."""
    ticker_symbol = COMPANY_TICKERS.get(company_key)
    if not ticker_symbol:
        return {"error": f"Unknown company: {company_key}"}

    ticker = yf.Ticker(ticker_symbol)
    info = ticker.info
    if not info or info.get("currentPrice") is None:
        return {"error": f"No price data available for {ticker_symbol}"}

    return {
        "company": company_key,
        "ticker": ticker_symbol,
        "current_price": info.get("currentPrice"),
        "market_cap": info.get("marketCap"),
        "52_week_high": info.get("fiftyTwoWeekHigh"),
        "52_week_low": info.get("fiftyTwoWeekLow"),
    }


def get_ttm_metrics(company_key: str) -> dict:
    """
    Fetch trailing-twelve-month (TTM) financial metrics - a rolling
    snapshot as of today, NOT tied to a specific fiscal year.
    Use this for questions like 'what is the current/latest revenue'.
    """
    ticker_symbol = COMPANY_TICKERS.get(company_key)
    if not ticker_symbol:
        return {"error": f"Unknown company: {company_key}"}

    ticker = yf.Ticker(ticker_symbol)
    info = ticker.info
    if not info or info.get("currentPrice") is None:
        return {"error": f"No price data available for {ticker_symbol}"}
    return {
        "company": company_key,
        "ticker": ticker_symbol,
        "period": "trailing twelve months (as of query date)",
        "revenue_ttm": info.get("totalRevenue"),
        "ebitda_ttm": info.get("ebitda"),
        "net_income_ttm": info.get("netIncomeToCommon"),
        "profit_margin": info.get("profitMargins"),
        "dividend_yield": info.get("dividendYield"),
    }


def get_financial_metrics(company_key: str, fiscal_year: str = None) -> dict:
    """
    Fetch financial metrics for a SPECIFIC fiscal year (matches annual
    report language like 'FY26'). Defaults to the most recent available
    fiscal year if fiscal_year is not provided.

    fiscal_year: e.g. '2026-03-31' - must match a column in the
                 underlying data; check financials.columns to see options.
    """
    ticker_symbol = COMPANY_TICKERS.get(company_key)
    if not ticker_symbol:
        return {"error": f"Unknown company: {company_key}"}
    
    ticker = yf.Ticker(ticker_symbol)
    financials = ticker.financials  # columns = fiscal year-end dates

    if financials.empty:
        return {"error": "No financial statement data available"}

    # Pick the requested year, or default to most recent (first column)
    year_col = fiscal_year if fiscal_year in financials.columns else financials.columns[0]

    def safe_get(row_name):
        return financials.loc[row_name, year_col] if row_name in financials.index else None

    return {
        "company": company_key,
        "ticker": ticker_symbol,
        "fiscal_year_end": str(year_col),
        "total_revenue": safe_get("Total Revenue"),
        "ebitda": safe_get("EBITDA"),
        "net_income": safe_get("Net Income"),
        "diluted_eps": safe_get("Diluted EPS"),
        "note": "Figures from Yahoo Finance annual income statement; may differ slightly from company-reported figures due to standalone/consolidated or restatement differences."
    }


if __name__ == "__main__":
    # Quick test across all 5 companies
    for company in COMPANY_TICKERS:
        print(f"\n--- {company} ---")
        print("Live price:", get_live_price(company))
        print("TTM metrics:", get_ttm_metrics(company))
        print("FY-specific metrics (latest):", get_financial_metrics(company))