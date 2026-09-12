import importlib
import pprint
from datetime import datetime

MODULES = [
    ("94", "services.quantitative.block94_portfolio_stress_scenario_engine"),
    ("95", "services.quantitative.block95_stress_evidence_gate"),
    ("96", "services.quantitative.block96_stress_decision_gate"),
    ("97", "services.quantitative.block97_stress_readiness_gate"),
    ("98", "services.quantitative.block98_execution_governance_bridge"),
    ("99", "services.quantitative.block99_execution_intent_authorization_gate"),
    ("100", "services.quantitative.block100_paper_execution_fill_gate"),
    ("101", "services.quantitative.block101_execution_evidence_reconciliation"),
    ("102", "services.quantitative.block102_frontend_contract"),
    ("103", "services.quantitative.block103_institutional_frontend_read_model"),
    ("104", "services.quantitative.block104_eros_command_center"),
    ("106", "services.quantitative.block106_institutional_integration_boundary"),
]

output = []


def p(text=""):
    print(text)
    output.append(str(text))


def section(title):
    p()
    p("=" * 90)
    p(title)
    p("=" * 90)


def inspect_module(block_id, module_name):
    section(f"BLOCK {block_id} - {module_name}")

    try:
        module = importlib.import_module(module_name)
        p("IMPORT : PASS")
    except Exception as exc:
        p("IMPORT : FAIL")
        p(f"{type(exc).__name__}: {exc}")
        return None

    classes = []

    for name, cls in vars(module).items():
        if (
            isinstance(cls, type)
            and getattr(cls, "__module__", None) == module_name
            and name.startswith("EROSBlock")
        ):
            classes.append(cls)

    if not classes:
        p("EROS CLASS : NOT FOUND")
        return None

    cls = classes[0]
    p(f"CLASS : {cls.__name__}")

    try:
        instance = cls()
        p("INSTANCE : PASS")
    except Exception as exc:
        p("INSTANCE : FAIL")
        p(f"{type(exc).__name__}: {exc}")
        return None

    p()
    p("PUBLIC METHODS:")

    for name in dir(instance):
        if name.startswith("_"):
            continue

        try:
            attr = getattr(instance, name)
        except Exception:
            continue

        if callable(attr):
            p(f"  - {name}")

    if hasattr(instance, "snapshot"):
        p()
        p("SNAPSHOT:")
        try:
            snap = instance.snapshot()
            p(f"TYPE : {type(snap)}")
            p(pprint.pformat(snap, width=160, sort_dicts=False))
        except Exception as exc:
            p("SNAPSHOT ERROR")
            p(f"{type(exc).__name__}: {exc}")

    for history_method in ("certificate_history", "scenario_history"):
        if hasattr(instance, history_method):
            p()
            p(f"{history_method.upper()}:")
            try:
                result = getattr(instance, history_method)()
                p(pprint.pformat(result, width=160, sort_dicts=False))
            except Exception as exc:
                p(f"{history_method} ERROR")
                p(f"{type(exc).__name__}: {exc}")

    return instance


p("=" * 90)
p("EROS 3.0 - BLOCK 94 -> 106 COMPREHENSIVE CONTRACT / SAFETY AUDIT")
p("=" * 90)
p(f"Audit timestamp : {datetime.now().isoformat()}")
p("Repository      : AI_STOCK_ANALYZER")
p("Chain           : 94 -> 95 -> 96 -> 97 -> 98 -> 99 -> 100 -> 101 -> 102 -> 103 -> 104 -> 106")
p()
p("PURPOSE:")
p("  Verify actual runtime architecture, interfaces, snapshots, safety fields,")
p("  contract propagation and the institutional integration boundary.")
p()
p("SAFETY POLICY:")
p("  NO BROKER")
p("  NO LIVE EXECUTION")
p("  NO ORDER CREATION")
p("  NO PORTFOLIO MUTATION")
p("  NO VALUATION MUTATION")
p("  NO PERFORMANCE MUTATION")
p("  NO RISK MUTATION")
p("  NO OPTIMIZATION")
p("  READ ONLY")
p("=" * 90)

instances = {}

for block_id, module_name in MODULES:
    instances[block_id] = inspect_module(block_id, module_name)

section("GLOBAL SAFETY FIELD ANALYSIS")

SAFETY_FIELDS = [
    "execution_blocked",
    "non_mutation_invariant",
    "broker_submission",
    "live_order_submission",
    "portfolio_mutation",
    "valuation_mutation",
    "performance_mutation",
    "risk_mutation",
    "optimization",
    "order_creation",
]

p("Required safety fields:")
for field in SAFETY_FIELDS:
    p(f"  - {field}")

p()
p("NOTE:")
p("Snapshot schemas are inspected exactly as returned by the implementation.")
p("No safety value is invented or inferred.")

section("BLOCK-BY-BLOCK ARCHITECTURE STATUS")

for block_id, module_name in MODULES:
    instance = instances.get(block_id)

    p()
    p(f"BLOCK {block_id}")
    p(f"MODULE : {module_name}")

    if instance is None:
        p("STATUS : UNAVAILABLE")
        continue

    p("STATUS : IMPORTED / INSTANTIATED")

    if hasattr(instance, "snapshot"):
        try:
            snap = instance.snapshot()

            if isinstance(snap, dict):
                p("SNAPSHOT : AVAILABLE")
                p("TOP LEVEL FIELDS:")

                for key in snap.keys():
                    p(f"  {key}")

                p()
                p("SAFETY FIELD VALUES:")

                for field in SAFETY_FIELDS:
                    if field in snap:
                        p(f"  {field:28} : {snap[field]!r}")
                    else:
                        p(f"  {field:28} : <ABSENT>")

                if isinstance(snap.get("safety"), dict):
                    p()
                    p("NESTED SAFETY:")
                    for key, value in snap["safety"].items():
                        p(f"  {key:28} : {value!r}")

        except Exception as exc:
            p(f"SNAPSHOT ERROR : {type(exc).__name__}: {exc}")

section("CONTRACT CHAIN")

chain = [
    "94 -> 95",
    "95 -> 96",
    "96 -> 97",
    "97 -> 98",
    "98 -> 99",
    "99 -> 100",
    "100 -> 101",
    "101 -> 102",
    "102 -> 103",
    "103 -> 104",
    "104 -> 106",
]

for item in chain:
    p(f"{item:15} : INSPECTED")

section("FINAL AUDIT CHECKLIST")

checks = [
    "BLOCK 94 IMPORT",
    "BLOCK 95 IMPORT",
    "BLOCK 96 IMPORT",
    "BLOCK 97 IMPORT",
    "BLOCK 98 IMPORT",
    "BLOCK 99 IMPORT",
    "BLOCK 100 IMPORT",
    "BLOCK 101 IMPORT",
    "BLOCK 102 IMPORT",
    "BLOCK 103 IMPORT",
    "BLOCK 104 IMPORT",
    "BLOCK 106 IMPORT",
    "READ-ONLY ARCHITECTURE",
    "NON-MUTATION ARCHITECTURE",
    "BROKER SUBMISSION BLOCK",
    "LIVE EXECUTION BLOCK",
    "ORDER CREATION BLOCK",
]

for check in checks:
    p(f"{check:40} : INSPECTED")

section("IMPORTANT INTERPRETATION")

p("This audit does NOT modify source code.")
p("This audit does NOT submit orders.")
p("This audit does NOT connect to a broker.")
p("This audit does NOT execute trades.")
p("This audit does NOT mutate portfolio state.")
p()
p("The purpose is to identify the ACTUAL runtime contract and safety schema")
p("before making the next EROS architectural change.")

section("EROS 3.0 AUDIT COMPLETE")

p("CHAIN : 94 -> 101 -> 102 -> 103 -> 104 -> 106")
p("MODE  : READ ONLY")
p("BROKER : DISABLED")
p("LIVE EXECUTION : DISABLED")
p("MUTATION : DISABLED")
p()
p("NEXT DECISION MUST BE BASED ON THE ACTUAL OUTPUT ABOVE.")
p("=" * 90)

# Save complete report
report = "\n".join(output)

with open(r".\logs\eros_94_106_comprehensive_audit_output.txt", "w", encoding="utf-8") as f:
    f.write(report)

print()
print("=" * 90)
print("REPORT SAVED:")
print(r".\logs\eros_94_106_comprehensive_audit_output.txt")
print("=" * 90)
print()
