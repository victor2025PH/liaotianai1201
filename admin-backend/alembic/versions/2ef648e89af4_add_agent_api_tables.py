"""add_agent_api_tables

Revision ID: 2ef648e89af4
Revises: f6b2d7826fdd
Create Date: 2025-12-23 04:10:16.455832

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision = '2ef648e89af4'
down_revision = 'f6b2d7826fdd'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 创建 agents 表
    op.create_table('agents',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('agent_id', sa.String(length=100), nullable=False),
        sa.Column('phone_number', sa.String(length=20), nullable=True),
        sa.Column('device_info', sa.JSON(), nullable=True),
        sa.Column('proxy_url', sa.String(length=500), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='offline'),
        sa.Column('current_task_id', sa.String(length=36), nullable=True),
        sa.Column('api_key', sa.String(length=100), nullable=True),
        sa.Column('agent_metadata', sa.JSON(), nullable=True),
        sa.Column('last_active_time', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_agents_agent_id', 'agents', ['agent_id'], unique=True)
    op.create_index('ix_agents_status', 'agents', ['status'], unique=False)
    op.create_index('ix_agents_phone_number', 'agents', ['phone_number'], unique=False)
    op.create_index('ix_agents_current_task_id', 'agents', ['current_task_id'], unique=False)
    op.create_index('ix_agents_last_active_time', 'agents', ['last_active_time'], unique=False)
    op.create_index('idx_agents_status_active', 'agents', ['status', 'last_active_time'], unique=False)
    
    # 创建 agent_tasks 表
    op.create_table('agent_tasks',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('task_id', sa.String(length=100), nullable=False),
        sa.Column('agent_id', sa.String(length=100), nullable=True),
        sa.Column('task_type', sa.String(length=50), nullable=False),
        sa.Column('scenario_data', sa.JSON(), nullable=True),
        sa.Column('variables', sa.JSON(), nullable=True),
        sa.Column('priority', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='pending'),
        sa.Column('result_data', sa.JSON(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('assigned_at', sa.DateTime(), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('executed_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_agent_tasks_task_id', 'agent_tasks', ['task_id'], unique=True)
    op.create_index('ix_agent_tasks_status', 'agent_tasks', ['status'], unique=False)
    op.create_index('ix_agent_tasks_task_type', 'agent_tasks', ['task_type'], unique=False)
    op.create_index('ix_agent_tasks_agent_id', 'agent_tasks', ['agent_id'], unique=False)
    op.create_index('ix_agent_tasks_priority', 'agent_tasks', ['priority'], unique=False)
    op.create_index('ix_agent_tasks_created_at', 'agent_tasks', ['created_at'], unique=False)
    op.create_index('idx_agent_tasks_status_priority', 'agent_tasks', ['status', 'priority', 'created_at'], unique=False)
    op.create_index('idx_agent_tasks_agent_status', 'agent_tasks', ['agent_id', 'status'], unique=False)


def downgrade() -> None:
    # 删除索引
    op.drop_index('idx_agent_tasks_agent_status', table_name='agent_tasks')
    op.drop_index('idx_agent_tasks_status_priority', table_name='agent_tasks')
    op.drop_index('ix_agent_tasks_created_at', table_name='agent_tasks')
    op.drop_index('ix_agent_tasks_priority', table_name='agent_tasks')
    op.drop_index('ix_agent_tasks_agent_id', table_name='agent_tasks')
    op.drop_index('ix_agent_tasks_task_type', table_name='agent_tasks')
    op.drop_index('ix_agent_tasks_status', table_name='agent_tasks')
    op.drop_index('ix_agent_tasks_task_id', table_name='agent_tasks')
    op.drop_table('agent_tasks')
    
    op.drop_index('idx_agents_status_active', table_name='agents')
    op.drop_index('ix_agents_last_active_time', table_name='agents')
    op.drop_index('ix_agents_current_task_id', table_name='agents')
    op.drop_index('ix_agents_phone_number', table_name='agents')
    op.drop_index('ix_agents_status', table_name='agents')
    op.drop_index('ix_agents_agent_id', table_name='agents')
    op.drop_table('agents')
