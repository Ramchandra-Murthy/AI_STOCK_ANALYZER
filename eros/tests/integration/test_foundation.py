from eros.api.service import evaluate
from eros.decision.pipeline import (
    create_context,
    finalize,
    run_foundation,
)


def test_empty_symbol_rejected():
    try:
        create_context("")
    except ValueError:
        return

    raise AssertionError("Empty symbol must be rejected")


def test_context_symbol_normalized():
    context = create_context(" reliance ")
    assert context.symbol == "RELIANCE"


def test_empty_input_is_safe():
    result = evaluate("RELIANCE")

    assert result["symbol"] == "RELIANCE"
    assert result["status"] == "INPUT_REQUIRED"
    assert result["warnings"]


def test_foundation_does_not_execute_without_data():
    context = create_context("RELIANCE")

    run_foundation(context)

    assert context.status == "INPUT_REQUIRED"
    assert context.score is None
    assert context.risk is None
    assert context.financials is None


def test_finalize_unexecuted_context_is_not_complete():
    context = create_context("RELIANCE")

    result = finalize(context)

    assert result["status"] == "INPUT_REQUIRED"
    assert result["warnings"]


def test_api_result_contains_provenance():
    result = evaluate("reliance")

    assert result["provenance"]["orchestrator"] == "EROS_3.0"
    assert result["provenance"]["symbol"] == "RELIANCE"
    assert result["provenance"]["pipeline_status"] == "INPUT_REQUIRED"
