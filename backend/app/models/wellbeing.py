import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class WellbeingAlert(Base):
    __tablename__ = "wellbeing_alerts"

    id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False, index=True
    )
    alert_level: Mapped[str] = mapped_column(
        sa.Enum("yellow", "red", name="alert_level"), nullable=False
    )
    triggered_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
    )
    resolved: Mapped[bool] = mapped_column(sa.Boolean, nullable=False, default=False)
    resolved_at: Mapped[datetime | None] = mapped_column(
        sa.DateTime(timezone=True), nullable=True
    )
