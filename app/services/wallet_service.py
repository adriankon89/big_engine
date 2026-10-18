from sqlalchemy.orm import Session

from app.core.exceptions import NoPermissionException
from app.models.user import User
from app.models.wallet import Wallet
from app.schemas import WalletUpdate
from app.value_objects.balance import Balance
from app.value_objects.money import Money


class WalletAlreadyExistsError(Exception):
    pass


# todo czy trzeba to przeniewść ? do exception zgodnie z ddd ? clean architecture
class WalletNotFoundError(Exception):
    pass


class WalletService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, user: User) -> Wallet:
        if user.wallet:
            raise WalletAlreadyExistsError("User already has an wallet.")

        new_wallet = Wallet(
            user_id=user.id,  # czy mogę dać tutaj samo user i sobie sql alchemy wyciągnie
            currency="PLN",
            balance_available=Money.zero().amount,
            balance_held=Money.zero().amount,
        )

        self.db.add(new_wallet)
        self.db.commit()
        self.db.refresh(new_wallet)

        return new_wallet

    def update(self, user: User, payload: WalletUpdate):
        if not user.wallet:
            raise WalletNotFoundError("User does not have a wallet.")

        # todo to chyba trzeba by w jakiegoś try catcha błąd w balance.py złapać i zwrócić jako 400 bad request
        # w update czy powinienem podawać kwotę o którą aktualizuję? chyba tak a nie o nową kwotę bo to jest update a nie replace
        wallet = user.wallet
        if wallet.user_id != user.id:
            raise NoPermissionException("User does not own this wallet.")

        balance = Balance.of(payload.balance)
        wallet.balance_available = balance.amount
        if payload.currency:
            wallet.currency = payload.currency

        self.db.commit()
        self.db.refresh(wallet)

        return wallet
