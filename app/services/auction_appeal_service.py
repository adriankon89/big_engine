from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from app.enums import Role
from app.models.auction import Auction
from app.models.auction_appeal import AuctionAppeal
from app.schemas.auction import CreateAuctionAppealRequest
from app.schemas.auction_appeal import AuctionAppealRead, AuctionAppealRequest
from app.schemas.pagination import PaginatedResponse


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

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = self.db.scalar(count_stmt) or 0

        stmt = stmt.order_by(desc(AuctionAppeal.created_at))
        stmt = stmt.offset(params.offset).limit(params.page_size)

        appeals = list(self.db.scalars(stmt).all())
        items = [AuctionAppealRead.model_validate(appeal) for appeal in appeals]

        return PaginatedResponse[AuctionAppealRead].create(
            items=items,
            total=total,
            params=params,
        )

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
