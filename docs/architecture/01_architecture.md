# AIERP - System Architecture & Subsystem Layout

## Architectural Layers
The system adheres to Clean Architecture principles divided into four primary tiers:

1. **Domain (`domain/`)**
   - Contains core business entities, value objects (Money, Percentage, FiscalYear, Ticker), and domain exceptions.
   - Independent of any external frameworks, databases, or UI layers.

2. **Application (`application/`)**
   - Orchestrates use cases and application workflows (e.g., ForecastService, ValuationDispatcher, ReportService).
   - Manages transactions, service coordination, and DTO transformations.

3. **Infrastructure (`infrastructure/`)**
   - External adapters, database repositories (SQLite/PostgreSQL), market data providers (NSE feeds), and PDF/HTML report generators.

4. **Services / Presentation (`services/`, `interfaces/`)**
   - Contains domain-specific computational engines (DCF, SOTP, NAV, Comparable, WACC) and user interfaces (FastAPI, Streamlit Dashboard).

## Core Subsystems
- **Valuation Subsystem (`services/valuation/`):** Centralized via `ValuationDispatcher`, orchestrating pluggable valuation engines adhering to common interfaces (`BaseEngine`).
- **Validation Engine (`core/validation/`):** Centralized rule validation with custom `ValidationError` handling.
- **Dependency Injection Container (`core/container/`):** Bootstraps services and manages object lifecycles cleanly.
