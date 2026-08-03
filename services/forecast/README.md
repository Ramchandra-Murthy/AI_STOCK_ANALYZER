# Forecast Engine Domain Layer

Provides frozen, immutable dataclasses for financial statement forecasting within the AI Institutional Equity Research Platform (AIIERP). 

## Architecture
All objects use Python frozen dataclasses with `slots=True` to guarantee thread safety, low memory overhead, and deterministic financial calculations.