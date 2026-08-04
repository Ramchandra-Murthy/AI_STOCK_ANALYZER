from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from core.types.currency import Currency
from core.exceptions import ValidationError

@dataclass(frozen=True, slots=True)
class Money:
    amount: Decimal
    currency: Currency

    def __init__(self, amount: float | int | Decimal | str, currency: Currency | str = "INR") -> None:
        try:
            dec_amount = Decimal(str(amount)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        except Exception as exc:
            raise ValidationError(f"Invalid monetary amount: {amount}") from exc

        curr = Currency(currency) if isinstance(currency, str) else currency

        object.__setattr__(self, "amount", dec_amount)
        object.__setattr__(self, "currency", curr)

    def __add__(self, other: Money) -> Money:
        if self.currency != other.currency:
            raise ValidationError(f"Cannot add different currencies: {self.currency} and {other.currency}")
        return Money(self.amount + other.amount, self.currency)

    def __sub__(self, other: Money) -> Money:
        if self.currency != other.currency:
            raise ValidationError(f"Cannot subtract different currencies: {self.currency} and {other.currency}")
        return Money(self.amount - other.amount, self.currency)

    def to_dict(self) -> dict[str, str | float]:
        return {
            "amount": float(self.amount),
            "currency": str(self.currency),
        }
