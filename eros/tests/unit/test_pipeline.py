from eros.api.service import evaluate
from eros.decision.pipeline import create_context


def test_context():
    context = create_context("RELIANCE")

    assert context.symbol == "RELIANCE"
    assert context.status == "INITIALIZED"


def test_finalize():
    result = evaluate("RELIANCE")

    assert result["symbol"] == "RELIANCE"

    # No financial payload was supplied.
    # EROS must not claim that evaluation completed.
    assert result["status"] == "INPUT_REQUIRED"

    assert result["warnings"]

    assert result["provenance"]["orchestrator"] == "EROS_3.0"
    assert result["provenance"]["pipeline_status"] == "INPUT_REQUIRED"
