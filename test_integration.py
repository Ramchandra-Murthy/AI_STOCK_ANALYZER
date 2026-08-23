from services.valuation.sotp_engine import SOTPEngine
from domain.valuation.result import ValuationMethod, ValuationStatus


def test_sotp_engine_contract():
    engine = SOTPEngine()

    data = {
        "company_name": "Test Company",
        "shares_outstanding": 100.0,
        "dcf_segments": [],
        "other_segments": [],
        "holdco_discount": 0.0,
    }

    result = engine.evaluate(data)

    assert result is not None
    assert result.method == ValuationMethod.SOTP
    assert result.status == ValuationStatus.SUCCESS
    assert isinstance(result.enterprise_value, (int, float))
    assert isinstance(result.equity_value, (int, float))
    assert isinstance(result.implied_share_price, (int, float))
    assert isinstance(result.details, dict)


def test_sotp_engine_default_data():
    engine = SOTPEngine()

    result = engine.evaluate({})

    assert result.method == ValuationMethod.SOTP
    assert result.status == ValuationStatus.SUCCESS
