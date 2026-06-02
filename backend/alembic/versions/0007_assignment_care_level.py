"""Add care_level to assignments

Revision ID: 0007
Revises: 0006
Create Date: 2026-03-30

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None


care_level_enum = sa.Enum("primary", "secondary", "tertiary", name="care_level")


def upgrade():
    bind = op.get_bind()
    dialect = bind.dialect.name

    if dialect == "postgresql":
        care_level_enum.create(bind, checkfirst=True)

    op.add_column(
        "assignments",
        sa.Column(
            "care_level",
            care_level_enum,
            nullable=False,
            server_default="primary",
        ),
    )


def downgrade():
    op.drop_column("assignments", "care_level")

    bind = op.get_bind()
    dialect = bind.dialect.name
    if dialect == "postgresql":
        care_level_enum.drop(bind, checkfirst=True)
