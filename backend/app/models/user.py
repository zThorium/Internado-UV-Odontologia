import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(sa.String, unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(sa.String, nullable=False)
    full_name: Mapped[str] = mapped_column(sa.String, nullable=False)
    role: Mapped[str] = mapped_column(
        sa.Enum("student", "tutor", "coordinator", name="user_role"),
        nullable=False,
    )
    profession: Mapped[str | None] = mapped_column(sa.String, nullable=True)
    available_hours_per_week: Mapped[int | None] = mapped_column(sa.Integer, nullable=True)
    tutor_training_status: Mapped[str | None] = mapped_column(
        sa.Enum("yes", "no", "in_progress", name="tutor_training_status"),
        nullable=True,
    )
    is_active: Mapped[bool] = mapped_column(sa.Boolean, default=True, nullable=False)
    has_completed_onboarding: Mapped[bool] = mapped_column(sa.Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
    )
