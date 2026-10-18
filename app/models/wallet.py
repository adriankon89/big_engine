from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Numeric, String
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.enums import WalletStatus
from app.models.base import Base


# do usera dodajemy model wallet  dostępne środki, zablokowane środki pod aukcje, waluta dodatkowo można dać wallet_transactions   wallet id amount, typ transakcji
class Wallet(Base):
    __tablename__ = "wallets"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), unique=True, index=True
    )
    balance_available: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=Decimal("0.00")
    )
    balance_held: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=Decimal("0.00")
    )
    currency: Mapped[str] = mapped_column(String(3), default="PLN")
    status: Mapped[WalletStatus] = mapped_column(
        SQLEnum(WalletStatus), default=WalletStatus.ACTIVE
    )
    version: Mapped[int] = mapped_column(default=1)  # Optimistic locking
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), onupdate=lambda: datetime.now(UTC)
    )

    @property
    def total_balance(self) -> Decimal:
        return self.balance_available + self.balance_held

    user: Mapped["User"] = relationship("User", back_populates="wallet")
