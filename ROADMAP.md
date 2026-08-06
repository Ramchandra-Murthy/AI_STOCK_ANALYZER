# AI Stock Analyzer V6 - Project Roadmap

## Vision
Build the best open-source institutional equity research platform focused on Indian markets, generating explainable, professional-quality equity research reports.

---

## Release Plan & Milestones

### V6.0 Alpha (Current Milestone)
* **Goal:** Establish core architecture, dependency injection, and unified valuation/forecast pipelines.
* **Status:** In Progress (Sprint 2A & 2B)
* **Success Criteria:**
  * [x] Dependency injection container & container resolution tests (`tests/core/test_core_container_root.py`)
  * [x] Valuation migration and strategy dispatcher (`ValuationDispatcher` with DCF, NAV, SOTP)
  * [x] Core validation rules & error handling standards (`ValidationError`)
  * [ ] Unified research report generation workflow

### V6.1
* Improved DCF assumptions, SOTP engine, relative valuation, enhanced charts, and PDF export.

### V6.2
* Portfolio Intelligence (analysis, diversification, rebalancing, and scenario simulation).

### V7.0
* AI Research Platform (Multi-agent architecture and long-form investment reporting).

---

## Sprint Backlog

* **Sprint 2A:** Finish valuation migration, remove legacy valuation callers, and establish architecture tests. *(Completed)*
* **Sprint 2B:** Finalize Dependency Injection, Service Registry, and Core Interfaces. *(In Progress)*
* **Sprint 2C:** Event Bus and Plugin Framework.
* **Sprint 2D:** Research Report Engine and PDF/HTML generation.
