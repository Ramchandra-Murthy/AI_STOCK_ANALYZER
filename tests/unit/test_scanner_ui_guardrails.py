import pandas as pd

from modules.scanner import _normalize_broad_market_confidence


def test_broad_market_output_removes_legacy_numeric_confidence() -> None:
    legacy = pd.DataFrame(
        {
            "Symbol": ["SSWL", "ETERNAL"],
            "AI Score": [0, 15],
            "Confidence": [100, 85],
        }
    )

    result = _normalize_broad_market_confidence(legacy)

    assert result["Confidence"].isna().all()
    assert result["Confidence Status"].eq("Not calibrated").all()
    assert legacy["Confidence"].tolist() == [100, 85]


def test_broad_market_output_adds_status_when_confidence_column_is_missing() -> None:
    frame = pd.DataFrame({"Symbol": ["TEST"], "AI Score": [0]})

    result = _normalize_broad_market_confidence(frame)

    assert result.loc[0, "Confidence"] is None or pd.isna(result.loc[0, "Confidence"])
    assert result.loc[0, "Confidence Status"] == "Not calibrated"
