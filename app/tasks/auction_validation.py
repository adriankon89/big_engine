from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.celery_app import celery_app
from app.database import SessionLocal
from app.models import Auction


@celery_app.task(name="auction_validation", bind=True)
def auction_validation(self, auction_id: int) -> dict[str, object]:
    with SessionLocal() as db:
        auction = db.scalar(
            select(Auction)
            .options(selectinload(Auction.images))
            .where(Auction.id == auction_id)
        )

        if auction is None:
            return {"error": "auction_not_found", "auction_id": auction_id}

        return {
            "auction_id": auction.id,
            "title": auction.title,
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
