from pydantic import Field

from app.enums import ModeratorSortBy, SortOrder, UserStatus
from app.schemas.pagination import PaginationParams


class ModeratorFilterParams(PaginationParams):
    sort_by: ModeratorSortBy = Field(
        default=ModeratorSortBy.CREATED_AT, description="Field to sort moderators by"
    )
    order: SortOrder = Field(default=SortOrder.ASC, description="Sort order")
    search: str | None = Field(default=None, description="Search by email")
    status: UserStatus | None = Field(default=None, description="Filter by status")
