from typing import Annotated

# todo tutaj nie powinieniem raczej korzystać z fast api co jak będzie inny framerowkr
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.exceptions import InvalidTokenError
from app.core.jwt import decode_access_token
from app.database import get_db
from app.enums import Role
from app.models import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")


# w przykłądzie było async def get_current_usr
def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = decode_access_token(token)
        user_id: str | None = payload.get("sub")
        token_version: int | None = payload.get("token_version")

        if user_id is None or token_version is None:
            raise credentials_exception

    except InvalidTokenError:
        raise credentials_exception

    user: User | None = db.get(User, int(user_id))
    if user is None:
        raise credentials_exception

    if user.token_version != token_version:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been invalidated (password changed)",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


# użycie  dependencies=[Depends(require_role(UserRole.ADMIN))], tutaj używam chyba fastapi depenceis a nie powinienem api agnostic
def require_role(required_role: Role):
    def dependency(
        current_user: Annotated[User, Depends(get_current_user)],
    ) -> User:
        if current_user.role != required_role:
            raise HTTPException(
                status_code=403,
                detail="Insufficient permissions",
            )

        return current_user

    return dependency


def require_roles(*allowed_roles: Role):
    def dependency(
        current_user: Annotated[User, Depends(get_current_user)],
    ) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return current_user

    return dependency
