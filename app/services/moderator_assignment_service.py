from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.enums import (
    ModeratorAssignmentStrategy,
    Role,
    UserStatus,
    VerificationStatus,
)
from app.models.auction import Auction
from app.models.moderator_assignment_state import ModeratorAssignmentState
from app.models.user import User


class ModeratorAssignmentService:
    def __init__(
        self,
        db: Session,
        strategy: ModeratorAssignmentStrategy = ModeratorAssignmentStrategy.ROUND_ROBIN,
    ) -> None:
        self.db: Session = db
        self.strategy = strategy

    def next_moderator_id(self, seller_id: int) -> int | None:
        state: ModeratorAssignmentState = self._lock_assignment_state()
        moderator_ids: list[int] = self._get_active_moderator_ids(seller_id)
        if not moderator_ids:
            return None

        if self.strategy == ModeratorAssignmentStrategy.ROUND_ROBIN:
            moderator_id = self._select_next_moderator_id(
                moderator_ids, state.last_moderator_id
            )
            state.last_moderator_id = moderator_id
        else:
            moderator_id = self._select_least_assigned_moderator_id(moderator_ids)
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

    def _select_least_assigned_moderator_id(self, moderator_ids: list[int]) -> int:
        assignment_counts: dict[int, int] = {}
        assignment_rows = self.db.execute(
            select(Auction.moderator_id, func.count(Auction.id))
            .where(
                Auction.moderator_id.in_(moderator_ids),
                Auction._verification_status.in_(
                    [
                        VerificationStatus.PENDING,
                        VerificationStatus.MANUAL_REVIEW,
                    ]
                ),
            )
            .group_by(Auction.moderator_id)
        )
        for moderator_id, assignment_count in assignment_rows:
            if moderator_id is not None:
                assignment_counts[moderator_id] = assignment_count
        return min(
            moderator_ids,
            key=lambda moderator_id: (
                assignment_counts.get(moderator_id, 0),
                moderator_id,
            ),
        )
