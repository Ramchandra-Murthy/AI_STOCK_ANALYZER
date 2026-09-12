from pathlib import Path

p = Path("/app/services/scoring/engine.py")
text = p.read_text(encoding="utf-8")

old = """        details = {
            "rating": rating,
            "engine_version": "EROS-3.0-BLOCK-15",
            "weights_used": weights,
            "growth_engine": growth_res.growth_details,
            "fundamental_engine": fund_res.pillar_details,
            "valuation_engine": {
"""

new = """        details = {
            "rating": rating,
            "engine_version": "EROS-3.0-BLOCK-15",
            "weights_used": weights,
            "growth_engine": growth_res.growth_details,

            # Block 10 audit contract while preserving the
            # existing FundamentalScoringEngine payload.
            "fundamental_engine": {
                **fund_res.pillar_details,
                "profitability_components": fund_res.pillar_details["profitability"],
                "quality_components": fund_res.pillar_details["quality"],
                "capital_allocation_components": fund_res.pillar_details["capital_efficiency"],
            },

            # Block 10 audit contract.
            "raw_ratios": fund_res.pillar_details["ratios"],

            "valuation_engine": {
"""

if old not in text:
    raise SystemExit("ERROR: expected details block not found")

p.write_text(text.replace(old, new, 1), encoding="utf-8")
print("SUCCESS: Added Block 10 audit aliases to unified scoring details")
