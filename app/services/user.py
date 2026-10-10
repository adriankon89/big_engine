# app/services/user_service.py

from sqlalchemy import asc, desc, func, select
from sqlalchemy.orm import Session

from app.core.exceptions import (
    BadRequestException,
    InvalidCredentialsException,
    UserAlreadyExistsError,
    UserNotFoundError,
)
from app.core.security import PasswordHasher
from app.enums import Role, SortOrder, UserSortBy, UserStatus
from app.models import User, Wallet
from app.schemas import (
    PaginatedResponse,
    UserCreate,
    UserFilterParams,
    UserResponse,
    UserUpdate,
)


class UserService:

    def __init__(
        self,
        db: Session,
        hasher: PasswordHasher,
    ) -> None:
        self.db: Session = db
        self.hasher: PasswordHasher = hasher

    def list_users(self, params: UserFilterParams) -> PaginatedResponse[UserResponse]:
        stmt = select(User).outerjoin(User.wallet)
        if params.min_balance is not None:
            stmt = stmt.where(Wallet.balance_available >= params.min_balance)

        if params.role is not None:
            stmt = stmt.where(User.role == params.role)

        if params.search:
            search_pattern = f"%{params.search}"
            stmt = stmt.where(User.email.ilike(search_pattern))

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = self.db.scalar(count_stmt) or 0

        sort_column_map = {
            UserSortBy.ID: User.id,
            UserSortBy.EMAIL: User.email,
            UserSortBy.BALANCE: Wallet.balance_available,
            UserSortBy.CREATED_AT: User.created_at,
        }

        target_column = sort_column_map[params.sort_by]
        order_func = desc if params.order == SortOrder.DESC else asc

        stmt = stmt.order_by(order_func(target_column))

        stmt.offset(params.offset).limit(params.page_size)

        users: list[User] = list(self.db.scalars(stmt).all())
        user_reads = [UserResponse.model_validate(user) for user in users]

        return PaginatedResponse[UserResponse].create(
            items=user_reads, total=total, params=params
        )

    def create_user(self, payload: UserCreate) -> User:
        existing_user: User | None = self.get_by_email(payload.email)
        if existing_user:
            raise UserAlreadyExistsError(email=payload.email)

        hashed_password: str = self.hasher.hash(payload.password)

        user_data = payload.model_dump(exclude={"password"})
        user = User(**user_data, hashed_password=hashed_password)

        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)

        return user

    def update_user(
        self, user_id: int, payload: UserUpdate, current_user: User
    ) -> User:
        user: User | None = self.get_by_id(user_id)
        if not user:
            raise UserNotFoundError(identifier=user_id)

        if current_user.role != Role.ADMIN.value:
            raise PermissionError("must be admin to update user")

        if current_user.role == Role.GUEST.value and current_user.id != user_id:
            raise PermissionError("must be admin or the user themselves to update user")

        for field, value in payload.model_dump(
            exclude={"password"}, exclude_unset=True
        ).items():

            setattr(user, field, value)

        self.db.commit()
        self.db.refresh(user)

        return user

    def get_by_email(self, email: str) -> User | None:  # -> Any:
        stmt = select(User).where(User.email == email)
        return self.db.scalar(stmt)

    def get_by_id(self, id: int) -> User | None:
        stmt = select(User).where(User.id == id)
        return self.db.scalar(stmt)

    def change_password(
        self, user: User, current_password: str, new_password: str
    ) -> User:
        if not self.hasher.verify(current_password, user.hashed_password):
            raise InvalidCredentialsException("Current password is incorrect")

        if self.hasher.verify(new_password, user.hashed_password):
            raise BadRequestException(
                "New password must be different from current password"
            )

        user.hashed_password = self.hasher.hash(new_password)
        user.token_version += 1

        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)

        return user

    def admin_reset_password(self, user_id: int, new_password: str) -> User:
        user: User | None = self.db.get(User, user_id)
        if not user:
            raise UserNotFoundError(identifier=user_id)

        user.hashed_password = self.hasher.hash(new_password)

        user.token_version += 1

        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)

        return user

    def update_status(
        self, user_id: int, new_status: UserStatus, reason: str | None = None
    ) -> User:
        user = self.get_by_id(user_id)
        if not user:
            raise UserNotFoundError(f"User {user_id} not found")

        user.status = new_status

        if new_status in (UserStatus.SUSPENDED, UserStatus.INACTIVE):
            user.token_version += 1

        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)

        # Optional: Log action or trigger notification email
        return user
