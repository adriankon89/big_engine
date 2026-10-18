from collections.abc import Sequence
from pathlib import Path

from .base import AuctionValidationResult, AuctionValidator


class MockAuctionValidator(AuctionValidator):
    def __init__(self, return_value: bool):
        self.return_value = return_value

    def validate_auction(
        self, image_paths: Sequence[Path], title: str, description: str
    ) -> AuctionValidationResult:

        print(f"[MOCK] Validating auction: {title} -> Returning {self.return_value}")
        reason = "Auction rejected by mock validator." if not self.return_value else ""
        return AuctionValidationResult(is_valid=self.return_value, reason=reason)
