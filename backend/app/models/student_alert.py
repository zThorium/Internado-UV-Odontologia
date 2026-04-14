import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class StudentAlert(Base):
    __tablename__ = "student_alerts"

    id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    alert_type: Mapped[str] = mapped_column(
        sa.Enum(
            "no_bitacora", "low_wellbeing", "no_evaluation",
            "no_tutor_validation", "absences", "incident_report",
            name="student_alert_type",
        ),
        nullable=False,
    )
    # 'yellow' | 'red'
    alert_level: Mapped[str] = mapped_column(sa.String(10), nullable=False)
    triggered_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
    )
    is_active: Mapped[bool] = mapped_column(sa.Boolean, nullable=False, default=True)
    resolved_at: Mapped[datetime | None] = mapped_column(
        sa.DateTime(timezone=True), nullable=True
    )
    resolved_by: Mapped[uuid.UUID | None] = mapped_column(
        sa.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True
    )
    coordinator_note: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
