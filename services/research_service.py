import math

import yfinance as yf

from services.market_service import get_latest_available_price


def _get_fast_info(ticker):
    """Return Yahoo's fast quote snapshot when available."""
    try:
        fast_info = ticker.fast_info
        if fast_info is None:
            return {}
        return fast_info
    except Exception:
        return {}


def _safe_float(value):
    """Convert a value to a finite float or return None."""
    try:
        value = float(value)
        if math.isnan(value) or math.isinf(value):
            return None
        return value
    except (TypeError, ValueError):
        return None


def _get_statement_value(statement, possible_names, column):
    """
    Find the first available financial-statement row
    from a list of possible Yahoo Finance row names.
    """
    if statement is None or statement.empty:
        return None

    for name in possible_names:
        if name in statement.index:
            try:
                value = statement.loc[name, column]
                return _safe_float(value)
            except Exception:
                continue

    return None


def _calculate_roe(ticker):
    """
    Calculate ROE when Yahoo Finance does not provide
    returnOnEquity.

    ROE = Net Income / Average Shareholders' Equity

    Returned as a decimal: 0.15 = 15%
    """
    try:
        income_statement = ticker.financials
        balance_sheet = ticker.balance_sheet

        if (
            income_statement is None
            or income_statement.empty
            or balance_sheet is None
            or balance_sheet.empty
        ):
            return None

        common_columns = [
            column for column in income_statement.columns if column in balance_sheet.columns
        ]

        if not common_columns:
            return None

        latest_column = common_columns[0]

        net_income = _get_statement_value(
            income_statement,
            [
                "Net Income",
                "Net Income Common Stockholders",
                "Net Income Including Noncontrolling Interests",
            ],
            latest_column,
        )

        if net_income is None:
            return None

        equity_names = [
            "Stockholders Equity",
            "Total Stockholder Equity",
            "Common Stock Equity",
        ]

        current_equity = _get_statement_value(
            balance_sheet,
            equity_names,
            latest_column,
        )

        if current_equity is None or current_equity <= 0:
            return None

        previous_equity = None

        try:
            latest_position = list(balance_sheet.columns).index(latest_column)
            if latest_position + 1 < len(balance_sheet.columns):
                previous_column = balance_sheet.columns[latest_position + 1]
                previous_equity = _get_statement_value(
                    balance_sheet,
                    equity_names,
                    previous_column,
                )
        except Exception:
            previous_equity = None

        if previous_equity is not None and previous_equity > 0:
            average_equity = (current_equity + previous_equity) / 2
        else:
            average_equity = current_equity

        if average_equity <= 0:
            return None

        roe = net_income / average_equity

        if not math.isfinite(roe):
            return None

        return roe

    except Exception as error:
        print(f"ROE Calculation Error: {error}")
        return None


def _calculate_roa(ticker):
    """
    Calculate Return on Assets.

    ROA = Net Income / Average Total Assets

    Returned as a decimal:
        0.05 = 5%
    """
    try:
        income_statement = ticker.financials
        balance_sheet = ticker.balance_sheet

        if (
            income_statement is None
            or income_statement.empty
            or balance_sheet is None
            or balance_sheet.empty
        ):
            return None

        common_columns = [
            column for column in income_statement.columns if column in balance_sheet.columns
        ]

        if not common_columns:
            return None

        latest_column = common_columns[0]

        net_income = _get_statement_value(
            income_statement,
            [
                "Net Income",
                "Net Income Common Stockholders",
                "Net Income Including Noncontrolling Interests",
            ],
            latest_column,
        )

        total_assets = _get_statement_value(
            balance_sheet,
            ["Total Assets"],
            latest_column,
        )

        if net_income is None or total_assets is None or total_assets <= 0:
            return None

        previous_assets = None

        try:
            columns = list(balance_sheet.columns)
            position = columns.index(latest_column)

            if position + 1 < len(columns):
                previous_column = columns[position + 1]
                previous_assets = _get_statement_value(
                    balance_sheet,
                    ["Total Assets"],
                    previous_column,
                )

        except Exception:
            previous_assets = None

        if previous_assets is not None and previous_assets > 0:
            average_assets = (total_assets + previous_assets) / 2
        else:
            average_assets = total_assets

        if average_assets <= 0:
            return None

        roa = net_income / average_assets

        if not math.isfinite(roa):
            return None

        return roa

    except Exception as error:
        print(f"ROA Calculation Error: {error}")
        return None


def _calculate_current_ratio(ticker):
    """
    Calculate Current Ratio.

    Current Ratio =
        Current Assets / Current Liabilities
    """
    try:
        balance_sheet = ticker.balance_sheet

        if balance_sheet is None or balance_sheet.empty:
            return None

        latest_column = balance_sheet.columns[0]

        current_assets = _get_statement_value(
            balance_sheet,
            [
                "Current Assets",
                "Total Current Assets",
            ],
            latest_column,
        )

        current_liabilities = _get_statement_value(
            balance_sheet,
            [
                "Current Liabilities",
                "Total Current Liabilities",
            ],
            latest_column,
        )

        if current_assets is None or current_liabilities is None or current_liabilities <= 0:
            return None

        ratio = current_assets / current_liabilities

        if not math.isfinite(ratio):
            return None

        return ratio

    except Exception as error:
        print(f"Current Ratio Calculation Error: {error}")
        return None


def _calculate_operating_cash_flow(ticker):
    """
    Retrieve operating cash flow from the
    latest annual cash-flow statement.
    """
    try:
        cash_flow = ticker.cashflow

        if cash_flow is None or cash_flow.empty:
            return None

        latest_column = cash_flow.columns[0]

        operating_cash_flow = _get_statement_value(
            cash_flow,
            [
                "Operating Cash Flow",
                "Total Cash From Operating Activities",
                "Cash Flow From Continuing Operating Activities",
            ],
            latest_column,
        )

        return operating_cash_flow

    except Exception as error:
        print(f"Operating Cash Flow Calculation Error: {error}")
        return None


def _calculate_free_cash_flow(ticker):
    """
    Retrieve or calculate Free Cash Flow.

    Preferred:
        Yahoo's Free Cash Flow statement row.

    Fallback:
        Operating Cash Flow - Capital Expenditure
    """
    try:
        cash_flow = ticker.cashflow

        if cash_flow is None or cash_flow.empty:
            return None

        latest_column = cash_flow.columns[0]

        free_cash_flow = _get_statement_value(
            cash_flow,
            ["Free Cash Flow"],
            latest_column,
        )

        if free_cash_flow is not None:
            return free_cash_flow

        operating_cash_flow = _get_statement_value(
            cash_flow,
            [
                "Operating Cash Flow",
                "Total Cash From Operating Activities",
                "Cash Flow From Continuing Operating Activities",
            ],
            latest_column,
        )

        capital_expenditure = _get_statement_value(
            cash_flow,
            [
                "Capital Expenditure",
                "Capital Expenditures",
            ],
            latest_column,
        )

        if operating_cash_flow is None or capital_expenditure is None:
            return None

        if capital_expenditure < 0:
            free_cash_flow = operating_cash_flow + capital_expenditure
        else:
            free_cash_flow = operating_cash_flow - capital_expenditure

        if not math.isfinite(free_cash_flow):
            return None

        return free_cash_flow

    except Exception as error:
        print(f"Free Cash Flow Calculation Error: {error}")
        return None


def get_stock_profile(symbol):
    """
    Fetch company profile, financial statistics and
    valuation data from Yahoo Finance.

    Bare symbols remain backward-compatible with NSE. Explicit .NS and .BO
    suffixes are preserved so BSE-selected stocks are not redirected to NSE.
    """
    symbol = symbol.strip().upper()

    if "." not in symbol:
        symbol += ".NS"

    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info or {}
        fast_info = _get_fast_info(ticker)

        market_quote = get_latest_available_price(symbol)
        canonical_price = _safe_float(market_quote.get("price"))
        canonical_previous_close = _safe_float(market_quote.get("previous_close"))
        fast_price = canonical_price
        fast_previous_close = canonical_previous_close

        fast_volume = _safe_float(fast_info.get("last_volume"))
        fast_trade_time = market_quote.get("observed_at")
        if hasattr(fast_trade_time, "isoformat"):
            fast_trade_time = fast_trade_time.isoformat()
        elif fast_trade_time is not None:
            fast_trade_time = str(fast_trade_time)

        roe = _safe_float(info.get("returnOnEquity"))
        if roe is None:
            roe = _calculate_roe(ticker)

        roa = _safe_float(info.get("returnOnAssets"))
        if roa is None:
            roa = _calculate_roa(ticker)

        debt_to_equity = _safe_float(info.get("debtToEquity"))
        current_ratio = _safe_float(info.get("currentRatio"))
        if current_ratio is None:
            current_ratio = _calculate_current_ratio(ticker)

        revenue_growth = _safe_float(info.get("revenueGrowth"))
        earnings_growth = _safe_float(info.get("earningsGrowth"))

        operating_cash_flow = _safe_float(info.get("operatingCashflow"))
        if operating_cash_flow is None:
            operating_cash_flow = _calculate_operating_cash_flow(ticker)

        free_cash_flow = _safe_float(info.get("freeCashflow"))
        if free_cash_flow is None:
            free_cash_flow = _calculate_free_cash_flow(ticker)

        total_debt = _safe_float(info.get("totalDebt"))
        total_cash = _safe_float(info.get("totalCash"))

        forward_eps = _safe_float(info.get("forwardEps"))
        ebitda = _safe_float(info.get("ebitda"))
        enterprise_value = _safe_float(info.get("enterpriseValue"))
        shares_outstanding = _safe_float(info.get("sharesOutstanding"))
        total_revenue = _safe_float(info.get("totalRevenue"))
        net_income = _safe_float(info.get("netIncomeToCommon"))
        enterprise_to_ebitda = _safe_float(info.get("enterpriseToEbitda"))
        enterprise_to_revenue = _safe_float(info.get("enterpriseToRevenue"))

        return {
            "company": info.get("longName", "N/A"),
            "symbol": symbol,
            "exchange": market_quote.get("exchange", "BSE" if symbol.endswith(".BO") else "NSE"),
            "price": fast_price,
            "previous_close": fast_previous_close,
            "price_source": market_quote.get("source", "Yahoo Finance"),
            "price_observed_at": fast_trade_time,
            "volume": fast_volume,
            "roe": roe,
            "roa": roa,
            "debt_to_equity": debt_to_equity,
            "current_ratio": current_ratio,
            "revenue_growth": revenue_growth,
            "earnings_growth": earnings_growth,
            "operating_cash_flow": operating_cash_flow,
            "free_cash_flow": free_cash_flow,
            "total_debt": total_debt,
            "total_cash": total_cash,
            "forward_eps": forward_eps,
            "ebitda": ebitda,
            "enterprise_value": enterprise_value,
            "shares_outstanding": shares_outstanding,
            "total_revenue": total_revenue,
            "net_income": net_income,
            "enterprise_to_ebitda": enterprise_to_ebitda,
            "enterprise_to_revenue": enterprise_to_revenue,
            "market_state": "UNKNOWN",
        }
    except Exception as error:
        print(f"Stock Profile Error: {error}")
        return None
