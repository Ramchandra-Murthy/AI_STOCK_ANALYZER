from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from services.monitoring.investment_monitor import InvestmentMonitoringSnapshot


@dataclass(frozen=True, slots=True)
class ChangeRecord:
    metric: str
    previous_value: Any
    current_value: Any
    absolute_change: float
    direction: str  # "IMPROVED", "DETERIORATED", "UNCHANGED", "CHANGED"
    severity: str  # "LOW", "MEDIUM", "HIGH", "CRITICAL"
    reason: str


@dataclass(frozen=True, slots=True)
class ChangeDetectionReport:
    symbol: str
    changes_detected: int
    high_severity_changes: int
    changes: list[ChangeRecord]
    details: dict[str, Any]


class InvestmentChangeDetector:
    """
    EROS 3.0 Block 20B Investment Change Detector.
    Compares two InvestmentMonitoringSnapshot states and flags institutional score, risk, and action deviations.
    """

    @staticmethod
    def detect_changes(
        previous: InvestmentMonitoringSnapshot, current: InvestmentMonitoringSnapshot
    ) -> ChangeDetectionReport:
        changes: list[ChangeRecord] = []

        def check_score_metric(
            name: str, prev_val: float, curr_val: float, threshold: float = 5.0
        ) -> None:
            diff = curr_val - prev_val
            abs_diff = abs(diff)
            if abs_diff >= threshold:
                direction = "IMPROVED" if diff > 0 else "DETERIORATED"
                severity = "HIGH" if abs_diff >= 15.0 else ("MEDIUM" if abs_diff >= 8.0 else "LOW")
                changes.append(
                    ChangeRecord(
                        metric=name,
                        previous_value=prev_val,
                        current_value=curr_val,
                        absolute_change=round(abs_diff, 2),
                        direction=direction,
                        severity=severity,
                        reason=f"{name} shifted by {diff:+.2f} points ({direction.lower()}).",
                    )
                )

        # Check numeric scores
        check_score_metric("Composite Score", previous.composite_score, current.composite_score)
        check_score_metric("Risk Score", previous.risk_score, current.risk_score)
        check_score_metric("Valuation Score", previous.valuation_score, current.valuation_score)
        check_score_metric("Momentum Score", previous.momentum_score, current.momentum_score)
        check_score_metric("Research Score", previous.research_score, current.research_score)
        check_score_metric("Confidence Score", previous.confidence_score, current.confidence_score)
        check_score_metric("Moat Score", previous.moat_score, current.moat_score)

        # Check Rating change
        if previous.rating != current.rating:
            changes.append(
                ChangeRecord(
                    metric="Rating Change",
                    previous_value=previous.rating,
                    current_value=current.rating,
                    absolute_change=1.0,
                    direction="CHANGED",
                    severity="HIGH",
                    reason=f"Rating shifted from {previous.rating} to {current.rating}.",
                )
            )

        # Check Action change
        if previous.action != current.action:
            changes.append(
                ChangeRecord(
                    metric="Action Change",
                    previous_value=previous.action,
                    current_value=current.action,
                    absolute_change=1.0,
                    direction="CHANGED",
                    severity="CRITICAL",
                    reason=f"Investment action shifted from {previous.action} to {current.action}.",
                )
            )

        # Check Portfolio Weight change (> 2% shift)
        weight_diff = current.portfolio_weight - previous.portfolio_weight
        if abs(weight_diff) >= 0.02:
            changes.append(
                ChangeRecord(
                    metric="Portfolio Weight",
                    previous_value=previous.portfolio_weight,
                    current_value=current.portfolio_weight,
                    absolute_change=round(abs(weight_diff), 4),
                    direction="IMPROVED" if weight_diff > 0 else "DETERIORATED",
                    severity="MEDIUM" if abs(weight_diff) >= 0.05 else "LOW",
                    reason=f"Portfolio target weight shifted by {weight_diff*100:+.2f}%.",
                )
            )

        high_sev = sum(1 for c in changes if c.severity in ("HIGH", "CRITICAL"))

        return ChangeDetectionReport(
            symbol=current.symbol,
            changes_detected=len(changes),
            high_severity_changes=high_sev,
            changes=changes,
            details={
                "engine_version": "EROS-3.0-BLOCK-20B",
                "previous_timestamp": previous.timestamp,
                "current_timestamp": current.timestamp,
            },
        )
