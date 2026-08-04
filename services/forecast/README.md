# Forecast Engine Subsystem

## Architecture Overview
The Forecast Engine is the quantitative core of the AI Institutional Equity Research Platform. It enforces immutable, strictly typed Python 3.13 dataclasses across all multi-statement financial projections.

## Public API
- `ForecastMethod`, `ConfidenceLevel`
- `RevenueForecast`, `MarginForecast`, `CapexForecast`, `DepreciationForecast`, `WorkingCapitalForecast`, `TaxForecast`
- `TerminalGrowthForecast`, `ForecastConfidence`, `ForecastAssumption`, `ForecastScenario`

## Dependency Graph
- Standard Library Only (`dataclasses`, `enum`, `typing`)

## Testing Instructions
Run pytest specifically on forecast modules:
```powershell
& .venv\Scripts\python.exe -m pytest tests/forecast/ -v --cov=services/forecast