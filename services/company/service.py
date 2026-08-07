from __future__ import annotations

import logging
from typing import Dict, Any, List
from services.company.models import CompanyIdentity, PeriodSnapshot, CompanyRecord
from services.company.repository import InMemoryCompanyRepository

logger = logging.getLogger(__name__)

class CompanyKnowledgeService:
    """Orchestrates company registry operations, historical tracking, and automated delta analysis."""

    def __init__(self, repository: InMemoryCompanyRepository) -> None:
        self.repo = repository

    def register_company(self, identity: CompanyIdentity) -> CompanyRecord:
        existing = self.repo.get_company(identity.symbol)
        history = existing.history if existing else []
        metadata = existing.metadata if existing else {"status": "active"}
        
        record = CompanyRecord(identity=identity, history=history, metadata=metadata)
        self.repo.save_company(record)
        return record

    def append_snapshot(self, symbol: str, snapshot: PeriodSnapshot) -> CompanyRecord:
        record = self.repo.get_company(symbol)
        if not record:
            raise ValueError(f"Company {symbol} not found in registry. Register first.")
        
        updated_history = list(record.history) + [snapshot]
        updated_record = CompanyRecord(identity=record.identity, history=updated_history, metadata=record.metadata)
        self.repo.save_company(updated_record)
        logger.info("Appended period snapshot %s for %s", snapshot.period, symbol)
        return updated_record

    @staticmethod
    def compute_delta(snapshot_a: PeriodSnapshot, snapshot_b: PeriodSnapshot) -> Dict[str, Any]:
        """Compares two historical periods (A -> B) and computes metric percentage deltas and AI reasoning."""
        metrics_a = snapshot_a.metrics
        metrics_b = snapshot_b.metrics
        
        deltas: Dict[str, float] = {}
        reasoning_bullets: List[str] = []

        all_keys = set(metrics_a.keys()).union(set(metrics_b.keys()))
        for key in all_keys:
            val_a = metrics_a.get(key, 0.0)
            val_b = metrics_b.get(key, 0.0)
            if val_a != 0.0:
                pct_change = round(((val_b - val_a) / abs(val_a)) * 100.0, 2)
            else:
                pct_change = 0.0 if val_b == 0.0 else 100.0
            deltas[key] = pct_change

        # Generate institutional narrative reasoning
        rev_growth = deltas.get("revenue", 0.0)
        margin_growth = deltas.get("operating_margin", 0.0)
        debt_change = deltas.get("total_debt", 0.0)

        if rev_growth > 0:
            reasoning_bullets.append(f"Revenue expanded by {rev_growth}% period-over-period.")
        else:
            reasoning_bullets.append(f"Revenue contracted by {abs(rev_growth)}% period-over-period.")

        if margin_growth > 0:
            reasoning_bullets.append(f"Operating margins strengthened by {margin_growth}%.")
        else:
            reasoning_bullets.append(f"Operating margins compressed by {abs(margin_growth)}%.")

        if debt_change < 0:
            reasoning_bullets.append(f"Capital discipline improved with total debt reduced by {abs(debt_change)}%.")

        return {
            "from_period": snapshot_a.period,
            "to_period": snapshot_b.period,
            "deltas": deltas,
            "narrative": reasoning_bullets
        }
