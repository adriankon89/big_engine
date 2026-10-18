from typing import Annotated

from fastapi import APIRouter, Depends, Request, status

from app.dependencies import get_auth_service
from app.infrastructure.rate_limiter import limiter
from app.schemas.auth import LoginRequest, TokenResponse
from app.services.auth import AuthService

router = APIRouter()


@router.post("/login", response_model=TokenResponse, status_code=status.HTTP_200_OK)
@limiter.limit("5/minute")
def login(
    request: Request,
    payload: LoginRequest,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> TokenResponse:
    token: str = auth_service.login(payload.email, payload.password)
    return TokenResponse(access_token=token)
