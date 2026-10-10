from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.dependencies import get_auth_service
from app.schemas import LoginRequest, TokenResponse
from app.services.auth import AuthService

router = APIRouter()


@router.post("/login", response_model=TokenResponse, status_code=status.HTTP_200_OK)
def login(
    payload: LoginRequest,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> TokenResponse:
    token: str = auth_service.login(payload.email, payload.password)
    return TokenResponse(access_token=token)
