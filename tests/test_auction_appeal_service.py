import unittest
from unittest.mock import MagicMock

from app.core.exceptions import AppealAlreadyClosedError, AuctionAppealNotFoundError
from app.enums import AppealReasonCode, AppealStatus
from app.models.auction_appeal import AuctionAppeal
from app.schemas.auction_appeal import AuctionAppealReviewRequest
from app.services.auction_appeal_service import AuctionAppealService


class AuctionAppealServiceTests(unittest.TestCase):
    def test_review_preserves_omitted_fields_and_clears_explicit_null(self) -> None:
        appeal = MagicMock()
        appeal.is_resolved = False
        appeal.status = AppealStatus.UNDER_REVIEW
        appeal.resolution_note = "Existing resolution"
        appeal.internal_notes = "Existing internal note"
        db = MagicMock()
        db.get.return_value = appeal
        service = AuctionAppealService(db)

        result = service.review_appeal(
            appeal_id=4,
            reviewer_id=12,
            payload=AuctionAppealReviewRequest(internal_notes=None),
        )

        self.assertIs(result, appeal)
        self.assertEqual(appeal.status, AppealStatus.UNDER_REVIEW)
        self.assertEqual(appeal.resolution_note, "Existing resolution")
        self.assertIsNone(appeal.internal_notes)
        self.assertEqual(appeal.reviewer_id, 12)
        self.assertIsNone(appeal.resolved_at)
        db.commit.assert_called_once()
        db.refresh.assert_called_once_with(appeal)

    def test_review_sets_resolved_timestamp_for_cancelled_appeal(self) -> None:
        appeal = AuctionAppeal(
            auction_id=4,
            reason="Incorrect decision",
            reason_code=AppealReasonCode.OTHER,
            status=AppealStatus.OPEN,
        )
        db = MagicMock()
        db.get.return_value = appeal
        service = AuctionAppealService(db)

        service.review_appeal(
            appeal_id=4,
            reviewer_id=12,
            payload=AuctionAppealReviewRequest(status=AppealStatus.CANCELLED),
        )

        self.assertEqual(appeal.status, AppealStatus.CANCELLED)
        self.assertIsNotNone(appeal.resolved_at)
        self.assertIsNotNone(appeal.resolved_at.tzinfo)

    def test_review_raises_for_missing_appeal(self) -> None:
        db = MagicMock()
        db.get.return_value = None
        service = AuctionAppealService(db)

        with self.assertRaises(AuctionAppealNotFoundError):
            service.review_appeal(
                appeal_id=4,
                reviewer_id=12,
                payload=AuctionAppealReviewRequest(),
            )

    def test_review_rejects_already_resolved_appeal(self) -> None:
        appeal = MagicMock()
        appeal.is_resolved = True
        db = MagicMock()
        db.get.return_value = appeal
        service = AuctionAppealService(db)

        with self.assertRaises(AppealAlreadyClosedError):
            service.review_appeal(
                appeal_id=4,
                reviewer_id=12,
                payload=AuctionAppealReviewRequest(),
            )

        db.commit.assert_not_called()
