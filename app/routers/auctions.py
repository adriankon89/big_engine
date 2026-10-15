import json
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from pydantic import ValidationError

from app.auth.dependencies import get_current_user
from app.core.upload_validation import IMAGE_UPLOAD_POLICY, validate_uploads
from app.dependencies import get_auction_service
from app.models import User
from app.schemas import AuctionCreate, AuctionRead
from app.services.auction_service import AuctionService
from app.services.dto import UploadedFileDTO

router = APIRouter()


@router.get(
    "/auctions", response_model=list[AuctionRead], status_code=status.HTTP_200_OK
)
def get_auctions(
    auction_service: Annotated[AuctionService, Depends(get_auction_service)],
):
    return auction_service.list()


@router.get(
    "/auctions/{auction_id}", response_model=AuctionRead, status_code=status.HTTP_200_OK
)
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
    if images is None:
        images = []

    validate_uploads(images, policy=IMAGE_UPLOAD_POLICY)

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

    file_dtos = [
        UploadedFileDTO(
            filename=image.filename or "upload",
            content_type=image.content_type or "application/octet-stream",
            content=image.file.read(),
        )
        for image in images
    ]

    auction = auction_service.create(
        payload=payload, images=file_dtos, user=current_user
    )
    return {
        "message": "Auction created",
        "auction_id": auction.id,
        "images_len": len(images),
    }
