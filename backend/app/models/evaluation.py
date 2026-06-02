import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class Evaluation(Base):
    __tablename__ = "evaluations"

    id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tutor_id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False, index=True
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False, index=True
    )
    assignment_id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(as_uuid=True), sa.ForeignKey("assignments.id"), nullable=False
    )
    period_label: Mapped[str] = mapped_column(sa.String, nullable=False)
    overall_comment: Mapped[str | None] = mapped_column(sa.String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
    )

    items: Mapped[list["EvaluationItem"]] = relationship(
        "EvaluationItem",
        back_populates="evaluation",
        cascade="all, delete-orphan",
    )


class EvaluationItem(Base):
    __tablename__ = "evaluation_items"

    id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    evaluation_id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(as_uuid=True), sa.ForeignKey("evaluations.id"), nullable=False, index=True
    )
    dimension: Mapped[str] = mapped_column(sa.String, nullable=False)
    score: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    comment: Mapped[str | None] = mapped_column(sa.String, nullable=True)

    evaluation: Mapped["Evaluation"] = relationship(
        "Evaluation",
        back_populates="items",
    )
