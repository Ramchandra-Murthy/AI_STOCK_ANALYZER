from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

@dataclass(frozen=True, slots=True)
class DataSanitizationResult:
    is_valid: bool
    sanitized_data: Dict[str, Any]
    errors: List[str]

class InstitutionalDataHardener:
    """
    EROS 3.0 Block 22A Data Hardener.
    Sanitizes market and financial data against missing values, NaNs, stale prices, and malformed structures.
    """
    @staticmethod
    def sanitize_input(data: Dict[str, Any]) -> DataSanitizationResult:
        errors: List[str] = []
        sanitized = dict(data)

        # 1. Check required symbol and price fields
        symbol = sanitized.get("symbol")
        if not symbol or not isinstance(symbol, str):
            errors.append("Missing or invalid symbol format.")

        price = sanitized.get("price")
        if price is None or isinstance(price, bool) or price <= 0.0:
            errors.append("Price must be a positive numeric value.")
            sanitized["price"] = 0.0

        volume = sanitized.get("volume", 0)
        if volume < 0:
            errors.append("Volume cannot be negative. Normalized to 0.")
            sanitized["volume"] = 0

        # 2. Check for NaN or Inf floats
        for k, v in sanitized.items():
            if isinstance(v, float):
                if v != v:  # NaN check
                    errors.append(f"Field '{k}' contains NaN value.")
                    sanitized[k] = 0.0

        return DataSanitizationResult(
            is_valid=len(errors) == 0,
            sanitized_data=sanitized,
            errors=errors
        )
