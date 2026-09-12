from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ValuationRequest(BaseModel):
    symbol: str = Field(..., description="Stock ticker symbol e.g. TCS.NS")
    current_price: float = Field(..., gt=0, description="Current market price")
    eps: float = Field(50.0, description="Earnings per share")
    growth_rate: float = Field(0.08, description="Expected earnings growth rate")
    discount_rate: float = Field(0.11, description="Required rate of return / discount rate")
    segments: list[dict[str, Any]] | None = Field(None, description="SOTP business segments")
    net_debt: float | None = Field(0.0, description="Net debt for SOTP valuation")
    non_operating_assets: float | None = Field(0.0, description="Non-operating assets for SOTP")
    shares_outstanding: float | None = Field(1.0, description="Shares outstanding")
    user: str | None = Field("institutional_research_user", description="User identifier")


class ValuationResponse(BaseModel):
    record_id: str
    symbol: str
    intrinsic_value: float
    current_price: float
    margin_of_safety: float
    recommendation: str
    valuation_model: str
    created_at: datetime
