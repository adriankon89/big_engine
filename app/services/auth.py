from app.core.exceptions import NoPermissionException, UnauthorizedException
from app.core.jwt import create_access_token as encode_access_token
from app.core.security import PasswordHasher
from app.enums import UserStatus
from app.models.user import User
from app.services.user import UserService


class AuthService:
    def __init__(
        self,
        user_service: UserService,
        hasher: PasswordHasher,
    ) -> None:
        self.user_service: UserService = user_service
        self.hasher: PasswordHasher = hasher

    def login(self, email: str, password: str):
        user: User | None = self.authenticate_user(email, password)

        if user is None:
            raise UnauthorizedException()

        if user.status != UserStatus.ACTIVE:
            raise NoPermissionException("User account is not active")

        return self.create_access_token(user)

    def authenticate_user(self, email: str, password: str) -> User | None:
        user: User | None = self.user_service.get_by_email(email)

        if not user or not self.hasher.verify(password, user.hashed_password):
            return None

        return user

    def create_access_token(self, user: User) -> str:
        return encode_access_token(
            {
                "sub": str(user.id),
                "email": user.email,
                "token_version": user.token_version,
                "role": user.role,
            }
        )
