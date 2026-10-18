from abc import ABC, abstractmethod
from collections.abc import Sequence
from pathlib import Path


class AuctionValidator(ABC):
    @abstractmethod
    def validate_auction(
        self, image_paths: Sequence[Path], title: str, description: str
    ) -> bool:
        pass
