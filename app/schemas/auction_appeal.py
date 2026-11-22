from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.enums import AppealReasonCode, AppealStatus
from app.schemas.pagination import PaginationParams


class AuctionAppealRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    auction_id: int
    status: AppealStatus
    reason: str
    reason_code: AppealReasonCode
    reviewer_id: int | None = None
    resolution_note: str | None = None
    internal_notes: str | None = None
    resolved_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class AuctionAppealRequest(PaginationParams):
    auction_id: int | None = None
    status: AppealStatus | None = Field(
        default=AppealStatus.OPEN, description="Filter by status"
    )
    reason_code: AppealReasonCode | None = None
    reviewer_id: int | None = None


class AuctionAppealReviewRequest(BaseModel):
    status: AppealStatus | None = None
    resolution_note: str | None = Field(default=None, max_length=2000)
    internal_notes: str | None = Field(default=None, max_length=2000)
