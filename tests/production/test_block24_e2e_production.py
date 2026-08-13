from services.workflow.production_orchestrator import EROSProductionWorkflowOrchestrator

def test_block24_e2e_production_workflow():
    orchestrator = EROSProductionWorkflowOrchestrator(policy_profile="Institutional")
    output = orchestrator.execute_workflow("INFY.NS")

    assert output is not None
    assert output["symbol"] == "INFY.NS"
    assert output["status"] in ["SUCCESS", "REJECTED_BY_INTEGRITY_GATE"]
    if output["status"] == "SUCCESS":
        assert "market_data" in output
        assert "confidence_metrics" in output
        assert "investment_decision" in output
        assert "audit_trace" in output
        assert output["investment_decision"]["final_action"] in ["BUY", "STRONG BUY", "HOLD", "REDUCE", "SELL"]
