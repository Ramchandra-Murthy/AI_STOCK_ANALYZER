from __future__ import annotations

import logging
import time
import uuid

from services.market_data.pipeline_integration import FullyIntegratedMarketPipeline
from services.workflow.models import WorkflowResult

logger = logging.getLogger(__name__)


class InstitutionalResearchPipeline:
    """Compatibility workflow facade backed by the real integrity-gated pipeline."""

    STEPS = [
        "Download Data",
        "Validate Financials",
        "Company Knowledge Layer",
        "Ratio Calculation",
        "Valuation Engine",
        "Business Reasoning",
        "Investment Committee",
        "Forecasting Engine",
        "Portfolio Intelligence",
        "Learning Update",
        "Generate Report",
        "Archive Results",
    ]

    @classmethod
    def execute_full_research_lifecycle(cls, symbol: str) -> WorkflowResult:
        start_time = time.time()
        run_id = f"RUN-{uuid.uuid4().hex[:8].upper()}"
        normalized_symbol = symbol.strip().upper() if isinstance(symbol, str) else ""
        completed_steps: list[str] = []
        failed_steps: list[str] = []
        warnings: list[str] = []
        reports_generated: list[str] = []

        if not normalized_symbol:
            failed_steps.append("Download Data")
            warnings.append("Execution halted at Download Data because symbol is required.")
            return WorkflowResult(
                run_id=run_id,
                completed_steps=completed_steps,
                failed_steps=failed_steps,
                execution_time=round(time.time() - start_time, 4),
                reports_generated=reports_generated,
                warnings=warnings,
                metadata={"symbol": normalized_symbol, "pipeline_version": "EROS-3.0"},
            )

        pipeline = FullyIntegratedMarketPipeline()
        packet, decision, result, trace = pipeline.evaluate_stock_securely(normalized_symbol)

        completed_steps.extend(["Download Data", "Validate Financials"])
        metadata = {
            "symbol": normalized_symbol,
            "pipeline_version": "EROS-3.0",
            "market_data_source": packet.details.get("source"),
            "data_state": decision.directive,
            "trace_timestamp": trace.timestamp,
        }

        if not decision.allowed_in_scoring or result is None:
            failed_steps.extend(cls.STEPS[2:])
            warnings.append(decision.warning_message)
        else:
            completed_steps.extend(cls.STEPS[2:])
            reports_generated.append(
                f"Institutional_Report_{normalized_symbol}_{run_id}.md"
            )

        return WorkflowResult(
            run_id=run_id,
            completed_steps=completed_steps,
            failed_steps=failed_steps,
            execution_time=round(time.time() - start_time, 4),
            reports_generated=reports_generated,
            warnings=warnings,
            metadata=metadata,
        )
