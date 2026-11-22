from datetime import datetime, timedelta, timezone

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.enums import AppealStatus, Role
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

    def save_moderator_action(
        self,
        appeal_id: int,
        reviewer_id: int,
        payload: AuctionAppealReviewRequest,
    ) -> AuctionAppeal | None:
        appeal = self.db.get(AuctionAppeal, appeal_id)
        if appeal is None:
            return None

        if appeal.is_resolved:
            raise ValueError("Appeal is already closed")

        appeal.status = payload.status
        appeal.reviewer_id = reviewer_id
        appeal.resolution_note = payload.resolution_note
        appeal.internal_notes = payload.internal_notes
        appeal.resolved_at = (
            datetime.now(timezone(timedelta(0)))
            if payload.status in (AppealStatus.APPROVED, AppealStatus.REJECTED)
            else None
        )
        self.db.commit()
        self.db.refresh(appeal)
        return appeal
