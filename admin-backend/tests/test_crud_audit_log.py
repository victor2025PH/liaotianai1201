"""
審計日誌 CRUD 操作測試
"""
import pytest
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.crud.audit_log import (
    create_audit_log,
    get_audit_logs,
    get_audit_log_by_id
)
from app.models.audit_log import AuditLog
from app.models.user import User


class TestCreateAuditLog:
    """創建審計日誌測試"""

    def test_create_audit_log_basic(self, prepare_database):
        """測試基本審計日誌創建"""
        from app.db import SessionLocal
        db = SessionLocal()
        try:
            log = create_audit_log(
                db,
                user_id=1,
                user_email="test@example.com",
                action="CREATE",
                resource_type="user"
            )
            
            assert log is not None
            assert log.user_id == 1
            assert log.user_email == "test@example.com"
            assert log.action == "CREATE"
            assert log.resource_type == "user"
            assert log.id is not None
            assert log.created_at is not None
        finally:
            db.close()

    def test_create_audit_log_with_all_fields(self, prepare_database):
        """測試帶所有字段的審計日誌創建"""
        from app.db import SessionLocal
        db = SessionLocal()
        try:
            before_state = {"status": "active"}
            after_state = {"status": "inactive"}
            
            log = create_audit_log(
                db,
                user_id=1,
                user_email="test@example.com",
                action="UPDATE",
                resource_type="user",
                resource_id="123",
                description="更新用戶狀態",
                before_state=before_state,
                after_state=after_state,
                ip_address="192.168.1.100",
                user_agent="Mozilla/5.0"
            )
            
            assert log.resource_id == "123"
            assert log.description == "更新用戶狀態"
            assert log.before_state == before_state
            assert log.after_state == after_state
            assert log.ip_address == "192.168.1.100"
            assert log.user_agent == "Mozilla/5.0"
        finally:
            db.close()

    def test_create_audit_log_with_none_fields(self, prepare_database):
        """測試帶 None 字段的審計日誌創建"""
        from app.db import SessionLocal
        db = SessionLocal()
        try:
            log = create_audit_log(
                db,
                user_id=1,
                user_email="test@example.com",
                action="DELETE",
                resource_type="user",
                resource_id=None,
                description=None,
                before_state=None,
                after_state=None,
                ip_address=None,
                user_agent=None
            )
            
            assert log.resource_id is None
            assert log.description is None
            assert log.before_state is None
            assert log.after_state is None
        finally:
            db.close()


class TestGetAuditLogs:
    """查詢審計日誌測試"""

    def test_get_audit_logs_basic(self, prepare_database):
        """測試基本查詢"""
        from app.db import SessionLocal
        db = SessionLocal()
        try:
            # 創建幾個審計日誌
            for i in range(5):
                create_audit_log(
                    db,
                    user_id=1,
                    user_email=f"user{i}@example.com",
                    action="CREATE",
                    resource_type="user"
                )
            
            logs, total = get_audit_logs(db)
            
            assert total >= 5
            assert len(logs) >= 5
            # 應該按創建時間降序排列
            assert logs[0].created_at >= logs[-1].created_at
        finally:
            db.close()

    def test_get_audit_logs_with_pagination(self, prepare_database):
        """測試分頁查詢"""
        from app.db import SessionLocal
        db = SessionLocal()
        try:
            # 創建多個審計日誌
            for i in range(10):
                create_audit_log(
                    db,
                    user_id=1,
                    user_email=f"user{i}@example.com",
                    action="CREATE",
                    resource_type="user"
                )
            
            # 第一頁
            logs1, total1 = get_audit_logs(db, skip=0, limit=5)
            assert len(logs1) <= 5
            assert total1 >= 10
            
            # 第二頁
            logs2, total2 = get_audit_logs(db, skip=5, limit=5)
            assert len(logs2) <= 5
            assert total2 == total1  # 總數應該相同
        finally:
            db.close()

    def test_get_audit_logs_filter_by_user_id(self, prepare_database):
        """測試按用戶ID過濾"""
        from app.db import SessionLocal
        db = SessionLocal()
        try:
            # 創建不同用戶的日誌
            create_audit_log(db, user_id=1, user_email="user1@example.com", action="CREATE", resource_type="user")
            create_audit_log(db, user_id=2, user_email="user2@example.com", action="CREATE", resource_type="user")
            create_audit_log(db, user_id=1, user_email="user1@example.com", action="UPDATE", resource_type="user")
            
            logs, total = get_audit_logs(db, user_id=1)
            
            assert all(log.user_id == 1 for log in logs)
            assert total >= 2
        finally:
            db.close()

    def test_get_audit_logs_filter_by_action(self, prepare_database):
        """測試按操作類型過濾"""
        from app.db import SessionLocal
        db = SessionLocal()
        try:
            create_audit_log(db, user_id=1, user_email="test@example.com", action="CREATE", resource_type="user")
            create_audit_log(db, user_id=1, user_email="test@example.com", action="UPDATE", resource_type="user")
            create_audit_log(db, user_id=1, user_email="test@example.com", action="DELETE", resource_type="user")
            
            logs, total = get_audit_logs(db, action="CREATE")
            
            assert all(log.action == "CREATE" for log in logs)
            assert total >= 1
        finally:
            db.close()

    def test_get_audit_logs_filter_by_resource_type(self, prepare_database):
        """測試按資源類型過濾"""
        from app.db import SessionLocal
        db = SessionLocal()
        try:
            create_audit_log(db, user_id=1, user_email="test@example.com", action="CREATE", resource_type="user")
            create_audit_log(db, user_id=1, user_email="test@example.com", action="CREATE", resource_type="role")
            create_audit_log(db, user_id=1, user_email="test@example.com", action="CREATE", resource_type="permission")
            
            logs, total = get_audit_logs(db, resource_type="user")
            
            assert all(log.resource_type == "user" for log in logs)
            assert total >= 1
        finally:
            db.close()

    def test_get_audit_logs_filter_by_resource_id(self, prepare_database):
        """測試按資源ID過濾"""
        from app.db import SessionLocal
        db = SessionLocal()
        try:
            create_audit_log(db, user_id=1, user_email="test@example.com", action="UPDATE", resource_type="user", resource_id="123")
            create_audit_log(db, user_id=1, user_email="test@example.com", action="UPDATE", resource_type="user", resource_id="456")
            
            logs, total = get_audit_logs(db, resource_id="123")
            
            assert all(log.resource_id == "123" for log in logs)
            assert total >= 1
        finally:
            db.close()

    def test_get_audit_logs_filter_by_date_range(self, prepare_database):
        """測試按日期範圍過濾"""
        from app.db import SessionLocal
        db = SessionLocal()
        try:
            # 創建一個較早的日誌
            old_log = create_audit_log(
                db,
                user_id=1,
                user_email="test@example.com",
                action="CREATE",
                resource_type="user"
            )
            
            # 創建一個較新的日誌
            new_log = create_audit_log(
                db,
                user_id=1,
                user_email="test@example.com",
                action="CREATE",
                resource_type="user"
            )
            
            # 查詢最近一天的日誌
            start_date = datetime.utcnow() - timedelta(days=1)
            end_date = datetime.utcnow() + timedelta(days=1)
            
            logs, total = get_audit_logs(db, start_date=start_date, end_date=end_date)
            
            assert total >= 2
            assert all(start_date <= log.created_at <= end_date for log in logs)
        finally:
            db.close()

    def test_get_audit_logs_multiple_filters(self, prepare_database):
        """測試多個過濾條件組合"""
        from app.db import SessionLocal
        db = SessionLocal()
        try:
            # 使用唯一的用戶郵箱避免唯一約束問題
            import time
            unique_email = f"test_{int(time.time())}@example.com"
            create_audit_log(db, user_id=1, user_email=unique_email, action="CREATE", resource_type="user")
            create_audit_log(db, user_id=1, user_email=unique_email, action="UPDATE", resource_type="user")
            create_audit_log(db, user_id=2, user_email=f"test2_{int(time.time())}@example.com", action="CREATE", resource_type="user")
            
            logs, total = get_audit_logs(db, user_id=1, action="CREATE", resource_type="user")
            
            assert all(log.user_id == 1 and log.action == "CREATE" and log.resource_type == "user" for log in logs)
            assert total >= 1
        finally:
            db.close()


class TestGetAuditLogById:
    """根據ID獲取審計日誌測試"""

    def test_get_audit_log_by_id_exists(self, prepare_database):
        """測試獲取存在的日誌"""
        from app.db import SessionLocal
        db = SessionLocal()
        try:
            log = create_audit_log(
                db,
                user_id=1,
                user_email="test@example.com",
                action="CREATE",
                resource_type="user"
            )
            
            found_log = get_audit_log_by_id(db, log_id=log.id)
            
            assert found_log is not None
            assert found_log.id == log.id
            assert found_log.user_email == log.user_email
        finally:
            db.close()

    def test_get_audit_log_by_id_not_exists(self, prepare_database):
        """測試獲取不存在的日誌"""
        from app.db import SessionLocal
        db = SessionLocal()
        try:
            log = get_audit_log_by_id(db, log_id=999999)
            assert log is None
        finally:
            db.close()

