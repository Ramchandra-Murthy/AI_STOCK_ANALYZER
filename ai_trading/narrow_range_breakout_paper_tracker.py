"""CSV-backed paper journal for NR4/NR7 breakout signals (no broker execution)."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

import pandas as pd

Pattern = Literal["NR4", "NR7"]
Side = Literal["LONG", "SHORT"]
Status = Literal["WATCHING", "OPEN", "CLOSED", "CANCELLED"]


@dataclass
class NarrowRangePaperTrade:
    """One tracked NR4/NR7 signal and its optional simulated trade outcome."""

    signal_id: str
    symbol: str
    pattern: Pattern
    side: Side
    signal_time: str
    trigger: float
    stop: float
    target: float
    status: Status = "WATCHING"
    entry_time: str | None = None
    entry_price: float | None = None
    exit_time: str | None = None
    exit_price: float | None = None
    exit_reason: str | None = None
    quantity: int = 0
    notes: str = ""

    @property
    def realized_pnl(self) -> float | None:
        """Return simulated gross P&L for a closed trade, if available."""
        if self.status != "CLOSED" or self.entry_price is None or self.exit_price is None:
            return None
        direction = 1 if self.side == "LONG" else -1
        return (self.exit_price - self.entry_price) * self.quantity * direction

    @property
    def realized_r(self) -> float | None:
        """Return realized R using the entry-to-stop risk per unit."""
        pnl = self.realized_pnl
        if pnl is None or self.entry_price is None:
            return None
        risk_per_unit = abs(self.entry_price - self.stop)
        risk = risk_per_unit * self.quantity
        return pnl / risk if risk > 0 else None


class NarrowRangePaperTracker:
    """Manage a small CSV-persisted NR4/NR7 paper-trade journal."""

    def __init__(self, trades: list[NarrowRangePaperTrade] | None = None) -> None:
        self.trades = list(trades or [])

    def add_signal(
        self,
        *,
        signal_id: str,
        symbol: str,
        pattern: Pattern,
        side: Side,
        trigger: float,
        stop: float,
        target: float,
        signal_time: str | None = None,
        notes: str = "",
    ) -> NarrowRangePaperTrade:
        """Record a signal after validating its directional levels."""
        if not signal_id.strip() or not symbol.strip():
            raise ValueError("signal_id and symbol are required")
        if pattern not in {"NR4", "NR7"} or side not in {"LONG", "SHORT"}:
            raise ValueError("pattern or side is invalid")
        trigger, stop, target = float(trigger), float(stop), float(target)
        if min(trigger, stop, target) <= 0:
            raise ValueError("trigger, stop, and target must be positive")
        if side == "LONG" and not stop < trigger < target:
            raise ValueError("LONG levels must satisfy stop < trigger < target")
        if side == "SHORT" and not target < trigger < stop:
            raise ValueError("SHORT levels must satisfy target < trigger < stop")
        if any(trade.signal_id == signal_id for trade in self.trades):
            raise ValueError("signal_id already exists")

        trade = NarrowRangePaperTrade(
            signal_id=signal_id,
            symbol=symbol.strip().upper(),
            pattern=pattern,
            side=side,
            signal_time=signal_time or datetime.now(UTC).isoformat(),
            trigger=trigger,
            stop=stop,
            target=target,
            notes=notes,
        )
        self.trades.append(trade)
        return trade

    def _get(self, signal_id: str) -> NarrowRangePaperTrade:
        for trade in self.trades:
            if trade.signal_id == signal_id:
                return trade
        raise KeyError(signal_id)

    def record_entry(
        self,
        signal_id: str,
        *,
        entry_price: float,
        quantity: int,
        entry_time: str | None = None,
    ) -> NarrowRangePaperTrade:
        """Mark a watched signal as entered in the paper journal."""
        trade = self._get(signal_id)
        price = float(entry_price)
        if trade.status != "WATCHING":
            raise ValueError("only WATCHING signals can be entered")
        if price <= 0 or quantity <= 0:
            raise ValueError("entry_price and quantity must be positive")
        trade.entry_price = price
        trade.quantity = int(quantity)
        trade.entry_time = entry_time or datetime.now(UTC).isoformat()
        trade.status = "OPEN"
        return trade

    def close_trade(
        self,
        signal_id: str,
        *,
        exit_price: float,
        exit_reason: str,
        exit_time: str | None = None,
    ) -> NarrowRangePaperTrade:
        """Record a simulated exit for an open paper trade."""
        trade = self._get(signal_id)
        price = float(exit_price)
        if trade.status != "OPEN":
            raise ValueError("only OPEN trades can be closed")
        if price <= 0 or not exit_reason.strip():
            raise ValueError("exit_price and exit_reason are required")
        trade.exit_price = price
        trade.exit_reason = exit_reason.strip().upper()
        trade.exit_time = exit_time or datetime.now(UTC).isoformat()
        trade.status = "CLOSED"
        return trade

    def cancel_signal(self, signal_id: str, *, notes: str = "") -> NarrowRangePaperTrade:
        """Cancel a signal that has not been entered."""
        trade = self._get(signal_id)
        if trade.status != "WATCHING":
            raise ValueError("only WATCHING signals can be cancelled")
        trade.status = "CANCELLED"
        if notes:
            trade.notes = notes
        return trade

    def to_frame(self) -> pd.DataFrame:
        """Return journal records as a DataFrame."""
        rows = []
        for trade in self.trades:
            row = asdict(trade)
            row["realized_pnl"] = trade.realized_pnl
            row["realized_r"] = trade.realized_r
            rows.append(row)
        return pd.DataFrame(rows)

    def save_csv(self, path: str | Path) -> None:
        """Persist the journal to CSV."""
        self.to_frame().to_csv(path, index=False)

    @classmethod
    def load_csv(cls, path: str | Path) -> NarrowRangePaperTracker:
        """Load journal records from CSV."""
        frame = pd.read_csv(path)
        trades = []
        for row in frame.to_dict(orient="records"):
            row.pop("realized_pnl", None)
            row.pop("realized_r", None)
            for field in ("entry_price", "exit_price"):
                if pd.isna(row[field]):
                    row[field] = None
            for field in ("entry_time", "exit_time", "exit_reason"):
                if pd.isna(row[field]):
                    row[field] = None
            if pd.isna(row["notes"]):
                row["notes"] = ""
            trades.append(NarrowRangePaperTrade(**row))
        return cls(trades)
