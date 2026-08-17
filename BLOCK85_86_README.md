# EROS 3.0 — Blocks 85 + 86

## Block 85

`block85_execution_certification.py`

Provides a deterministic certification gate over Block 84 execution outputs.

It does not:
- submit broker orders
- fetch market data
- replace the portfolio optimizer
- replace the risk engine
- replace the execution engine

It does:
- validate order structure
- calculate transaction-cost analysis using the existing TCA service
- aggregate risk/governance/validation/simulation evidence
- surface assumptions
- produce CERTIFIED / REVIEW / BLOCKED status

## Block 86

`block86_control_plane.py`

Consumes Block 85 certification and creates a final institutional control decision.

Non-bypass rule:

> Block 86 can preserve or restrict Block 85 permission, but cannot upgrade a BLOCKED or REVIEW certification into EXECUTE.

No broker submission is performed.

## Validation

From the repository root:

```powershell
python -m compileall -q .\services\quantitative
python .\services\quantitative\block85_test_harness.py
python .\services\quantitative\block86_test_harness.py
```

Expected:

```text
Block 85: PASS
Block 86: PASS
```
