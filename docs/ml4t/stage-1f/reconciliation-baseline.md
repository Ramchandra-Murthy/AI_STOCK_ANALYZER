# Stage 1F — Real-Data Reconciliation Baseline

**Baseline date reported:** 2026-11-20  
**Status:** Reported results recorded; raw-bundle provenance not independently reproduced in this documentation commit.

## Reported reconciliation counts

| Measure | Count |
|---|---:|
| Common NSE/BSE ISINs | 6,649 |
| NSE-only ISINs | 10,248 |
| BSE-only ISINs | 13,427 |
| Unique ISINs | 30,324 |

Arithmetic check:

`6,649 + 10,248 + 13,427 = 30,324`

The reported category totals reconcile arithmetically to the reported unique-ISIN total.

## Reported validation result

The run report stated that all reconciliation bundle consistency checks passed. This is recorded as a reported internal validation result, not as independent exchange validation, broker approval, or proof that every source record is eligible to trade.

## Provenance limitation

The raw NSE and BSE source files, exact filenames, source publication dates, schema versions, SHA-256 hashes, reconciliation command, and machine-readable run output were not available for independent inspection when this document was prepared.

Accordingly:
- The counts above are retained as the supplied 2026-11-20 baseline.
- They must not be represented as independently reproduced by this documentation update.
- A future reproducibility package must attach the raw source identifiers, hashes, run configuration, reconciliation output, and validation log.
- If the raw bundle produces different counts on rerun, preserve both runs and explain the source/version difference rather than overwriting the baseline.

## Eligibility is not reconciliation

ISIN matching establishes an identity relationship across exchange records. It does not establish normal-market eligibility, current market status, closing-auction eligibility, or broker/account permission.

The reconciliation counts must not be used as a proxy for the number of currently tradable securities.
