# Stage 1F — Source Evidence Register

**Evidence review date:** 2026-11-21  
**Purpose:** Record authoritative references and unresolved evidence requirements.

## NSE references

### E1 — NSE FAQ index

- Publisher: National Stock Exchange of India Limited.
- URL: https://www.nseindia.in/static/resources/faqs
- Relevant section: Continuous Markets FAQs; Pre-open Session in Capital Market (CM) Segment.
- Use: Official NSE FAQ index and publication location. The FAQ content identifies the MII security-file normal-market status and eligibility fields separately.
- Evidence recorded: MII security-file field 19 is `SctyStsNrmlMkt`; field 20 is `ElgbltyNrmlMkt`. The eligibility values are `0` = Not Eligible in Normal Market and `1` = Eligible in Normal Market.
- Limitation: Preserve the downloaded FAQ artifact and its retrieval date/hash with the next evidence bundle so the exact revision can be audited.

### E2 — NSE Masters Data specification

- Publisher: National Stock Exchange of India Limited / NSE Data & Analytics archive.
- URL: https://nsearchives.nseindia.com/web/sites/default/files/inline-files/NSE-Masters%20Data-v1.6.pdf
- Relevant section: `ST_SECURITY_ELIGIBILITY_PER_MARKET`.
- Use: Corroborates that the market eligibility indicator and security status are separate fields; its generic market eligibility description defines `1` as allowed to trade and `0` as not allowed to trade.
- Limitation: This is a separate master-data specification. Do not assume its generic field is interchangeable with the MII CSV tag unless the applicable schema confirms that mapping.

### E3 — NSE circular metadata / pre-open FAQ context

- Reference: NSE circular NSE/CMTR/74969, dated 2026-07-01, effective 2026-09-07.
- Publicly indexed summary: https://www.compliedai.com/updates/nse/modifications-in-the-pre-open-call-auction-framework-2pavbo
- Use: Secondary indexed summary points to the revised pre-open FAQ and reproduces the distinction between normal-market status and eligibility fields.
- Limitation: This is not the primary NSE publication host. Treat the official NSE FAQ and original circular as controlling if any discrepancy exists. Obtain and archive the original circular/FAQ before relying on details beyond the field mapping already confirmed.

## BSE references

No authoritative BSE field specification establishing normal-market trading-permission semantics has been accepted into this evidence package.

Required next evidence:
- Official BSE security-master or scrip master specification.
- Relevant circular or official data dictionary.
- Complete field/value semantics and applicable schema version.

Until obtained and reviewed, BSE trading permission remains UNKNOWN.

## Evidence-handling requirements

For every source file used in a future run, capture:
- Exchange and segment.
- Exact filename.
- Publication/trading date.
- Schema/specification version.
- Download timestamp and timezone.
- SHA-256 hash.
- Raw header or field/tag list.
- Parsing/reconciliation tool version.

Do not cite a secondary summary as if it were the primary exchange publication.
