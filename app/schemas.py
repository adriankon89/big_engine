from datetime import UTC, datetime
from decimal import Decimal
from math import ceil
from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator

from app.enums import Role, SortOrder, UserSortBy, UserStatus

# auth # app/schemas/auth.py


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


# end auth


# user


class UserCreate(BaseModel):
    email: EmailStr = Field(..., max_length=200)
    password: str = Field(..., min_length=8, max_length=128)


class UserUpdate(BaseModel):
    email: EmailStr | None = Field(None, max_length=200)
    role: Role | None = None


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    created_at: datetime
    role: Role
    status: UserStatus


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(
        ..., min_length=8, max_length=128, description="Old password"
    )
    new_password: str = Field(
        ..., min_length=8, max_length=128, description="New password"
    )


class AdminResetPasswordRequest(BaseModel):
    new_password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="New password for the user, set by admin",
    )


class UserStatusUpdate(BaseModel):
    status: UserStatus


# role: Role


class UserFilterParams(BaseModel):
    page: int = Field(default=1, ge=1, description="Page number")
    page_size: int = Field(
        default=20, ge=1, le=100, description="Elements amount per page"
    )
    sort_by: UserSortBy = Field(
        default=UserSortBy.CREATED_AT, description="Sort order field"
    )
    order: SortOrder = Field(default=SortOrder.ASC, description="Sort order")

    min_balance: float | None = Field(default=None, ge=0, description="minimal balance")
    search: str | None = Field(default=None, description="Search by email")
    role: Role | None = Field(default=None, description="User role")

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size


# end user


class WalletResponse(BaseModel):
    balance_available: Decimal
    balance_held: Decimal
    currency: str


class WalletUpdate(BaseModel):
    balance: Decimal = Field(..., ge=0, max_digits=12, decimal_places=2)
    currency: str | None = None  # todo dorzucic enum


class BidCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)


# zwraca title i amount i id bo dziedziczy po BidCreate
class BidRead(BidCreate):
    model_config = ConfigDict(
        from_attributes=True
    )  # TODO co to robi to chyba ze z atrybutów sobie samo pobiera

    id: int


# auction
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


# pagination

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    page_size: int
    total_pages: int

    @classmethod
    def create(
        cls, items: list[T], total: int, params: UserFilterParams
    ) -> "PaginatedResponse[T]":
        return cls(
            items=items,
            total=total,
            page=params.page,
            page_size=params.page_size,
            total_pages=ceil(total / params.page_size) if params.page_size > 0 else 0,
        )
