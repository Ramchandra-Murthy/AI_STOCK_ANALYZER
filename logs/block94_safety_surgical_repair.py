from pathlib import Path
from datetime import datetime

path = Path(
    r"services\quantitative\block94_portfolio_stress_scenario_engine.py"
)

print("=" * 100)
print("EROS 3.0 - BLOCK 94 SAFETY CONTRACT SURGICAL REPAIR")
print("=" * 100)

if not path.exists():
    raise FileNotFoundError(path)

source = path.read_text(encoding="utf-8-sig")

backup = path.with_suffix(
    path.suffix +
    ".backup_block94_safety_" +
    datetime.now().strftime("%Y%m%d_%H%M%S")
)

backup.write_text(source, encoding="utf-8")

print()
print("SOURCE :", path)
print("BACKUP :", backup)

old = '''    def _blocked(reason: str) -> Dict[str, Any]:
        return {
            "status": STATUS_BLOCKED,
            "block_id": BLOCK_ID,
            "reason": reason,
            "broker_submission": False,
            "live_order_submission": False,
            "portfolio_mutation": False,
            "valuation_mutation": False,
        }
'''

new = '''    def _blocked(reason: str) -> Dict[str, Any]:
        return {
            "status": STATUS_BLOCKED,
            "block_id": BLOCK_ID,
            "reason": reason,
            "non_mutation_invariant": True,
            "execution_blocked": True,
            "broker_submission": False,
            "live_order_submission": False,
            "portfolio_mutation": False,
            "valuation_mutation": False,
        }
'''

count = source.count(old)

print()
print("EXACT TARGET MATCH COUNT:", count)

if count != 1:
    raise RuntimeError(
        f"Expected exactly 1 Block 94 _blocked helper, found {count}"
    )

source = source.replace(old, new, 1)

path.write_text(
    source,
    encoding="utf-8"
)

print()
print("SOURCE UPDATE : PASS")

print()
print("FIELDS ADDED:")
print('  "non_mutation_invariant": True')
print('  "execution_blocked": True')

print()
print("FIELDS PRESERVED:")
print('  "broker_submission": False')
print('  "live_order_submission": False')
print('  "portfolio_mutation": False')
print('  "valuation_mutation": False')

print()
print("NO BROKER")
print("NO LIVE EXECUTION")
print("NO ORDER CREATION")
print("NO PORTFOLIO MUTATION")
print("NO VALUATION MUTATION")

print()
print("=" * 100)
print("BLOCK 94 REPAIR COMPLETE")
print("=" * 100)
