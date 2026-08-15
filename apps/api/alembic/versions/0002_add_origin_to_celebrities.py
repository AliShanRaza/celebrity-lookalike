"""Add origin column to celebrities table

Revision ID: 0002_add_origin_to_celebrities
Revises: 0001_initial_schema
Create Date: 2026-07-31 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0002_add_origin_to_celebrities'
down_revision: Union[str, None] = '0001_initial_schema'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'celebrities',
        sa.Column('origin', sa.String(length=50), server_default='bollywood', nullable=False)
    )
    op.create_index(op.f('ix_celebrities_origin'), 'celebrities', ['origin'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_celebrities_origin'), table_name='celebrities')
    op.drop_column('celebrities', 'origin')
