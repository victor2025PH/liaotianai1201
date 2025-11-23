"""add_role_assignment_schemes_tables

Revision ID: cb4ad7ca2507
Revises: ea5d525f9c2a
Create Date: 2025-11-18 10:43:20.541185

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision = 'cb4ad7ca2507'
down_revision = 'ea5d525f9c2a'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 創建角色分配方案表
    op.create_table(
        'group_ai_role_assignment_schemes',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('script_id', sa.String(100), nullable=False),
        sa.Column('assignments', sa.JSON(), nullable=False),
        sa.Column('mode', sa.String(20), nullable=False, server_default='auto'),
        sa.Column('account_ids', sa.JSON(), nullable=False, server_default='[]'),
        sa.Column('created_by', sa.String(100), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    
    # 創建索引
    op.create_index('ix_group_ai_role_assignment_schemes_name', 'group_ai_role_assignment_schemes', ['name'])
    op.create_index('ix_group_ai_role_assignment_schemes_script_id', 'group_ai_role_assignment_schemes', ['script_id'])
    op.create_index('ix_group_ai_role_assignment_schemes_created_at', 'group_ai_role_assignment_schemes', ['created_at'])
    
    # 創建角色分配歷史記錄表
    op.create_table(
        'group_ai_role_assignment_history',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('scheme_id', sa.String(36), nullable=False),
        sa.Column('script_id', sa.String(100), nullable=False),
        sa.Column('account_id', sa.String(100), nullable=False),
        sa.Column('role_id', sa.String(100), nullable=False),
        sa.Column('applied_by', sa.String(100), nullable=True),
        sa.Column('applied_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('extra_data', sa.JSON(), nullable=True, server_default='{}'),
    )
    
    # 創建索引
    op.create_index('ix_group_ai_role_assignment_history_scheme_id', 'group_ai_role_assignment_history', ['scheme_id'])
    op.create_index('ix_group_ai_role_assignment_history_script_id', 'group_ai_role_assignment_history', ['script_id'])
    op.create_index('ix_group_ai_role_assignment_history_account_id', 'group_ai_role_assignment_history', ['account_id'])
    op.create_index('ix_group_ai_role_assignment_history_applied_at', 'group_ai_role_assignment_history', ['applied_at'])


def downgrade() -> None:
    # 刪除索引
    op.drop_index('ix_group_ai_role_assignment_history_applied_at', table_name='group_ai_role_assignment_history')
    op.drop_index('ix_group_ai_role_assignment_history_account_id', table_name='group_ai_role_assignment_history')
    op.drop_index('ix_group_ai_role_assignment_history_script_id', table_name='group_ai_role_assignment_history')
    op.drop_index('ix_group_ai_role_assignment_history_scheme_id', table_name='group_ai_role_assignment_history')
    op.drop_index('ix_group_ai_role_assignment_schemes_created_at', table_name='group_ai_role_assignment_schemes')
    op.drop_index('ix_group_ai_role_assignment_schemes_script_id', table_name='group_ai_role_assignment_schemes')
    op.drop_index('ix_group_ai_role_assignment_schemes_name', table_name='group_ai_role_assignment_schemes')
    
    # 刪除表
    op.drop_table('group_ai_role_assignment_history')
    op.drop_table('group_ai_role_assignment_schemes')
