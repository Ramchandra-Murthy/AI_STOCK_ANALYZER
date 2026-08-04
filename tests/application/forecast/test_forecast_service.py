from __future__ import annotations

import pytest
from decimal import Decimal
from domain.forecast.models import ForecastMethod, ForecastAssumption
from application.forecast.forecast_service import ForecastApplicationService

def test_forecast_application_service_cagr() -> None:
    service = ForecastApplicationService()
    history = (Decimal("100"), Decimal("110"), Decimal("121"))
    assumption = ForecastAssumption(
        method=ForecastMethod.CAGR,
        periods=2,
        growth_rate=Decimal("0.10")
    )
    
    result = service.execute_forecast(history, assumption)
    
    assert result.method == ForecastMethod.CAGR
    assert len(result.historical_values) == 3
    assert len(result.projected_values) == 2
    assert result.projected_values[0] == Decimal("133.10")
    assert result.projected_values[1] == Decimal("146.41")
