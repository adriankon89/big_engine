import builtins
from uuid import uuid4

from sqlalchemy.orm import Session

from app.dto import UploadedFileDTO
from app.enums import RejectionSource
from app.models.auction import Auction
from app.models.auction_image import AuctionImage
from app.models.user import User
from app.schemas.auction import AuctionCreate
from app.services.file_storage import FileStorage
from app.tasks.auction_validation import auction_validation


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

    def create(
        self, payload: AuctionCreate, images: builtins.list[UploadedFileDTO], user: User
    ) -> Auction:
        auction_data = payload.model_dump(exclude={"images"})
        auction = Auction(**auction_data)
        auction.seller_id = user.id
        self.db.add(auction)
        saved_storage_keys: list[str] = []

        try:
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
            auction_validation.delay(auction.id)

        except Exception:
            self.db.rollback()
            for storage_key in saved_storage_keys:
                self.storage.delete(storage_key)
            raise

        return auction
