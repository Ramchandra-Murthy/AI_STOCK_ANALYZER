from pathlib import Path

p = Path("/app/tests/test_eros_golden_chain.py")
s = p.read_text()

old = """    assert governance["governance_id"] == "EROS98-TEST"
    assert governance["source_block"] == "97"
    assert governance["source_decision_id"] == "EROS96-TEST"
"""

new = """    assert governance["governance_id"] == "EROS98-TEST"
    assert str(governance.get("source_readiness_id")) == "EROS97-TEST"
    assert str(governance.get("source_decision_id")) == "EROS96-TEST"
"""

if old not in s:
    raise SystemExit("ERROR: Expected assertion block was not found; file was not modified.")

p.write_text(s.replace(old, new))
print("SUCCESS: Governance lineage assertions corrected.")
