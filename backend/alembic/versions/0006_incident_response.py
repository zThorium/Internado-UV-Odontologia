"""Add coordinator_response to incidents

Revision ID: 0006
Revises: 0005
Create Date: 2026-03-27

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0006'
down_revision = '0005'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('incidents', sa.Column('coordinator_response', sa.Text(), nullable=True))


def downgrade():
    op.drop_column('incidents', 'coordinator_response')
