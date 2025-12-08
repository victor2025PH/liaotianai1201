"""合并迁移分支并添加性能索引

Revision ID: 005_merge_heads_and_add_indexes
Revises: ('003_add_script_version_management', 'fc673460c426', 'cb4ad7ca2507', 'ea5d525f9c2a', 'ccaf23c9b58a')
Create Date: 2025-12-09
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = '005_merge_heads_and_add_indexes'
# 合并所有分支：基于最新的两个 head
down_revision = ('004_add_performance_indexes', 'xxxx_add_telegram_registration')
branch_labels = None
depends_on = None


def upgrade():
    """添加性能優化索引"""
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    tables = inspector.get_table_names()
    
    # 群組 AI 賬號表 - 複合索引優化
    if 'group_ai_accounts' in tables:
        # script_id + active 複合索引（常用過濾組合）
        try:
            op.create_index(
                'idx_account_script_active',
                'group_ai_accounts',
                ['script_id', 'active'],
                unique=False,
                if_not_exists=True
            )
        except Exception:
            pass
        
        # server_id + active 複合索引（服務器過濾）
        try:
            op.create_index(
                'idx_account_server_active',
                'group_ai_accounts',
                ['server_id', 'active'],
                unique=False,
                if_not_exists=True
            )
        except Exception:
            pass
        
        # account_id 索引（用於快速查找）
        try:
            op.create_index(
                'idx_account_account_id',
                'group_ai_accounts',
                ['account_id'],
                unique=False,
                if_not_exists=True
            )
        except Exception:
            pass
    
    # 群組 AI 劇本表 - 狀態和時間複合索引
    if 'group_ai_scripts' in tables:
        # status + created_at 複合索引（狀態過濾和排序）
        try:
            op.create_index(
                'idx_script_status_created',
                'group_ai_scripts',
                ['status', 'created_at'],
                unique=False,
                if_not_exists=True
            )
        except Exception:
            pass
    
    # 對話歷史表 - 優化時間範圍查詢
    if 'group_ai_dialogue_history' in tables:
        # account_id + group_id + timestamp 複合索引（常用查詢模式）
        try:
            op.create_index(
                'idx_dialogue_account_group_time',
                'group_ai_dialogue_history',
                ['account_id', 'group_id', 'timestamp'],
                unique=False,
                if_not_exists=True
            )
        except Exception:
            pass
        
        # timestamp 索引（時間範圍查詢）
        try:
            op.create_index(
                'idx_dialogue_timestamp',
                'group_ai_dialogue_history',
                ['timestamp'],
                unique=False,
                if_not_exists=True
            )
        except Exception:
            pass
    
    # 指標表 - 優化聚合查詢
    if 'group_ai_metrics' in tables:
        # account_id + metric_type + timestamp 複合索引（指標查詢）
        try:
            op.create_index(
                'idx_metric_account_type_time',
                'group_ai_metrics',
                ['account_id', 'metric_type', 'timestamp'],
                unique=False,
                if_not_exists=True
            )
        except Exception:
            pass
        
        # timestamp 索引（時間範圍查詢）
        try:
            op.create_index(
                'idx_metric_timestamp',
                'group_ai_metrics',
                ['timestamp'],
                unique=False,
                if_not_exists=True
            )
        except Exception:
            pass
    
    # 紅包日誌表 - 優化查詢
    if 'group_ai_redpacket_logs' in tables:
        # account_id + group_id + timestamp 複合索引
        try:
            op.create_index(
                'idx_redpacket_account_group_time',
                'group_ai_redpacket_logs',
                ['account_id', 'group_id', 'timestamp'],
                unique=False,
                if_not_exists=True
            )
        except Exception:
            pass
    
    # 通知表 - 優化查詢
    if 'notifications' in tables:
        # recipient + read + created_at 複合索引（未讀通知查詢）
        try:
            op.create_index(
                'idx_notification_recipient_read_created',
                'notifications',
                ['recipient', 'read', 'created_at'],
                unique=False,
                if_not_exists=True
            )
        except Exception:
            pass
        
        # status + created_at 複合索引（狀態過濾）
        try:
            op.create_index(
                'idx_notification_status_created',
                'notifications',
                ['status', 'created_at'],
                unique=False,
                if_not_exists=True
            )
        except Exception:
            pass
    
    # 審計日誌表 - 優化查詢
    if 'audit_logs' in tables:
        # user_id + resource_type + created_at 複合索引
        try:
            op.create_index(
                'idx_audit_user_resource_created',
                'audit_logs',
                ['user_id', 'resource_type', 'created_at'],
                unique=False,
                if_not_exists=True
            )
        except Exception:
            pass
    
    # 自動化任務表 - 優化調度查詢
    if 'group_ai_automation_tasks' in tables:
        # enabled + next_run_at 複合索引（調度查詢）
        try:
            op.create_index(
                'idx_task_enabled_next_run',
                'group_ai_automation_tasks',
                ['enabled', 'next_run_at'],
                unique=False,
                if_not_exists=True
            )
        except Exception:
            pass
        
        # task_type + enabled 複合索引（類型過濾）
        try:
            op.create_index(
                'idx_task_type_enabled',
                'group_ai_automation_tasks',
                ['task_type', 'enabled'],
                unique=False,
                if_not_exists=True
            )
        except Exception:
            pass
    
    # 自動化任務日誌表 - 優化查詢
    if 'group_ai_automation_task_logs' in tables:
        # task_id + status + started_at 複合索引
        try:
            op.create_index(
                'idx_task_log_task_status_started',
                'group_ai_automation_task_logs',
                ['task_id', 'status', 'started_at'],
                unique=False,
                if_not_exists=True
            )
        except Exception:
            pass


def downgrade():
    """刪除性能優化索引"""
    # 注意：在生產環境中，通常不建議刪除索引，因為可能影響性能
    # 這裡僅提供回滾功能，實際使用時應謹慎
    pass

