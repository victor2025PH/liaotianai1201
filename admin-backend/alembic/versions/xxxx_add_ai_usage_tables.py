"""add_ai_usage_tables

Revision ID: xxxx_add_ai_usage
Revises: 2ef648e89af4
Create Date: 2025-12-23 17:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision = 'xxxx_add_ai_usage'
down_revision = '2ef648e89af4'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 创建 ai_usage_logs 表
    op.create_table('ai_usage_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('request_id', sa.String(length=100), nullable=False),
        sa.Column('session_id', sa.String(length=100), nullable=True),  # 会话 ID
        sa.Column('user_ip', sa.String(length=50), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('site_domain', sa.String(length=200), nullable=True),
        sa.Column('provider', sa.String(length=50), nullable=False),
        sa.Column('model', sa.String(length=100), nullable=False),
        sa.Column('prompt_tokens', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('completion_tokens', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('total_tokens', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('estimated_cost', sa.Float(), nullable=True, server_default='0.0'),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='success'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id')
    )
    
    # 创建索引
    op.create_index('ix_ai_usage_logs_request_id', 'ai_usage_logs', ['request_id'], unique=True)
    op.create_index('ix_ai_usage_logs_session_id', 'ai_usage_logs', ['session_id'], unique=False)  # 会话 ID 索引
    op.create_index('ix_ai_usage_logs_user_ip', 'ai_usage_logs', ['user_ip'], unique=False)
    op.create_index('ix_ai_usage_logs_site_domain', 'ai_usage_logs', ['site_domain'], unique=False)
    op.create_index('ix_ai_usage_logs_provider', 'ai_usage_logs', ['provider'], unique=False)
    op.create_index('ix_ai_usage_logs_created_at', 'ai_usage_logs', ['created_at'], unique=False)
    op.create_index('idx_provider_created', 'ai_usage_logs', ['provider', 'created_at'], unique=False)
    op.create_index('idx_site_created', 'ai_usage_logs', ['site_domain', 'created_at'], unique=False)
    op.create_index('idx_session_created', 'ai_usage_logs', ['session_id', 'created_at'], unique=False)  # 会话统计索引
    
    # 创建 ai_usage_stats 表
    op.create_table('ai_usage_stats',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('stat_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('provider', sa.String(length=50), nullable=False),
        sa.Column('model', sa.String(length=100), nullable=False),
        sa.Column('site_domain', sa.String(length=200), nullable=True),
        sa.Column('total_requests', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('success_requests', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('error_requests', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_prompt_tokens', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_completion_tokens', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_tokens', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_cost', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id')
    )
    
    # 创建索引
    op.create_index('ix_ai_usage_stats_stat_date', 'ai_usage_stats', ['stat_date'], unique=False)
    op.create_index('ix_ai_usage_stats_provider', 'ai_usage_stats', ['provider'], unique=False)
    op.create_index('ix_ai_usage_stats_site_domain', 'ai_usage_stats', ['site_domain'], unique=False)
    # 唯一索引：确保每天每个 provider+model+site 只有一条记录
    op.create_index('idx_unique_stat', 'ai_usage_stats', ['stat_date', 'provider', 'model', 'site_domain'], unique=True)


def downgrade() -> None:
    # 删除索引
    op.drop_index('idx_unique_stat', table_name='ai_usage_stats')
    op.drop_index('ix_ai_usage_stats_site_domain', table_name='ai_usage_stats')
    op.drop_index('ix_ai_usage_stats_provider', table_name='ai_usage_stats')
    op.drop_index('ix_ai_usage_stats_stat_date', table_name='ai_usage_stats')
    
    op.drop_index('idx_site_created', table_name='ai_usage_logs')
    op.drop_index('idx_provider_created', table_name='ai_usage_logs')
    op.drop_index('ix_ai_usage_logs_created_at', table_name='ai_usage_logs')
    op.drop_index('ix_ai_usage_logs_provider', table_name='ai_usage_logs')
    op.drop_index('ix_ai_usage_logs_site_domain', table_name='ai_usage_logs')
    op.drop_index('ix_ai_usage_logs_user_ip', table_name='ai_usage_logs')
    op.drop_index('ix_ai_usage_logs_request_id', table_name='ai_usage_logs')
    
    # 删除表
    op.drop_table('ai_usage_stats')
    op.drop_table('ai_usage_logs')

