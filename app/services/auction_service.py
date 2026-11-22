import builtins
import logging
from typing import Any
from uuid import uuid4

from sqlalchemy import asc, desc, func, select
from sqlalchemy.orm import Session, selectinload

from app.dto import UploadedFileDTO
from app.enums import AuctionSortBy, RejectionSource, SortOrder, VerificationStatus
from app.models.auction import Auction
from app.models.auction_appeal import AuctionAppeal
from app.models.auction_image import AuctionImage
from app.schemas.auction import (
    AuctionCreate,
    AuctionImageCreate,
    AuctionsForManualReviewResponse,
    CreateAuctionAppealRequest,
    MyAuctionFilterParams,
    MyAuctionRead,
)
from app.schemas.moderation import ModeratorAuctionFilterParams
from app.schemas.pagination import PaginatedResponse
from app.services.file_storage import FileStorage
from app.services.moderator_assignment_service import ModeratorAssignmentService
from app.tasks.auction_validation import auction_validation

logger = logging.getLogger(__name__)


class AuctionService:
    def __init__(
        self,
        db: Session,
        storage: FileStorage,
        moderator_assignment: ModeratorAssignmentService,
    ) -> None:
        self.db: Session = db
        self.storage = storage
        self.moderator_assignment = moderator_assignment

    def list(self) -> list[Auction]:
        return list(self.db.query(Auction).all())

    def list_auctions_by_seller(
        self, params: MyAuctionFilterParams, seller_id: int
    ) -> PaginatedResponse[MyAuctionRead]:
        stmt = (
            select(Auction)
            .options(selectinload(Auction.appeal))
            .where(Auction.seller_id == seller_id)
        )

        if params.status is not None:
            stmt = stmt.where(Auction._status == params.status)
        if params.verification_status is not None:
            stmt = stmt.where(
                Auction._verification_status == params.verification_status
            )

        order_func = desc if params.order == SortOrder.DESC else asc
        sort_column = {
            AuctionSortBy.ID: Auction.id,
            AuctionSortBy.TITLE: Auction.title,
            AuctionSortBy.START_TIME: Auction.starts_at,
            AuctionSortBy.END_TIME: Auction.ends_at,
            AuctionSortBy.CREATED_AT: Auction.created_at,
        }[params.sort_by]
        stmt = stmt.order_by(order_func(sort_column))

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = self.db.scalar(count_stmt) or 0

        stmt = stmt.offset(params.offset).limit(params.page_size)

        auctions: list[Auction] = list(self.db.scalars(stmt).all())
        auction_reads: builtins.list[MyAuctionRead] = [
            MyAuctionRead.model_validate(auction) for auction in auctions
        ]

        return PaginatedResponse[MyAuctionRead].create(
            items=auction_reads, total=total, params=params
        )

    def get(self, auction_id: int) -> Auction | None:
        return self.db.get(Auction, auction_id)

    @staticmethod
    def _build_auction_image(
        auction_id: int,
        storage_key: str,
        image: UploadedFileDTO,
        position: int,
        is_primary: bool,
    ) -> AuctionImage:
        return AuctionImage(
            auction_id=auction_id,
            storage_key=storage_key,
            original_filename=image.filename,
            file_size=len(image.content),
            mime_type=image.content_type,
            position=position,
            is_primary=is_primary,
        )

    def create(
        self,
        payload: AuctionCreate,
        images: builtins.list[UploadedFileDTO],
        userId: int,
    ) -> Auction:
        auction_data: builtins.dict[builtins.str, Any] = payload.model_dump(
            exclude={"images"}
        )
        saved_storage_keys: list[str] = []

        try:
            for image in images:
                storage_key = uuid4().hex
                self.storage.save(storage_key, image.content)
                saved_storage_keys.append(storage_key)

            moderator_id: builtins.int | None = (
                self.moderator_assignment.next_moderator_id(userId)
            )
            auction = Auction(
                **auction_data,
                seller_id=userId,
                moderator_id=moderator_id,
            )
            self.db.add(auction)
            self.db.flush()
            for position, image in enumerate(images):
                metadata: AuctionImageCreate | None = (
                    payload.images[position] if position < len(payload.images) else None
                )
                self.db.add(
                    self._build_auction_image(
                        auction_id=auction.id,
                        storage_key=saved_storage_keys[position],
                        image=image,
                        position=metadata.order if metadata else position,
                        is_primary=(
                            metadata.is_primary
                            if metadata
                            else position == 0 and not payload.images
                        ),
                    )
                )

            self.db.commit()
        except Exception:
            self.db.rollback()
            for storage_key in saved_storage_keys:
                try:
                    self.storage.delete(storage_key)
                except Exception:
                    logger.exception(
                        "Failed to clean up auction image after creation failure",
                        extra={"storage_key": storage_key},
                    )
            raise

        self.db.refresh(auction)
        if moderator_id is None:
            logger.warning(
                "Auction created without an assigned moderator",
                extra={"auction_id": auction.id, "seller_id": userId},
            )
        auction_validation.delay(auction.id)

        return auction

    def list_auctions_for_manual_review(
        self, params: ModeratorAuctionFilterParams, current_moderator_id: int
    ) -> PaginatedResponse[AuctionsForManualReviewResponse]:
        stmt = select(Auction)
        stmt = stmt.where(
            Auction._verification_status == VerificationStatus.MANUAL_REVIEW
        )

        if params.reject_reason is not None:
            stmt = stmt.where(Auction.rejection_reason == params.reject_reason)
        if params.reject_source is not None:
            stmt = stmt.where(Auction.rejection_source == params.reject_source)
        if params.rejected_by_id is not None:
            stmt = stmt.where(Auction.rejected_by_id == params.rejected_by_id)
        if params.moderator_id is not None:
            stmt = stmt.where(Auction.moderator_id == params.moderator_id)
        if params.show_mine:
            stmt = stmt.where(Auction.moderator_id == current_moderator_id)

        order_func = desc if params.order == SortOrder.DESC else asc
        sort_column = {
            AuctionSortBy.ID: Auction.id,
            AuctionSortBy.TITLE: Auction.title,
            AuctionSortBy.START_TIME: Auction.starts_at,
            AuctionSortBy.END_TIME: Auction.ends_at,
            AuctionSortBy.CREATED_AT: Auction.created_at,
        }[params.sort_by]
        stmt = stmt.order_by(order_func(sort_column))

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = self.db.scalar(count_stmt) or 0

        stmt = stmt.offset(params.offset).limit(params.page_size)

        auctions: list[Auction] = list(self.db.scalars(stmt).all())
        auction_reads = [
            AuctionsForManualReviewResponse.model_validate(auction)
            for auction in auctions
        ]

        return PaginatedResponse[AuctionsForManualReviewResponse].create(
            items=auction_reads, total=total, params=params
        )

    def approve_auction_manual_review(
        self, auction_id: int, moderator_id: int, reason: str
    ) -> Auction | None:
        auction: Auction | None = self.get(auction_id)
        if auction is None:
            return None

        auction.approve_manual_review(moderator_id=moderator_id, reason=reason)
        self.db.commit()
        self.db.refresh(auction)
        return auction

    def reject_auction_manual_review(
        self,
        auction_id: int,
        moderator_id: int,
        reason: str,
    ) -> Auction | None:
        auction: Auction | None = self.get(auction_id)
        if auction is None:
            return None

        auction.reject(
            source=RejectionSource.USER,
            reason=reason,
            rejected_by_id=moderator_id,
        )
        self.db.commit()
        self.db.refresh(auction)
        return auction

    def create_auction_appeal(
        self, payload: "CreateAuctionAppealRequest", seller_id: int
    ) -> AuctionAppeal:
        auction = self.db.get(Auction, payload.auction_id)
        if auction is None:
            raise ValueError("Auction not found")
        if auction.seller_id != seller_id:
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
        self.db.refresh(auction)

        return appeal
