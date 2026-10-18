from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.celery_app import celery_app
from app.config import get_settings
from app.database import SessionLocal
from app.enums import RejectionSource
from app.models.auction import Auction
from app.services.auction_validator.base import (
    AuctionValidationResult,
    AuctionValidator,
)
from app.services.auction_validator.factory import get_auction_validator


@celery_app.task(
    name="auction_validation", bind=True, max_retries=2, retry_backoff=True
)
def auction_validation(self, auction_id: int) -> dict[str, object]:
    with SessionLocal() as db:
        auction = db.scalar(
            select(Auction)
            .options(selectinload(Auction.images))
            .where(Auction.id == auction_id)
        )

        if auction is None:
            return {"error": "auction_not_found", "auction_id": auction_id}

        auction_validator: AuctionValidator = get_auction_validator()
        image_paths: list[Path] = [
            Path(get_settings().UPLOAD_DIR) / image.storage_key
            for image in auction.images
        ]
        validation_result: AuctionValidationResult = auction_validator.validate_auction(
            image_paths, auction.title, auction.description
        )

        if not validation_result.is_valid:
            auction.reject(
                source=RejectionSource.AI,
                reason=validation_result.reason,
            )

        db.commit()

        return {
            "auction_id": auction.id,
            "title": auction.title,
            "is_valid": validation_result.is_valid,
            "reason": validation_result.reason,
            "images": [
                {
                    "id": image.id,
                    "storage_key": image.storage_key,
                    "original_filename": image.original_filename,
                    "position": image.position,
                    "is_primary": image.is_primary,
                }
                for image in auction.images
            ],
        }
