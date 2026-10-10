from sqlalchemy.orm import Session

from app.schemas import AuctionCreate


class AuctionService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, payload: AuctionCreate):
        pass
