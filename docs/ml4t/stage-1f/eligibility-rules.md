# Stage 1F — Eligibility Assessment Rules

**Status:** Approved specification; documentation only  
**No executable implementation is included.**

## 1. Keep dimensions separate

The assessment must preserve these independent dimensions:

- Security identity (including ISIN where available).
- Exchange listing presence.
- Normal-market eligibility.
- Market/session status.
- Closing-auction eligibility.
- Broker/account/order permissions.

A positive result in one dimension does not imply a positive result in another.

## 2. NSE normal-market assessment

For the documented NSE MII security-master field `ElgbltyNrmlMkt`:

| Raw value | Assessment |
|---|---|
| `1` | `ELIGIBLE` |
| `0` | `INELIGIBLE` |
| Missing, null, blank, malformed, or unrecognised | `UNKNOWN` |

This rule applies only when the source file is positively identified as the matching NSE schema/version and the field is correctly parsed.

The field `PrtdToTrad` is not used to derive this assessment and remains `UNKNOWN`.

## 3. BSE assessment

BSE normal-market trading permission remains `UNKNOWN` until its own authoritative field semantics and code dictionary are verified.

No NSE-to-BSE inheritance or cross-exchange inference is allowed.

## 4. Market status

Market status is evaluated separately from eligibility. For example, a security may be marked eligible in the normal market while its current session status is pre-open, suspended, or otherwise not open. The status field must not overwrite or reinterpret the eligibility field.

## 5. Closing-auction eligibility

Closing-auction eligibility is a separate market-specific dimension. It must not be used as evidence of normal-market eligibility, and normal-market eligibility must not be used as evidence of closing-auction eligibility.

## 6. UNKNOWN handling

UNKNOWN is a first-class result, not a synonym for eligible, ineligible, or missing listing.

- Preserve the raw value.
- Preserve the source filename, publication date, schema version, and parsing context.
- Retain unresolved records in reconciliation outputs.
- Do not silently coerce unfamiliar values.
- Do not exclude a record merely because its eligibility is UNKNOWN unless a separately approved downstream policy explicitly requires that behaviour.

## 7. Scope exclusions

Stage 1F does not introduce price, volume, liquidity, turnover, settlement, surveillance, or strategy filters. It does not establish broker or account-level order acceptance.

## 8. Implementation gate

Any code, schema, scanner, or trading-logic implementation requires separate user approval after review of this documentation and the remaining evidence gaps.
