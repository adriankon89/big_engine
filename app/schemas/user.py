from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.enums import Role, SortOrder, UserSortBy, UserStatus


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
