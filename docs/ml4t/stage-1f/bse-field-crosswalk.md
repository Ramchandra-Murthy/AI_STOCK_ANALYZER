# Stage 1F — BSE Field Crosswalk

**Assessment:** Trading-permission semantics unresolved  
**Exchange:** BSE Limited

## Current treatment

| Information | Assessment | Stage 1F treatment |
|---|---|---|
| ISIN identity used in the reconciliation bundle | Present in the reported reconciliation | Preserve as identity/matching data |
| BSE listing presence | Present in the reported reconciliation | Record listing presence separately |
| BSE normal-market trading permission | No authoritative field/value mapping verified for this stage | UNKNOWN |
| BSE market/session status | Not mapped in this evidence package | UNKNOWN / separate dimension |
| BSE auction eligibility | Not mapped in this evidence package | UNKNOWN / separate dimension |
| Any other unverified BSE field | Not verified | UNKNOWN |

## Evidence required to change UNKNOWN

A BSE permission field may be mapped only after the evidence package contains:

1. An authoritative BSE specification, circular, or official data dictionary.
2. The exact file name and schema/version to which the definition applies.
3. The field name/tag and data type.
4. The complete value dictionary, including null, blank, reserved, and exceptional values where documented.
5. Evidence that the field describes the same market/session and eligibility concept being assessed.
6. A versioned source reference and a reproducible test against representative BSE records.

## Prohibited inferences

- Do not infer BSE permission from NSE fields or NSE eligibility.
- Do not infer permission from BSE listing presence alone.
- Do not infer permission from an ISIN match.
- Do not infer permission from market-status, surveillance, series, or auction fields without an authoritative semantic mapping.
- Do not convert missing or unfamiliar values into ELIGIBLE.

Until the required evidence is reviewed and approved, BSE trading permission remains `UNKNOWN`.
