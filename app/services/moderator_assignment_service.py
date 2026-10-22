from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.enums import Role, UserStatus
from app.models.moderator_assignment_state import ModeratorAssignmentState
from app.models.user import User


class ModeratorAssignmentService:
    def __init__(self, db: Session) -> None:
        self.db: Session = db

    def next_moderator_id(self, seller_id: int) -> int | None:
        state: ModeratorAssignmentState = self._lock_assignment_state()
        moderator_ids: list[int] = self._get_active_moderator_ids(seller_id)
        if not moderator_ids:
            return None

        moderator_id: int = self._select_next_moderator_id(
            moderator_ids, state.last_moderator_id
        )
        state.last_moderator_id = moderator_id
        return moderator_id

    def _lock_assignment_state(self) -> ModeratorAssignmentState:
        state_id = 1
        self.db.execute(
            update(ModeratorAssignmentState)
            .where(ModeratorAssignmentState.id == state_id)
            .values(last_moderator_id=ModeratorAssignmentState.last_moderator_id)
        )
        state: ModeratorAssignmentState | None = self.db.scalar(
            select(ModeratorAssignmentState)
            .where(ModeratorAssignmentState.id == state_id)
            .with_for_update()
        )
        if state is None:
            raise RuntimeError("Moderator assignment state has not been initialized")
        return state

    def _get_active_moderator_ids(self, seller_id: int) -> list[int]:
        moderator_ids: list[int] = list(
            self.db.scalars(
                select(User.id)
                .where(
                    User.role.in_([Role.ADMIN.value, Role.MODERATOR.value]),
                    User.status == UserStatus.ACTIVE.value,
                    User.id != seller_id,
                )
                .order_by(User.id)
            ).all()
        )
        return moderator_ids

    @staticmethod
    def _select_next_moderator_id(
        moderator_ids: list[int], last_moderator_id: int | None
    ) -> int:
        if last_moderator_id is None:
            next_index = 0
        else:
            try:
                previous_index: int = moderator_ids.index(last_moderator_id)
            except ValueError:
                next_index = 0
            else:
                next_index: int = (previous_index + 1) % len(moderator_ids)

        return moderator_ids[next_index]
