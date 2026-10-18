from abc import ABC, abstractmethod
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AuctionValidationResult:
    is_valid: bool
    reason: str


class AuctionValidator(ABC):
    @abstractmethod
    def validate_auction(
        self, image_paths: Sequence[Path], title: str, description: str
    ) -> AuctionValidationResult:
        pass
