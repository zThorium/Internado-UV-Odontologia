"""add attendance_records table

Revision ID: 0002
Revises: 0001
Create Date: 2026-03-23 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    attendance_status = sa.Enum("present", "absent", "justified", name="attendance_status")

    op.create_table(
        "attendance_records",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "student_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("date", sa.Date, nullable=False),
        sa.Column("status", attendance_status, nullable=False),
        sa.Column("observation", sa.Text, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_attendance_student_id", "attendance_records", ["student_id"])
    op.create_unique_constraint(
        "uq_attendance_student_date",
        "attendance_records",
        ["student_id", "date"],
    )


def downgrade() -> None:
    op.drop_table("attendance_records")
    sa.Enum(name="attendance_status").drop(op.get_bind(), checkfirst=True)
