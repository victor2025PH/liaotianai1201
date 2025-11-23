"""create group ai tables

Revision ID: 001_group_ai
Revises: 
Create Date: 2024-12-19 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001_group_ai'
down_revision = '000_initial_base'
branch_labels = None
depends_on = None


def upgrade():
    # 創建群組 AI 賬號表
    op.create_table(
        'group_ai_accounts',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('account_id', sa.String(100), nullable=False, unique=True),
        sa.Column('session_file', sa.String(500), nullable=False),
        sa.Column('script_id', sa.String(100), nullable=False),
        sa.Column('group_ids', sa.JSON, nullable=False),
        sa.Column('active', sa.Boolean, nullable=False, default=True),
        sa.Column('reply_rate', sa.Float, nullable=False, default=0.3),
        sa.Column('redpacket_enabled', sa.Boolean, nullable=False, default=True),
        sa.Column('redpacket_probability', sa.Float, nullable=False, default=0.5),
        sa.Column('max_replies_per_hour', sa.Integer, nullable=False, default=50),
        sa.Column('min_reply_interval', sa.Integer, nullable=False, default=3),
        sa.Column('config', sa.JSON, nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index('ix_group_ai_accounts_account_id', 'group_ai_accounts', ['account_id'])
    op.create_index('ix_group_ai_accounts_script_id', 'group_ai_accounts', ['script_id'])
    
    # 創建群組 AI 劇本表
    op.create_table(
        'group_ai_scripts',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('script_id', sa.String(100), nullable=False, unique=True),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('version', sa.String(20), nullable=False),
        sa.Column('yaml_content', sa.Text, nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index('ix_group_ai_scripts_script_id', 'group_ai_scripts', ['script_id'])
    
    # 創建群組 AI 對話歷史表
    op.create_table(
        'group_ai_dialogue_history',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('account_id', sa.String(100), nullable=False),
        sa.Column('group_id', sa.BigInteger, nullable=False),
        sa.Column('message_id', sa.BigInteger, nullable=False),
        sa.Column('user_id', sa.BigInteger, nullable=False),
        sa.Column('message_text', sa.Text, nullable=True),
        sa.Column('reply_text', sa.Text, nullable=True),
        sa.Column('timestamp', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('context_snapshot', sa.JSON, nullable=True),
    )
    op.create_index('ix_group_ai_dialogue_history_account_id', 'group_ai_dialogue_history', ['account_id'])
    op.create_index('ix_group_ai_dialogue_history_group_id', 'group_ai_dialogue_history', ['group_id'])
    op.create_index('ix_group_ai_dialogue_history_user_id', 'group_ai_dialogue_history', ['user_id'])
    op.create_index('ix_group_ai_dialogue_history_timestamp', 'group_ai_dialogue_history', ['timestamp'])
    
    # 創建群組 AI 紅包日誌表
    op.create_table(
        'group_ai_redpacket_logs',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('account_id', sa.String(100), nullable=False),
        sa.Column('group_id', sa.BigInteger, nullable=False),
        sa.Column('redpacket_id', sa.String(100), nullable=False),
        sa.Column('amount', sa.Float, nullable=True),
        sa.Column('success', sa.Boolean, nullable=False),
        sa.Column('timestamp', sa.DateTime, nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_group_ai_redpacket_logs_account_id', 'group_ai_redpacket_logs', ['account_id'])
    op.create_index('ix_group_ai_redpacket_logs_group_id', 'group_ai_redpacket_logs', ['group_id'])
    op.create_index('ix_group_ai_redpacket_logs_redpacket_id', 'group_ai_redpacket_logs', ['redpacket_id'])
    op.create_index('ix_group_ai_redpacket_logs_timestamp', 'group_ai_redpacket_logs', ['timestamp'])
    
    # 創建群組 AI 指標表
    op.create_table(
        'group_ai_metrics',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('account_id', sa.String(100), nullable=True),
        sa.Column('metric_type', sa.String(50), nullable=False),
        sa.Column('metric_value', sa.Float, nullable=False),
        sa.Column('timestamp', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('extra_data', sa.JSON, nullable=True),
    )
    op.create_index('ix_group_ai_metrics_account_id', 'group_ai_metrics', ['account_id'])
    op.create_index('ix_group_ai_metrics_metric_type', 'group_ai_metrics', ['metric_type'])
    op.create_index('ix_group_ai_metrics_timestamp', 'group_ai_metrics', ['timestamp'])


def downgrade():
    op.drop_index('ix_group_ai_metrics_timestamp', table_name='group_ai_metrics')
    op.drop_index('ix_group_ai_metrics_metric_type', table_name='group_ai_metrics')
    op.drop_index('ix_group_ai_metrics_account_id', table_name='group_ai_metrics')
    op.drop_table('group_ai_metrics')
    
    op.drop_index('ix_group_ai_redpacket_logs_timestamp', table_name='group_ai_redpacket_logs')
    op.drop_index('ix_group_ai_redpacket_logs_redpacket_id', table_name='group_ai_redpacket_logs')
    op.drop_index('ix_group_ai_redpacket_logs_group_id', table_name='group_ai_redpacket_logs')
    op.drop_index('ix_group_ai_redpacket_logs_account_id', table_name='group_ai_redpacket_logs')
    op.drop_table('group_ai_redpacket_logs')
    
    op.drop_index('ix_group_ai_dialogue_history_timestamp', table_name='group_ai_dialogue_history')
    op.drop_index('ix_group_ai_dialogue_history_user_id', table_name='group_ai_dialogue_history')
    op.drop_index('ix_group_ai_dialogue_history_group_id', table_name='group_ai_dialogue_history')
    op.drop_index('ix_group_ai_dialogue_history_account_id', table_name='group_ai_dialogue_history')
    op.drop_table('group_ai_dialogue_history')
    
    op.drop_index('ix_group_ai_scripts_script_id', table_name='group_ai_scripts')
    op.drop_table('group_ai_scripts')
    
    op.drop_index('ix_group_ai_accounts_script_id', table_name='group_ai_accounts')
    op.drop_index('ix_group_ai_accounts_account_id', table_name='group_ai_accounts')
    op.drop_table('group_ai_accounts')

