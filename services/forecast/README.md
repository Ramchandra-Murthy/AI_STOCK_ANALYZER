# Forecast Engine Subsystem

## Architecture Overview
The Forecast Engine is the quantitative core of the AI Institutional Equity Research Platform. It enforces immutable, strictly typed Python dataclasses for all financial time-series projections, multi-scenario analysis, and valuation preparation.

## Public API
- **Enums**: `ForecastMethod`, `ConfidenceLevel`, `ForecastFrequency`, `ScenarioType`
- **Metadata**: `ForecastMetadata`, `ForecastConfidence`, `ForecastAssumption`
- **Time Series**: `RevenueForecast`, `MarginForecast`, `CapexForecast`, `DepreciationForecast`, `WorkingCapitalForecast`, `TaxForecast`, `TerminalGrowthForecast`
- **Aggregates**: `ForecastScenario`, `ForecastPackage`

## Testing Instructions
Run pytest across the forecast module with coverage:
```powershell
& .venv\Scripts\python.exe -m pytest services/forecast/tests/ -v --cov=services/forecast