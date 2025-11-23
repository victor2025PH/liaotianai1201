"""
通知系統 CRUD 操作測試
"""
import pytest
from datetime import datetime

from app.crud.notification import (
    create_notification_config,
    get_notification_config,
    list_notification_configs,
    update_notification_config,
    delete_notification_config,
    create_notification,
    get_notifications,
    get_unread_count,
    mark_notification_read,
    mark_all_read,
    update_notification_status,
    create_notification_template,
    list_notification_templates,
    get_notification_template,
    update_notification_template,
    delete_notification_template,
    find_matching_template,
    mark_notifications_as_read,
    delete_notifications,
)
from app.models.notification import (
    NotificationConfig,
    Notification,
    NotificationType,
    NotificationStatus,
    NotificationTemplate,
)


class TestNotificationConfig:
    """通知配置 CRUD 測試"""

    def test_create_notification_config_basic(self, prepare_database):
        """測試基本通知配置創建"""
        from app.db import SessionLocal
        db = SessionLocal()
        try:
            # 使用唯一名稱避免唯一約束問題
            import time
            unique_name = f"測試配置_{int(time.time())}"
            config = create_notification_config(
                db,
                name=unique_name,
                notification_type=NotificationType.EMAIL,
                config_data={"smtp_host": "smtp.example.com"},
                recipients=["admin@example.com"]
            )
            
            assert config is not None
            assert config.name == unique_name
            assert config.notification_type == NotificationType.EMAIL
            assert config.config_data == {"smtp_host": "smtp.example.com"}
            assert config.recipients == ["admin@example.com"]
            assert config.enabled is True  # 默認值
        finally:
            db.close()

    def test_create_notification_config_with_all_fields(self, prepare_database):
        """測試帶所有字段的通知配置創建"""
        from app.db import SessionLocal
        db = SessionLocal()
        try:
            # 使用唯一名稱
            import time
            unique_name = f"完整配置_{int(time.time())}"
            config = create_notification_config(
                db,
                name=unique_name,
                description="測試描述",
                notification_type=NotificationType.WEBHOOK,
                alert_levels=["critical", "warning"],
                event_types=["error", "alert"],
                config_data={"url": "https://example.com/webhook"},
                recipients=["admin@example.com", "user@example.com"],
                enabled=False
            )
            
            assert config.description == "測試描述"
            assert config.alert_levels == ["critical", "warning"]
            assert config.event_types == ["error", "alert"]
            assert config.enabled is False
        finally:
            db.close()

    def test_get_notification_config(self, prepare_database):
        """測試獲取通知配置"""
        from app.db import SessionLocal
        import uuid
        db = SessionLocal()
        try:
            # 使用 UUID 確保唯一性
            unique_name = f"測試配置_{uuid.uuid4().hex[:8]}"
            created = create_notification_config(
                db,
                name=unique_name,
                notification_type=NotificationType.EMAIL,
                config_data={},
                recipients=["admin@example.com"]
            )
            
            found = get_notification_config(db, config_id=created.id)
            
            assert found is not None
            assert found.id == created.id
            assert found.name == created.name
        finally:
            db.close()

    def test_get_notification_config_not_exists(self, prepare_database):
        """測試獲取不存在的配置"""
        from app.db import SessionLocal
        db = SessionLocal()
        try:
            config = get_notification_config(db, config_id=999999)
            assert config is None
        finally:
            db.close()

    def test_list_notification_configs(self, prepare_database):
        """測試列出通知配置"""
        from app.db import SessionLocal
        db = SessionLocal()
        try:
            # 創建多個配置（使用唯一名稱）
            import time
            unique_suffix = int(time.time())
            create_notification_config(db, name=f"配置1_{unique_suffix}", notification_type=NotificationType.EMAIL, config_data={}, recipients=[])
            create_notification_config(db, name=f"配置2_{unique_suffix}", notification_type=NotificationType.WEBHOOK, config_data={}, recipients=[])
            
            configs, total = list_notification_configs(db)
            
            assert total >= 2
            assert len(configs) >= 2
        finally:
            db.close()

    def test_list_notification_configs_filter_enabled(self, prepare_database):
        """測試過濾啟用的配置"""
        from app.db import SessionLocal
        db = SessionLocal()
        try:
            # 使用唯一名稱
            import time
            unique_suffix = int(time.time())
            create_notification_config(db, name=f"啟用配置_{unique_suffix}", notification_type=NotificationType.EMAIL, config_data={}, recipients=[], enabled=True)
            create_notification_config(db, name=f"禁用配置_{unique_suffix}", notification_type=NotificationType.EMAIL, config_data={}, recipients=[], enabled=False)
            
            enabled_configs, _ = list_notification_configs(db, enabled=True)
            assert all(c.enabled is True for c in enabled_configs)
            
            disabled_configs, _ = list_notification_configs(db, enabled=False)
            assert all(c.enabled is False for c in disabled_configs)
        finally:
            db.close()

    def test_update_notification_config(self, prepare_database):
        """測試更新通知配置"""
        from app.db import SessionLocal
        db = SessionLocal()
        try:
            # 使用唯一名稱
            import time
            unique_name = f"原始名稱_{int(time.time())}"
            config = create_notification_config(
                db,
                name=unique_name,
                notification_type=NotificationType.EMAIL,
                config_data={},
                recipients=["admin@example.com"]
            )
            
            updated_name = f"更新名稱_{int(time.time())}"
            updated = update_notification_config(
                db,
                config=config,
                name=updated_name,
                description="新描述",
                enabled=False
            )
            
            assert updated.name == updated_name
            assert updated.description == "新描述"
            assert updated.enabled is False
        finally:
            db.close()

    def test_delete_notification_config(self, prepare_database):
        """測試刪除通知配置"""
        from app.db import SessionLocal
        db = SessionLocal()
        try:
            # 使用唯一名稱
            import time
            unique_name = f"待刪除配置_{int(time.time())}"
            config = create_notification_config(
                db,
                name=unique_name,
                notification_type=NotificationType.EMAIL,
                config_data={},
                recipients=[]
            )
            
            result = delete_notification_config(db, config_id=config.id)
            assert result is True
            
            # 驗證已刪除
            found = get_notification_config(db, config_id=config.id)
            assert found is None
        finally:
            db.close()

    def test_delete_notification_config_not_exists(self, prepare_database):
        """測試刪除不存在的配置"""
        from app.db import SessionLocal
        db = SessionLocal()
        try:
            result = delete_notification_config(db, config_id=999999)
            assert result is False
        finally:
            db.close()


class TestNotification:
    """通知記錄 CRUD 測試"""

    def test_create_notification_basic(self, prepare_database):
        """測試基本通知創建"""
        from app.db import SessionLocal
        db = SessionLocal()
        try:
            notification = create_notification(
                db,
                notification_type=NotificationType.EMAIL,
                title="測試通知",
                message="這是一個測試通知",
                recipient="user@example.com"
            )
            
            assert notification is not None
            assert notification.title == "測試通知"
            assert notification.message == "這是一個測試通知"
            assert notification.recipient == "user@example.com"
        finally:
            db.close()

    def test_get_notifications(self, prepare_database):
        """測試查詢通知"""
        from app.db import SessionLocal
        db = SessionLocal()
        try:
            create_notification(db, notification_type=NotificationType.EMAIL, title="通知1", message="消息1", recipient="user@example.com")
            create_notification(db, notification_type=NotificationType.EMAIL, title="通知2", message="消息2", recipient="user@example.com")
            
            notifications, total = get_notifications(db)
            
            assert total >= 2
            assert len(notifications) >= 2
        finally:
            db.close()

    def test_get_notifications_filter_recipient(self, prepare_database):
        """測試按接收者過濾"""
        from app.db import SessionLocal
        db = SessionLocal()
        try:
            create_notification(db, notification_type=NotificationType.EMAIL, title="通知", message="消息", recipient="user1@example.com")
            create_notification(db, notification_type=NotificationType.EMAIL, title="通知", message="消息", recipient="user2@example.com")
            
            notifications, total = get_notifications(db, recipient="user1@example.com")
            
            assert all(n.recipient == "user1@example.com" for n in notifications)
            assert total >= 1
        finally:
            db.close()

    def test_get_unread_count(self, prepare_database):
        """測試獲取未讀通知數量"""
        from app.db import SessionLocal
        db = SessionLocal()
        try:
            # 創建未讀通知
            create_notification(
                db,
                notification_type=NotificationType.BROWSER,
                title="未讀通知",
                message="消息",
                recipient="user@example.com"
            )
            
            count = get_unread_count(db, recipient="user@example.com")
            assert count >= 1
        finally:
            db.close()

    def test_mark_notification_read(self, prepare_database):
        """測試標記通知為已讀"""
        from app.db import SessionLocal
        db = SessionLocal()
        try:
            notification = create_notification(
                db,
                notification_type=NotificationType.BROWSER,
                title="未讀通知",
                message="消息",
                recipient="user@example.com"
            )
            
            result = mark_notification_read(db, notification_id=notification.id, recipient="user@example.com")
            assert result is True
            
            db.refresh(notification)
            assert notification.read is True
            assert notification.read_at is not None
        finally:
            db.close()

    def test_mark_all_read(self, prepare_database):
        """測試標記所有通知為已讀"""
        from app.db import SessionLocal
        db = SessionLocal()
        try:
            # 創建多個未讀通知
            create_notification(db, notification_type=NotificationType.BROWSER, title="通知1", message="消息", recipient="user@example.com")
            create_notification(db, notification_type=NotificationType.BROWSER, title="通知2", message="消息", recipient="user@example.com")
            
            count = mark_all_read(db, recipient="user@example.com")
            assert count >= 2
        finally:
            db.close()

    def test_update_notification_status(self, prepare_database):
        """測試更新通知狀態"""
        from app.db import SessionLocal
        db = SessionLocal()
        try:
            notification = create_notification(
                db,
                notification_type=NotificationType.EMAIL,
                title="通知",
                message="消息",
                recipient="user@example.com"
            )
            
            result = update_notification_status(
                db,
                notification_id=notification.id,
                status=NotificationStatus.SENT
            )
            
            assert result is True
            db.refresh(notification)
            assert notification.status == NotificationStatus.SENT
            assert notification.sent_at is not None
        finally:
            db.close()


class TestNotificationTemplate:
    """通知模板 CRUD 測試"""

    def test_create_notification_template(self, prepare_database):
        """測試創建通知模板"""
        from app.db import SessionLocal
        db = SessionLocal()
        try:
            # 使用唯一名稱
            import time
            unique_name = f"測試模板_{int(time.time())}"
            template = create_notification_template(
                db,
                name=unique_name,
                notification_type=NotificationType.EMAIL,
                title_template="標題: {{title}}",
                body_template="內容: {{message}}"
            )
            
            assert template is not None
            assert template.name == unique_name
            assert template.title_template == "標題: {{title}}"
        finally:
            db.close()

    def test_find_matching_template(self, prepare_database):
        """測試查找匹配的模板"""
        from app.db import SessionLocal
        db = SessionLocal()
        try:
            # 使用唯一名稱
            import time
            unique_name = f"匹配模板_{int(time.time())}"
            template = create_notification_template(
                db,
                name=unique_name,
                notification_type=NotificationType.EMAIL,
                title_template="標題",
                body_template="內容",
                conditions={
                    "alert_levels": ["critical"],
                    "event_types": ["error"]
                }
            )
            
            found = find_matching_template(
                db,
                notification_type=NotificationType.EMAIL,
                alert_level="critical",
                event_type="error"
            )
            
            assert found is not None
            assert found.id == template.id
        finally:
            db.close()

    def test_mark_notifications_as_read(self, prepare_database):
        """測試批量標記為已讀"""
        from app.db import SessionLocal
        db = SessionLocal()
        try:
            n1 = create_notification(db, notification_type=NotificationType.BROWSER, title="通知1", message="消息", recipient="user@example.com")
            n2 = create_notification(db, notification_type=NotificationType.BROWSER, title="通知2", message="消息", recipient="user@example.com")
            
            count = mark_notifications_as_read(db, notification_ids=[n1.id, n2.id], recipient="user@example.com")
            assert count == 2
        finally:
            db.close()

    def test_delete_notifications(self, prepare_database):
        """測試批量刪除通知"""
        from app.db import SessionLocal
        db = SessionLocal()
        try:
            n1 = create_notification(db, notification_type=NotificationType.EMAIL, title="通知1", message="消息", recipient="user@example.com")
            n2 = create_notification(db, notification_type=NotificationType.EMAIL, title="通知2", message="消息", recipient="user@example.com")
            
            count = delete_notifications(db, notification_ids=[n1.id, n2.id], recipient="user@example.com")
            assert count == 2
        finally:
            db.close()

