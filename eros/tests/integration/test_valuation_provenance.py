from eros.api.service import evaluate


def test_pipeline_result_preserves_eros_provenance():
    result = evaluate("RELIANCE")

    assert result["provenance"]["orchestrator"] == "EROS_3.0"
    assert result["provenance"]["symbol"] == "RELIANCE"
