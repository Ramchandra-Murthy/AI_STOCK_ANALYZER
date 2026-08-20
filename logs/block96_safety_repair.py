from pathlib import Path
import shutil
from datetime import datetime

path = Path(r"services\quantitative\block96_stress_decision_gate.py")

print("=" * 100)
print("EROS 3.0 - BLOCK 96 SAFETY CONTRACT SURGICAL REPAIR")
print("=" * 100)

if not path.exists():
    raise SystemExit(f"SOURCE FILE NOT FOUND: {path}")

source = path.read_text(encoding="utf-8-sig")

old = '''            "downstream_risk_gate": STATUS_BLOCKED,
            "broker_submission": False,
            "live_order_submission": False,
'''

new = '''            "downstream_risk_gate": STATUS_BLOCKED,
            "non_mutation_invariant": True,
            "execution_blocked": True,
            "broker_submission": False,
            "live_order_submission": False,
'''

count = source.count(old)

print()
print("EXACT TARGET MATCH COUNT:", count)

if count != 1:
    raise SystemExit(
        "ABORTED: Expected exactly one Block 96 safety dictionary target."
    )

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup = path.with_name(
    f"{path.name}.backup_block96_safety_{timestamp}"
)

shutil.copy2(path, backup)

updated = source.replace(old, new, 1)

path.write_text(updated, encoding="utf-8")

print()
print("BACKUP :", backup)
print("SOURCE UPDATE : PASS")

print()
print("FIELDS ADDED:")
print('  "non_mutation_invariant": True')
print('  "execution_blocked": True')

print()
print("FIELDS PRESERVED:")
print('  "broker_submission": False')
print('  "live_order_submission": False')
print('  "downstream_risk_gate": STATUS_BLOCKED')

print()
print("NO BROKER")
print("NO LIVE EXECUTION")
print("NO ORDER CREATION")
print("NO MUTATION")

print()
print("=" * 100)
print("BLOCK 96 REPAIR COMPLETE")
print("=" * 100)
