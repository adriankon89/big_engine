import unittest
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from app.enums import (
    AppealReasonCode,
    AppealStatus,
    AuctionStatus,
    VerificationStatus,
)
from app.models.auction import Auction
from app.models.auction_appeal import AuctionAppeal

UTC = UTC


class AuctionApprovalTests(unittest.TestCase):
    def test_only_manual_review_auctions_can_be_approved(self) -> None:
        for verification_status in (
            VerificationStatus.PENDING,
            VerificationStatus.APPROVED,
            VerificationStatus.REJECTED,
        ):
            with self.subTest(verification_status=verification_status):
                auction = self._auction(verification_status)

                with self.assertRaisesRegex(
                    ValueError, "Only auctions in manual review can be approved"
                ):
                    auction.approve_manual_review(moderator_id=12)

                self.assertEqual(auction.verification_status, verification_status)
                self.assertIsNone(auction.moderator_id)

    def test_manual_review_auction_can_be_approved(self) -> None:
        auction = self._auction(VerificationStatus.MANUAL_REVIEW)

        auction.approve_manual_review(moderator_id=12)

        self.assertEqual(auction.verification_status, VerificationStatus.APPROVED)
        self.assertEqual(auction.moderator_id, 12)

    @staticmethod
    def _auction(verification_status: VerificationStatus) -> Auction:
        now = datetime.now(UTC)
        return Auction(
            seller_id=1,
            title="Test auction",
            description="Test description",
            starting_price=Decimal("1.00"),
            minimum_price=Decimal("1.00"),
            starts_at=now,
            ends_at=now,
            _status=AuctionStatus.DRAFT,
            _verification_status=verification_status,
        )


class AuctionAppealTests(unittest.TestCase):
    def test_appeal_eligibility(self):
        auction = Auction(
            seller_id=1,
            title="Test auction",
            description="Test description",
            starting_price=Decimal("1.00"),
            minimum_price=Decimal("1.00"),
            starts_at=datetime.now(UTC),
            ends_at=datetime.now(UTC),
            _status=AuctionStatus.DRAFT,
            _verification_status=VerificationStatus.REJECTED,
        )
        auction.created_at = datetime.now(UTC)
        self.assertTrue(auction.allow_appeal)

        auction._verification_status = VerificationStatus.APPROVED
        self.assertTrue(auction.allow_appeal)

    def test_appeal_reason_code(self):
        appeal = AuctionAppeal(auction_id=1, reason_code=AppealReasonCode.OTHER)
        self.assertEqual(appeal.reason_code, AppealReasonCode.OTHER)

    def test_auction_allows_appeal_within_30_days_without_appeal(self) -> None:
        auction = self._auction(VerificationStatus.REJECTED)
        auction.created_at = datetime.now(UTC) - timedelta(days=29)

        self.assertTrue(auction.allow_appeal)

    def test_auction_rejects_appeal_at_30_days_or_with_existing_appeal(self) -> None:
        auction = self._auction(VerificationStatus.REJECTED)
        auction.created_at = datetime.now(UTC) - timedelta(days=30)

        self.assertFalse(auction.allow_appeal)

        auction.created_at = datetime.now(UTC)
        auction.appeal = AuctionAppeal(
            reason="Incorrect rejection",
            reason_code=AppealReasonCode.OTHER,
        )

        self.assertFalse(auction.allow_appeal)

    def test_appeal_resolved_property(self) -> None:
        appeal = AuctionAppeal(auction_id=1, reason_code=AppealReasonCode.OTHER)

        self.assertFalse(appeal.is_resolved)

        for status in (
            AppealStatus.APPROVED,
            AppealStatus.REJECTED,
            AppealStatus.CANCELLED,
        ):
            with self.subTest(status=status):
                appeal.status = status
                self.assertTrue(appeal.is_resolved)

    @staticmethod
    def _auction(verification_status: VerificationStatus) -> Auction:
        now = datetime.now(UTC)
        return Auction(
            seller_id=1,
            title="Test auction",
            description="Test description",
            starting_price=Decimal("1.00"),
            minimum_price=Decimal("1.00"),
            starts_at=now,
            ends_at=now,
            _status=AuctionStatus.DRAFT,
            _verification_status=verification_status,
        )


if __name__ == "__main__":
    unittest.main()
