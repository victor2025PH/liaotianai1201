"""merge_migration_heads

Revision ID: f6b2d7826fdd
Revises: 004_add_performance_indexes, 005_merge_heads_and_add_indexes, 006_unified_features, 007_add_theater_tables
Create Date: 2025-12-23 04:09:18.056280

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f6b2d7826fdd'
down_revision = ('004_add_performance_indexes', '005_merge_heads_and_add_indexes', '006_unified_features', '007_add_theater_tables')
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass

