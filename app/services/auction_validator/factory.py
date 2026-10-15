from app.config import Settings, get_settings

from .base import AuctionValidator
from .mock_validator import MockAuctionValidator
from .real_llm import RealLLMAuctionValidator

settings: Settings = get_settings()


def get_auction_validator() -> AuctionValidator:

    if settings.AUCTION_VALIDATOR_MODE == "mock":
        return MockAuctionValidator()
    return RealLLMAuctionValidator()
