from __future__ import annotations

import logging
from typing import Any

from services.fundamentals.models import (
    BalanceSheet,
    CashFlowStatement,
    FinancialStatements,
)
from services.financials.income_statement import IncomeStatement

logger = logging.getLogger(__name__)


class FinancialNormalizer:
    """Normalize provider payloads into canonical FinancialStatements objects."""

    def normalize(self, raw_data: dict[str, Any]) -> FinancialStatements:
        symbol = raw_data.get("symbol", "RELIANCE.NS")
        provider = raw_data.get("provider", "YahooFinance")

        logger.info(
            "Normalizing financial data for symbol: %s from provider: %s",
            symbol,
            provider,
        )

        raw_income = raw_data.get("income_statements")
        if raw_income is None:
            legacy_income = raw_data.get("income_statement", {})
            raw_income = [legacy_income] if legacy_income else []

        raw_balance = raw_data.get("balance_sheets")
        if raw_balance is None:
            legacy_balance = raw_data.get("balance_sheet", {})
            raw_balance = [legacy_balance] if legacy_balance else []

        raw_cashflow = raw_data.get("cash_flows")
        if raw_cashflow is None:
            legacy_cashflow = raw_data.get("cash_flow", {})
            raw_cashflow = [legacy_cashflow] if legacy_cashflow else []

        income_statements = []

        for item in raw_income:
            income_statements.append(
                IncomeStatement(
                    period=str(item.get("period", "UNKNOWN")),
                    revenue=float(item.get("revenue", 0.0)),
                    other_operating_income=float(
                        item.get("other_operating_income", 0.0)
                    ),
                    total_operating_income=float(
                        item.get(
                            "total_operating_income",
                            item.get("operating_income", 0.0),
                        )
                    ),
                    cost_of_goods_sold=float(
                        item.get("cost_of_goods_sold", 0.0)
                    ),
                    operating_expenses=float(
                        item.get("operating_expenses", 0.0)
                    ),
                    depreciation_and_amortization=float(
                        item.get("depreciation_and_amortization", 0.0)
                    ),
                    ebitda=float(item.get("ebitda", 0.0)),
                    ebit=float(item.get("ebit", 0.0)),
                    finance_cost=float(item.get("finance_cost", 0.0)),
                    finance_income=float(item.get("finance_income", 0.0)),
                    profit_before_tax=float(
                        item.get("profit_before_tax", 0.0)
                    ),
                    tax_expense=float(item.get("tax_expense", 0.0)),
                    net_income=float(item.get("net_income", 0.0)),
                    shares_outstanding=float(
                        item.get("shares_outstanding", 0.0)
                    ),
                    eps=float(item.get("eps", 0.0)),
                )
            )

        balance_sheets = []

        for item in raw_balance:
            balance_sheets.append(
                BalanceSheet(
                    period=str(item.get("period", "UNKNOWN")),
                    cash=float(item.get("cash", 0.0)),
                    cash_equivalents=float(
                        item.get("cash_equivalents", 0.0)
                    ),
                    short_term_investments=float(
                        item.get("short_term_investments", 0.0)
                    ),
                    accounts_receivable=float(
                        item.get("accounts_receivable", 0.0)
                    ),
                    inventory=float(item.get("inventory", 0.0)),
                    total_current_assets=float(
                        item.get("total_current_assets", 0.0)
                    ),
                    total_assets=float(item.get("total_assets", 0.0)),
                    short_term_debt=float(
                        item.get("short_term_debt", 0.0)
                    ),
                    total_current_liabilities=float(
                        item.get("total_current_liabilities", 0.0)
                    ),
                    long_term_debt=float(
                        item.get(
                            "long_term_debt",
                            item.get("debt", 0.0),
                        )
                    ),
                    total_liabilities=float(
                        item.get("total_liabilities", 0.0)
                    ),
                    total_equity=float(
                        item.get(
                            "total_equity",
                            item.get("shareholders_equity", 0.0),
                        )
                    ),
                )
            )

        cash_flows = []

        for item in raw_cashflow:
            cash_flows.append(
                CashFlowStatement(
                    period=str(item.get("period", "UNKNOWN")),
                    operating_cash_flow=float(
                        item.get("operating_cash_flow", 0.0)
                    ),
                    capital_expenditure=float(
                        item.get(
                            "capital_expenditure",
                            item.get("capex", 0.0),
                        )
                    ),
                    investing_cash_flow=float(
                        item.get("investing_cash_flow", 0.0)
                    ),
                    financing_cash_flow=float(
                        item.get("financing_cash_flow", 0.0)
                    ),
                )
            )

        return FinancialStatements(
            symbol=symbol,
            income_statements=income_statements,
            balance_sheets=balance_sheets,
            cash_flows=cash_flows,
            metadata={
                "provider": provider,
            },
        )
