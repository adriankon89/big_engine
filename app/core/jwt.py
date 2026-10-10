from datetime import datetime, timedelta, timezone

import jwt

from app.config import get_settings
from app.core.exceptions import InvalidTokenError

settings = get_settings()
SECRET_KEY = settings.SECRET_KEY.get_secret_value()
ALGORITHM = settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()

    now: datetime = datetime.now(timezone.utc)
    if expires_delta:
        expire: datetime = now + expires_delta
    else:
        expire = now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire, "iat": now})

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> dict:
    """Dekoduje token i weryfikuje jego podpis oraz czas ważności."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise InvalidTokenError("Token has expired")
    except jwt.PyJWTError:
        raise InvalidTokenError("Could not validate credentials")
