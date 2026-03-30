"""initial schema

Revision ID: 0001
Revises:
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Enums
    user_role = sa.Enum("student", "tutor", "coordinator", name="user_role")
    logbook_status = sa.Enum("draft", "submitted", "reviewed", name="logbook_status")
    incident_type = sa.Enum("abuse", "harassment", "discrimination", "other", name="incident_type")
    incident_status = sa.Enum("submitted", "under_review", "resolved", name="incident_status")
    evaluation_score = sa.Enum("achieved", "in_progress", "not_achieved", name="evaluation_score")

    # users
    op.create_table(
        "users",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String, nullable=False, unique=True),
        sa.Column("hashed_password", sa.String, nullable=False),
        sa.Column("full_name", sa.String, nullable=False),
        sa.Column("role", user_role, nullable=False),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_users_email", "users", ["email"])

    # cohorts
    op.create_table(
        "cohorts",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String, nullable=False),
        sa.Column("year", sa.Integer, nullable=False),
        sa.Column("semester", sa.Integer, nullable=False),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )

    # assignments
    op.create_table(
        "assignments",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "student_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "tutor_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "cohort_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("cohorts.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("clinical_site", sa.String, nullable=False),
        sa.Column("start_date", sa.Date, nullable=False),
        sa.Column("end_date", sa.Date, nullable=False),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.text("true")),
    )
    op.create_index("ix_assignments_student_id", "assignments", ["student_id"])
    op.create_index("ix_assignments_tutor_id", "assignments", ["tutor_id"])
    op.create_index(
        "ix_assignments_tutor_student_active",
        "assignments",
        ["tutor_id", "student_id", "is_active"],
    )

    # logbook_entries
    op.create_table(
        "logbook_entries",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "student_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "cohort_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("cohorts.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("week_number", sa.Integer, nullable=False),
        sa.Column("week_start_date", sa.Date, nullable=False),
        sa.Column("status", logbook_status, nullable=False, server_default="draft"),
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
    op.create_index("ix_logbook_entries_student_id", "logbook_entries", ["student_id"])
    op.create_index(
        "ix_logbook_entries_student_week",
        "logbook_entries",
        ["student_id", "week_number"],
    )

    # logbook_procedures
    op.create_table(
        "logbook_procedures",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "entry_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("logbook_entries.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String, nullable=False),
        sa.Column("description", sa.String, nullable=False, server_default=""),
        sa.Column("quantity", sa.Integer, nullable=False),
    )
    op.create_index("ix_logbook_procedures_entry_id", "logbook_procedures", ["entry_id"])

    # incidents
    op.create_table(
        "incidents",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "student_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("incident_type", incident_type, nullable=False),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("event_date", sa.Date, nullable=False),
        sa.Column("status", incident_status, nullable=False, server_default="submitted"),
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
    op.create_index("ix_incidents_student_id", "incidents", ["student_id"])

    # evaluations
    op.create_table(
        "evaluations",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tutor_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "student_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "assignment_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("assignments.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("period_label", sa.String, nullable=False),
        sa.Column("overall_comment", sa.String, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_evaluations_tutor_id", "evaluations", ["tutor_id"])
    op.create_index("ix_evaluations_student_id", "evaluations", ["student_id"])

    # evaluation_items
    op.create_table(
        "evaluation_items",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "evaluation_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("evaluations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("dimension", sa.String, nullable=False),
        sa.Column("score", evaluation_score, nullable=False),
        sa.Column("comment", sa.String, nullable=True),
    )
    op.create_index("ix_evaluation_items_evaluation_id", "evaluation_items", ["evaluation_id"])


def downgrade() -> None:
    op.drop_table("evaluation_items")
    op.drop_table("evaluations")
    op.drop_table("incidents")
    op.drop_table("logbook_procedures")
    op.drop_table("logbook_entries")
    op.drop_table("assignments")
    op.drop_table("cohorts")
    op.drop_table("users")

    # Drop enums
    sa.Enum(name="evaluation_score").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="incident_status").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="incident_type").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="logbook_status").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="user_role").drop(op.get_bind(), checkfirst=True)
