from eros import evaluate
from eros.decision import create_context, finalize


def test_context():
    ctx = create_context("reliance")

    assert ctx.symbol == "RELIANCE"
    assert ctx.status == "INITIALIZED"


def test_finalize():
    result = evaluate("RELIANCE")

    assert result["symbol"] == "RELIANCE"
    assert result["status"] == "COMPLETE"
    assert result["provenance"]["orchestrator"] == "EROS_3.0"
