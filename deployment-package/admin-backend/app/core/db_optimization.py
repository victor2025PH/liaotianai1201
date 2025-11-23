"""
數據庫查詢優化工具
包括索引優化和 N+1 查詢優化
"""
from sqlalchemy import Index
from sqlalchemy.orm import joinedload, selectinload, Session, Query
from typing import Type, TypeVar, List

T = TypeVar('T')


def optimize_query_for_list(
    query: Query,
    model_class: Type[T],
    relationships: List[str] = None,
) -> Query:
    """
    優化列表查詢，避免 N+1 問題
    
    Args:
        query: SQLAlchemy 查詢對象
        model_class: 模型類
        relationships: 需要預加載的關係列表
    
    Returns:
        優化後的查詢對象
    """
    if relationships:
        for rel in relationships:
            if hasattr(model_class, rel):
                # 使用 selectinload 進行批量加載（性能更好）
                query = query.options(selectinload(getattr(model_class, rel)))
    
    return query


def get_optimized_user_query(db: Session, include_roles: bool = True) -> Query:
    """獲取優化的用戶查詢（預加載角色）"""
    from app.models.user import User
    query = db.query(User)
    if include_roles:
        query = query.options(selectinload(User.roles))
    return query


def get_optimized_role_query(db: Session, include_permissions: bool = True) -> Query:
    """獲取優化的角色查詢（預加載權限）"""
    from app.models.role import Role
    query = db.query(Role)
    if include_permissions:
        query = query.options(selectinload(Role.permissions))
    return query


# 定義需要添加的複合索引
ADDITIONAL_INDEXES = {
    "group_ai_accounts": [
        Index("idx_account_script_status", "script_id", "active"),
        Index("idx_account_server", "server_id", "active"),
        Index("idx_account_created", "created_at"),
    ],
    "group_ai_scripts": [
        Index("idx_script_status_created", "status", "created_at"),
    ],
    "group_ai_dialogue_history": [
        Index("idx_dialogue_account_group", "account_id", "group_id", "timestamp"),
        Index("idx_dialogue_timestamp", "timestamp"),
    ],
    "group_ai_metrics": [
        Index("idx_metric_account_type_time", "account_id", "metric_type", "timestamp"),
        Index("idx_metric_timestamp", "timestamp"),
    ],
    "group_ai_redpacket_logs": [
        Index("idx_redpacket_account_group", "account_id", "group_id", "timestamp"),
    ],
    "notifications": [
        Index("idx_notification_recipient_read", "recipient", "read", "created_at"),
        Index("idx_notification_status_created", "status", "created_at"),
    ],
    "audit_logs": [
        Index("idx_audit_user_resource", "user_id", "resource_type", "created_at"),
    ],
    "group_ai_automation_tasks": [
        Index("idx_task_enabled_next_run", "enabled", "next_run_at"),
        Index("idx_task_type_enabled", "task_type", "enabled"),
    ],
    "group_ai_automation_task_logs": [
        Index("idx_task_log_task_status", "task_id", "status", "started_at"),
    ],
}


def create_additional_indexes(engine):
    """
    創建額外的數據庫索引
    
    注意：這需要在數據庫遷移中執行，而不是在運行時動態創建
    """
    from sqlalchemy import inspect
    
    inspector = inspect(engine)
    existing_indexes = {}
    
    # 獲取現有索引
    for table_name in inspector.get_table_names():
        existing_indexes[table_name] = [
            idx["name"] for idx in inspector.get_indexes(table_name)
        ]
    
    # 創建缺失的索引
    for table_name, indexes in ADDITIONAL_INDEXES.items():
        if table_name in inspector.get_table_names():
            for index in indexes:
                index_name = index.name if hasattr(index, "name") else str(index)
                if index_name not in existing_indexes.get(table_name, []):
                    try:
                        index.create(engine)
                        print(f"✓ 創建索引: {table_name}.{index_name}")
                    except Exception as e:
                        print(f"✗ 創建索引失敗 {table_name}.{index_name}: {e}")

