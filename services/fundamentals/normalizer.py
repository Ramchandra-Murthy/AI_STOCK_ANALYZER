from __future__ import annotations

import logging
from typing import Any
from services.fundamentals.models import (
    BalanceSheet,
    CashFlowStatement,
    FinancialStatements,
    IncomeStatement,
)

logger = logging.getLogger(__name__)


class FinancialNormalizer:
    """Normalizes raw provider payloads into canonical immutable FinancialStatements objects."""

    def normalize(self, raw_data: dict[str, Any]) -> FinancialStatements:
        symbol = raw_data.get("symbol", "RELIANCE.NS")
        provider = raw_data.get("provider", "YahooFinance")
        logger.info("Normalizing financial data for symbol: %s from provider: %s", symbol, provider)

        raw_inc = raw_data.get("income_statement", {})
        raw_bs = raw_data.get("balance_sheet", {})
        raw_cf = raw_data.get("cash_flow", {})

        inc = IncomeStatement(
            period=raw_inc.get("period", "FY2025"),
            revenue=float(raw_inc.get("revenue", 0.0)),
            operating_income=float(raw_inc.get("operating_income", 0.0)),
            ebit=float(raw_inc.get("ebit", 0.0)),
            net_income=float(raw_inc.get("net_income", 0.0)),
            eps=float(raw_inc.get("eps", 0.0)),
        )

        bs = BalanceSheet(
            period=raw_bs.get("period", "FY2025"),
            total_assets=float(raw_bs.get("total_assets", 0.0)),
            total_liabilities=float(raw_bs.get("total_liabilities", 0.0)),
            shareholders_equity=float(raw_bs.get("shareholders_equity", 0.0)),
            cash=float(raw_bs.get("cash", 0.0)),
            debt=float(raw_bs.get("debt", 0.0)),
        )

        cf = CashFlowStatement(
            period=raw_cf.get("period", "FY2025"),
            operating_cash_flow=float(raw_cf.get("operating_cash_flow", 0.0)),
            capex=float(raw_cf.get("capex", 0.0)),
            free_cash_flow=float(raw_cf.get("free_cash_flow", 0.0)),
            investing_cash_flow=float(raw_cf.get("investing_cash_flow", 0.0)),
            financing_cash_flow=float(raw_cf.get("financing_cash_flow", 0.0)),
        )

        return FinancialStatements(
            symbol=symbol,
            income_statements=[inc],
            balance_sheets=[bs],
            cash_flows=[cf],
            metadata={"provider": provider},
        )
