from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class Money:
    amount: Decimal

    @classmethod
    def zero(cls) -> "Money":
        return cls(amount=Decimal("0.00"))

    @classmethod
    def of(cls, amount: float | str | Decimal) -> "Money":
        return cls(amount=Decimal(str(amount)))
