from services.eros_frontend_adapter import EROSFrontendAdapter

print("=" * 70)
print("EROS 3.0 - V3.8.18 FRONTEND TRACEABILITY RUNTIME TEST")
print("=" * 70)

symbol = "RELIANCE.NS"

print("")
print("SYMBOL :", symbol)

adapter = EROSFrontendAdapter()

print("")
print("=" * 70)
print("TRACEABILITY API")
print("=" * 70)

traceability = adapter.decision_traceability(symbol)

print("RESULT TYPE :", type(traceability).__name__)

if not isinstance(traceability, dict):
    raise RuntimeError("EROS_TRACEABILITY_NOT_DICT")

print("RESULT TYPE : dict")

decision = traceability.get("decision", {})
interpretation = traceability.get("interpretation", {})
conclusion = traceability.get("conclusion", {})
trace = traceability.get("trace", {})
governance = traceability.get("governance", {})

print("")
print("DECISION:")
print(decision)

print("")
print("INTERPRETATION:")
print(interpretation)

print("")
print("CONCLUSION:")
print(conclusion)

print("")
print("TRACE STAGES:")

stages = [
    "stage_1_evidence",
    "stage_2_intelligence",
    "stage_3_interpretation",
    "stage_4_action_framework",
    "stage_5_action_explanation",
    "stage_6_scenario_engine",
    "stage_7_scenario_explanation",
    "stage_8_convergence",
]

available = 0

for stage in stages:

    block = trace.get(stage)

    if isinstance(block, dict):

        status = block.get("status", "UNKNOWN")
        source = block.get("source", "UNKNOWN")

        print(f"{stage} : AVAILABLE | " f"SOURCE={source} | STATUS={status}")

        available += 1

    else:

        print(f"{stage} : NOT AVAILABLE")

print("")
print("TRACE STAGES AVAILABLE :", available)
print("TRACE STAGES EXPECTED   :", len(stages))

if available != len(stages):
    raise RuntimeError("EROS_TRACEABILITY_STAGE_COUNT_FAILURE")

print("")
print("GOVERNANCE:")
print(governance)

if governance.get("read_only") is not True:
    raise RuntimeError("GOVERNANCE_READ_ONLY_FAILURE")

if governance.get("execution_blocked") is not True:
    raise RuntimeError("GOVERNANCE_EXECUTION_BLOCK_FAILURE")

if governance.get("non_mutation_invariant") is not True:
    raise RuntimeError("GOVERNANCE_NON_MUTATION_FAILURE")

print("")
print("=" * 70)
print("V3.8.18 RUNTIME TEST : PASS")
print("=" * 70)

print("")
print("SAFETY")
print("=" * 70)
print("NO SOURCE PATCH")
print("NO DATABASE WRITE")
print("NO BROKER CALL")
print("NO ORDER CREATION")
print("NO PORTFOLIO MUTATION")
print("NO GIT OPERATION")

print("")
print("=" * 70)
print("V3.8.18 FRONTEND TRACEABILITY RUNTIME TEST COMPLETE")
print("=" * 70)
