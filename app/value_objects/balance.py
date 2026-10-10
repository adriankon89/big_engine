from dataclasses import dataclass
from decimal import Decimal


class NegativeBalanceError(ValueError):
    pass


@dataclass(frozen=True)
class Balance:
    amount: Decimal

    def __post_init__(self) -> None:
        if self.amount < 0:
            raise NegativeBalanceError("Balance cannot be negative")

    @classmethod
    def of(cls, amount: str | float | Decimal) -> "Balance":
        return cls(amount=Decimal(str(amount)))
