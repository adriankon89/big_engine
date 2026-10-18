from google import genai

from app.config import Settings, get_settings

from .base import AuctionValidator
from .gen_ai_auction_validator import GenAIAuctionValidator
from .mock_validator import MockAuctionValidator

settings: Settings = get_settings()


def get_auction_validator() -> AuctionValidator:

    if settings.AUCTION_VALIDATOR_MODE == "mock":
        return MockAuctionValidator()
    return GenAIAuctionValidator(genai.Client())
