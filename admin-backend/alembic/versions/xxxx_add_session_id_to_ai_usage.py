"""add_session_id_to_ai_usage

Revision ID: xxxx_add_session_id
Revises: xxxx_add_ai_usage
Create Date: 2025-12-23 18:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'xxxx_add_session_id'
down_revision = 'xxxx_add_ai_usage'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 添加 session_id 字段到 ai_usage_logs 表
    op.add_column('ai_usage_logs', 
        sa.Column('session_id', sa.String(length=100), nullable=True)
    )
    
    # 创建 session_id 索引
    op.create_index('ix_ai_usage_logs_session_id', 'ai_usage_logs', ['session_id'], unique=False)
    
    # 创建复合索引用于会话统计
    op.create_index('idx_session_created', 'ai_usage_logs', ['session_id', 'created_at'], unique=False)


def downgrade() -> None:
    # 删除索引
    op.drop_index('idx_session_created', table_name='ai_usage_logs')
    op.drop_index('ix_ai_usage_logs_session_id', table_name='ai_usage_logs')
    
    # 删除 session_id 字段
    op.drop_column('ai_usage_logs', 'session_id')

