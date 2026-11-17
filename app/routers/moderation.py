from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.auth.dependencies import get_current_user, require_role, require_roles
from app.dependencies import get_auction_service, get_user_service
from app.enums import Role
from app.models import User
from app.models.auction import Auction
from app.schemas.auction import AuctionReviewRead, AuctionsForManualReviewResponse
from app.schemas.moderation import ModeratorAuctionFilterParams, ModeratorFilterParams
from app.schemas.pagination import PaginatedResponse
from app.schemas.user import UserResponse
from app.services.auction_service import AuctionService
from app.services.user import UserService

router = APIRouter(prefix="/moderation")


@router.get(
    "/moderators",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_role(Role.ADMIN))],
)
def list_moderators(
    params: Annotated[ModeratorFilterParams, Depends()],
    user_service: Annotated[UserService, Depends(get_user_service)],
    _: Annotated[User, Depends(require_role(Role.ADMIN))],
) -> PaginatedResponse[UserResponse]:
    return user_service.list_moderators(params)


@router.get(
    "/auctions/manual-review",
)
def auction_manual_review(
    params: Annotated[ModeratorAuctionFilterParams, Depends()],
    auction_service: Annotated[AuctionService, Depends(get_auction_service)],
    _: Annotated[User, Depends(require_roles(Role.ADMIN, Role.MODERATOR))],
) -> PaginatedResponse[AuctionsForManualReviewResponse]:
    return auction_service.list_auctions_for_manual_review(params)


@router.post(
    "/auctions/{auction_id}/manual-review/approve",
    response_model=AuctionReviewRead,
    status_code=status.HTTP_200_OK,
)
def approve_auction_manual_review(
    auction_id: int,
    auction_service: Annotated[AuctionService, Depends(get_auction_service)],
    current_user: Annotated[User, Depends(get_current_user)],
    _: Annotated[User, Depends(require_roles(Role.ADMIN, Role.MODERATOR))],
) -> AuctionReviewRead:
    try:
        auction: Auction | None = auction_service.approve_auction_manual_review(
            auction_id, current_user.id
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=str(exc)
        ) from exc

    if auction is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Auction not found"
        )
    return AuctionReviewRead.model_validate(auction)
