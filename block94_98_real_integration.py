from copy import deepcopy

from services.quantitative.block94_portfolio_stress_scenario_engine import (
    EROSBlock94PortfolioStressScenarioEngine,
)
from services.quantitative.block95_stress_evidence_gate import (
    EROSBlock95StressEvidenceGate,
)
from services.quantitative.block96_stress_decision_gate import (
    EROSBlock96StressDecisionGate,
)
from services.quantitative.block97_stress_readiness_gate import (
    EROSBlock97StressReadinessGate,
)
from services.quantitative.block98_execution_governance_bridge import (
    EROSBlock98ExecutionGovernanceBridge,
)

print("")
print("================================================================")
print("EROS 3.0 - REAL BLOCK 94 -> 95 -> 96 -> 97 -> 98 INTEGRATION")
print("================================================================")

# ================================================================
# REAL UPSTREAM INPUTS
# ================================================================

valuation = {
    "status": "PASS",
    "valuation_id": "EROS91-INTEGRATION-VAL-001",
    "valuation": {
        "valuation_id": "EROS91-INTEGRATION-VAL-001",
        "portfolio_id": "EROS-INTEGRATION-PORTFOLIO",
        "portfolio_equity": 10_400_000.0,
        "market_value": 10_000_000.0,
    },
    "certificate": {
        "status": "CERTIFIED",
        "valuation_id": "EROS91-INTEGRATION-VAL-001",
    },
}

performance = {
    "status": "PASS",
    "performance_id": "EROS92-INTEGRATION-PERF-001",
    "performance": {
        "performance_id": "EROS92-INTEGRATION-PERF-001",
    },
    "certificate": {
        "status": "CERTIFIED",
        "performance_id": "EROS92-INTEGRATION-PERF-001",
    },
}

risk = {
    "status": "PASS",
    "certificate_id": "EROS93-INTEGRATION-RISK-001",
    "risk_certificate": {
        "certificate_id": "EROS93-INTEGRATION-RISK-001",
    },
    "certificate": {
        "status": "CERTIFIED",
        "certificate_id": "EROS93-INTEGRATION-RISK-001",
    },
}

positions = [
    {
        "symbol": "RELIANCE.NS",
        "quantity": 4000.0,
        "market_value": 10_000_000.0,
        "current_price": 2500.0,
        "weight_pct": 100.0,
    }
]

scenarios = [
    {
        "scenario_id": "EROS94-INTEGRATION-DOWN-001",
        "scenario_type": "MARKET",
        "name": "Market Downside",
        "market_shock_pct": -15.0,
    },
    {
        "scenario_id": "EROS94-INTEGRATION-UP-001",
        "scenario_type": "MARKET",
        "name": "Market Upside",
        "market_shock_pct": 10.0,
    },
]

# ================================================================
# BLOCK 94
# ================================================================

print("")
print("BLOCK 94")
print("--------")

b94 = EROSBlock94PortfolioStressScenarioEngine()

certificate = b94.certify(
    valuation=deepcopy(valuation),
    performance=deepcopy(performance),
    risk=deepcopy(risk),
    positions=deepcopy(positions),
    scenarios=deepcopy(scenarios),
)

print("Status             :", certificate.get("status"))
print("Certificate status :", certificate.get("certificate_status"))
print("Certificate ID     :", certificate.get("certificate_id"))
print("Scenario count     :", certificate.get("scenario_count"))

assert certificate.get("status") == "CERTIFIED", certificate
assert certificate.get("certificate_status") == "CERTIFIED", certificate
assert certificate.get("block_id") == "EROS-BLOCK-94", certificate
assert certificate.get("scenario_count") == 2, certificate

# ================================================================
# BLOCK 95
# ================================================================

print("")
print("BLOCK 95")
print("--------")

b95 = EROSBlock95StressEvidenceGate()

gate95 = b95.gate(
    stress_certificate=deepcopy(certificate)
)

print("Status             :", gate95.get("status"))
print("Gate status        :", gate95.get("gate_status"))
print("Block ID            :", gate95.get("block_id"))
print("Source block        :", gate95.get("source_block"))
print("Source certificate  :", gate95.get("source_certificate_id"))
print("Gate ID             :", gate95.get("gate_id"))
print("Scenario count     :", gate95.get("scenario_count"))
print("Downstream gate    :", gate95.get("downstream_risk_gate"))

assert gate95.get("status") == "CERTIFIED", gate95
assert gate95.get("gate_status") == "CERTIFIED", gate95
assert gate95.get("block_id") == "95", gate95
assert gate95.get("source_block") == "94", gate95
assert (
    gate95.get("source_certificate_id")
    == certificate.get("certificate_id")
), gate95

# ================================================================
# BLOCK 96
# ================================================================

print("")
print("BLOCK 96")
print("--------")

b96 = EROSBlock96StressDecisionGate()

decision = b96.decide(
    stress_gate=deepcopy(gate95)
)

print("Status             :", decision.get("status"))
print("Decision status    :", decision.get("decision_status"))
print("Decision           :", decision.get("decision"))
print("Decision ID        :", decision.get("decision_id"))
print("Block ID           :", decision.get("block_id"))
print("Source block       :", decision.get("source_block"))
print("Source gate ID     :", decision.get("source_gate_id"))
print("Source certificate :", decision.get("source_certificate_id"))
print("Scenario count     :", decision.get("scenario_count"))
print("Execution blocked  :", decision.get("execution_blocked"))

assert decision.get("status") == "CERTIFIED", decision
assert decision.get("decision_status") == "CERTIFIED", decision
assert decision.get("decision") == "ADMITTED", decision
assert decision.get("block_id") == "96", decision
assert decision.get("source_block") == "95", decision
assert decision.get("source_gate_id") == gate95.get("gate_id"), decision
assert (
    decision.get("source_certificate_id")
    == gate95.get("source_certificate_id")
), decision

# ================================================================
# BLOCK 97
# ================================================================

print("")
print("BLOCK 97")
print("--------")

b97 = EROSBlock97StressReadinessGate()

readiness = b97.certify(
    decision=deepcopy(decision)
)

print("Status             :", readiness.get("status"))
print("Readiness status   :", readiness.get("readiness_status"))
print("Readiness ID       :", readiness.get("readiness_id"))
print("Block ID           :", readiness.get("block_id"))
print("Source block       :", readiness.get("source_block"))
print("Source decision    :", readiness.get("source_decision_id"))
print("Source gate ID     :", readiness.get("source_gate_id"))
print("Source certificate :", readiness.get("source_certificate_id"))
print("Decision           :", readiness.get("decision"))
print("Scenario count     :", readiness.get("scenario_count"))
print("Non-mutation       :", readiness.get("non_mutation_invariant"))
print("Execution blocked  :", readiness.get("execution_blocked"))

assert readiness.get("status") == "CERTIFIED", readiness
assert readiness.get("readiness_status") == "READY", readiness
assert readiness.get("block_id") == "97", readiness
assert readiness.get("source_block") == "96", readiness
assert (
    readiness.get("source_decision_id")
    == decision.get("decision_id")
), readiness
assert (
    readiness.get("source_gate_id")
    == decision.get("source_gate_id")
), readiness
assert (
    readiness.get("source_certificate_id")
    == decision.get("source_certificate_id")
), readiness

# ================================================================
# BLOCK 98
# ================================================================

print("")
print("BLOCK 98")
print("--------")

b98 = EROSBlock98ExecutionGovernanceBridge()

governance = b98.certify(
    decision=deepcopy(readiness)
)

print("Status             :", governance.get("status"))
print("Governance status  :", governance.get("governance_status"))
print("Governance ID      :", governance.get("governance_id"))
print("Block ID           :", governance.get("block_id"))
print("Source block       :", governance.get("source_block"))
print("Source readiness   :", governance.get("source_readiness_id"))
print("Source decision    :", governance.get("source_decision_id"))
print("Source gate ID     :", governance.get("source_gate_id"))
print("Source certificate :", governance.get("source_certificate_id"))
print("Readiness status   :", governance.get("readiness_status"))
print("Decision           :", governance.get("decision"))
print("Scenario count     :", governance.get("scenario_count"))
print("Execution action   :", governance.get("execution_action"))
print("Non-mutation       :", governance.get("non_mutation_invariant"))
print("Broker submission  :", governance.get("broker_submission"))
print("Live execution     :", governance.get("live_order_submission"))
print("Execution blocked  :", governance.get("execution_blocked"))

assert governance.get("status") == "CERTIFIED", governance
assert governance.get("governance_status") == "APPROVED", governance
assert governance.get("block_id") == "98", governance
assert governance.get("source_block") == "97", governance
assert (
    governance.get("source_readiness_id")
    == readiness.get("readiness_id")
), governance
assert (
    governance.get("source_decision_id")
    == readiness.get("source_decision_id")
), governance
assert (
    governance.get("source_gate_id")
    == readiness.get("source_gate_id")
), governance
assert (
    governance.get("source_certificate_id")
    == readiness.get("source_certificate_id")
), governance
assert governance.get("readiness_status") == "READY", governance
assert governance.get("decision") == "ADMITTED", governance
assert governance.get("scenario_count") == 2, governance
assert governance.get("execution_action") == "EXECUTE", governance

# ================================================================
# SAFETY ASSERTIONS
# ================================================================

print("")
print("SAFETY ASSERTIONS")
print("-----------------")

assert governance.get("portfolio_mutation") is False
assert governance.get("valuation_mutation") is False
assert governance.get("performance_mutation") is False
assert governance.get("risk_mutation") is False
assert governance.get("optimization") is False
assert governance.get("order_creation") is False
assert governance.get("non_mutation_invariant") is True
assert governance.get("broker_submission") is False
assert governance.get("live_order_submission") is False
assert governance.get("execution_blocked") is True

print("Portfolio mutation   : FALSE")
print("Valuation mutation   : FALSE")
print("Performance mutation : FALSE")
print("Risk mutation        : FALSE")
print("Optimization         : FALSE")
print("Order creation       : FALSE")
print("Broker submission    : FALSE")
print("Live execution       : FALSE")
print("Execution blocked    : TRUE")

# ================================================================
# FINAL
# ================================================================

print("")
print("================================================================")
print("REAL BLOCK 94 -> 95 -> 96 -> 97 -> 98 INTEGRATION : PASS")
print("================================================================")
print("")
print("94 Certificate :", certificate.get("certificate_id"))
print("95 Gate        :", gate95.get("gate_id"))
print("96 Decision    :", decision.get("decision_id"))
print("97 Readiness   :", readiness.get("readiness_id"))
print("98 Governance  :", governance.get("governance_id"))
print("")
print("Lineage preserved     : YES")
print("Scenario evidence     : YES")
print("Decision              : ADMITTED")
print("Readiness             : READY")
print("Governance            : APPROVED")
print("Action                : EXECUTE")
print("Non-mutation          : YES")
print("Execution actually run: NO")
print("Broker submission     : NO")
print("Live execution        : NO")
print("")
print("================================================================")
