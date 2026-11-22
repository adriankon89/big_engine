from datetime import datetime, timedelta, timezone

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.core.exceptions import AppealAlreadyClosedError, AuctionAppealNotFoundError
from app.enums import Role
from app.models.auction import Auction
from app.models.auction_appeal import AuctionAppeal
from app.schemas.auction import CreateAuctionAppealRequest
from app.schemas.auction_appeal import (
    AuctionAppealRead,
    AuctionAppealRequest,
    AuctionAppealReviewRequest,
)
from app.schemas.pagination import PaginatedResponse
from app.services.pagination import paginate


class AuctionAppealService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list(
        self, params: AuctionAppealRequest
    ) -> PaginatedResponse[AuctionAppealRead]:
        stmt = select(AuctionAppeal)

        if params.auction_id is not None:
            stmt = stmt.where(AuctionAppeal.auction_id == params.auction_id)
        if params.status is not None:
            stmt = stmt.where(AuctionAppeal.status == params.status)
        if params.reason_code is not None:
            stmt = stmt.where(AuctionAppeal.reason_code == params.reason_code)
        if params.reviewer_id is not None:
            stmt = stmt.where(AuctionAppeal.reviewer_id == params.reviewer_id)

        stmt = stmt.order_by(desc(AuctionAppeal.created_at))
        return paginate(self.db, stmt, params, AuctionAppealRead)

    def create(
        self,
        payload: CreateAuctionAppealRequest,
        actor_id: int,
        actor_role: Role | str,
    ) -> AuctionAppeal:
        auction = self.db.get(Auction, payload.auction_id)
        if auction is None:
            raise ValueError("Auction not found")

        privileged_roles = (Role.ADMIN, Role.MODERATOR)
        is_privileged = actor_role in privileged_roles or actor_role in (
            Role.ADMIN.value,
            Role.MODERATOR.value,
        )
        if auction.seller_id != actor_id and not is_privileged:
            raise ValueError("You are not the seller of this auction")
        if not auction.allow_appeal:
            raise ValueError("This auction is not eligible for appeal")

        appeal = AuctionAppeal(
            auction_id=auction.id,
            reason_code=payload.reason_code,
            reason=payload.reason,
        )
        self.db.add(appeal)
        self.db.commit()
        self.db.refresh(appeal)

        return appeal

    def review_appeal(
        self,
        appeal_id: int,
        reviewer_id: int,
        payload: AuctionAppealReviewRequest,
    ) -> AuctionAppeal:
        appeal = self.db.get(AuctionAppeal, appeal_id)
        if appeal is None:
            raise AuctionAppealNotFoundError(appeal_id)

        if appeal.is_resolved:
            raise AppealAlreadyClosedError("Appeal is already closed")

        if payload.status is not None:
            appeal.status = payload.status
        appeal.reviewer_id = reviewer_id
        if "resolution_note" in payload.model_fields_set:
            appeal.resolution_note = payload.resolution_note
        if "internal_notes" in payload.model_fields_set:
            appeal.internal_notes = payload.internal_notes
        appeal.resolved_at = (
            datetime.now(timezone(timedelta(0))) if appeal.is_resolved else None
        )
        self.db.commit()
        self.db.refresh(appeal)
        return appeal
