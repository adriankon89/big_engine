import builtins
from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import Auction, AuctionImage, User
from app.schemas import AuctionCreate


# todo UploadFile framework agnostic
class AuctionService:
    def __init__(self, db: Session) -> None:
        self.db: Session = db

    def list(self):
        print(len(self.db.query(Auction).all()))
        return list(self.db.query(Auction).all())

    def create(
        self, payload: AuctionCreate, images: builtins.list[UploadFile], user: User
    ):

        auction_data = payload.model_dump(exclude={"images"})
        auction = Auction(**auction_data)
        auction.seller_id = user.id
        self.db.add(auction)
        saved_paths: list[Path] = []

        try:
            self.db.flush()
            upload_dir = get_settings().UPLOAD_DIR
            if images:
                upload_dir.mkdir(parents=True, exist_ok=True)

            for position, image in enumerate(images):
                contents = image.file.read()
                storage_key = uuid4().hex
                file_path = upload_dir / storage_key
                file_path.write_bytes(contents)
                saved_paths.append(file_path)

                metadata = (
                    payload.images[position] if position < len(payload.images) else None
                )
                self.db.add(
                    AuctionImage(
                        auction_id=auction.id,
                        storage_key=storage_key,
                        original_filename=image.filename or "upload",
                        file_size=len(contents),
                        mime_type=image.content_type or "application/octet-stream",
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
        except Exception:
            self.db.rollback()
            for file_path in saved_paths:
                file_path.unlink(missing_ok=True)
            raise

        return auction
