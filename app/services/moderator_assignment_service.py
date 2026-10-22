from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.enums import Role, UserStatus
from app.models.moderator_assignment_state import ModeratorAssignmentState
from app.models.user import User


class ModeratorAssignmentService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def next_moderator_id(self, seller_id: int) -> int | None:
        state_id = 1
        self.db.execute(
            update(ModeratorAssignmentState)
            .where(ModeratorAssignmentState.id == state_id)
            .values(last_moderator_id=ModeratorAssignmentState.last_moderator_id)
        )
        state = self.db.scalar(
            select(ModeratorAssignmentState)
            .where(ModeratorAssignmentState.id == state_id)
            .with_for_update()
        )
        if state is None:
            raise RuntimeError("Moderator assignment state has not been initialized")

        moderator_ids = list(
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
        if not moderator_ids:
            return None

        if state.last_moderator_id is None:
            next_index = 0
        else:
            try:
                previous_index = moderator_ids.index(state.last_moderator_id)
            except ValueError:
                next_index = 0
            else:
                next_index = (previous_index + 1) % len(moderator_ids)

        moderator_id = moderator_ids[next_index]
        state.last_moderator_id = moderator_id
        return moderator_id
