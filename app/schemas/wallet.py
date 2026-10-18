from decimal import Decimal

from pydantic import BaseModel, Field


class WalletResponse(BaseModel):
    balance_available: Decimal
    balance_held: Decimal
    currency: str


class WalletUpdate(BaseModel):
    balance: Decimal = Field(..., ge=0, max_digits=12, decimal_places=2)
    currency: str | None = None  # todo dorzucic enum
