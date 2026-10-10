from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    SmallInteger,
    String,
    Text,
    func,
    text,
)
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from app.enums import AuctionStatus, Role, UserStatus, VerificationStatus, WalletStatus


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(200), unique=True, index=True)
    status: Mapped[UserStatus] = mapped_column(String(50), default=UserStatus.ACTIVE)
    hashed_password: Mapped[str] = mapped_column(String(200))
    role: Mapped[Role] = mapped_column(String(50), default=Role.USER)
    token_version: Mapped[int] = mapped_column(
        default=1, server_default="1", nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    wallet: Mapped[Optional["Wallet"]] = relationship(
        "Wallet", back_populates="user", uselist=False
    )


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
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), onupdate=lambda: datetime.now(timezone.utc)
    )

    @property
    def total_balance(self) -> Decimal:
        return self.balance_available + self.balance_held

    user: Mapped["User"] = relationship("User", back_populates="wallet")


# do usera dodajemy model wallet  dostępne środki, zablokowane środki pod aukcje, waluta dodatkowo można dać wallet_transactions   wallet id amount, typ transakcji


class Bid(Base):
    __tablename__ = "bids"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))


class Auction(Base):
    __tablename__ = "auctions"
    id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"), primary_key=True
    )
    seller_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text)
    starting_price: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    minimum_price: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    current_price: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    bid_increment: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    status: Mapped[AuctionStatus] = mapped_column(
        SQLEnum(AuctionStatus),
        default=AuctionStatus.DRAFT,
        nullable=False,
        # todo jaka różnia pomiędzy sqlnum a enum w sqlalchemy
    )
    verification_status: Mapped[VerificationStatus] = mapped_column(
        Enum(VerificationStatus),
        default=VerificationStatus.PENDING,
        nullable=False,
    )
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    winner_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), nullable=True, index=True
    )
    version: Mapped[int] = mapped_column(default=1, server_default="1", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=lambda: datetime.now(timezone.utc),
    )


class AuctionImage(Base):
    __tablename__ = "auction_images"

    __table_args__ = (
        Index(
            "uq_auction_images_primary",
            "auction_id",
            unique=True,
            postgresql_where=text("is_primary = true"),
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    auction_id: Mapped[int] = mapped_column(
        ForeignKey("auctions.id", ondelete="CASCADE"),
        index=True,
    )
    storage_key: Mapped[str] = mapped_column(
        String(500),
        unique=True,
    )
    file_size: Mapped[int] = mapped_column(Integer)
    mime_type: Mapped[str] = mapped_column(String(100))
    position: Mapped[int] = mapped_column(
        SmallInteger,
        default=0,
        server_default=text("0"),
    )
    is_primary: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        server_default=text("false"),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    auction: Mapped["Auction"] = relationship(
        back_populates="images",
    )
