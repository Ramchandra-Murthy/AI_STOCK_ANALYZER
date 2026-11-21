# ML4T Stage 1F — Exchange Eligibility Evidence Package

**Status:** Specification approved; documentation package prepared for review  
**Scope:** NSE/BSE field crosswalk and evidence documentation only  
**Implementation status:** Not authorised  
**Repository branch:** `docs/ml4t-stage-1f-crosswalk`

## Purpose

Stage 1F documents how exchange-supplied security-master fields may be interpreted for normal-market eligibility. It deliberately separates listing identity, normal-market eligibility, market status, auction eligibility, and broker/account permissions.

## Documents

1. [NSE field crosswalk](nse-field-crosswalk.md)
2. [BSE field crosswalk](bse-field-crosswalk.md)
3. [Eligibility assessment rules](eligibility-rules.md)
4. [Source evidence register](source-evidence.md)
5. [Real-data reconciliation baseline](reconciliation-baseline.md)

## Approved decisions

- NSE `ElgbltyNrmlMkt` is the verified normal-market eligibility field.
- `ElgbltyNrmlMkt = 1` means eligible in the normal market.
- `ElgbltyNrmlMkt = 0` means not eligible in the normal market.
- Missing, blank, malformed, or unrecognised values resolve to `UNKNOWN`.
- NSE `PrtdToTrad` remains `UNKNOWN`; no semantics are inferred from its name.
- BSE trading permission remains `UNKNOWN` pending an authoritative BSE field definition and value dictionary.
- Market-status and closing-auction eligibility remain separate dimensions.
- Raw exchange fields and source provenance must be preserved.

## Important limitation

The normal-market eligibility indicator is an exchange-data attribute. It is not a guarantee that an order will be accepted by a broker or exchange. It does not establish account permissions, instrument/series support, live session state, order-type constraints, price-band validity, or operational availability.

## Change control

This package is documentation only. It does not authorise Python changes, schema migrations, scanner filtering changes, trading logic changes, commits to `main`, pull-request creation, or merging. Any implementation requires separate approval.

## Review checklist

- [x] Revised Stage 1F specification approved.
- [x] NSE normal-market eligibility field documented.
- [x] Unresolved NSE/BSE mappings explicitly retained as UNKNOWN.
- [x] Reported reconciliation counts recorded with provenance limitation.
- [ ] Raw reconciliation bundle and source-file hashes attached.
- [ ] BSE authoritative permission semantics verified.
- [ ] Stage 1F documentation package reviewed and accepted.
