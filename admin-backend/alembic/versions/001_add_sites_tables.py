"""add sites tables

Revision ID: 001_add_sites_tables
Revises: 000_initial_base_tables
Create Date: 2025-12-24 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision = '001_add_sites_tables'
down_revision = 'xxxx_add_session_id'  # 基于最新的 AI usage 迁移（添加 session_id）
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    inspector = inspect(conn)

    # 创建站点表
    if not inspector.has_table('sites'):
        op.create_table(
            'sites',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('name', sa.String(length=100), nullable=False),
            sa.Column('url', sa.String(length=255), nullable=False),
            sa.Column('site_type', sa.String(length=50), nullable=False),
            sa.Column('status', sa.String(length=20), nullable=True),
            sa.Column('config', sa.JSON(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index('ix_sites_id', 'sites', ['id'], unique=False)
        op.create_index('ix_sites_site_type', 'sites', ['site_type'], unique=False)
    else:
        print("表 'sites' 已存在，跳过创建。")

    # 创建访问记录表
    if not inspector.has_table('site_visits'):
        op.create_table(
            'site_visits',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('site_id', sa.Integer(), nullable=False),
            sa.Column('ip_address', sa.String(length=45), nullable=True),
            sa.Column('user_agent', sa.Text(), nullable=True),
            sa.Column('referer', sa.String(length=255), nullable=True),
            sa.Column('page_path', sa.String(length=255), nullable=True),
            sa.Column('session_id', sa.String(length=100), nullable=True),
            sa.Column('visit_duration', sa.Integer(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['site_id'], ['sites.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index('ix_site_visits_id', 'site_visits', ['id'], unique=False)
        op.create_index('ix_site_visits_site_id', 'site_visits', ['site_id'], unique=False)
        op.create_index('ix_site_visits_session_id', 'site_visits', ['session_id'], unique=False)
        op.create_index('ix_site_visits_site_id_created_at', 'site_visits', ['site_id', 'created_at'], unique=False)
    else:
        print("表 'site_visits' 已存在，跳过创建。")

    # 创建 AI 对话记录表
    if not inspector.has_table('ai_conversations'):
        op.create_table(
            'ai_conversations',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('site_id', sa.Integer(), nullable=False),
            sa.Column('session_id', sa.String(length=100), nullable=True),
            sa.Column('user_message', sa.Text(), nullable=True),
            sa.Column('ai_response', sa.Text(), nullable=True),
            sa.Column('ai_provider', sa.String(length=20), nullable=True),
            sa.Column('response_time', sa.Integer(), nullable=True),
            sa.Column('tokens_used', sa.Integer(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['site_id'], ['sites.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index('ix_ai_conversations_id', 'ai_conversations', ['id'], unique=False)
        op.create_index('ix_ai_conversations_site_id', 'ai_conversations', ['site_id'], unique=False)
        op.create_index('ix_ai_conversations_session_id', 'ai_conversations', ['session_id'], unique=False)
        op.create_index('ix_ai_conversations_site_id_created_at', 'ai_conversations', ['site_id', 'created_at'], unique=False)
    else:
        print("表 'ai_conversations' 已存在，跳过创建。")

    # 创建联系表单表
    if not inspector.has_table('contact_forms'):
        op.create_table(
            'contact_forms',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('site_id', sa.Integer(), nullable=False),
            sa.Column('contact_type', sa.String(length=20), nullable=True),
            sa.Column('contact_value', sa.String(length=255), nullable=True),
            sa.Column('message', sa.Text(), nullable=True),
            sa.Column('status', sa.String(length=20), nullable=True),
            sa.Column('notes', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['site_id'], ['sites.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index('ix_contact_forms_id', 'contact_forms', ['id'], unique=False)
        op.create_index('ix_contact_forms_site_id', 'contact_forms', ['site_id'], unique=False)
        op.create_index('ix_contact_forms_status', 'contact_forms', ['status'], unique=False)
        op.create_index('ix_contact_forms_site_id_created_at', 'contact_forms', ['site_id', 'created_at'], unique=False)
    else:
        print("表 'contact_forms' 已存在，跳过创建。")

    # 创建站点统计表
    if not inspector.has_table('site_analytics'):
        op.create_table(
            'site_analytics',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('site_id', sa.Integer(), nullable=False),
            sa.Column('date', sa.DateTime(), nullable=False),
            sa.Column('pv', sa.Integer(), nullable=True),
            sa.Column('uv', sa.Integer(), nullable=True),
            sa.Column('conversations', sa.Integer(), nullable=True),
            sa.Column('contacts', sa.Integer(), nullable=True),
            sa.Column('avg_session_duration', sa.Integer(), nullable=True),
            sa.Column('bounce_rate', sa.Integer(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['site_id'], ['sites.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('site_id', 'date', name='ix_site_analytics_site_id_date')
        )
        op.create_index('ix_site_analytics_id', 'site_analytics', ['id'], unique=False)
        op.create_index('ix_site_analytics_site_id', 'site_analytics', ['site_id'], unique=False)
        op.create_index('ix_site_analytics_date', 'site_analytics', ['date'], unique=False)
    else:
        print("表 'site_analytics' 已存在，跳过创建。")


def downgrade():
    conn = op.get_bind()
    inspector = inspect(conn)
    
    # 删除站点统计表（如果存在）
    if inspector.has_table('site_analytics'):
        # 检查索引是否存在再删除
        indexes = [idx['name'] for idx in inspector.get_indexes('site_analytics')]
        if 'ix_site_analytics_date' in indexes:
            op.drop_index('ix_site_analytics_date', table_name='site_analytics')
        if 'ix_site_analytics_site_id' in indexes:
            op.drop_index('ix_site_analytics_site_id', table_name='site_analytics')
        if 'ix_site_analytics_id' in indexes:
            op.drop_index('ix_site_analytics_id', table_name='site_analytics')
        op.drop_table('site_analytics')
    
    # 删除联系表单表（如果存在）
    if inspector.has_table('contact_forms'):
        indexes = [idx['name'] for idx in inspector.get_indexes('contact_forms')]
        if 'ix_contact_forms_site_id_created_at' in indexes:
            op.drop_index('ix_contact_forms_site_id_created_at', table_name='contact_forms')
        if 'ix_contact_forms_status' in indexes:
            op.drop_index('ix_contact_forms_status', table_name='contact_forms')
        if 'ix_contact_forms_site_id' in indexes:
            op.drop_index('ix_contact_forms_site_id', table_name='contact_forms')
        if 'ix_contact_forms_id' in indexes:
            op.drop_index('ix_contact_forms_id', table_name='contact_forms')
        op.drop_table('contact_forms')
    
    # 删除 AI 对话记录表（如果存在）
    if inspector.has_table('ai_conversations'):
        indexes = [idx['name'] for idx in inspector.get_indexes('ai_conversations')]
        if 'ix_ai_conversations_site_id_created_at' in indexes:
            op.drop_index('ix_ai_conversations_site_id_created_at', table_name='ai_conversations')
        if 'ix_ai_conversations_session_id' in indexes:
            op.drop_index('ix_ai_conversations_session_id', table_name='ai_conversations')
        if 'ix_ai_conversations_site_id' in indexes:
            op.drop_index('ix_ai_conversations_site_id', table_name='ai_conversations')
        if 'ix_ai_conversations_id' in indexes:
            op.drop_index('ix_ai_conversations_id', table_name='ai_conversations')
        op.drop_table('ai_conversations')
    
    # 删除访问记录表（如果存在）
    if inspector.has_table('site_visits'):
        indexes = [idx['name'] for idx in inspector.get_indexes('site_visits')]
        if 'ix_site_visits_site_id_created_at' in indexes:
            op.drop_index('ix_site_visits_site_id_created_at', table_name='site_visits')
        if 'ix_site_visits_session_id' in indexes:
            op.drop_index('ix_site_visits_session_id', table_name='site_visits')
        if 'ix_site_visits_site_id' in indexes:
            op.drop_index('ix_site_visits_site_id', table_name='site_visits')
        if 'ix_site_visits_id' in indexes:
            op.drop_index('ix_site_visits_id', table_name='site_visits')
        op.drop_table('site_visits')
    
    # 删除站点表（如果存在）
    if inspector.has_table('sites'):
        indexes = [idx['name'] for idx in inspector.get_indexes('sites')]
        if 'ix_sites_site_type' in indexes:
            op.drop_index('ix_sites_site_type', table_name='sites')
        if 'ix_sites_id' in indexes:
            op.drop_index('ix_sites_id', table_name='sites')
        op.drop_table('sites')

