from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.auth.dependencies import get_current_user, require_role
from app.dependencies import get_user_service
from app.enums import Role
from app.models import User
from app.schemas import (
    AdminResetPasswordRequest,
    ChangePasswordRequest,
    PaginatedResponse,
    UserCreate,
    UserFilterParams,
    UserResponse,
    UserStatusUpdate,
    UserUpdate,
)
from app.services.user import UserService

router = APIRouter()


@router.get(
    "/users",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_role(Role.ADMIN))],
)
def list_users(
    params: Annotated[UserFilterParams, Depends()],
    user_service: Annotated[UserService, Depends(get_user_service)],
) -> PaginatedResponse[UserResponse]:
    return user_service.list_users(params)


@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    payload: UserCreate,
    user_service: Annotated[UserService, Depends(get_user_service)],
) -> User:
    return user_service.create_user(payload)


@router.patch(
    "/users/{user_id}", response_model=UserResponse, status_code=status.HTTP_200_OK
)
def update_user(
    user_id: int,
    payload: UserUpdate,
    user_service: Annotated[UserService, Depends(get_user_service)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    return user_service.update_user(user_id, payload, current_user=current_user)


@router.post("/users/change-password", status_code=status.HTTP_204_NO_CONTENT)
def change_password(
    payload: ChangePasswordRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    user_service: Annotated[UserService, Depends(get_user_service)],
):
    user_service.change_password(
        user=current_user,
        current_password=payload.current_password,
        new_password=payload.new_password,
    )


@router.post("users/{user_id}/reset-password", status_code=status.HTTP_204_NO_CONTENT)
def admin_reset_password(
    user_id: int,
    payload: AdminResetPasswordRequest,
    user_service: Annotated[UserService, Depends(get_user_service)],
    _: Annotated[User, Depends(require_role(Role.ADMIN))],
):
    user_service.admin_reset_password(
        user_id=user_id, new_password=payload.new_password
    )


@router.post(
    "users/{user_id}/status",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_role(Role.ADMIN))],
)
def update_status(
    user_id: int,
    payload: UserStatusUpdate,
    user_service: Annotated[UserService, Depends(get_user_service)],
):
    return user_service.update_status(
        user_id=user_id,
        new_status=payload.status,
    )
