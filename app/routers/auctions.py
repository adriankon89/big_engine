from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.auth.dependencies import get_current_user
from app.dependencies import get_auction_service
from app.models import User
from app.schemas import AuctionCreate
from app.services.auction_service import AuctionService

router = APIRouter()


@router.get("/auctions")
def get_auctions():
    return {"message": "List of auctions"}


@router.get("/auctions/{auction_id}")
def get_auction(auction_id: int):
    return {"message": f"Details of auction {auction_id}"}


@router.post(
    "/auctions",
    # response_model=AuctionCreateResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_auction(
    payload: AuctionCreate,
    auction_service: Annotated[AuctionService, Depends(get_auction_service)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    # auction_service.create(payload)
    return {"message": "Auction created"}
