from eros.valuation import ValuationBoundary


def test_empty_valuation_input_is_safe():
    result = ValuationBoundary().evaluate({})

    assert result["status"] == "INPUT_REQUIRED"
    assert result["sotp"] is None
    assert result["dcf"] is None
    assert result["warnings"]


def test_partial_valuation_input_does_not_create_fake_values():
    result = ValuationBoundary().evaluate(
        {
            "sotp": None,
            "dcf": None,
        }
    )

    assert result["status"] == "INPUT_REQUIRED"
    assert result["sotp"] is None
    assert result["dcf"] is None


def test_valuation_boundary_exposes_independent_authorities():
    boundary = ValuationBoundary()

    assert hasattr(boundary, "evaluate_sotp")
    assert hasattr(boundary, "evaluate_dcf")


def test_sotp_engine_import_is_canonical():
    from services.valuation.sotp_engine import SOTPValuationEngine

    engine = SOTPValuationEngine()

    assert engine.valuation_method == "SOTP"


def test_dcf_engine_import_is_canonical():
    from services.valuation.dcf_engine import DCFValuationEngine

    engine = DCFValuationEngine()

    assert engine.valuation_method == "DCF"
