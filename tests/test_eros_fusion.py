import pandas as pd

from scanner.eros_fusion import compute_eros_fusion


def test_fusion_combines_available_components():
    confluence = pd.DataFrame(
        {
            "Symbol": ["AAA", "BBB"],
            "Exchange": ["NSE", "NSE"],
            "Confluence Score": [90.0, 60.0],
        }
    )
    history = pd.DataFrame(
        {
            "Timestamp": pd.to_datetime(["2026-09-18 10:00", "2026-09-18 10:02"]),
            "Symbol": ["AAA", "AAA"],
            "Exchange": ["NSE", "NSE"],
        }
    )
    jumps = pd.DataFrame({"Symbol": ["AAA"], "Exchange": ["NSE"]})
    result = compute_eros_fusion(
        confluence,
        history,
        jumps,
        {"score": 80.0},
    )
    assert result.iloc[0]["Symbol"] == "AAA"
    assert result.iloc[0]["Fusion Score"] > result.iloc[1]["Fusion Score"]
    assert result.iloc[0]["Fusion Coverage"] == 4


def test_empty_confluence_returns_empty():
    assert compute_eros_fusion(pd.DataFrame()).empty
