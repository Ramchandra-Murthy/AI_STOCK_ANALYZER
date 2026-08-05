from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class ForecastLineItem:
    name: str
    values: tuple[float, ...]

    def to_dict(self) -> dict[str, Any]:
        return {"name": self.name, "values": list(self.values)}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ForecastLineItem:
        return cls(name=data["name"], values=tuple(data["values"]))


@dataclass(frozen=True, slots=True)
class ForecastPackage:
    ticker: str
    years: tuple[int, ...]
    revenue: ForecastLineItem
    net_income: ForecastLineItem
    capex: ForecastLineItem
    depreciation: ForecastLineItem
    working_capital: ForecastLineItem
    tax_rate: ForecastLineItem
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ticker": self.ticker,
            "years": list(self.years),
            "revenue": self.revenue.to_dict(),
            "net_income": self.net_income.to_dict(),
            "capex": self.capex.to_dict(),
            "depreciation": self.depreciation.to_dict(),
            "working_capital": self.working_capital.to_dict(),
            "tax_rate": self.tax_rate.to_dict(),
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ForecastPackage:
        return cls(
            ticker=data["ticker"],
            years=tuple(data["years"]),
            revenue=ForecastLineItem.from_dict(data["revenue"]),
            net_income=ForecastLineItem.from_dict(data["net_income"]),
            capex=ForecastLineItem.from_dict(data["capex"]),
            depreciation=ForecastLineItem.from_dict(data["depreciation"]),
            working_capital=ForecastLineItem.from_dict(data["working_capital"]),
            tax_rate=ForecastLineItem.from_dict(data["tax_rate"]),
            metadata=dict(data.get("metadata", {})),
        )
