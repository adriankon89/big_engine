import unittest
from datetime import UTC, datetime
from decimal import Decimal

from pydantic import ValidationError
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.config import Settings
from app.enums import (
    AuctionStatus,
    ModeratorAssignmentStrategy,
    Role,
    UserStatus,
    VerificationStatus,
)
from app.models import Auction, Base, ModeratorAssignmentState, User
from app.services.moderator_assignment_service import ModeratorAssignmentService


class ModeratorAssignmentServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        self.db = Session(self.engine)
        self.db.add_all(
            [
                User(id=1, email="seller@example.com", role=Role.USER),
                User(id=2, email="moderator2@example.com", role=Role.MODERATOR),
                User(id=3, email="moderator3@example.com", role=Role.ADMIN),
                ModeratorAssignmentState(id=1, last_moderator_id=None),
            ]
        )
        self.db.commit()

    def tearDown(self) -> None:
        self.db.close()
        self.engine.dispose()

    def test_default_strategy_preserves_round_robin(self) -> None:
        self.db.get(ModeratorAssignmentState, 1).last_moderator_id = 2
        service = ModeratorAssignmentService(self.db)

        self.assertEqual(service.next_moderator_id(seller_id=1), 3)

    def test_least_assigned_counts_only_open_review_work(self) -> None:
        self._add_auction(2, VerificationStatus.PENDING)
        self._add_auction(2, VerificationStatus.MANUAL_REVIEW)
        self._add_auction(3, VerificationStatus.PENDING)
        self._add_auction(3, VerificationStatus.APPROVED)
        self._add_auction(3, VerificationStatus.REJECTED)
        self.db.commit()
        service = ModeratorAssignmentService(
            self.db, ModeratorAssignmentStrategy.LEAST_ASSIGNED
        )

        self.assertEqual(service.next_moderator_id(seller_id=1), 3)

    def test_least_assigned_uses_lowest_id_for_equal_workload(self) -> None:
        self._add_auction(2, VerificationStatus.PENDING)
        self._add_auction(3, VerificationStatus.MANUAL_REVIEW)
        self.db.commit()
        service = ModeratorAssignmentService(
            self.db, ModeratorAssignmentStrategy.LEAST_ASSIGNED
        )

        self.assertEqual(service.next_moderator_id(seller_id=1), 2)

    def test_least_assigned_includes_moderators_with_zero_workload(self) -> None:
        self._add_auction(3, VerificationStatus.PENDING)
        self.db.commit()
        service = ModeratorAssignmentService(
            self.db, ModeratorAssignmentStrategy.LEAST_ASSIGNED
        )

        self.assertEqual(service.next_moderator_id(seller_id=1), 2)

    def test_returns_none_when_no_other_active_moderators_exist(self) -> None:
        moderator = self.db.get(User, 3)
        moderator.status = UserStatus.INACTIVE
        self.db.commit()
        service = ModeratorAssignmentService(
            self.db, ModeratorAssignmentStrategy.LEAST_ASSIGNED
        )

        self.assertIsNone(service.next_moderator_id(seller_id=2))

    def _add_auction(
        self, moderator_id: int, verification_status: VerificationStatus
    ) -> None:
        now = datetime.now(UTC)
        self.db.add(
            Auction(
                seller_id=1,
                moderator_id=moderator_id,
                title="Test auction",
                description="Test",
                starting_price=Decimal("1.00"),
                minimum_price=Decimal("1.00"),
                starts_at=now,
                ends_at=now,
                _status=AuctionStatus.DRAFT,
                _verification_status=verification_status,
            )
        )


class ModeratorAssignmentSettingsTests(unittest.TestCase):
    def test_round_robin_is_the_default_strategy(self) -> None:
        settings = Settings.model_validate({})

        self.assertEqual(
            settings.MODERATOR_ASSIGNMENT_STRATEGY,
            ModeratorAssignmentStrategy.ROUND_ROBIN,
        )

    def test_unknown_strategy_is_rejected(self) -> None:
        with self.assertRaises(ValidationError):
            Settings.model_validate({"MODERATOR_ASSIGNMENT_STRATEGY": "unknown"})


if __name__ == "__main__":
    unittest.main()
