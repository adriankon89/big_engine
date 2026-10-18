from datetime import UTC, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class AuctionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str
    starting_price: Decimal
    minimum_price: Decimal
    current_price: Decimal | None
    bid_increment: Decimal | None
    status: str
    starts_at: datetime
    ends_at: datetime


class AuctionImageCreate(BaseModel):
    storage_path: str = Field(max_length=500)
    file_size: int | None = Field(default=None)
    mime_type: str | None = Field(default=None)
    order: int = Field(default=0, ge=0, le=32767)
    is_primary: bool = False


class AuctionCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=40, max_length=1000)
    starting_price: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    minimum_price: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    currency: str = Field(min_length=3, max_length=3)
    starts_at: datetime
    ends_at: datetime
    images: list[AuctionImageCreate] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_schedule(self) -> "AuctionCreate":
        starts_at = self.starts_at
        ends_at = self.ends_at

        if starts_at.tzinfo is None:
            starts_at: datetime = starts_at.replace(tzinfo=UTC)
        if ends_at.tzinfo is None:
            ends_at: datetime = ends_at.replace(tzinfo=UTC)

        if starts_at < datetime.now(UTC):
            raise ValueError("starts_at must be greater than or equal to now")
        if ends_at < starts_at:
            raise ValueError("ends_at must be greater than or equal to starts_at")

        if self.images:
            primary_count = sum(1 for img in self.images if img.is_primary)
            if primary_count > 1:
                raise ValueError("Only one image can be marked as primary.")
            elif primary_count == 0 and self.images:
                self.images[0].is_primary = True

        return self


class AuctionCreateResponse(BaseModel):
    id: int
