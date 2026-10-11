import json
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from pydantic import ValidationError

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
    auction_data: Annotated[str, Form(description="JSON string of AuctionCreate")],
    auction_service: Annotated[AuctionService, Depends(get_auction_service)],
    current_user: Annotated[User, Depends(get_current_user)],
    images: Annotated[list[UploadFile] | None, File()] = None,
):
    # auction_service.create(payload)
    if images is None:
        images = []

    try:
        auction_dict = json.loads(auction_data)
        payload = AuctionCreate(**auction_dict)
    except json.JSONDecodeError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid JSON format: {e.msg}",
        ) from e
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=e.errors()
        ) from e
    print(payload)
    for index, image in enumerate(images):
        print(index)

    return {"message": "Auction created", "images_len": len(images)}
