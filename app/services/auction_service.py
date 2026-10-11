import builtins

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.models import Auction, User
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
        auction_data = payload.model_dump()
        auction = Auction(**auction_data)
        auction.seller_id = user.id
        self.db.add(auction)
        self.db.commit()
        self.db.refresh(auction)
