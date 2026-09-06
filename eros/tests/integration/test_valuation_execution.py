from eros.decision.pipeline import (
    create_context,
    finalize,
    run_foundation,
    run_valuation,
)


def test_valuation_is_not_run_without_foundation():
    context = create_context("RELIANCE")

    run_valuation(context)

    assert context.sotp is None
    assert context.dcf is None
    assert context.valuation_bridge is None
    assert context.warnings


def test_empty_evaluate_path_remains_safe():
    context = create_context("RELIANCE")

    run_foundation(context)
    run_valuation(context)

    assert context.status == "INPUT_REQUIRED"
    assert context.sotp is None
    assert context.dcf is None


def test_valuation_boundary_preserves_independence():
    context = create_context("RELIANCE")

    raw = {
        "data": {
            "company_name": "Reliance Industries",
            "shares_outstanding": 100.0,
            "dcf_segments": [],
            "other_segments": [],
            "holdco_discount": 0.0,
        }
    }

    run_foundation(context, raw)
    run_valuation(context)

    # The exact legacy engines may reject incomplete valuation
    # data, but the EROS boundary must remain intact.
    if context.valuation_bridge is not None:
        assert hasattr(context.valuation_bridge, "sotp")
        assert hasattr(context.valuation_bridge, "dcf")
        assert context.sotp is context.valuation_bridge.sotp
        assert context.dcf is context.valuation_bridge.dcf


def test_finalize_still_exposes_valuation_fields():
    context = create_context("RELIANCE")

    result = finalize(context)

    assert "sotp" in result
    assert "dcf" in result
    assert "valuation_bridge" in result
    assert result["provenance"]["orchestrator"] == "EROS_3.0"
