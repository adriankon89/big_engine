from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class BidCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)


class BidRead(BidCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
