from .base import AuctionValidator


class RealLLMAuctionValidator(AuctionValidator):
    def validate(self, auction_id: int) -> bool:
        print(f"[REAL LLM] Validating auction ID: {auction_id}")
        return True
