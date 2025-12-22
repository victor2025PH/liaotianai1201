"""添加智能剧场表（Phase 3）

Revision ID: 007_add_theater_tables
Revises: xxxx_add_telegram_registration
Create Date: 2025-01-20 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision = '007_add_theater_tables'
down_revision = 'xxxx_add_telegram_registration'
branch_labels = None
depends_on = None


def upgrade():
    # 创建 theater_scenarios 表（剧场场景表）
    op.create_table(
        'theater_scenarios',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('roles', sa.JSON(), nullable=False, server_default='[]'),  # 角色列表
        sa.Column('timeline', sa.JSON(), nullable=False, server_default='[]'),  # 时间轴动作列表
        sa.Column('enabled', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('created_by', sa.String(100), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    
    # 创建索引
    op.create_index('ix_theater_scenarios_id', 'theater_scenarios', ['id'])
    op.create_index('ix_theater_scenarios_name', 'theater_scenarios', ['name'])
    op.create_index('ix_theater_scenarios_enabled', 'theater_scenarios', ['enabled'])
    
    # 创建 theater_executions 表（执行记录表）
    op.create_table(
        'theater_executions',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('scenario_id', sa.String(36), nullable=False),
        sa.Column('scenario_name', sa.String(200), nullable=False),
        sa.Column('group_id', sa.String(100), nullable=False),
        sa.Column('agent_mapping', sa.JSON(), nullable=False, server_default='{}'),  # Agent 映射
        sa.Column('status', sa.String(20), nullable=False, server_default='pending'),  # pending, running, completed, failed, cancelled
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('duration_seconds', sa.Integer(), nullable=True),
        sa.Column('executed_actions', sa.JSON(), server_default='[]'),  # 已执行的动作列表
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_by', sa.String(100), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    
    # 创建索引
    op.create_index('ix_theater_executions_id', 'theater_executions', ['id'])
    op.create_index('ix_theater_executions_scenario_id', 'theater_executions', ['scenario_id'])
    op.create_index('ix_theater_executions_group_id', 'theater_executions', ['group_id'])
    op.create_index('ix_theater_executions_status', 'theater_executions', ['status'])
    op.create_index('ix_theater_executions_created_at', 'theater_executions', ['created_at'])


def downgrade():
    # 删除表（按依赖顺序）
    op.drop_table('theater_executions')
    op.drop_table('theater_scenarios')
