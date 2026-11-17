import unittest
from unittest.mock import MagicMock

from app.models.auction import Auction
from app.services.auction_service import AuctionService


class AuctionServiceTests(unittest.TestCase):
    def test_list_for_seller_filters_by_seller_id(self) -> None:
        seller_id = 7
        auctions = [MagicMock(spec=Auction)]
        db = MagicMock()
        db.query.return_value.filter.return_value.all.return_value = auctions
        service = AuctionService(
            db=db, storage=MagicMock(), moderator_assignment=MagicMock()
        )

        result = service.list_auctions_by_seller(seller_id)

        self.assertEqual(result, auctions)
        db.query.assert_called_once_with(Auction)
        filter_expression = db.query.return_value.filter.call_args.args[0]
        compiled_filter = filter_expression.compile()
        self.assertEqual(str(compiled_filter), "auctions.seller_id = :seller_id_1")
        self.assertEqual(compiled_filter.params["seller_id_1"], seller_id)


if __name__ == "__main__":
    unittest.main()
