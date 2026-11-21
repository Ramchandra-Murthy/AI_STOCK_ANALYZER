# Stage 1F — NSE Field Crosswalk

**Assessment:** Partial; one normal-market eligibility field verified  
**Exchange:** National Stock Exchange of India (NSE)

## Verified normal-market eligibility field

| File/schema context | Field number | Field/tag | Type | Value | Meaning | Stage 1F treatment |
|---|---:|---|---|---|---|---|
| MII security master | 20 | `ElgbltyNrmlMkt` | Character, one character | `1` | Eligible in Normal Market | `ELIGIBLE` |
| MII security master | 20 | `ElgbltyNrmlMkt` | Character, one character | `0` | Not Eligible in Normal Market | `INELIGIBLE` |
| Legacy `security.gz` layout | 9 | `Eligibility` | Source-defined | `1` / `0` | Normal-market eligibility values documented in NSE FAQ | Apply only to that documented file layout |

The current NSE FAQ identifies the MII security-file field as field 20, ISO tag `ElgbltyNrmlMkt`, and documents the values `0` and `1`. It separately identifies the normal-market security-status field. See the source register.

## Separate market-status field

| File/schema context | Field number | Field/tag | Documented values | Meaning |
|---|---:|---|---|---|
| MII security master | 19 | `SctyStsNrmlMkt` | `1` | Pre-open (normal market) |
| MII security master | 19 | `SctyStsNrmlMkt` | `2` | Open |
| MII security master | 19 | `SctyStsNrmlMkt` | `3` | Suspended |
| MII security master | 19 | `SctyStsNrmlMkt` | `4` | Pre-open extended |
| MII security master | 19 | `SctyStsNrmlMkt` | `5` | Stock Open With Market |
| MII security master | 19 | `SctyStsNrmlMkt` | `6` | Price Discovery (only for securities eligible in pre-open) |

These status values describe market/session state. They must not be substituted for `ElgbltyNrmlMkt`.

## Unresolved fields

| Field | Status | Required evidence before mapping |
|---|---|---|
| `PrtdToTrad` | UNKNOWN | Authoritative NSE definition for the exact file version and its complete value dictionary |
| Closing-auction eligibility fields | UNKNOWN / separate dimension | Applicable NSE specification and exact file/version mapping |
| Other fields not explicitly verified in the source register | UNKNOWN | Authoritative field definition, type, value dictionary, and version applicability |

No interpretation is inferred from field names, numeric appearance, neighbouring columns, or legacy layouts.

## Version and layout controls

- Do not assume a field number in the legacy `security.gz` layout is the same as a field number in the MII CSV layout.
- Do not map by column position alone.
- Record the exact source filename, exchange publication date, schema/specification version, header/tag, and source hash with each future reconciliation run.
- If a file layout differs from the documented layout, do not silently shift field mappings. Mark the affected mapping `UNKNOWN` until reconciled.

## Non-goals

This crosswalk does not define broker order permissions, account entitlements, instrument eligibility outside the normal market, order-type acceptance, or real-time market availability.
