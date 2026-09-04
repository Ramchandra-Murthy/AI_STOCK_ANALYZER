from __future__ import annotations

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Dict, Any

class ValuationRequest(BaseModel):
    symbol: str = Field(..., description="Stock ticker symbol e.g. TCS.NS")
    current_price: float = Field(..., gt=0, description="Current market price")
    eps: float = Field(50.0, description="Earnings per share")
    growth_rate: float = Field(0.08, description="Expected earnings growth rate")
    discount_rate: float = Field(0.11, description="Required rate of return / discount rate")
    segments: Optional[List[Dict[str, Any]]] = Field(None, description="SOTP business segments")
    net_debt: Optional[float] = Field(0.0, description="Net debt for SOTP valuation")
    non_operating_assets: Optional[float] = Field(0.0, description="Non-operating assets for SOTP")
    shares_outstanding: Optional[float] = Field(1.0, description="Shares outstanding")
    user: Optional[str] = Field("institutional_research_user", description="User identifier")

class ValuationResponse(BaseModel):
    record_id: str
    symbol: str
    intrinsic_value: float
    current_price: float
    margin_of_safety: float
    recommendation: str
    valuation_model: str
    created_at: datetime
