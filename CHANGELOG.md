# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]
### Added
- Repository foundation (M0) including directory structure, CI/CD workflows, governance documents, and tool configurations.
- Next-day scanner validation suite (calendar/session boundaries, live-vs-evaluation parity,
  look-ahead, costs, bad-data handling) and an append-only paper-trading log with
  after-the-session outcomes, baselines and costs. Research only; no orders are placed.

### Fixed
- Next-day scanner walk-forward evaluation no longer rejects a symbol for the whole history
  because of invalid rows that only occur later (look-ahead through data-quality filtering);
  the live scan and the evaluation now apply the same per-date rule.
- Next-day scanner returns `UNAVAILABLE` when stocks traded on a day the configured calendar
  marks closed, instead of ranking against a possibly wrong cutoff and target date.
- Next-day scanner page warns when the displayed result was produced for a different exchange
  or shortlist-size selection.
- Intraday momentum engine (`scanner/momentum_engine.py`): transparent 0-100 momentum-strength score from 1/5/10/15-minute windows with volume and multi-timeframe confirmation, UP/DOWN/MIXED/NEUTRAL direction, explainable components, and explicit handling of missing, stale and insufficient data. Pure computation; not a probability or recommendation.
- NSE/BSE momentum ranking (`scanner/momentum_ranking.py`) and a "Momentum ranking" panel in the Live Top-10 scanner. Ranks only symbols the engine could score, with deterministic tie-breaks; symbols that are stale, too short or missing are listed as not ranked, never estimated. The Top-10 movers table and its existing columns are unchanged.
