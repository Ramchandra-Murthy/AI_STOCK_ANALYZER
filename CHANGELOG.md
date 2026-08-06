# Changelog

All notable changes to this project will be documented in this file.

## [6.0.0-alpha] - 2026-04-06
### Added
- Centralized `ValuationDispatcher` supporting DCF, NAV, and SOTP valuation strategies.
- Core Domain-Driven Design layout (`Core`, `Application`, `Infrastructure`, `Services`).
- Robust validation rules package (`core/validation/rules.py`) with strict `ValidationError` handling.
- Comprehensive test suite for container bootstrapping and valuation dispatchers.
