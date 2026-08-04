from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Tuple
from services.forecast.input import ForecastInput

class BaseForecastAlgorithm(ABC):
    @abstractmethod
    def calculate_revenue(self, forecast_input: ForecastInput) -> Tuple[float, ...]: pass
    @abstractmethod
    def calculate_margins(self, forecast_input: ForecastInput) -> Tuple[float, ...]: pass
    @abstractmethod
    def calculate_capex(self, forecast_input: ForecastInput) -> Tuple[float, ...]: pass
    @abstractmethod
    def calculate_depreciation(self, forecast_input: ForecastInput) -> Tuple[float, ...]: pass
    @abstractmethod
    def calculate_working_capital(self, forecast_input: ForecastInput) -> Tuple[float, ...]: pass
    @abstractmethod
    def calculate_taxes(self, forecast_input: ForecastInput) -> Tuple[float, ...]: pass
