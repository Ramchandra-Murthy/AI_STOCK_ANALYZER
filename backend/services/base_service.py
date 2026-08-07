from __future__ import annotations

import logging
import time
from typing import Any, Callable
from sqlalchemy.orm import Session
from backend.exceptions import ServiceError, ValidationError

logger = logging.getLogger(__name__)

class BaseService:
    """Enterprise Base Service providing standardized logging, timing, validation hooks, and transaction boundaries."""

    def __init__(self) -> None:
        self.logger = logging.getLogger(self.__class__.__name__)

    def execute_with_lifecycle(self, operation_name: str, action: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        start_time = time.perf_counter()
        self.logger.info("START: %s", operation_name)
        try:
            result = action(*args, **kwargs)
            duration_ms = round((time.perf_counter() - start_time) * 1000.0, 2)
            self.logger.info("END: %s | Duration: %s ms", operation_name, duration_ms)
            return result
        except (ValidationError, ServiceError) as e:
            self.logger.error("ValidationError in %s: %s", operation_name, str(e))
            raise
        except Exception as e:
            self.logger.exception("Unexpected error in %s: %s", operation_name, str(e))
            raise ServiceError(f"Operation {operation_name} failed: {str(e)}") from e

    @staticmethod
    def begin_transaction(session: Session) -> None:
        if not session.in_transaction():
            session.begin()

    @staticmethod
    def commit_transaction(session: Session) -> None:
        session.commit()

    @staticmethod
    def rollback_transaction(session: Session) -> None:
        session.rollback()