from pathlib import Path

p = Path("/app/tests/scoring/test_block10_fundamental_scoring.py")
text = p.read_text(encoding="utf-8-sig")

old = """    assert details["engine_version"] == "EROS-3.0-BLOCK-10"
"""

new = """    # AIScoringEngine is the unified Block 15 engine.
    assert details["engine_version"] == "EROS-3.0-BLOCK-15"

    # Fundamental scoring remains independently versioned as Block 10.
    assert details["fundamental_engine"]["engine_version"] == "EROS-3.0-BLOCK-10"
"""

if old not in text:
    raise SystemExit("PATCH ABORTED: expected Block 10 assertion not found")

p.write_text(text.replace(old, new, 1), encoding="utf-8")
print("SUCCESS: Corrected Block 10 test to distinguish unified and component engine versions")
