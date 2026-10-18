from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.models.bid import Bid
from app.models.user import User
from app.schemas import BidCreate, BidRead

router = APIRouter()


@router.post("/bids", response_model=BidRead, status_code=status.HTTP_201_CREATED)
def create_bid(payload: BidCreate, db: Annotated[Session, Depends(get_db)]) -> Bid:
    bid = Bid(**payload.model_dump())
    db.add(bid)
    db.commit()
    db.refresh(bid)
    return bid


@router.get("/bids", response_model=list[BidRead])
def list_bids(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> list[Bid]:
    return list(db.query(Bid).order_by(Bid.id).all())
