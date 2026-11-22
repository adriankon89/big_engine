from typing import Annotated

from fastapi import APIRouter, Depends, Request, status

from app.auth.dependencies import get_current_user, require_role
from app.dependencies import (
    get_auction_appeal_service,
    get_auction_service,
    get_user_service,
)
from app.enums import Role
from app.infrastructure.rate_limiter import limiter
from app.models.user import User
from app.schemas.auction import (
    CreateAuctionAppealRequest,
    MyAuctionFilterParams,
    MyAuctionRead,
)
from app.schemas.pagination import PaginatedResponse
from app.schemas.user import (
    AdminResetPasswordRequest,
    ChangePasswordRequest,
    UserCreate,
    UserFilterParams,
    UserResponse,
    UserStatusUpdate,
    UserUpdate,
)
from app.services.auction_appeal_service import AuctionAppealService
from app.services.auction_service import AuctionService
from app.services.user import UserService

router = APIRouter(prefix="/users")


@router.get(
    "/me/auctions",
    response_model=PaginatedResponse[MyAuctionRead],
    status_code=status.HTTP_200_OK,
)
def get_my_auctions(
    current_user: Annotated[User, Depends(get_current_user)],
    auction_service: Annotated[AuctionService, Depends(get_auction_service)],
    params: MyAuctionFilterParams,
) -> PaginatedResponse[MyAuctionRead]:
    return auction_service.list_auctions_by_seller(params, current_user.id)


@router.post(
    "/me/auctions/appeal",
    status_code=status.HTTP_201_CREATED,
)
def create_auction_appeal(
    current_user: Annotated[User, Depends(get_current_user)],
    appeal_service: Annotated[
        AuctionAppealService,
        Depends(get_auction_appeal_service),
    ],
    payload: CreateAuctionAppealRequest,
) -> None:
    appeal_service.create(payload, current_user.id, current_user.role)


@router.get(
    "",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_role(Role.ADMIN))],
)
def list_users(
    params: Annotated[UserFilterParams, Depends()],
    user_service: Annotated[UserService, Depends(get_user_service)],
) -> PaginatedResponse[UserResponse]:
    return user_service.list_users(params)


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/hour")
def create_user(
    request: Request,
    payload: UserCreate,
    user_service: Annotated[UserService, Depends(get_user_service)],
) -> User:
    return user_service.create_user(payload)


@router.patch("/{user_id}", response_model=UserResponse, status_code=status.HTTP_200_OK)
@limiter.limit("30/minute")
def update_user(
    request: Request,
    user_id: int,
    payload: UserUpdate,
    user_service: Annotated[UserService, Depends(get_user_service)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    return user_service.update_user(user_id, payload, current_user=current_user)


@router.post("/change-password", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("5/hour")
def change_password(
    request: Request,
    payload: ChangePasswordRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    user_service: Annotated[UserService, Depends(get_user_service)],
):
    user_service.change_password(
        user=current_user,
        current_password=payload.current_password,
        new_password=payload.new_password,
    )


@router.post("/{user_id}/reset-password", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("10/hour")
def admin_reset_password(
    request: Request,
    user_id: int,
    payload: AdminResetPasswordRequest,
    user_service: Annotated[UserService, Depends(get_user_service)],
    _: Annotated[User, Depends(require_role(Role.ADMIN))],
):
    user_service.admin_reset_password(
        user_id=user_id, new_password=payload.new_password
    )


@router.post(
    "/{user_id}/status",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_role(Role.ADMIN))],
)
@limiter.limit("30/minute")
def update_status(
    request: Request,
    user_id: int,
    payload: UserStatusUpdate,
    user_service: Annotated[UserService, Depends(get_user_service)],
):
    return user_service.update_status(
        user_id=user_id,
        new_status=payload.status,
    )
