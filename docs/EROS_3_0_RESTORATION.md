# EROS 3.0 Restoration

This branch is intentionally rooted at the historical EROS 3.0 checkpoint:

- Restore anchor: `b6be2cf05bca760cd0266015c2c7498736f2af85`
- Historical tag: `eros3-pre-cleanup-20260824`
- Restoration branch: `rebuild/eros-3-0-restored`

## Restoration rules

1. The historical checkpoint is preserved; it is never rewritten.
2. Ultra is not part of the restored EROS runtime path.
3. CLI, Streamlit, and future API entry points resolve the same EROS application service.
4. Production execution must use real services, not hard-coded success responses.
5. Stage failures are recorded as `PARTIAL` with an explicit error list.
6. Deterministic scoring and valuation engines remain separate from presentation/UI.
7. New changes should be accompanied by regression tests.

## Current repaired boundary

`entry point -> DI container -> EROSResearchService -> existing EROS analysis services`

The branch deliberately avoids merging the later large Sprint 19 cleanup because that change removed financial models/parser code and is not required to establish a safe restoration baseline.

## Validation

Run locally from the repository root:

```powershell
python -m pytest tests/test_eros_restoration_boundary.py -q
python main.py --ticker RELIANCE.NS
```

The second command is a live data smoke test and may report `PARTIAL` when an external provider or optional analysis stage is unavailable. That is a diagnostic result, not a reason to fabricate success.
