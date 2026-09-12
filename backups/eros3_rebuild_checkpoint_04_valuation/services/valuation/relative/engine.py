from __future__ import annotations

import logging

from services.financials.financial_statement import FinancialStatements
from services.valuation.relative.models import RelativeValuationResult

logger = logging.getLogger(__name__)


class RelativeValuationEngine:
    """Engine computing relative valuation metrics (P/E, EV/EBITDA, EV/Sales, P/B, PEG) vs industry benchmarks."""

    def evaluate(
        self,
        financials: FinancialStatements,
        current_price: float = 1400.0,
        yahoo_ebitda: float | None = None,
        shares_outstanding: float | None = None,
    ) -> RelativeValuationResult:
        symbol = financials.ticker
        logger.info("Running Relative Valuation for symbol: %s", symbol)

        inc = financials.income_statement
        bs = financials.balance_sheet

        eps = inc.eps if inc and inc.eps > 0 else 45.0
        # EBITDA lineage:
        # 1. Prefer normalized EBITDA when available.
        # 2. Otherwise use explicitly supplied live Yahoo EBITDA.
        # 3. Never fabricate a unit-incompatible fallback.
        normalized_ebitda = getattr(inc, "ebitda", 0.0) if inc else 0.0

        if normalized_ebitda and normalized_ebitda > 0:
            ebitda = float(normalized_ebitda)
            ebitda_source = "normalized"
        elif yahoo_ebitda is not None and float(yahoo_ebitda) > 0:
            ebitda = float(yahoo_ebitda)
            ebitda_source = "yahoo"
        else:
            raise ValueError(
                f"EBITDA unavailable for {symbol}; "
                "Relative Valuation requires a valid normalized or Yahoo EBITDA value."
            )

        logger.info(
            "Relative Valuation EBITDA source=%s value=%s",
            ebitda_source,
            ebitda,
        )
        revenue = inc.revenue if inc else 1000000.0
        equity = getattr(bs, "shareholders_equity", 0.0)
        if not equity:
            equity = getattr(bs, "total_equity", 0.0)
        if not (bs and equity > 0):
            raise ValueError(
                f"Equity unavailable for {symbol}; "
                "Relative Valuation requires valid shareholders equity."
            )
        debt = (
            (
                (getattr(bs, "short_term_debt", 0.0) or 0.0)
                + (getattr(bs, "long_term_debt", getattr(bs, "debt", 0.0)) or 0.0)
            )
            if bs
            else 500000.0
        )
        cash = (
            ((getattr(bs, "cash", 0.0) or 0.0) + (getattr(bs, "cash_equivalents", 0.0) or 0.0))
            if bs
            else 300000.0
        )

        # Live shares lineage:
        # 1. Prefer explicitly supplied live shares.
        # 2. Otherwise use normalized shares if available.
        # 3. Never fabricate a unit-incompatible fallback.

        normalized_shares = getattr(inc, "shares_outstanding", 0.0) if inc else 0.0

        if shares_outstanding is not None and float(shares_outstanding) > 0:
            shares = float(shares_outstanding)
            shares_source = "explicit_live"
        elif normalized_shares and normalized_shares > 0:
            shares = float(normalized_shares)
            shares_source = "normalized"
        else:
            raise ValueError(
                f"Shares outstanding unavailable for {symbol}; "
                "Relative Valuation requires a valid live or normalized share count."
            )

        logger.info(
            "Relative Valuation shares source=%s value=%s",
            shares_source,
            shares,
        )

        market_cap = current_price * shares
        net_debt = debt - cash
        ev = market_cap + net_debt

        pe_ratio = round(current_price / eps, 2) if eps > 0 else 20.0
        ev_ebitda = round(ev / ebitda, 2) if ebitda > 0 else 12.0
        ev_sales = round(ev / revenue, 2) if revenue > 0 else 2.5
        pb_ratio = round(market_cap / equity, 2) if equity > 0 else 2.0
        peg_ratio = round(pe_ratio / 15.0, 2)  # Assuming 15% growth

        # Implied valuation based on sector median multiples (Sector P/E = 22, Sector EV/EBITDA = 14)
        implied_pe_val = eps * 22.0
        implied_ev_ebitda_val = (ebitda * 14.0 - net_debt) / shares
        blend_val = round((implied_pe_val + implied_ev_ebitda_val) / 2.0, 2)

        benchmarks = {
            "sector_pe": 22.0,
            "sector_ev_ebitda": 14.0,
            "industry": "Conglomerate / Energy",
        }

        return RelativeValuationResult(
            symbol=symbol,
            pe_ratio=pe_ratio,
            ev_ebitda=ev_ebitda,
            ev_sales=ev_sales,
            pb_ratio=pb_ratio,
            peg_ratio=peg_ratio,
            implied_value_pe=round(implied_pe_val, 2),
            implied_value_ev_ebitda=round(implied_ev_ebitda_val, 2),
            blend_relative_value=blend_val,
            comparison_benchmarks=benchmarks,
        )
