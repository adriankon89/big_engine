from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.auth.dependencies import require_role, require_roles
from app.dependencies import get_auction_service, get_user_service
from app.enums import Role
from app.models import User
from app.schemas.auction import AuctionsForManualReviewResponse
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
