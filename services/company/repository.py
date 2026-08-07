from __future__ import annotations

import logging
from typing import Dict, List, Optional
from services.company.models import CompanyIdentity, PeriodSnapshot, CompanyRecord

logger = logging.getLogger(__name__)

class InMemoryCompanyRepository:
    """Thread-safe institutional memory repository for company registry and historical financial snapshots."""

    def __init__(self) -> None:
        self._store: Dict[str, CompanyRecord] = {}

    def save_company(self, record: CompanyRecord) -> None:
        logger.info("Saving company record for %s to institutional repository", record.identity.symbol)
        self._store[record.identity.symbol] = record

    def get_company(self, symbol: str) -> Optional[CompanyRecord]:
        return self._store.get(symbol)

    def list_symbols(self) -> List[str]:
        return list(self._store.keys())
