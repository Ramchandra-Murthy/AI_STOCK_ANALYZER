# Forecast Engine

Institutional-grade, modular financial forecasting service built with Domain-Driven Design (DDD) principles in Python 3.13+.

## Architecture

- **Domain Models (`models.py`)**: Immutable dataclasses (`frozen=True`, `slots=True`) representing revenue, margins, capex, depreciation, working capital, tax liabilities, and terminal growth.
- **Input DTOs (`input.py`)**: Strict input validation containers ensuring type safety and correct dimensionality.
- **Validation Layer (`validation.py`)**: Business-rule validation checks for financial time-series data.
- **Result DTOs (`result.py`)**: Comprehensive output aggregators containing projection paths, metadata, and serialization methods.
- **Algorithmic Suite (`algorithms/`)**: Quantitative methods including CAGR, Linear Regression, Mean Reversion, and Rolling Averages.

## Usage Example

```python
from services.forecast.examples.basic_forecast import main

if __name__ == "__main__":
    main()