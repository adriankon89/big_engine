from .base import AuctionValidator


class MockAuctionValidator(AuctionValidator):
    def validate(self, auction_id: int) -> bool:
        print(f"[MOCK] Validating auction ID: {auction_id}")
        return True
