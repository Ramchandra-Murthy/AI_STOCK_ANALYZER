from typing import Dict, List, Any


class SOTPValuationEngine:
    """Computes Sum-of-the-Parts valuation for multi-segment enterprises."""

    def __init__(
        self,
        symbol: str,
        segments: List[Dict[str, Any]],
        net_debt: float,
        non_operating_assets: float,
        shares_outstanding: float,
    ):
        self.symbol = symbol
        self.segments = segments
        self.net_debt = net_debt
        self.non_operating_assets = non_operating_assets
        self.shares_outstanding = shares_outstanding

    def calculate_enterprise_value(self) -> Dict[str, Any]:
        segment_valuations = {}
        total_ev = 0.0

        for segment in self.segments:
            name = segment.get("name")
            value = segment.get("valuation", 0.0)
            segment_valuations[name] = value
            total_ev += value

        return {"segment_breakdown": segment_valuations, "total_enterprise_value": total_ev}

    def compute_intrinsic_value(self) -> Dict[str, Any]:
        ev_data = self.calculate_enterprise_value()
        total_ev = ev_data["total_enterprise_value"]

        equity_value = total_ev - self.net_debt + self.non_operating_assets

        intrinsic_value_per_share = (
            equity_value / self.shares_outstanding if self.shares_outstanding > 0 else 0.0
        )

        return {
            "symbol": self.symbol,
            "enterprise_value": total_ev,
            "segment_breakdown": ev_data["segment_breakdown"],
            "net_debt": self.net_debt,
            "non_operating_assets": self.non_operating_assets,
            "equity_value": equity_value,
            "shares_outstanding": self.shares_outstanding,
            "intrinsic_value": round(intrinsic_value_per_share, 2),
        }


engine = SOTPValuationEngine(
    symbol="TEST",
    segments=[
        {"name": "Segment A", "valuation": 6000.0},
        {"name": "Segment B", "valuation": 3000.0},
        {"name": "Segment C", "valuation": 1000.0},
    ],
    net_debt=2000.0,
    non_operating_assets=500.0,
    shares_outstanding=100.0,
)

print(engine.compute_intrinsic_value())
