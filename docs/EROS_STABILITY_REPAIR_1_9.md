# EROS Stability Repair 1–9

## 1. Current-code audit
Reviewed the active research path and its scoring/data-boundary contracts from the current `main` baseline.

## 2. Failure-path repair
The research UI now treats malformed engine returns and missing market/history data as unavailable evidence instead of allowing invalid values to flow into display logic.

## 3. Research UI consistency
The research page now exposes the results already produced by the thesis, scenario, fundamental valuation, and V4.3 valuation engines. Dividend yield is displayed through the shared formatter.

## 4. Dependency cleanup
Removed the unused `ReportGenerator` import from the research page. This avoids an undeclared `reportlab` runtime dependency being required just to import the research module.

## 5. Regression coverage
Added tests covering scenario-analysis evidence gates, invalid scenario price levels, missing valuation P/E evidence, and missing valuation price/earnings data.

## 6. Git repair branch
Changes are isolated on `eros/stability-1-9` so the stable `main` branch remains unchanged until validation completes.

## 7. CI validation
Pull request #5 runs the repository CI matrix on Python 3.13 with dependency installation, Ruff, Black, MyPy, and PyTest.

## 8. Re-audit target
After CI completes, the pull request head will be checked again for changed-file scope, expected contracts, and unintended regressions before merge.

## 9. Stable-baseline gate
The EROS repair is considered stable only when the CI gate is green and the final re-audit confirms the repaired contract boundaries. No feature expansion is part of this repair batch.
