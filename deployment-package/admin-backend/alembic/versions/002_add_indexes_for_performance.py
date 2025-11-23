"""添加數據庫索引優化查詢性能

Revision ID: 002_add_indexes
Revises: 001_group_ai
Create Date: 2025-01-07
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = '002_add_indexes'
down_revision = '001_group_ai'
branch_labels = None
depends_on = None


def upgrade():
    # 檢查表是否存在（兼容性處理）
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    tables = inspector.get_table_names()
    
    # 群組 AI 賬號表索引
    if 'group_ai_accounts' in tables:
        # 狀態索引（用於過濾查詢）
        try:
            op.create_index(
                'idx_group_ai_account_active',
                'group_ai_accounts',
                ['active'],
                unique=False,
                if_not_exists=True
            )
        except Exception:
            pass  # 索引可能已存在
        
        # 創建時間索引（用於排序）
        try:
            op.create_index(
                'idx_group_ai_account_created',
                'group_ai_accounts',
                ['created_at'],
                unique=False,
                if_not_exists=True
            )
        except Exception:
            pass
        
        # 更新時間索引
        try:
            op.create_index(
                'idx_group_ai_account_updated',
                'group_ai_accounts',
                ['updated_at'],
                unique=False,
                if_not_exists=True
            )
        except Exception:
            pass
    
    # 群組 AI 劇本表索引
    if 'group_ai_scripts' in tables:
        # 版本索引（用於查詢特定版本）
        try:
            op.create_index(
                'idx_group_ai_script_version',
                'group_ai_scripts',
                ['version'],
                unique=False,
                if_not_exists=True
            )
        except Exception:
            pass
        
        # 創建時間索引
        try:
            op.create_index(
                'idx_group_ai_script_created',
                'group_ai_scripts',
                ['created_at'],
                unique=False,
                if_not_exists=True
            )
        except Exception:
            pass
    
    # 群組 AI 指標表複合索引
    if 'group_ai_metrics' in tables:
        # 賬號ID和時間戳複合索引（常用查詢模式）
        try:
            op.create_index(
                'idx_group_ai_metrics_account_time',
                'group_ai_metrics',
                ['account_id', 'timestamp'],
                unique=False,
                if_not_exists=True
            )
        except Exception:
            pass
        
        # 指標類型和時間戳複合索引
        try:
            op.create_index(
                'idx_group_ai_metrics_type_time',
                'group_ai_metrics',
                ['metric_type', 'timestamp'],
                unique=False,
                if_not_exists=True
            )
        except Exception:
            pass
    
    # 對話歷史表複合索引
    if 'group_ai_dialogue_history' in tables:
        # 賬號ID和群組ID複合索引
        try:
            op.create_index(
                'idx_group_ai_dialogue_account_group',
                'group_ai_dialogue_history',
                ['account_id', 'group_id'],
                unique=False,
                if_not_exists=True
            )
        except Exception:
            pass


def downgrade():
    # 刪除索引（如果存在）
    tables_to_check = [
        'group_ai_accounts',
        'group_ai_scripts',
        'group_ai_metrics',
        'group_ai_dialogue_history'
    ]
    
    indexes_to_drop = [
        ('group_ai_accounts', 'idx_group_ai_account_active'),
        ('group_ai_accounts', 'idx_group_ai_account_created'),
        ('group_ai_accounts', 'idx_group_ai_account_updated'),
        ('group_ai_scripts', 'idx_group_ai_script_version'),
        ('group_ai_scripts', 'idx_group_ai_script_created'),
        ('group_ai_metrics', 'idx_group_ai_metrics_account_time'),
        ('group_ai_metrics', 'idx_group_ai_metrics_type_time'),
        ('group_ai_dialogue_history', 'idx_group_ai_dialogue_account_group'),
    ]
    
    for table_name, index_name in indexes_to_drop:
        try:
            op.drop_index(index_name, table_name=table_name, if_exists=True)
        except Exception:
            pass

