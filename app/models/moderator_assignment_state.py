from sqlalchemy import Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class ModeratorAssignmentState(Base):
    __tablename__ = "moderator_assignment_state"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    last_moderator_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
