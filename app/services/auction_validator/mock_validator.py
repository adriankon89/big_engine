from collections.abc import Sequence
from pathlib import Path

from .base import AuctionValidator


class MockAuctionValidator(AuctionValidator):
    def validate_auction(
        self, image_paths: Sequence[Path], title: str, description: str
    ) -> bool:
        print(f"[MOCK] Validating auction: {title}")
        return True
