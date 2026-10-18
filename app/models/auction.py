from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.enums import AuctionStatus, VerificationStatus
from app.models.base import Base


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
    current_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=True)
    bid_increment: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=True)
    _status: Mapped[AuctionStatus] = mapped_column(
        SQLEnum(AuctionStatus),
        default=AuctionStatus.DRAFT,
        nullable=False,
        # todo jaka różnia pomiędzy sqlnum a enum w sqlalchemy
    )
    _verification_status: Mapped[VerificationStatus] = mapped_column(
        "verification_status",
        Enum(VerificationStatus),
        default=VerificationStatus.PENDING,
        nullable=False,
    )
    currency: Mapped[str] = mapped_column(String(3), default="PLN")
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    winner_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), nullable=True, index=True
    )
    version: Mapped[int] = mapped_column(default=1, server_default="1", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        default=lambda: datetime.now(UTC),
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=lambda: datetime.now(UTC),
    )

    images: Mapped[list["AuctionImage"]] = relationship(back_populates="auction")

    @property
    def status(self) -> AuctionStatus:
        return self._status

    @property
    def verification_status(self) -> VerificationStatus:
        return self._verification_status

    def reject(self) -> None:
        self._verification_status = VerificationStatus.REJECTED
