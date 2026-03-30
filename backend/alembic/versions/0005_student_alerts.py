"""student_alerts table

Revision ID: 0005
Revises: 0004
Create Date: 2025-01-01 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_type WHERE typname = 'student_alert_type'
            ) THEN
                CREATE TYPE student_alert_type AS ENUM (
                    'no_bitacora', 'low_wellbeing', 'no_evaluation',
                    'absences', 'incident_report'
                );
            END IF;
        END$$;
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS student_alerts (
            id UUID PRIMARY KEY,
            student_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            alert_type student_alert_type NOT NULL,
            alert_level VARCHAR(10) NOT NULL,
            triggered_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            is_active BOOLEAN NOT NULL DEFAULT true,
            resolved_at TIMESTAMPTZ,
            resolved_by UUID REFERENCES users(id),
            coordinator_note TEXT
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_student_alerts_student_id ON student_alerts (student_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_student_alerts_active ON student_alerts (student_id, is_active)")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS student_alerts")
    op.execute("DROP TYPE IF EXISTS student_alert_type")
