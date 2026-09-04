import pandas as pd

from services.technical_score_service import calculate_technical_score


def _sample_history():
    prices = [
        100, 101, 102, 103, 104,
        105, 106, 107, 108, 109,
        110, 111, 112, 113, 114,
        115, 116, 117, 118, 119,
        120, 121, 122, 123, 124,
        125, 126, 127, 128, 129,
        130, 131, 132, 133, 134,
        135, 136, 137, 138, 139,
        140, 141, 142, 143, 144,
        145, 146, 147, 148, 149,
        150,
    ]

    return pd.DataFrame(
        {
            "Close": prices,
            "High": [p + 1 for p in prices],
            "Low": [p - 1 for p in prices],
            "Open": prices,
            "Volume": [1_000_000] * len(prices),
        }
    )


def test_technical_score_returns_score_and_reasons():
    history = _sample_history()

    score, reasons = calculate_technical_score(history)

    assert isinstance(score, (int, float))
    assert 0 <= score <= 100
    assert isinstance(reasons, list)


def test_technical_score_is_bounded():
    history = _sample_history()

    score, _ = calculate_technical_score(history)

    assert 0 <= score <= 100


def test_technical_score_handles_empty_history():
    history = pd.DataFrame()

    score, reasons = calculate_technical_score(history)

    assert isinstance(score, (int, float))
    assert isinstance(reasons, list)
