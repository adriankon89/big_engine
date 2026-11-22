import unittest
from datetime import datetime
from decimal import Decimal
from unittest.mock import MagicMock

from sqlalchemy.dialects import sqlite

from app.enums import (
    AuctionSortBy,
    AuctionStatus,
    RejectionSource,
    SortOrder,
    VerificationStatus,
)
from app.models.auction import Auction
from app.schemas.auction import MyAuctionFilterParams
from app.schemas.moderation import ModeratorAuctionFilterParams
from app.services.auction_service import AuctionService


class AuctionServiceTests(unittest.TestCase):
    def test_list_for_seller_filters_by_seller_id(self) -> None:
        seller_id = 7
        params = MyAuctionFilterParams(
            page=2,
            page_size=10,
            status=AuctionStatus.CLOSED,
            verification_status=VerificationStatus.REJECTED,
            sort_by=AuctionSortBy.START_TIME,
            order=SortOrder.DESC,
        )
        auctions = [
            Auction(
                id=1,
                title="Vintage camera",
                description="A well-kept camera for collectors.",
                starting_price=Decimal("10.00"),
                minimum_price=Decimal("10.00"),
                current_price=Decimal("10.00"),
                bid_increment=Decimal("1.00"),
                _status=AuctionStatus.CLOSED,
                starts_at=datetime(2026, 1, 1),
                ends_at=datetime(2026, 1, 2),
            )
        ]
        db = MagicMock()
        db.scalar.return_value = 15
        db.scalars.return_value.all.return_value = auctions
        service = AuctionService(
            db=db, storage=MagicMock(), moderator_assignment=MagicMock()
        )

        result = service.list_auctions_by_seller(params, seller_id)

        self.assertEqual(len(result.items), 1)
        self.assertEqual(result.items[0].id, 1)
        self.assertEqual(result.total, 15)
        self.assertEqual(result.page, 2)
        self.assertEqual(result.page_size, 10)
        self.assertEqual(result.total_pages, 2)
        statement = db.scalars.call_args.args[0]
        compiled = statement.compile(dialect=sqlite.dialect())
        sql = str(compiled)
        self.assertIn("auctions.seller_id =", sql)
        self.assertIn("auctions.status =", sql)
        self.assertIn("auctions.verification_status =", sql)
        self.assertIn("ORDER BY auctions.starts_at DESC", sql)
        self.assertIn("LIMIT", sql)
        self.assertIn("OFFSET", sql)
        self.assertIn(seller_id, compiled.params.values())
        self.assertIn(params.offset, compiled.params.values())
        self.assertIn(params.page_size, compiled.params.values())

    def test_list_for_seller_defaults_to_open_status(self) -> None:
        params = MyAuctionFilterParams()
        db = MagicMock()
        db.scalar.return_value = 0
        db.scalars.return_value.all.return_value = []
        service = AuctionService(
            db=db, storage=MagicMock(), moderator_assignment=MagicMock()
        )

        result = service.list_auctions_by_seller(params, seller_id=7)

        self.assertEqual(result.items, [])
        self.assertEqual(result.total, 0)

        statement = db.scalars.call_args.args[0]
        compiled = statement.compile(dialect=sqlite.dialect())
        self.assertIn("auctions.status =", str(compiled))
        self.assertIn(AuctionStatus.OPEN, compiled.params.values())

    def test_manual_review_filters_and_sort_mapping(self) -> None:
        params = ModeratorAuctionFilterParams(
            sort_by=AuctionSortBy.START_TIME,
            order=SortOrder.DESC,
            reject_reason="policy concern",
            reject_source=RejectionSource.AI,
            rejected_by_id=11,
            moderator_id=12,
        )
        db = MagicMock()
        db.scalar.return_value = 0
        db.scalars.return_value.all.return_value = []
        service = AuctionService(
            db=db, storage=MagicMock(), moderator_assignment=MagicMock()
        )

        service.list_auctions_for_manual_review(params, current_moderator_id=12)

        statement = db.scalars.call_args.args[0]
        sql = str(statement.compile(dialect=sqlite.dialect()))
        self.assertIn("auctions.verification_status =", sql)
        self.assertIn("auctions.rejection_reason =", sql)
        self.assertIn("auctions.rejection_source =", sql)
        self.assertIn("auctions.rejected_by_id =", sql)
        self.assertIn("auctions.moderator_id =", sql)
        self.assertIn("ORDER BY auctions.starts_at DESC", sql)

    def test_manual_review_show_mine_filters_by_current_moderator(self) -> None:
        current_moderator_id = 17
        params = ModeratorAuctionFilterParams(show_mine=True)
        db = MagicMock()
        db.scalar.return_value = 0
        db.scalars.return_value.all.return_value = []
        service = AuctionService(
            db=db, storage=MagicMock(), moderator_assignment=MagicMock()
        )

        service.list_auctions_for_manual_review(params, current_moderator_id)

        statement = db.scalars.call_args.args[0]
        compiled = statement.compile(dialect=sqlite.dialect())
        self.assertIn("auctions.moderator_id =", str(compiled))
        self.assertIn(current_moderator_id, compiled.params.values())

    def test_manual_review_sort_by_maps_to_auction_columns(self) -> None:
        expected_columns = {
            AuctionSortBy.ID: "id",
            AuctionSortBy.TITLE: "title",
            AuctionSortBy.START_TIME: "starts_at",
            AuctionSortBy.END_TIME: "ends_at",
            AuctionSortBy.CREATED_AT: "created_at",
        }

        for sort_by, column in expected_columns.items():
            with self.subTest(sort_by=sort_by):
                db = MagicMock()
                db.scalar.return_value = 0
                db.scalars.return_value.all.return_value = []
                service = AuctionService(
                    db=db, storage=MagicMock(), moderator_assignment=MagicMock()
                )

                service.list_auctions_for_manual_review(
                    ModeratorAuctionFilterParams(sort_by=sort_by),
                    current_moderator_id=1,
                )

                statement = db.scalars.call_args.args[0]
                sql = str(statement.compile(dialect=sqlite.dialect()))
                self.assertIn(f"ORDER BY auctions.{column} ASC", sql)


if __name__ == "__main__":
    unittest.main()
