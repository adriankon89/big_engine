from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, Text
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from app.enums import AppealReasonCode, AppealStatus
from app.models.auction import Auction
from app.models.base import BaseWithTimestamps


class AuctionAppeal(BaseWithTimestamps):
    __tablename__ = "auction_appeals"

    id: Mapped[int] = mapped_column(primary_key=True)
    auction_id: Mapped[int] = mapped_column(
        ForeignKey("auctions.id", ondelete="CASCADE"),
        index=True,
    )
    status: Mapped[AppealStatus] = mapped_column(
        SQLEnum(
            AppealStatus,
            name="appealstatus",
            values_callable=lambda enum: [member.value for member in enum],
        ),
        default=AppealStatus.OPEN,
        server_default=AppealStatus.OPEN.value,
        nullable=False,
    )
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    reason_code: Mapped[AppealReasonCode] = mapped_column(
        SQLEnum(
            AppealReasonCode,
            name="appealreasoncode",
            values_callable=lambda enum: [member.value for member in enum],
        ),
        nullable=False,
    )
    reviewer_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), nullable=True, index=True
    )
    resolution_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    internal_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    auction: Mapped["Auction"] = relationship(back_populates="appeal")

    @validates("status")
    def _set_resolved_at_for_status(
        self, _key: str, status: AppealStatus
    ) -> AppealStatus:
        self.resolved_at = (
            datetime.now(UTC) if self._status_is_resolved(status) else None
        )
        return status

    @staticmethod
    def _status_is_resolved(status: AppealStatus) -> bool:
        return status in (
            AppealStatus.APPROVED,
            AppealStatus.REJECTED,
            AppealStatus.CANCELLED,
        )

    @property
    def is_resolved(self) -> bool:
        return self._status_is_resolved(self.status)
