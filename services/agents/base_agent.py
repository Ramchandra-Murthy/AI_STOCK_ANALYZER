from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class AgentOpinion:
    agent_name: str
    recommendation: str  # "BUY", "HOLD", "SELL"
    confidence: float
    evidence: list[str]
    risks: list[str]
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())


class BaseSpecialistAgent(ABC):
    """Abstract base class for all MARIN specialist AI agents."""

    @property
    @abstractmethod
    def agent_name(self) -> str:
        pass

    @abstractmethod
    def evaluate(self, symbol: str) -> AgentOpinion:
        pass


class ValuationAgent(BaseSpecialistAgent):
    @property
    def agent_name(self) -> str:
        return "ValuationAgent"

    def evaluate(self, symbol: str) -> AgentOpinion:
        return AgentOpinion(
            agent_name=self.agent_name,
            recommendation="BUY",
            confidence=0.94,
            evidence=["DCF Upside: +15%", "Blended fair value ₹3,420"],
            risks=["WACC sensitivity to interest rate hikes"],
        )


class QualityAgent(BaseSpecialistAgent):
    @property
    def agent_name(self) -> str:
        return "QualityAgent"

    def evaluate(self, symbol: str) -> AgentOpinion:
        return AgentOpinion(
            agent_name=self.agent_name,
            recommendation="BUY",
            confidence=0.91,
            evidence=["ROIC (19%) > WACC (10%)", "Consistent cash conversion"],
            risks=["Working capital intensity in retail expansion"],
        )


class MarketAgent(BaseSpecialistAgent):
    @property
    def agent_name(self) -> str:
        return "MarketAgent"

    def evaluate(self, symbol: str) -> AgentOpinion:
        return AgentOpinion(
            agent_name=self.agent_name,
            recommendation="BUY",
            confidence=0.87,
            evidence=["Strong relative strength in sector", "Institutional accumulation"],
            risks=["Broad market volatility"],
        )


class RiskAgent(BaseSpecialistAgent):
    @property
    def agent_name(self) -> str:
        return "RiskAgent"

    def evaluate(self, symbol: str) -> AgentOpinion:
        return AgentOpinion(
            agent_name=self.agent_name,
            recommendation="HOLD",
            confidence=0.72,
            evidence=["Debt-to-equity within acceptable bounds"],
            risks=["Elevated financial leverage relative to peers"],
        )
