from collections.abc import Sequence
from pathlib import Path

from .base import AuctionValidator


class MockAuctionValidator(AuctionValidator):
    def __init__(self, return_value: bool):
        self.return_value = return_value

    def validate_auction(
        self, image_paths: Sequence[Path], title: str, description: str
    ) -> bool:

        print(f"[MOCK] Validating auction: {title} -> Returning {self.return_value}")
        return self.return_value
