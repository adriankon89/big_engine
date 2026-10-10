from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.security import PasswordHasher
from app.database import get_db
from app.services.auth import AuthService
from app.services.user import UserService
from app.services.wallet_service import WalletService


def get_user_service(db: Annotated[Session, Depends(get_db)]) -> UserService:
    return UserService(db=db, hasher=PasswordHasher())


def get_auction_service(db: Annotated[Session, Depends(get_db)]) -> WalletService:
    return WalletService(db=db)


def get_auth_service(
    user_service: Annotated[UserService, Depends(get_user_service)],
) -> AuthService:
    return AuthService(user_service=user_service, hasher=PasswordHasher())


def get_wallet_service(db: Annotated[Session, Depends(get_db)]) -> WalletService:
    return WalletService(db=db)
