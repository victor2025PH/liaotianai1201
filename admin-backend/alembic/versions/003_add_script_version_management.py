"""添加劇本版本管理功能

Revision ID: 003_add_script_version_management
Revises: 002_add_indexes_for_performance
Create Date: 2025-01-07

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision = '003_add_script_version_management'
down_revision = '002_add_indexes'
branch_labels = None
depends_on = None


def upgrade():
    # 添加劇本狀態和審核相關字段
    op.add_column('group_ai_scripts', sa.Column('status', sa.String(20), server_default='draft', nullable=False))
    op.add_column('group_ai_scripts', sa.Column('created_by', sa.String(100), nullable=True))
    op.add_column('group_ai_scripts', sa.Column('reviewed_by', sa.String(100), nullable=True))
    op.add_column('group_ai_scripts', sa.Column('reviewed_at', sa.DateTime(), nullable=True))
    op.add_column('group_ai_scripts', sa.Column('published_at', sa.DateTime(), nullable=True))
    op.add_column('group_ai_scripts', sa.Column('tags', sa.JSON(), nullable=True))
    
    # 創建狀態索引
    op.create_index('ix_group_ai_scripts_status', 'group_ai_scripts', ['status'])
    
    # 創建版本歷史表
    op.create_table(
        'group_ai_script_versions',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('script_id', sa.String(100), nullable=False, index=True),
        sa.Column('version', sa.String(20), nullable=False),
        sa.Column('yaml_content', sa.Text(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_by', sa.String(100), nullable=True),
        sa.Column('change_summary', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, index=True),
    )
    
    # 創建 script_id + version 的複合索引（用於快速查詢特定版本）
    op.create_index('ix_group_ai_script_versions_script_version', 'group_ai_script_versions', ['script_id', 'version'])


def downgrade():
    # 刪除版本歷史表
    op.drop_table('group_ai_script_versions')
    
    # 刪除索引
    op.drop_index('ix_group_ai_scripts_status', table_name='group_ai_scripts')
    
    # 刪除字段
    op.drop_column('group_ai_scripts', 'tags')
    op.drop_column('group_ai_scripts', 'published_at')
    op.drop_column('group_ai_scripts', 'reviewed_at')
    op.drop_column('group_ai_scripts', 'reviewed_by')
    op.drop_column('group_ai_scripts', 'created_by')
    op.drop_column('group_ai_scripts', 'status')

