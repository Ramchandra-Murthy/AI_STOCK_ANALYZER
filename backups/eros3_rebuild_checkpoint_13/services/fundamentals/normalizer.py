from __future__ import annotations

import logging
from typing import Any

from services.financials.balance_sheet import BalanceSheet
from services.financials.cash_flow import CashFlowStatement
from services.financials.financial_statement import (
    FinancialStatements,
    PeriodFinancials,
)
from services.financials.income_statement import IncomeStatement

logger = logging.getLogger(__name__)


def _float(value: Any) -> float:
    """Safely convert provider values to float."""
    if value is None:
        return 0.0

    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


class FinancialNormalizer:
    """Normalize provider payloads into canonical FinancialStatements."""

    def normalize(self, raw_data: dict[str, Any]) -> FinancialStatements:
        symbol = str(raw_data.get("symbol", "RELIANCE.NS"))
        provider = str(raw_data.get("provider", "YahooFinance"))

        logger.info(
            "Normalizing financial data for symbol: %s from provider: %s",
            symbol,
            provider,
        )

        # Support both current plural provider payloads
        # and legacy singular payloads.
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

        income_by_period = {
            str(item.get("period", "UNKNOWN")): item
            for item in raw_income
        }

        balance_by_period = {
            str(item.get("period", "UNKNOWN")): item
            for item in raw_balance
        }

        cashflow_by_period = {
            str(item.get("period", "UNKNOWN")): item
            for item in raw_cashflow
        }

        periods = sorted(
            set(income_by_period)
            | set(balance_by_period)
            | set(cashflow_by_period)
        )

        period_financials: list[PeriodFinancials] = []

        for period in periods:
            income_raw = income_by_period.get(period, {})
            balance_raw = balance_by_period.get(period, {})
            cashflow_raw = cashflow_by_period.get(period, {})

            income = IncomeStatement(
                period=period,
                revenue=_float(income_raw.get("revenue")),
                operating_income=_float(
                    income_raw.get("operating_income")
                ),
                other_operating_income=_float(
                    income_raw.get("other_operating_income")
                ),
                total_operating_income=_float(
                    income_raw.get(
                        "total_operating_income",
                        income_raw.get("operating_income"),
                    )
                ),
                cost_of_goods_sold=_float(
                    income_raw.get("cost_of_goods_sold")
                ),
                operating_expenses=_float(
                    income_raw.get("operating_expenses")
                ),
                depreciation_and_amortization=_float(
                    income_raw.get("depreciation_and_amortization")
                ),
                ebitda=_float(income_raw.get("ebitda")),
                ebit=_float(income_raw.get("ebit")),
                finance_cost=_float(income_raw.get("finance_cost")),
                finance_income=_float(income_raw.get("finance_income")),
                profit_before_tax=_float(
                    income_raw.get("profit_before_tax")
                ),
                tax_expense=_float(income_raw.get("tax_expense")),
                net_income=_float(income_raw.get("net_income")),
                shares_outstanding=_float(
                    income_raw.get("shares_outstanding")
                ),
                eps=_float(income_raw.get("eps")),
            )

            balance = BalanceSheet(
                period=period,
                cash=_float(balance_raw.get("cash")),
                cash_equivalents=_float(
                    balance_raw.get("cash_equivalents")
                ),
                short_term_investments=_float(
                    balance_raw.get("short_term_investments")
                ),
                accounts_receivable=_float(
                    balance_raw.get("accounts_receivable")
                ),
                inventory=_float(balance_raw.get("inventory")),
                other_current_assets=_float(
                    balance_raw.get("other_current_assets")
                ),
                total_current_assets=_float(
                    balance_raw.get("total_current_assets")
                ),
                property_plant_equipment=_float(
                    balance_raw.get("property_plant_equipment")
                ),
                right_of_use_assets=_float(
                    balance_raw.get("right_of_use_assets")
                ),
                goodwill=_float(balance_raw.get("goodwill")),
                intangible_assets=_float(
                    balance_raw.get("intangible_assets")
                ),
                long_term_investments=_float(
                    balance_raw.get("long_term_investments")
                ),
                associates_and_joint_ventures=_float(
                    balance_raw.get("associates_and_joint_ventures")
                ),
                deferred_tax_assets=_float(
                    balance_raw.get("deferred_tax_assets")
                ),
                other_non_current_assets=_float(
                    balance_raw.get("other_non_current_assets")
                ),
                total_non_current_assets=_float(
                    balance_raw.get("total_non_current_assets")
                ),
                total_assets=_float(
                    balance_raw.get("total_assets")
                ),
                accounts_payable=_float(
                    balance_raw.get("accounts_payable")
                ),
                short_term_debt=_float(
                    balance_raw.get("short_term_debt")
                ),
                current_lease_liabilities=_float(
                    balance_raw.get("current_lease_liabilities")
                ),
                accrued_expenses=_float(
                    balance_raw.get("accrued_expenses")
                ),
                other_current_liabilities=_float(
                    balance_raw.get("other_current_liabilities")
                ),
                total_current_liabilities=_float(
                    balance_raw.get("total_current_liabilities")
                ),
                long_term_debt=_float(
                    balance_raw.get("long_term_debt")
                ),
                long_term_lease_liabilities=_float(
                    balance_raw.get("long_term_lease_liabilities")
                ),
                deferred_tax_liabilities=_float(
                    balance_raw.get("deferred_tax_liabilities")
                ),
                pension_liabilities=_float(
                    balance_raw.get("pension_liabilities")
                ),
                other_non_current_liabilities=_float(
                    balance_raw.get("other_non_current_liabilities")
                ),
                total_non_current_liabilities=_float(
                    balance_raw.get("total_non_current_liabilities")
                ),
                total_liabilities=_float(
                    balance_raw.get("total_liabilities")
                ),
                share_capital=_float(
                    balance_raw.get("share_capital")
                ),
                retained_earnings=_float(
                    balance_raw.get("retained_earnings")
                ),
                reserves=_float(balance_raw.get("reserves")),
                minority_interest=_float(
                    balance_raw.get("minority_interest")
                ),
                total_equity=_float(
                    balance_raw.get(
                        "total_equity",
                        balance_raw.get("shareholders_equity"),
                    )
                ),
                shareholders_equity=_float(
                    balance_raw.get("shareholders_equity")
                ),
                debt=_float(balance_raw.get("debt")),
            )

            cashflow = CashFlowStatement(
                period=period,
                net_income=_float(
                    cashflow_raw.get("net_income")
                ),
                depreciation_and_amortization=_float(
                    cashflow_raw.get("depreciation_and_amortization")
                ),
                share_based_compensation=_float(
                    cashflow_raw.get("share_based_compensation")
                ),
                deferred_tax=_float(
                    cashflow_raw.get("deferred_tax")
                ),
                change_in_working_capital=_float(
                    cashflow_raw.get("change_in_working_capital")
                ),
                other_operating_items=_float(
                    cashflow_raw.get("other_operating_items")
                ),
                operating_cash_flow=_float(
                    cashflow_raw.get("operating_cash_flow")
                ),
                capital_expenditure=_float(
                    cashflow_raw.get(
                        "capital_expenditure",
                        cashflow_raw.get("capex"),
                    )
                ),
                capex=_float(cashflow_raw.get("capex")),
                acquisitions=_float(
                    cashflow_raw.get("acquisitions")
                ),
                asset_sales=_float(
                    cashflow_raw.get("asset_sales")
                ),
                investment_purchases=_float(
                    cashflow_raw.get("investment_purchases")
                ),
                investment_sales=_float(
                    cashflow_raw.get("investment_sales")
                ),
                investing_cash_flow=_float(
                    cashflow_raw.get("investing_cash_flow")
                ),
                debt_issued=_float(
                    cashflow_raw.get("debt_issued")
                ),
                debt_repaid=_float(
                    cashflow_raw.get("debt_repaid")
                ),
                dividends_paid=_float(
                    cashflow_raw.get("dividends_paid")
                ),
                share_repurchases=_float(
                    cashflow_raw.get("share_repurchases")
                ),
                equity_issued=_float(
                    cashflow_raw.get("equity_issued")
                ),
                financing_cash_flow=_float(
                    cashflow_raw.get("financing_cash_flow")
                ),
                net_change_in_cash=_float(
                    cashflow_raw.get("net_change_in_cash")
                ),
                beginning_cash=_float(
                    cashflow_raw.get("beginning_cash")
                ),
                ending_cash=_float(
                    cashflow_raw.get("ending_cash")
                ),
                free_cash_flow=_float(
                    cashflow_raw.get("free_cash_flow")
                ),
            )

            period_financials.append(
                PeriodFinancials(
                    period=period,
                    income_statement=income,
                    balance_sheet=balance,
                    cash_flow_statement=cashflow,
                )
            )

        if not period_financials:
            raise ValueError(
                f"No usable financial periods found for {symbol}"
            )

        # Use the first available period as the canonical current statement.
        primary = period_financials[0]

        return FinancialStatements(
            company_name=symbol,
            ticker=symbol,
            currency=str(raw_data.get("currency", "INR")),
            fiscal_year=primary.period,
            income_statement=primary.income_statement,
            balance_sheet=primary.balance_sheet,
            cash_flow_statement=primary.cash_flow_statement,
            periods=period_financials,
            metadata={
                "provider": provider,
                "period_count": len(period_financials),
            },
        )