"""add_automation_task_dependencies_and_notifications

Revision ID: ccaf23c9b58a
Revises: cb4ad7ca2507
Create Date: 2025-11-18 18:39:05.776448

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ccaf23c9b58a'
down_revision = 'cb4ad7ca2507'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 檢查表是否存在，如果不存在則先創建（用於通過 init_db_tables.py 創建表的情況）
    from sqlalchemy import inspect
    from alembic import context
    
    conn = context.get_bind()
    inspector = inspect(conn)
    tables = inspector.get_table_names()
    
    if 'group_ai_automation_tasks' not in tables:
        # 如果表不存在，先創建表（基本結構）
        op.create_table(
            'group_ai_automation_tasks',
            sa.Column('id', sa.String(36), primary_key=True),
            sa.Column('name', sa.String(200), nullable=False),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('task_type', sa.String(50), nullable=False),
            sa.Column('task_action', sa.String(100), nullable=False),
            sa.Column('schedule_config', sa.JSON(), nullable=True),
            sa.Column('trigger_config', sa.JSON(), nullable=True),
            sa.Column('action_config', sa.JSON(), nullable=False),
            sa.Column('enabled', sa.Boolean(), nullable=False, server_default='1'),
            sa.Column('last_run_at', sa.DateTime(), nullable=True),
            sa.Column('next_run_at', sa.DateTime(), nullable=True),
            sa.Column('run_count', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('success_count', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('failure_count', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('last_result', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.Column('created_by', sa.String(100), nullable=True),
            # 新字段
            sa.Column('dependent_tasks', sa.JSON(), nullable=True),
            sa.Column('notify_on_success', sa.Boolean(), nullable=False, server_default='0'),
            sa.Column('notify_on_failure', sa.Boolean(), nullable=False, server_default='1'),
            sa.Column('notify_recipients', sa.JSON(), nullable=True),
        )
        op.create_index('ix_group_ai_automation_tasks_name', 'group_ai_automation_tasks', ['name'])
        op.create_index('ix_group_ai_automation_tasks_task_type', 'group_ai_automation_tasks', ['task_type'])
        op.create_index('ix_group_ai_automation_tasks_enabled', 'group_ai_automation_tasks', ['enabled'])
        op.create_index('ix_group_ai_automation_tasks_next_run_at', 'group_ai_automation_tasks', ['next_run_at'])
    else:
        # 表已存在，只添加新字段
        # 檢查字段是否已存在
        columns = [col['name'] for col in inspector.get_columns('group_ai_automation_tasks')]
        
        if 'dependent_tasks' not in columns:
            op.add_column('group_ai_automation_tasks', 
                          sa.Column('dependent_tasks', sa.JSON(), nullable=True))
        
        if 'notify_on_success' not in columns:
            op.add_column('group_ai_automation_tasks',
                          sa.Column('notify_on_success', sa.Boolean(), nullable=False, server_default='0'))
        
        if 'notify_on_failure' not in columns:
            op.add_column('group_ai_automation_tasks',
                          sa.Column('notify_on_failure', sa.Boolean(), nullable=False, server_default='1'))
        
        if 'notify_recipients' not in columns:
            op.add_column('group_ai_automation_tasks',
                          sa.Column('notify_recipients', sa.JSON(), nullable=True))


def downgrade() -> None:
    # 刪除通知配置字段
    op.drop_column('group_ai_automation_tasks', 'notify_recipients')
    op.drop_column('group_ai_automation_tasks', 'notify_on_failure')
    op.drop_column('group_ai_automation_tasks', 'notify_on_success')
    
    # 刪除任務依賴字段
    op.drop_column('group_ai_automation_tasks', 'dependent_tasks')

