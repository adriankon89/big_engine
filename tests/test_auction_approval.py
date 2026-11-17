import unittest
from datetime import UTC, datetime
from decimal import Decimal

from app.enums import AuctionStatus, VerificationStatus
from app.models.auction import Auction


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


if __name__ == "__main__":
    unittest.main()
