from datetime import datetime

from pydantic import BaseModel, ConfigDict

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
    status: AppealStatus | None = None
    reason_code: AppealReasonCode | None = None
    reviewer_id: int | None = None
