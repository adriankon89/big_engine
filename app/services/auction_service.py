import builtins
import logging
from uuid import uuid4

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.dto import UploadedFileDTO
from app.enums import RejectionSource, Role, UserStatus
from app.models.auction import Auction
from app.models.auction_image import AuctionImage
from app.models.moderator_assignment_state import ModeratorAssignmentState
from app.models.user import User
from app.schemas.auction import AuctionCreate
from app.services.file_storage import FileStorage
from app.tasks.auction_validation import auction_validation

logger = logging.getLogger(__name__)


class AuctionService:
    def __init__(self, db: Session, storage: FileStorage) -> None:
        self.db: Session = db
        self.storage = storage

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

    def _next_moderator_id(self, seller_id: int) -> int | None:
        state_id = 1
        self.db.execute(
            update(ModeratorAssignmentState)
            .where(ModeratorAssignmentState.id == state_id)
            .values(last_moderator_id=ModeratorAssignmentState.last_moderator_id)
        )
        state = self.db.scalar(
            select(ModeratorAssignmentState)
            .where(ModeratorAssignmentState.id == state_id)
            .with_for_update()
        )
        if state is None:
            raise RuntimeError("Moderator assignment state has not been initialized")

        moderator_ids = list(
            self.db.scalars(
                select(User.id)
                .where(
                    User.role.in_([Role.ADMIN.value, Role.MODERATOR.value]),
                    User.status == UserStatus.ACTIVE.value,
                    User.id != seller_id,
                )
                .order_by(User.id)
            ).all()
        )
        if not moderator_ids:
            return None

        if state.last_moderator_id is None:
            next_index = 0
        else:
            try:
                previous_index = moderator_ids.index(state.last_moderator_id)
            except ValueError:
                next_index = 0
            else:
                next_index = (previous_index + 1) % len(moderator_ids)

        moderator_id = moderator_ids[next_index]
        state.last_moderator_id = moderator_id
        return moderator_id

    def create(
        self, payload: AuctionCreate, images: builtins.list[UploadedFileDTO], user: User
    ) -> Auction:
        auction_data = payload.model_dump(exclude={"images"})
        saved_storage_keys: list[str] = []

        try:
            moderator_id = self._next_moderator_id(user.id)
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

                metadata = (
                    payload.images[position] if position < len(payload.images) else None
                )
                self.db.add(
                    AuctionImage(
                        auction_id=auction.id,
                        storage_key=storage_key,
                        original_filename=image.filename,
                        file_size=len(image.content),
                        mime_type=image.content_type,
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
