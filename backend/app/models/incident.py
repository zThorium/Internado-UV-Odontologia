import uuid
from datetime import date, datetime

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class Incident(Base):
    __tablename__ = "incidents"

    id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    reported_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    reporter_role: Mapped[str] = mapped_column(
        sa.Enum("student", "tutor", name="incident_reporter_role"),
        nullable=False,
        default="student",
        server_default="student",
    )
    title: Mapped[str | None] = mapped_column(sa.String, nullable=True)
    incident_type: Mapped[str] = mapped_column(
        sa.Enum("abuse", "harassment", "discrimination", "other", name="incident_type"),
        nullable=False,
    )
    urgency_level: Mapped[str] = mapped_column(
        sa.Enum("low", "medium", "high", "critical", name="incident_urgency_level"),
        nullable=False,
        default="medium",
        server_default="medium",
    )
    description: Mapped[str] = mapped_column(sa.Text, nullable=False)
    event_date: Mapped[date] = mapped_column(sa.Date, nullable=False)
    status: Mapped[str] = mapped_column(
        sa.Enum("submitted", "under_review", "resolved", name="incident_status"),
        nullable=False,
        default="submitted",
        server_default="submitted",
    )
    coordinator_response: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        server_default=sa.func.now(),
        onupdate=sa.func.now(),
        nullable=False,
    )
