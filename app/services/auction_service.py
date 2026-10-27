import builtins
import logging
from typing import Any
from uuid import uuid4

from sqlalchemy.orm import Session

from app.dto import UploadedFileDTO
from app.enums import RejectionSource
from app.models.auction import Auction
from app.models.auction_image import AuctionImage
from app.models.user import User
from app.schemas.auction import AuctionCreate, AuctionImageCreate
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

    def get(self, auction_id: int) -> Auction | None:
        return self.db.get(Auction, auction_id)

    def reject(self, auction_id: int, reason: str, moderator: User) -> Auction | None:
        auction = self.get(auction_id)
        if auction is None:
            return None

        auction.reject(
            source=RejectionSource.USER,
            reason=reason,
            rejected_by_id=moderator.id,
        )
        self.db.commit()
        self.db.refresh(auction)
        return auction

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
        self, payload: AuctionCreate, images: builtins.list[UploadedFileDTO], user: User
    ) -> Auction:
        auction_data: builtins.dict[builtins.str, Any] = payload.model_dump(
            exclude={"images"}
        )
        saved_storage_keys: list[str] = []

        try:
            moderator_id: builtins.int | None = (
                self.moderator_assignment.next_moderator_id(user.id)
            )
            auction = Auction(
                **auction_data,
                seller_id=user.id,
                moderator_id=moderator_id,
            )
            self.db.add(auction)
            self.db.flush()
            for position, image in enumerate(images):
                storage_key = uuid4().hex
                self.storage.save(storage_key, image.content)
                saved_storage_keys.append(storage_key)

                metadata: AuctionImageCreate | None = (
                    payload.images[position] if position < len(payload.images) else None
                )
                self.db.add(
                    self._build_auction_image(
                        auction_id=auction.id,
                        storage_key=storage_key,
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
            self.db.refresh(auction)
            if moderator_id is None:
                logger.warning(
                    "Auction created without an assigned moderator",
                    extra={"auction_id": auction.id, "seller_id": user.id},
                )
            auction_validation.delay(auction.id)

        except Exception:
            self.db.rollback()
            for storage_key in saved_storage_keys:
                self.storage.delete(storage_key)
            raise

        return auction
