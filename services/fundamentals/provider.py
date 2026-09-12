from __future__ import annotations

import logging
from typing import Any, Protocol, runtime_checkable

import pandas as pd
import yfinance as yf

logger = logging.getLogger(__name__)


@runtime_checkable
class IFundamentalProvider(Protocol):
    """Protocol defining interface for fundamental data providers."""

    def download(self, symbol: str) -> dict[str, Any]: ...


class YahooFinanceProvider:
    """Yahoo Finance adapter implementing IFundamentalProvider."""

    @staticmethod
    def _safe_value(frame: pd.DataFrame, row: str, column: Any) -> float:
        try:
            if row not in frame.index:
                return 0.0

            value = frame.loc[row, column]

            if pd.isna(value):
                return 0.0

            return float(value)
        except (TypeError, ValueError, KeyError):
            return 0.0

    @staticmethod
    def _period(column: Any) -> str:
        try:
            return pd.Timestamp(column).strftime("%Y-%m-%d")
        except Exception:
            return str(column)

    def download(self, symbol: str) -> dict[str, Any]:
        logger.info(
            "Downloading real financials from Yahoo Finance for symbol: %s",
            symbol,
        )

        ticker = yf.Ticker(symbol)

        income = ticker.income_stmt
        balance = ticker.balance_sheet
        cashflow = ticker.cashflow

        if income is None or income.empty:
            raise RuntimeError(f"Yahoo Finance returned no income statement for {symbol}")

        if balance is None or balance.empty:
            raise RuntimeError(f"Yahoo Finance returned no balance sheet for {symbol}")

        if cashflow is None or cashflow.empty:
            raise RuntimeError(f"Yahoo Finance returned no cash flow statement for {symbol}")

        income_records = []
        balance_records = []
        cashflow_records = []

        columns = list(income.columns)

        for column in columns:
            revenue = self._safe_value(income, "Total Revenue", column)
            operating_income = self._safe_value(income, "Operating Income", column)
            ebit = self._safe_value(income, "EBIT", column)
            net_income = self._safe_value(income, "Net Income", column)

            eps = self._safe_value(income, "Diluted EPS", column)

            if eps == 0.0:
                eps = self._safe_value(income, "Basic EPS", column)

            if revenue == 0.0 and ebit == 0.0 and net_income == 0.0:
                continue

            income_records.append(
                {
                    "period": self._period(column),
                    "revenue": revenue,
                    "operating_income": operating_income,
                    "ebit": ebit,
                    "net_income": net_income,
                    "eps": eps,
                }
            )

        for column in list(balance.columns):
            total_assets = self._safe_value(balance, "Total Assets", column)
            total_liabilities = self._safe_value(
                balance,
                "Total Liabilities Net Minority Interest",
                column,
            )
            shareholders_equity = self._safe_value(
                balance,
                "Stockholders Equity",
                column,
            )

            if shareholders_equity == 0.0:
                shareholders_equity = self._safe_value(
                    balance,
                    "Common Stock Equity",
                    column,
                )

            cash = self._safe_value(
                balance,
                "Cash Cash Equivalents And Short Term Investments",
                column,
            )

            debt = self._safe_value(balance, "Total Debt", column)

            if total_assets == 0.0 and total_liabilities == 0.0 and shareholders_equity == 0.0:
                continue

            balance_records.append(
                {
                    "period": self._period(column),
                    "total_assets": total_assets,
                    "total_liabilities": total_liabilities,
                    "shareholders_equity": shareholders_equity,
                    "cash": cash,
                    "debt": debt,
                }
            )

        for column in list(cashflow.columns):
            operating_cash_flow = self._safe_value(
                cashflow,
                "Operating Cash Flow",
                column,
            )

            raw_capex = self._safe_value(
                cashflow,
                "Capital Expenditure",
                column,
            )

            capex = abs(raw_capex)

            free_cash_flow = self._safe_value(
                cashflow,
                "Free Cash Flow",
                column,
            )

            if free_cash_flow == 0.0 and operating_cash_flow != 0.0:
                free_cash_flow = operating_cash_flow - capex

            investing_cash_flow = self._safe_value(
                cashflow,
                "Investing Cash Flow",
                column,
            )

            financing_cash_flow = self._safe_value(
                cashflow,
                "Financing Cash Flow",
                column,
            )

            if operating_cash_flow == 0.0 and capex == 0.0 and free_cash_flow == 0.0:
                continue

            cashflow_records.append(
                {
                    "period": self._period(column),
                    "operating_cash_flow": operating_cash_flow,
                    "capex": capex,
                    "free_cash_flow": free_cash_flow,
                    "investing_cash_flow": investing_cash_flow,
                    "financing_cash_flow": financing_cash_flow,
                }
            )

        if not income_records:
            raise RuntimeError(f"No usable income records found for {symbol}")

        return {
            "symbol": symbol,
            "provider": "YahooFinance",
            "income_statements": income_records,
            "balance_sheets": balance_records,
            "cash_flows": cashflow_records,
        }
