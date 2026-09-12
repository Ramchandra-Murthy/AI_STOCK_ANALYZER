from pathlib import Path

p = Path("/app/services/reporting/report_builder.py")
s = p.read_text(encoding="utf-8-sig")

old = """        rec = (
            getattr(committee_decision, "final_action", None)
            or getattr(decision, "action", None)
            or "HOLD"
        )"""

new = """        rec = (
            getattr(committee_decision, "final_action", None)
            or getattr(committee_decision, "consensus_signal", None)
            or getattr(decision, "action", None)
            or "HOLD"
        )"""

if old not in s:
    raise SystemExit("ERROR: Expected recommendation block not found; no changes made.")

p.write_text(s.replace(old, new), encoding="utf-8")
print("SUCCESS: ResearchReportBuilder now supports consensus_signal.")
