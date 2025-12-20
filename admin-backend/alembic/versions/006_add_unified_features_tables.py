"""添加統一功能數據表（關鍵詞觸發、定時消息、群組管理等）

Revision ID: 006_unified_features
Revises: ccaf23c9b58a
Create Date: 2025-12-21 01:11:54.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision = '006_unified_features'
down_revision = 'ccaf23c9b58a'  # 修改為最新的遷移版本
branch_labels = None
depends_on = None


def upgrade():
    # 創建關鍵詞觸發規則表
    op.create_table(
        'keyword_trigger_rules',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('rule_id', sa.String(100), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('enabled', sa.Boolean(), nullable=False),
        sa.Column('keywords', sa.JSON(), nullable=False),
        sa.Column('pattern', sa.Text(), nullable=True),
        sa.Column('match_type', sa.String(20), nullable=False),
        sa.Column('case_sensitive', sa.Boolean(), nullable=False),
        sa.Column('sender_ids', sa.JSON(), nullable=True),
        sa.Column('sender_blacklist', sa.JSON(), nullable=True),
        sa.Column('time_range_start', sa.String(10), nullable=True),
        sa.Column('time_range_end', sa.String(10), nullable=True),
        sa.Column('weekdays', sa.JSON(), nullable=True),
        sa.Column('group_ids', sa.JSON(), nullable=True),
        sa.Column('message_length_min', sa.Integer(), nullable=True),
        sa.Column('message_length_max', sa.Integer(), nullable=True),
        sa.Column('condition_logic', sa.String(10), nullable=False),
        sa.Column('actions', sa.JSON(), nullable=False),
        sa.Column('priority', sa.Integer(), nullable=False),
        sa.Column('context_window', sa.Integer(), nullable=False),
        sa.Column('trigger_count', sa.Integer(), nullable=False),
        sa.Column('last_triggered_at', sa.DateTime(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_by', sa.String(100), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_keyword_trigger_rules_rule_id', 'keyword_trigger_rules', ['rule_id'], unique=True)
    op.create_index('ix_keyword_trigger_rules_enabled', 'keyword_trigger_rules', ['enabled'])
    op.create_index('ix_keyword_trigger_rules_priority', 'keyword_trigger_rules', ['priority'])
    op.create_index('idx_keyword_trigger_enabled_priority', 'keyword_trigger_rules', ['enabled', 'priority'])
    
    # 創建定時消息任務表
    op.create_table(
        'scheduled_message_tasks',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('task_id', sa.String(100), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('enabled', sa.Boolean(), nullable=False),
        sa.Column('schedule_type', sa.String(20), nullable=False),
        sa.Column('cron_expression', sa.String(100), nullable=True),
        sa.Column('interval_seconds', sa.Integer(), nullable=True),
        sa.Column('start_time', sa.String(10), nullable=True),
        sa.Column('end_time', sa.String(10), nullable=True),
        sa.Column('timezone', sa.String(50), nullable=False),
        sa.Column('condition', sa.Text(), nullable=True),
        sa.Column('check_interval', sa.Integer(), nullable=False),
        sa.Column('groups', sa.JSON(), nullable=False),
        sa.Column('accounts', sa.JSON(), nullable=False),
        sa.Column('rotation', sa.Boolean(), nullable=False),
        sa.Column('rotation_strategy', sa.String(20), nullable=False),
        sa.Column('message_template', sa.Text(), nullable=False),
        sa.Column('template_variables', sa.JSON(), nullable=True),
        sa.Column('media_path', sa.String(500), nullable=True),
        sa.Column('delay_min', sa.Integer(), nullable=False),
        sa.Column('delay_max', sa.Integer(), nullable=False),
        sa.Column('retry_times', sa.Integer(), nullable=False),
        sa.Column('retry_interval', sa.Integer(), nullable=False),
        sa.Column('last_run_at', sa.DateTime(), nullable=True),
        sa.Column('next_run_at', sa.DateTime(), nullable=True),
        sa.Column('run_count', sa.Integer(), nullable=False),
        sa.Column('success_count', sa.Integer(), nullable=False),
        sa.Column('failure_count', sa.Integer(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_by', sa.String(100), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_scheduled_message_tasks_task_id', 'scheduled_message_tasks', ['task_id'], unique=True)
    op.create_index('ix_scheduled_message_tasks_enabled', 'scheduled_message_tasks', ['enabled'])
    op.create_index('ix_scheduled_message_tasks_next_run_at', 'scheduled_message_tasks', ['next_run_at'])
    op.create_index('idx_scheduled_task_enabled_next_run', 'scheduled_message_tasks', ['enabled', 'next_run_at'])
    
    # 創建定時消息執行日誌表
    op.create_table(
        'scheduled_message_logs',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('task_id', sa.String(100), nullable=False),
        sa.Column('account_id', sa.String(100), nullable=False),
        sa.Column('group_id', sa.BigInteger(), nullable=False),
        sa.Column('success', sa.Boolean(), nullable=False),
        sa.Column('message_sent', sa.Text(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('executed_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_scheduled_message_logs_task_id', 'scheduled_message_logs', ['task_id'])
    op.create_index('ix_scheduled_message_logs_account_id', 'scheduled_message_logs', ['account_id'])
    op.create_index('ix_scheduled_message_logs_group_id', 'scheduled_message_logs', ['group_id'])
    op.create_index('ix_scheduled_message_logs_success', 'scheduled_message_logs', ['success'])
    op.create_index('ix_scheduled_message_logs_executed_at', 'scheduled_message_logs', ['executed_at'])
    op.create_index('idx_scheduled_log_task_executed', 'scheduled_message_logs', ['task_id', 'executed_at'])
    
    # 創建群組加入配置表
    op.create_table(
        'group_join_configs',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('config_id', sa.String(100), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('enabled', sa.Boolean(), nullable=False),
        sa.Column('join_type', sa.String(20), nullable=False),
        sa.Column('invite_link', sa.String(500), nullable=True),
        sa.Column('username', sa.String(100), nullable=True),
        sa.Column('group_id', sa.BigInteger(), nullable=True),
        sa.Column('search_keywords', sa.JSON(), nullable=True),
        sa.Column('account_ids', sa.JSON(), nullable=False),
        sa.Column('min_members', sa.Integer(), nullable=True),
        sa.Column('max_members', sa.Integer(), nullable=True),
        sa.Column('group_types', sa.JSON(), nullable=True),
        sa.Column('post_join_actions', sa.JSON(), nullable=True),
        sa.Column('priority', sa.Integer(), nullable=False),
        sa.Column('join_count', sa.Integer(), nullable=False),
        sa.Column('last_joined_at', sa.DateTime(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_by', sa.String(100), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_group_join_configs_config_id', 'group_join_configs', ['config_id'], unique=True)
    op.create_index('ix_group_join_configs_enabled', 'group_join_configs', ['enabled'])
    op.create_index('ix_group_join_configs_group_id', 'group_join_configs', ['group_id'])
    op.create_index('ix_group_join_configs_priority', 'group_join_configs', ['priority'])
    op.create_index('idx_group_join_enabled_priority', 'group_join_configs', ['enabled', 'priority'])
    
    # 創建群組加入日誌表
    op.create_table(
        'group_join_logs',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('config_id', sa.String(100), nullable=False),
        sa.Column('account_id', sa.String(100), nullable=False),
        sa.Column('group_id', sa.BigInteger(), nullable=False),
        sa.Column('success', sa.Boolean(), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('joined_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_group_join_logs_config_id', 'group_join_logs', ['config_id'])
    op.create_index('ix_group_join_logs_account_id', 'group_join_logs', ['account_id'])
    op.create_index('ix_group_join_logs_group_id', 'group_join_logs', ['group_id'])
    op.create_index('ix_group_join_logs_success', 'group_join_logs', ['success'])
    op.create_index('ix_group_join_logs_joined_at', 'group_join_logs', ['joined_at'])
    op.create_index('idx_group_join_log_config_joined', 'group_join_logs', ['config_id', 'joined_at'])
    
    # 創建統一配置表
    op.create_table(
        'unified_configs',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('config_id', sa.String(100), nullable=False),
        sa.Column('config_level', sa.String(20), nullable=False),
        sa.Column('level_id', sa.String(100), nullable=True),
        sa.Column('chat_config', sa.JSON(), nullable=True),
        sa.Column('redpacket_config', sa.JSON(), nullable=True),
        sa.Column('keyword_config', sa.JSON(), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_by', sa.String(100), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_unified_configs_config_id', 'unified_configs', ['config_id'], unique=True)
    op.create_index('ix_unified_configs_config_level', 'unified_configs', ['config_level'])
    op.create_index('ix_unified_configs_level_id', 'unified_configs', ['level_id'])
    op.create_index('idx_unified_config_level_id', 'unified_configs', ['config_level', 'level_id'])
    
    # 創建群組活動指標表
    op.create_table(
        'group_activity_metrics',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('group_id', sa.BigInteger(), nullable=False),
        sa.Column('message_count_24h', sa.Integer(), nullable=False),
        sa.Column('active_members_24h', sa.Integer(), nullable=False),
        sa.Column('new_members_24h', sa.Integer(), nullable=False),
        sa.Column('redpacket_count_24h', sa.Integer(), nullable=False),
        sa.Column('last_activity', sa.DateTime(), nullable=True),
        sa.Column('health_score', sa.Float(), nullable=False),
        sa.Column('recorded_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_group_activity_metrics_group_id', 'group_activity_metrics', ['group_id'])
    op.create_index('ix_group_activity_metrics_recorded_at', 'group_activity_metrics', ['recorded_at'])
    op.create_index('idx_group_metrics_group_recorded', 'group_activity_metrics', ['group_id', 'recorded_at'])


def downgrade():
    # 刪除表（按相反順序）
    op.drop_index('idx_group_metrics_group_recorded', table_name='group_activity_metrics')
    op.drop_index('ix_group_activity_metrics_recorded_at', table_name='group_activity_metrics')
    op.drop_index('ix_group_activity_metrics_group_id', table_name='group_activity_metrics')
    op.drop_table('group_activity_metrics')
    
    op.drop_index('idx_unified_config_level_id', table_name='unified_configs')
    op.drop_index('ix_unified_configs_level_id', table_name='unified_configs')
    op.drop_index('ix_unified_configs_config_level', table_name='unified_configs')
    op.drop_index('ix_unified_configs_config_id', table_name='unified_configs')
    op.drop_table('unified_configs')
    
    op.drop_index('idx_group_join_log_config_joined', table_name='group_join_logs')
    op.drop_index('ix_group_join_logs_joined_at', table_name='group_join_logs')
    op.drop_index('ix_group_join_logs_success', table_name='group_join_logs')
    op.drop_index('ix_group_join_logs_group_id', table_name='group_join_logs')
    op.drop_index('ix_group_join_logs_account_id', table_name='group_join_logs')
    op.drop_index('ix_group_join_logs_config_id', table_name='group_join_logs')
    op.drop_table('group_join_logs')
    
    op.drop_index('idx_group_join_enabled_priority', table_name='group_join_configs')
    op.drop_index('ix_group_join_configs_priority', table_name='group_join_configs')
    op.drop_index('ix_group_join_configs_group_id', table_name='group_join_configs')
    op.drop_index('ix_group_join_configs_enabled', table_name='group_join_configs')
    op.drop_index('ix_group_join_configs_config_id', table_name='group_join_configs')
    op.drop_table('group_join_configs')
    
    op.drop_index('idx_scheduled_log_task_executed', table_name='scheduled_message_logs')
    op.drop_index('ix_scheduled_message_logs_executed_at', table_name='scheduled_message_logs')
    op.drop_index('ix_scheduled_message_logs_success', table_name='scheduled_message_logs')
    op.drop_index('ix_scheduled_message_logs_group_id', table_name='scheduled_message_logs')
    op.drop_index('ix_scheduled_message_logs_account_id', table_name='scheduled_message_logs')
    op.drop_index('ix_scheduled_message_logs_task_id', table_name='scheduled_message_logs')
    op.drop_table('scheduled_message_logs')
    
    op.drop_index('idx_scheduled_task_enabled_next_run', table_name='scheduled_message_tasks')
    op.drop_index('ix_scheduled_message_tasks_next_run_at', table_name='scheduled_message_tasks')
    op.drop_index('ix_scheduled_message_tasks_enabled', table_name='scheduled_message_tasks')
    op.drop_index('ix_scheduled_message_tasks_task_id', table_name='scheduled_message_tasks')
    op.drop_table('scheduled_message_tasks')
    
    op.drop_index('idx_keyword_trigger_enabled_priority', table_name='keyword_trigger_rules')
    op.drop_index('ix_keyword_trigger_rules_priority', table_name='keyword_trigger_rules')
    op.drop_index('ix_keyword_trigger_rules_enabled', table_name='keyword_trigger_rules')
    op.drop_index('ix_keyword_trigger_rules_rule_id', table_name='keyword_trigger_rules')
    op.drop_table('keyword_trigger_rules')
