from __future__ import annotations

from copy import deepcopy
from typing import Any

from scanner.market_scanner import market_scan
from services.analyzer import analyze_stock
from services.quantitative.block109_institutional_application_query_gateway import (
    EROSBlock109InstitutionalApplicationQueryGateway,
)


class EROSFrontendAdapter:
    """
    EROS 3.0 read-only frontend adapter.

    Purpose:
        Provide a stable interface between the Streamlit frontend
        and the existing EROS / AI Stock Analyzer services.

    Safety:
        - Read only
        - No order creation
        - No broker submission
        - No live execution
        - No portfolio mutation
        - No valuation mutation
        - No performance mutation
        - No risk mutation
        - No optimization
    """

    VERSION = "1.0"

    SAFETY_POLICY = {
        "read_only": True,
        "allow_order_creation": False,
        "allow_broker_submission": False,
        "allow_live_execution": False,
        "allow_portfolio_mutation": False,
        "allow_valuation_mutation": False,
        "allow_performance_mutation": False,
        "allow_risk_mutation": False,
        "allow_optimization": False,
        "execution_blocked": True,
        "non_mutation_invariant": True,
    }

    def __init__(self) -> None:

        self._query_gateway = EROSBlock109InstitutionalApplicationQueryGateway()

    # ==========================================================
    # GOVERNANCE
    # ==========================================================

    def governance(self) -> dict[str, Any]:
        """
        Return the frontend-visible EROS governance state.
        """

        return {
            "system": "EROS 3.0",
            "status": "CERTIFIED",
            "query_gateway": {
                "block_id": "109",
                "name": ("Institutional Application Query Gateway"),
                "status": "CERTIFIED",
            },
            "safety": deepcopy(self.SAFETY_POLICY),
        }

    # ==========================================================
    # STOCK ANALYSIS
    # ==========================================================

    def stock_analysis(
        self,
        symbol: str,
    ) -> dict[str, Any]:
        """
        Read-only stock analysis using the existing
        AI Stock Analyzer service.
        """

        if not isinstance(symbol, str):
            raise TypeError("symbol must be a string")

        symbol = symbol.strip().upper()

        if not symbol:
            raise ValueError("symbol cannot be empty")

        result = analyze_stock(symbol)

        return result

    # ==========================================================
    # MARKET SCANNER
    # ==========================================================

    def market_scan(self):
        """
        Read-only market scanner.

        Returns the existing scanner dataframe.
        """

        return market_scan()

    # ==========================================================
    # DASHBOARD SNAPSHOT
    # ==========================================================

    def dashboard_snapshot(
        self,
    ) -> dict[str, Any]:
        """
        Return a frontend-safe dashboard snapshot.
        """

        governance = self.governance()

        return {
            "system": {
                "name": "EROS 3.0",
                "description": ("Institutional Intelligence " "Command Center"),
                "status": "CERTIFIED",
            },
            "gateway": governance["query_gateway"],
            "safety": governance["safety"],
        }

    # ==========================================================
    # SNAPSHOT
    # ==========================================================

    def snapshot(self) -> dict[str, Any]:
        """
        Return immutable frontend adapter metadata.
        """

        return {
            "name": "EROSFrontendAdapter",
            "version": self.VERSION,
            "source": "Block 109",
            "mode": "READ_ONLY",
            "safety": deepcopy(self.SAFETY_POLICY),
        }
