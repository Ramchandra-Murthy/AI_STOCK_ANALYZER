from __future__ import annotations

from pydantic import BaseModel, Field
from datetime import datetime

class ValuationRequest(BaseModel):
    symbol: str = Field(..., description="Stock ticker symbol e.g. TCS.NS")
    current_price: float = Field(..., gt=0, description="Current market price")
    eps: float = Field(..., description="Earnings per share")
    growth_rate: float = Field(0.08, description="Expected earnings growth rate")
    discount_rate: float = Field(0.11, description="Required rate of return / discount rate")

class ValuationResponse(BaseModel):
    record_id: str
    symbol: str
    intrinsic_value: float
    current_price: float
    margin_of_safety: float
    recommendation: str
    valuation_model: str
    created_at: datetime