import uuid
from datetime import date, datetime

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class LogbookEntry(Base):
    __tablename__ = "logbook_entries"

    id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False, index=True
    )
    cohort_id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(as_uuid=True), sa.ForeignKey("cohorts.id"), nullable=False
    )
    week_number: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    week_start_date: Mapped[date] = mapped_column(sa.Date, nullable=False)
    status: Mapped[str] = mapped_column(
        sa.Enum("draft", "submitted", "reviewed", name="logbook_status"),
        nullable=False,
        default="draft",
        server_default="draft",
    )
    wellbeing_status: Mapped[str | None] = mapped_column(
        sa.Enum("good", "regular", "difficult", name="wellbeing_status"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        server_default=sa.func.now(),
        onupdate=sa.func.now(),
        nullable=False,
    )

    procedures: Mapped[list["LogbookProcedure"]] = relationship(
        "LogbookProcedure",
        back_populates="entry",
        cascade="all, delete-orphan",
    )
    tutor_validation: Mapped["LogbookValidation"] = relationship(
        "LogbookValidation",
        back_populates="entry",
        uselist=False,
        cascade="all, delete-orphan",
    )


class LogbookProcedure(Base):
    __tablename__ = "logbook_procedures"

    id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    entry_id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(as_uuid=True), sa.ForeignKey("logbook_entries.id"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(sa.String, nullable=False)
    description: Mapped[str] = mapped_column(sa.String, nullable=False, default="")
    quantity: Mapped[int] = mapped_column(sa.Integer, nullable=False)

    entry: Mapped["LogbookEntry"] = relationship(
        "LogbookEntry",
        back_populates="procedures",
    )
