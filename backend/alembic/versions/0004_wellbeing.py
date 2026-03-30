"""wellbeing module

Revision ID: 0004
Revises: 0003
Create Date: 2024-01-01 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Crear enums de forma idempotente (CREATE TYPE no soporta IF NOT EXISTS para ENUM en PG)
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_type WHERE typname = 'wellbeing_status'
            ) THEN
                CREATE TYPE wellbeing_status AS ENUM ('good', 'regular', 'difficult');
            END IF;
        END$$;
    """)
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_type WHERE typname = 'alert_level'
            ) THEN
                CREATE TYPE alert_level AS ENUM ('yellow', 'red');
            END IF;
        END$$;
    """)

    # Agregar wellbeing_status a logbook_entries (nullable para entradas existentes)
    # Usamos DO $$ para hacerlo idempotente
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name='logbook_entries' AND column_name='wellbeing_status'
            ) THEN
                ALTER TABLE logbook_entries ADD COLUMN wellbeing_status wellbeing_status;
            END IF;
        END$$;
    """)

    # Tabla de alertas de bienestar
    op.execute("""
        CREATE TABLE IF NOT EXISTS wellbeing_alerts (
            id UUID PRIMARY KEY,
            student_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            alert_level alert_level NOT NULL,
            triggered_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            resolved BOOLEAN NOT NULL DEFAULT false,
            resolved_at TIMESTAMPTZ
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_wellbeing_alerts_student_id ON wellbeing_alerts (student_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_wellbeing_alerts_student_resolved ON wellbeing_alerts (student_id, resolved)")


def downgrade() -> None:
    op.drop_index("ix_wellbeing_alerts_student_resolved", "wellbeing_alerts")
    op.drop_index("ix_wellbeing_alerts_student_id", "wellbeing_alerts")
    op.drop_table("wellbeing_alerts")
    op.drop_column("logbook_entries", "wellbeing_status")
    op.execute("DROP TYPE IF EXISTS alert_level")
    op.execute("DROP TYPE IF EXISTS wellbeing_status")
