from abc import ABC, abstractmethod


class AuctionValidator(ABC):
    @abstractmethod
    def validate(self, auction_id: int) -> bool:
        pass
