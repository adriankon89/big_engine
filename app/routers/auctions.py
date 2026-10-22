import json
from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Request,
    UploadFile,
    status,
)
from pydantic import ValidationError

from app.auth.dependencies import get_current_user, require_roles
from app.core.upload_validation import IMAGE_UPLOAD_POLICY, validate_uploads
from app.dependencies import get_auction_service
from app.dto import UploadedFileDTO
from app.enums import Role
from app.infrastructure.rate_limiter import limiter
from app.models.user import User
from app.schemas.auction import (
    AuctionCreate,
    AuctionRead,
    AuctionRejectRequest,
    AuctionReviewRead,
)
from app.services.auction_service import AuctionService

router = APIRouter()


@router.get(
    "/auctions", response_model=list[AuctionRead], status_code=status.HTTP_200_OK
)
def get_auctions(
    auction_service: Annotated[AuctionService, Depends(get_auction_service)],
):
    return auction_service.list()


@router.get(
    "/auctions/{auction_id}",
    response_model=AuctionReviewRead,
    status_code=status.HTTP_200_OK,
)
def get_auction(
    auction_id: int,
    auction_service: Annotated[AuctionService, Depends(get_auction_service)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    auction = auction_service.get(auction_id)
    if auction is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Auction not found"
        )
    if auction.seller_id != current_user.id and current_user.role not in (
        Role.ADMIN,
        Role.MODERATOR,
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
        )
    return auction


@router.post(
    "/auctions/{auction_id}/reject",
    response_model=AuctionReviewRead,
    status_code=status.HTTP_200_OK,
)
@limiter.limit("20/minute")
def reject_auction(
    request: Request,
    auction_id: int,
    payload: AuctionRejectRequest,
    auction_service: Annotated[AuctionService, Depends(get_auction_service)],
    moderator: Annotated[User, Depends(require_roles(Role.ADMIN, Role.MODERATOR))],
):
    auction = auction_service.reject(auction_id, payload.reason, moderator)
    if auction is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Auction not found"
        )
    return auction


@router.post(
    "/admin/auctions",
    response_model=list[AuctionReviewRead],
    status_code=status.HTTP_200_OK,
)
def get_admin_auctions(
    auction_service: Annotated[AuctionService, Depends(get_auction_service)],
    _: Annotated[User, Depends(require_roles(Role.ADMIN, Role.MODERATOR))],
):
    return auction_service.list()


@router.post(
    "/auctions",
    # response_model=AuctionCreateResponse,
    status_code=status.HTTP_201_CREATED,
)
@limiter.limit("5/hour")
def create_auction(
    request: Request,
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
