# Navigating the Stock Market: book-to-code audit

**Source:** User-uploaded chapter material from *Navigating the Stock Market* (19 chapters).
**Repository audited:** `Ramchandra-Murthy/AI_STOCK_ANALYZER`
**Audit baseline:** `main` at `fae9440e683afb3d1ddee518d21bc580a4f40d7a` (9 November 2026).
**Purpose:** Map the book's visible concepts to existing repository capabilities, identify genuine gaps, and prevent duplicate implementations.

## Scope and confidence

This is a repository-level capability audit based on the uploaded chapter pages/headings and inspection of the current `main` tree and representative source files. Some uploaded page images were narrow, low-resolution, or partially obscured. Accordingly, this document does not claim verbatim extraction of every paragraph or formula, nor does it claim that every chapter example has been reproduced. Statuses describe evidence visible in the repository, not proof of predictive performance or production readiness.

Status meanings:
- **Substantial foundation:** Relevant modules, tests, or dashboards exist; integration, coverage, data quality, or validation may still need work.
- **Partial:** Some related functionality exists, but it does not fully implement the book's broader concept.
- **Gap / not verified:** No dedicated implementation was identified in the audited tree. This is not a claim that no related data could exist elsewhere.

## Executive assessment

The repository already has substantial foundations for technical screening, company fundamentals, valuation, market-regime analysis, institutional cash-flow context, quantitative research, execution-cost analysis, portfolio allocation, risk measurement, and AI model validation. Recent merged work through PR #856 further added full curated-universe scanning, a 09:25 IST first automatic intraday scan, Level-2 order-book research, execution-fill diagnostics, walk-forward portfolio allocation, selection-bias diagnostics, and deterministic portfolio stress scenarios.

The highest-value next step is **not** to add another generic indicator or another composite score. It is to connect and validate existing capabilities, close the data gaps around Indian macroeconomic and ownership disclosures, strengthen point-in-time evidence and explainability, and make exit/portfolio controls consistent across research workflows.

## Book-to-repository capability matrix

| Book concepts | Repository evidence on audited `main` | Assessment | Recommended treatment |
|---|---|---|---|
| Stock screening, price/volume indicators, trends and chart patterns | `indicators/` (ATR, Bollinger, MACD, moving averages, RSI, support/resistance, trend); `scanner/market_scanner.py`, `scanner/universe.py`, `scanner/unusual_activity.py`, momentum and NR4/NR7 modules | **Substantial foundation** | Reuse existing indicators and scanners. Validate incremental value, avoid correlated-indicator double counting, and do not add another generic scoring layer without evidence. |
| Market regime, breadth and sector/market context | `algorithmic_trading/regime_engine.py`, `services/intraday_market_regime.py`, extensive `scanner/eros_regime_*.py`, `scanner/eros_regime_breadth.py`, sector mapping and institutional momentum | **Substantial foundation** | Consolidate shared regime definitions and verify consistency between intraday, swing and portfolio workflows. |
| Company fundamentals and business quality | `modules/fundamentals.py`, `services/fundamental_score_service.py`, `ai_trading/fundamental_intelligence.py`, financial statement/ratio services, `pages/AI_Fundamental_Intelligence.py` | **Substantial foundation** | Improve point-in-time financial data, sector-aware comparisons, data completeness, and evidence behind every score. Avoid a second fundamental score engine. |
| Company/sector peer analysis and competitive position | `services/peer_valuation_service.py`, sector mapping, financial ratios and peer selection | **Partial** | Validate peer membership, sector comparability, stale data, and coverage. Market-share/product-demand/competitive-moat data are not verified as systematic inputs. |
| Stock valuation: P/E, P/B, EV multiples, DCF, WACC, SOTP/NAV and fair value | `services/valuation/` (DCF, comparable multiples, NAV, SOTP, dispatcher), `services/valuation_service.py`, `services/peer_valuation_service.py`, WACC and valuation services | **Substantial foundation** | Audit assumptions, source timestamps, sector-specific methods, sensitivity ranges and margin-of-safety presentation. PEG/history-relative valuation should be checked for completeness before adding anything. |
| Technical entry/exit, trading plans and stop protection | `services/trade_plan_service.py`, `services/investment_thesis_service.py`, `algorithmic_trading/risk_protection.py`, intraday setup evaluation, ATR/technical indicators | **Partial to substantial** | Reuse existing trade-plan and stop logic. A unified, thesis-aware exit monitor across technical, fundamental and portfolio states was not verified. |
| Macroeconomic indicators: inflation, IIP, GDP, consumption, capacity utilisation, money supply, rates, currency and central-bank policy | No dedicated CPI/IIP/GDP/RBI repo-rate/Fed/money-supply/India-VIX ingestion module was found by path audit. Existing currency primitives are not a macro data pipeline. | **Gap / not verified** | Highest-priority data gap. Add source-specific, timestamped Indian macro observations only after defining authoritative sources, release calendars, revisions and point-in-time availability. Track US Fed and global variables as context, not as substitutes for RBI data. |
| Market monitoring, news, sentiment and event effects | `services/news_service.py`, `ai_trading/news_sentiment.py`, `pages/AI_News_Sentiment.py`, financial-news event studies and sentiment research; market data/status services | **Partial to substantial** | Current headline scoring is a transparent lexicon approach and the page accepts pasted headlines. Improve reliable automated ingestion, entity/event extraction, timestamps, deduplication and point-in-time replay before claiming full NLP coverage. |
| FII/DII flows, institutional positioning and short interest | `scanner/institutional_flow.py`, `scanner/institutional_momentum.py`, `scanner/institutional_momentum_history.py`, `scanner/short_regime.py` | **Partial** | FII/DII cash-flow context exists. `short_regime.py` classifies price regimes; it is not evidence of a stock-level short-interest dataset. Verify exchange short-selling/SLBM/F&O data semantics before building short-position signals. |
| Promoter/insider transactions, pledging and mutual-fund cash levels | No dedicated promoter/insider transaction, pledge-history, or mutual-fund cash-level ingestion module was identified in the audited tree. | **Gap / not verified** | Add only with reliable NSE/BSE/SEBI/AMFI disclosures, transaction-type classification, event dates, reporting dates and historical point-in-time storage. Do not infer insider sentiment from ordinary ownership snapshots. |
| Portfolio allocation, risk, performance and stress | `algorithmic_trading/portfolio_risk.py`, `algorithmic_trading/robust_portfolio_allocation.py`, `algorithmic_trading/portfolio_walk_forward.py`, `ai_trading/risk_metrics.py`, `ai_trading/rolling_risk.py`, position sizing, portfolio dashboards; PRs #850, #851 and #856 | **Substantial foundation** | Integrate risk limits and exposure views across scanner, paper trading and portfolio pages. Continue validating costs, missing prices, concentration, correlation and stress assumptions. |
| Execution, liquidity and market microstructure | `ai_trading/intraday_microstructure.py`, `ai_trading/order_book.py`, `ai_trading/order_book_replay.py`, `algorithmic_trading/execution_backtester.py`, impact calibration and fill diagnostics; PRs #837–#840 and #841–#853 | **Research foundation; live-feed dependent** | Preserve the distinction between OHLCV, aggregated Level-2 snapshots and true order/trade events. Do not imply queue position or live execution quality without validated feeds. |
| AI/ML prediction, quantitative analysis, pattern recognition and forecasting | `ai_trading/` includes feature factory, ML/ensemble/sequence models, LSTM research, prediction stability, strategy selection, walk-forward and calibration; forecasting services and dashboards | **Substantial research foundation** | Prioritise out-of-sample utility, calibrated probabilities, simple baselines, regime robustness and net-of-cost performance. A prediction score is not a probability unless calibrated and evaluated as one. |
| AI governance, data quality, drift, leakage and reproducibility | `ai_trading/lookahead.py`, `ai_trading/feature_drift.py`, `ai_trading/experiment_manifest.py`, calibration, strategy quality gates, selection-bias diagnostics and CI/tests | **Substantial foundation; governance partial** | Extend source lineage, prediction/decision audit records, model cards, drift response policy and reproducible point-in-time datasets. Keep human review and risk gates independent of model scores. |
| Market manipulation, fraud detection, ethical/legal oversight and systemic AI risk | `scanner/surveillance.py` provides an NSE safety/regulatory snapshot and liquidity warnings; no verified dedicated manipulation/fraud detector or formal AI governance/compliance workflow was identified. | **Partial / gap** | Do not label generic unusual-volume alerts as fraud or manipulation detection. Treat this as a later, data- and legal-review-dependent research area with explainable flags and human investigation. |

## Important distinctions and non-duplication rules

1. **Price regime is not short interest.** The existing `scanner/short_regime.py` detects price/swing regimes; it must not be represented as exchange short-position data.
2. **FII/DII cash flow is not mutual-fund cash reserves.** Existing institutional flow helpers do not establish fund-level uninvested cash balances.
3. **A news lexicon is not a full NLP pipeline.** Existing headline scoring is useful and transparent, but entity linking, event classification, source credibility, deduplication and point-in-time replay remain separate requirements.
4. **NSE safety flags are not fraud findings.** Surveillance filters and liquidity warnings should remain descriptive and should not make allegations about issuers or participants.
5. **DCF/peer/SOTP infrastructure already exists.** Improve assumptions and evidence lineage before creating another valuation implementation.
6. **Existing regime and indicator families are extensive.** Consolidate and validate rather than add duplicate market-regime or indicator-score modules.
7. **Research execution models are not broker execution.** OHLCV and static Level-2 research tools have explicit limitations; no live execution capability should be inferred from them.

## Prioritized follow-up plan

### P0 — Evidence integrity before new predictive features

- Define a common point-in-time observation contract: source, instrument/entity, value, unit, period-end, publication/availability timestamp, retrieval timestamp, revision/version and quality status.
- Audit data freshness and stale-data behavior in scanner, fundamentals, news and market-context paths.
- Ensure every backtest and event study uses only information available at the simulated decision time.
- Add explicit missing/partial coverage reporting; never silently convert unavailable data into neutral or bullish evidence.

### P1 — Close the clearest book-derived Indian-market data gaps

- Build a source-reviewed Indian macro data adapter and historical store for selected RBI/MoSPI/official indicators (for example CPI, IIP, policy rates, money supply and capacity utilisation). Include release calendars, revisions and point-in-time semantics.
- Add a separate disclosure ingestion design for promoter/insider transactions and pledging, plus AMFI mutual-fund portfolio/cash observations, only where source coverage and historical availability can be validated.
- Extend news NLP from headline lexicon scoring to timestamped entity/event classification and event-study evaluation; keep the existing lexicon as a baseline.
- Add an exit/thesis-monitor integration using existing trade-plan, investment-thesis and risk-protection services rather than a parallel exit engine.

### P2 — Governance and portfolio decision support

- Add a model/strategy registry or model-card record linking version, training window, features, data sources, parameters, validation results and known limitations.
- Record signal explanations and the exact data snapshot used to produce each research result.
- Define drift alerts and a documented review/disable policy; drift detection alone should not automatically retrain or deploy a model.
- Validate strategy correlation and common factor exposures in portfolio stress scenarios.
- Consider manipulation/fraud research only after suitable event-level data, clear definitions, legal review and human investigation workflow exist.

## Recommended delivery sequence

1. **Documentation audit (this PR):** establish the book-to-code baseline and explicit non-duplication rules.
2. **Point-in-time data contract and freshness audit:** shared foundation for macro, ownership, news and fundamentals.
3. **Indian macro data ingestion:** source-specific, revision-aware, point-in-time observations and tests.
4. **Promoter/insider and pledge disclosure ingestion:** event classification and historical replay.
5. **Mutual-fund holdings/cash disclosure research:** source coverage and publication-date handling.
6. **News NLP/event pipeline:** entity resolution, event types, deduplication, timestamps and baseline comparison.
7. **Unified exit/thesis monitoring:** combine existing trade plan, fundamental thesis and risk protection.
8. **Model governance/audit trail:** model cards, prediction lineage, drift response and reproducibility.
9. **Manipulation/fraud research feasibility review:** no detection claims until validated event data and legal controls exist.

The order may change if source availability or repository inspection reveals a dependency or an existing implementation that already closes a gap. Every code PR must add focused tests, preserve existing behavior unless explicitly intended, and pass the repository's required CI/quality gates before merge.

## Acceptance principles for future work

- No fabricated, stale or silently imputed market/fundamental/macro observations.
- No look-ahead leakage, including publication-time and revised-data leakage.
- No new score unless its components, missing-data behavior and out-of-sample incremental value are documented.
- No duplicated indicator, valuation, regime, risk or sentiment engine.
- Report universe selected, successfully analysed and skipped symbols separately.
- Keep research signals distinct from investment advice and broker orders.
- Measure results after realistic costs and compare with simple baselines.
- Keep human oversight and hard risk limits outside model discretion.
