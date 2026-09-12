from copy import deepcopy

from services.quantitative.block102_frontend_contract import EROSBlock102FrontendContract
from services.quantitative.block103_institutional_frontend_read_model import (
    EROSBlock103InstitutionalFrontendReadModel,
)
from services.quantitative.block104_eros_command_center import EROSBlock104CommandCenter
from services.quantitative.block106_institutional_integration_boundary import (
    EROSBlock106InstitutionalIntegrationBoundary,
)
from services.quantitative.block107_application_read_boundary import (
    EROSBlock107ApplicationReadBoundary,
)
from services.quantitative.block108_institutional_application_service_boundary import (
    EROSBlock108InstitutionalApplicationServiceBoundary,
)
from services.quantitative.block109_institutional_application_query_gateway import (
    EROSBlock109InstitutionalApplicationQueryGateway,
)


def build_chain():
    b94 = {
        "status": "CERTIFIED",
        "certificate_status": "CERTIFIED",
        "certificate_id": "EROS94-TEST",
        "scenario_count": 5,
        "downside_pnl": -1500000.0,
        "upside_pnl": 1000000.0,
        "execution_blocked": True,
    }

    b95 = {
        "status": "CERTIFIED",
        "gate_id": "EROS95-TEST",
        "execution_blocked": True,
    }

    b96 = {
        "status": "CERTIFIED",
        "decision_status": "ADMITTED",
        "decision": "ADMITTED",
        "decision_id": "EROS96-TEST",
        "source_block": "95",
        "execution_blocked": True,
    }

    b97 = {
        "status": "CERTIFIED",
        "readiness_status": "READY",
        "readiness_id": "EROS97-TEST",
        "source_block": "96",
        "source_decision_id": "EROS96-TEST",
        "execution_blocked": True,
    }

    b98 = {
        "status": "CERTIFIED",
        "governance_status": "APPROVED",
        "governance_id": "EROS98-TEST",
        "execution_action": "EXECUTE",
        "source_block": "97",
        "source_readiness_id": "EROS97-TEST",
        "source_decision_id": "EROS96-TEST",
        "execution_blocked": True,
    }

    b99 = {
        "status": "CERTIFIED",
        "intent_status": "AUTHORIZED",
        "authorization_status": "AUTHORIZED",
        "intent_id": "EROS99-TEST",
        "intent_action": "PREPARE",
        "source_block": "98",
        "source_governance_id": "EROS98-TEST",
        "symbol": "RELIANCE.NS",
        "action": "BUY",
        "quantity": 100.0,
        "reference_price": 2500.0,
        "execution_blocked": True,
    }

    b100 = {
        "status": "CERTIFIED",
        "execution_status": "SIMULATED",
        "execution_id": "EROS100-TEST",
        "source_block": "99",
        "symbol": "RELIANCE.NS",
        "action": "BUY",
        "requested_quantity": 100.0,
        "filled_quantity": 100.0,
        "reference_price": 2500.0,
        "fill_price": 2501.25,
        "fill_status": "FILLED",
        "slippage_bps": 5.0,
        "transaction_cost": 250.0,
        "net_value": 250125.0,
        "execution_blocked": True,
    }

    b101 = {
        "status": "CERTIFIED",
        "reconciliation_status": "RECONCILED",
        "reconciliation_id": "EROS101-TEST",
        "source_block": "100",
        "source_execution_id": "EROS100-TEST",
        "quantity_reconciled": True,
        "price_reconciled": True,
        "value_reconciled": True,
        "cost_reconciled": True,
        "lineage_reconciled": True,
        "execution_blocked": True,
    }

    m102 = EROSBlock102FrontendContract().build(
        block94=b94,
        block95=b95,
        block96=b96,
        block97=b97,
        block98=b98,
        block99=b99,
        block100=b100,
        block101=b101,
    )

    m103 = EROSBlock103InstitutionalFrontendReadModel().build(contract=m102)
    m104 = EROSBlock104CommandCenter().render_model(read_model=m103)

    e106 = EROSBlock106InstitutionalIntegrationBoundary()
    m106 = e106.build_integration_payload(m104)

    m107 = EROSBlock107ApplicationReadBoundary.build_application_snapshot(m106)

    e108 = EROSBlock108InstitutionalApplicationServiceBoundary()
    m108 = e108.build_application_service_model(m107)

    e109 = EROSBlock109InstitutionalApplicationQueryGateway()
    m109 = e109.build_query_model(application_service_model=m108)

    return locals()


def test_full_chain_valid():
    c = build_chain()

    assert c["m102"]["status"] == "CERTIFIED"
    assert c["m103"]["status"] == "CERTIFIED"
    assert isinstance(c["m104"], dict)
    assert c["e106"].validate_payload(c["m106"])
    assert EROSBlock107ApplicationReadBoundary.validate_application_snapshot(c["m107"])
    assert c["e108"].validate_application_service_model(c["m108"])
    assert c["e109"].validate_query_model(c["m109"])


def test_complete_lineage():
    c = build_chain()

    assert str(c["m106"]["lineage"]["source_block_id"]) == "104"
    assert str(c["m107"]["application"]["source_block_id"]) == "106"
    assert str(c["m108"]["lineage"]["source_block"]) == "107"
    assert str(c["m109"]["lineage"]["source_block"]) == "108"


def test_semantic_consistency():
    c = build_chain()

    intent = c["m102"]["intent"]
    execution = c["m102"]["execution"]
    reconciliation = c["m102"]["reconciliation"]
    governance = c["m102"]["governance"]

    assert intent["symbol"] == execution["symbol"]
    assert intent["action"] == execution["action"]
    assert intent["quantity"] == execution["requested_quantity"]
    assert intent["reference_price"] == execution["reference_price"]
    assert execution["filled_quantity"] == execution["requested_quantity"]

    assert reconciliation["source_execution_id"] == execution["execution_id"]
    assert reconciliation["quantity_reconciled"] is True
    assert reconciliation["price_reconciled"] is True
    assert reconciliation["value_reconciled"] is True
    assert reconciliation["cost_reconciled"] is True
    assert reconciliation["lineage_reconciled"] is True

    assert governance["status"] == "APPROVED"
    assert governance["execution_action"] == "EXECUTE"
    assert governance["governance_id"] == "EROS98-TEST"
    assert str(governance.get("source_readiness_id")) == "EROS97-TEST"
    assert str(governance.get("source_decision_id")) == "EROS96-TEST"


def test_safety_invariants():
    c = build_chain()

    for block in (c["m106"], c["m107"], c["m108"], c["m109"]):
        safety = block["safety"]

        assert safety["allow_order_creation"] is False
        assert safety["allow_broker_submission"] is False
        assert safety["allow_live_execution"] is False
        assert safety["allow_portfolio_mutation"] is False
        assert safety["allow_valuation_mutation"] is False
        assert safety["allow_performance_mutation"] is False
        assert safety["allow_risk_mutation"] is False
        assert safety["allow_optimization"] is False
        assert safety["execution_blocked"] is True
        assert safety["non_mutation_invariant"] is True


def test_upstream_immutability():
    c = build_chain()

    before = {k: deepcopy(c[k]) for k in ("b94", "b95", "b96", "b97", "b98", "b99", "b100", "b101")}

    build_chain()

    for k, original in before.items():
        assert c[k] == original


def test_108_lineage_tamper_rejected():
    c = build_chain()

    tampered = deepcopy(c["m108"])
    tampered["lineage"]["source_block"] = "999"

    assert c["e108"].validate_application_service_model(tampered) is False


def test_109_lineage_tamper_rejected():
    c = build_chain()

    tampered = deepcopy(c["m109"])
    tampered["lineage"]["source_block"] = "999"

    assert c["e109"].validate_query_model(tampered) is False


def test_109_source_tamper_rejected():
    c = build_chain()

    tampered = deepcopy(c["m109"])
    tampered["query"]["source_block_id"] = "999"

    assert c["e109"].validate_query_model(tampered) is False


def test_109_capability_tamper_rejected():
    c = build_chain()

    tampered = deepcopy(c["m109"])
    tampered["query"]["capabilities"].append("order_creation")

    assert c["e109"].validate_query_model(tampered) is False


def test_109_gateway_is_read_only():
    c = build_chain()

    public_methods = {
        name
        for name in dir(c["e109"])
        if not name.startswith("_") and callable(getattr(c["e109"], name, None))
    }

    forbidden = {
        "create_order",
        "submit_order",
        "execute_order",
        "place_order",
        "register_order",
        "mutate",
        "optimize",
        "broker_submit",
        "live_execute",
    }

    assert forbidden.isdisjoint(public_methods)
