"""Tutor module enhancements: incidents, evaluations, logbook validation, tutor profile

Revision ID: 0008
Revises: 0007
Create Date: 2026-04-14

"""

from alembic import op
import sqlalchemy as sa


revision = "0008"
down_revision = "0007"
branch_labels = None
depends_on = None


tutor_training_status_enum = sa.Enum(
    "yes",
    "no",
    "in_progress",
    name="tutor_training_status",
)
incident_reporter_role_enum = sa.Enum(
    "student",
    "tutor",
    name="incident_reporter_role",
)
incident_urgency_level_enum = sa.Enum(
    "low",
    "medium",
    "high",
    "critical",
    name="incident_urgency_level",
)

def upgrade() -> None:
    bind = op.get_bind()
    dialect = bind.dialect.name

    if dialect == "postgresql":
        tutor_training_status_enum.create(bind, checkfirst=True)
        incident_reporter_role_enum.create(bind, checkfirst=True)
        incident_urgency_level_enum.create(bind, checkfirst=True)

    # users: extended tutor profile
    op.add_column("users", sa.Column("profession", sa.String(), nullable=True))
    op.add_column("users", sa.Column("available_hours_per_week", sa.Integer(), nullable=True))
    op.add_column("users", sa.Column("tutor_training_status", tutor_training_status_enum, nullable=True))

    # incidents: reporting metadata for tutor-created incidents
    op.add_column("incidents", sa.Column("reported_by_user_id", sa.UUID(as_uuid=True), nullable=True))
    op.add_column(
        "incidents",
        sa.Column(
            "reporter_role",
            incident_reporter_role_enum,
            nullable=False,
            server_default="student",
        ),
    )
    op.add_column("incidents", sa.Column("title", sa.String(), nullable=True))
    op.add_column(
        "incidents",
        sa.Column(
            "urgency_level",
            incident_urgency_level_enum,
            nullable=False,
            server_default="medium",
        ),
    )
    op.create_foreign_key(
        "fk_incidents_reported_by_user_id_users",
        "incidents",
        "users",
        ["reported_by_user_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        "ix_incidents_reported_by_user_id",
        "incidents",
        ["reported_by_user_id"],
        unique=False,
    )

    # logbook validation by tutor
    op.create_table(
        "logbook_validations",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "entry_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("logbook_entries.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column(
            "student_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "tutor_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "assignment_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("assignments.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "validated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_logbook_validations_entry_id", "logbook_validations", ["entry_id"], unique=True)
    op.create_index("ix_logbook_validations_student_id", "logbook_validations", ["student_id"], unique=False)
    op.create_index("ix_logbook_validations_tutor_id", "logbook_validations", ["tutor_id"], unique=False)
    op.create_index("ix_logbook_validations_assignment_id", "logbook_validations", ["assignment_id"], unique=False)

    # evaluations: score to numeric rubric (1-5)
    op.add_column("evaluation_items", sa.Column("score_int", sa.Integer(), nullable=True))
    op.execute(
        """
        UPDATE evaluation_items
        SET score_int = CASE score
            WHEN 'achieved' THEN 5
            WHEN 'in_progress' THEN 3
            WHEN 'not_achieved' THEN 1
            ELSE 3
        END
        """
    )

    if dialect == "sqlite":
        with op.batch_alter_table("evaluation_items") as batch_op:
            batch_op.drop_column("score")
            batch_op.alter_column("score_int", new_column_name="score", nullable=False)
    else:
        op.drop_column("evaluation_items", "score")
        op.alter_column("evaluation_items", "score_int", new_column_name="score", nullable=False)

    if dialect == "postgresql":
        op.execute("DROP TYPE IF EXISTS evaluation_score")
        op.execute("ALTER TYPE student_alert_type ADD VALUE IF NOT EXISTS 'no_tutor_validation'")


def downgrade() -> None:
    bind = op.get_bind()
    dialect = bind.dialect.name

    # evaluations: score back to legacy enum values
    evaluation_score_enum = sa.Enum(
        "achieved",
        "in_progress",
        "not_achieved",
        name="evaluation_score",
    )

    if dialect == "postgresql":
        evaluation_score_enum.create(bind, checkfirst=True)

    op.add_column("evaluation_items", sa.Column("score_legacy", evaluation_score_enum, nullable=True))
    op.execute(
        """
        UPDATE evaluation_items
        SET score_legacy = CASE
            WHEN score >= 4 THEN 'achieved'
            WHEN score >= 2 THEN 'in_progress'
            ELSE 'not_achieved'
        END
        """
    )

    if dialect == "sqlite":
        with op.batch_alter_table("evaluation_items") as batch_op:
            batch_op.drop_column("score")
            batch_op.alter_column("score_legacy", new_column_name="score", nullable=False)
    else:
        op.drop_column("evaluation_items", "score")
        op.alter_column("evaluation_items", "score_legacy", new_column_name="score", nullable=False)

    # logbook_validations
    op.drop_index("ix_logbook_validations_assignment_id", table_name="logbook_validations")
    op.drop_index("ix_logbook_validations_tutor_id", table_name="logbook_validations")
    op.drop_index("ix_logbook_validations_student_id", table_name="logbook_validations")
    op.drop_index("ix_logbook_validations_entry_id", table_name="logbook_validations")
    op.drop_table("logbook_validations")

    # incidents
    op.drop_index("ix_incidents_reported_by_user_id", table_name="incidents")
    op.drop_constraint("fk_incidents_reported_by_user_id_users", "incidents", type_="foreignkey")
    op.drop_column("incidents", "urgency_level")
    op.drop_column("incidents", "title")
    op.drop_column("incidents", "reporter_role")
    op.drop_column("incidents", "reported_by_user_id")

    # users
    op.drop_column("users", "tutor_training_status")
    op.drop_column("users", "available_hours_per_week")
    op.drop_column("users", "profession")

    if dialect == "postgresql":
        incident_urgency_level_enum.drop(bind, checkfirst=True)
        incident_reporter_role_enum.drop(bind, checkfirst=True)
        tutor_training_status_enum.drop(bind, checkfirst=True)
