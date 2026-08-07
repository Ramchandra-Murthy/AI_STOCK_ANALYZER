from __future__ import annotations

import logging
from typing import List, Dict, Any
from services.committee.models import AnalystOpinion, CommitteeDecision

logger = logging.getLogger(__name__)

class ArtificialCIO:
    """Artificial Chief Investment Officer (CIO) responsible for weighting specialist opinions, resolving conflicts, and synthesizing consensus."""

    DEPARTMENT_WEIGHTS: Dict[str, float] = {
        "Valuation Analyst": 0.25,
        "Quality Analyst": 0.20,
        "Risk Analyst": 0.20,
        "Management Analyst": 0.15,
        "Economic Moat Analyst": 0.10,
        "Market Analyst": 0.05,
        "Macro Analyst": 0.05
    }

    @classmethod
    def synthesize(cls, symbol: str, opinions: List[AnalystOpinion]) -> CommitteeDecision:
        logger.info("Artificial CIO synthesizing %d department opinions for %s", len(opinions), symbol)

        if not opinions:
            raise ValueError(f"Cannot synthesize committee decision without opinions for {symbol}.")

        total_weight = 0.0
        weighted_score_sum = 0.0
        weighted_conf_sum = 0.0

        all_strengths: List[str] = []
        all_concerns: List[str] = []
        all_evidence: List[str] = []

        buy_weight = 0.0
        hold_weight = 0.0
        sell_weight = 0.0

        for op in opinions:
            weight = cls.DEPARTMENT_WEIGHTS.get(op.department, 0.10)
            total_weight += weight

            weighted_score_sum += op.score * weight
            weighted_conf_sum += op.confidence * weight

            if op.signal == "BUY":
                buy_weight += weight
            elif op.signal == "HOLD":
                hold_weight += weight
            elif op.signal == "SELL":
                sell_weight += weight

            all_strengths.extend(op.strengths)
            all_concerns.extend(op.concerns)
            all_evidence.extend(op.evidence)

        norm_weight = max(total_weight, 0.01)
        final_score = round(weighted_score_sum / norm_weight, 2)
        final_confidence = round(weighted_conf_sum / norm_weight, 2)

        if buy_weight >= hold_weight and buy_weight >= sell_weight:
            consensus = "BUY"
        elif sell_weight > buy_weight and sell_weight >= hold_weight:
            consensus = "SELL"
        else:
            consensus = "HOLD"

        risk_summary = "; ".join(set(all_concerns[:3])) if all_concerns else "No material risk factors identified."
        narrative = (
            f"Artificial Investment Committee consensus for {symbol}: "
            f"Recommended action is {consensus} with an aggregate confidence of {int(final_confidence * 100)}% "
            f"and a weighted institutional score of {final_score}/100. "
            f"Primary supporting evidence points to robust fundamental drivers. "
            f"Principal monitored risks: {risk_summary}."
        )

        return CommitteeDecision(
            symbol=symbol,
            consensus_signal=consensus,
            overall_confidence=final_confidence,
            weighted_score=final_score,
            analyst_opinions=opinions,
            supporting_evidence=list(set(all_evidence)),
            major_risks=list(set(all_concerns)),
            cio_narrative=narrative
        )
