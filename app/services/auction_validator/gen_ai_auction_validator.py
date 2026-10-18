from collections.abc import Sequence
from pathlib import Path

import PIL.Image
from google import genai
from google.genai import types
from pydantic import BaseModel

from .base import AuctionValidator


class AuctionCheckResult(BaseModel):
    is_valid: bool
    reason: str


class GenAIAuctionValidator(AuctionValidator):

    def __init__(self, client: genai.Client):
        self.client = client

    def validate_auction(
        self, image_paths: Sequence[Path], title: str, description: str
    ) -> bool:
        images = [PIL.Image.open(image_path) for image_path in image_paths]

        prompt = """
        Analyze this auction listing (image, title and description) for policy violations.
        Check specifically for:
        1. Nudity, sexually explicit content, or adult themes.
        2. Profanity, hate speech, or offensive language in the description.
        3. Illegal items or dangerous goods.
        """

        response = self.client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[*images, title, description, prompt],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=AuctionCheckResult,
            ),
        )

        return response.parsed.is_valid
