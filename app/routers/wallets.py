from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.auth.dependencies import get_current_user
from app.dependencies import get_wallet_service
from app.models.user import User
from app.models.wallet import Wallet
from app.schemas import WalletResponse, WalletUpdate
from app.services.wallet_service import WalletAlreadyExistsError, WalletService

router = APIRouter()


@router.post(
    "/wallets", response_model=WalletResponse, status_code=status.HTTP_201_CREATED
)
def create_wallet(
    current_user: Annotated[User, Depends(get_current_user)],
    wallet_service: Annotated[WalletService, Depends(get_wallet_service)],
) -> Wallet:
    try:
        return wallet_service.create(user=current_user)
    except WalletAlreadyExistsError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error))


@router.patch(
    "/wallets/{wallet_id}",
    response_model=WalletResponse,
    status_code=status.HTTP_200_OK,
)
def update_wallet(
    payload: WalletUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    wallet_service: Annotated[WalletService, Depends(get_wallet_service)],
) -> Wallet:
    return wallet_service.update(user=current_user, payload=payload)
