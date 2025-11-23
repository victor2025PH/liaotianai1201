"""
告警規則 CRUD 操作測試
"""
import pytest
from sqlalchemy.orm import Session

from app.crud.alert_rule import (
    create_alert_rule,
    get_alert_rule,
    get_alert_rule_by_name,
    list_alert_rules,
    get_enabled_alert_rules,
    update_alert_rule,
    delete_alert_rule
)
from app.schemas.alert_rule import AlertRuleCreate, AlertRuleUpdate
from app.models.group_ai import GroupAIAlertRule


class TestCreateAlertRule:
    """創建告警規則測試"""

    def test_create_alert_rule_basic(self, prepare_database):
        """測試基本告警規則創建"""
        from app.db import SessionLocal
        import uuid
        db = SessionLocal()
        try:
            unique_name = f"測試規則_{uuid.uuid4().hex[:8]}"
            rule_data = AlertRuleCreate(
                name=unique_name,
                rule_type="metric",
                alert_level="warning",
                threshold_value=100.0,
                threshold_operator=">",
                enabled=True,
                notification_method="email",
                notification_target="admin@example.com"
            )
            
            rule = create_alert_rule(db, rule=rule_data)
            
            assert rule is not None
            assert rule.name == unique_name
            assert rule.rule_type == "metric"
            assert rule.alert_level == "warning"
            assert rule.threshold_value == 100.0
            assert rule.threshold_operator == ">"
            assert rule.enabled is True
        finally:
            db.close()

    def test_create_alert_rule_with_all_fields(self, prepare_database):
        """測試帶所有字段的告警規則創建"""
        from app.db import SessionLocal
        import uuid
        db = SessionLocal()
        try:
            unique_name = f"完整規則_{uuid.uuid4().hex[:8]}"
            rule_data = AlertRuleCreate(
                name=unique_name,
                rule_type="metric",
                alert_level="critical",
                threshold_value=200.0,
                threshold_operator=">=",
                enabled=True,
                notification_method="webhook",
                notification_target="https://example.com/webhook",
                rule_conditions={"metric": "cpu_usage"},
                description="測試描述"
            )
            
            rule = create_alert_rule(db, rule=rule_data, created_by="admin@example.com")
            
            assert rule.description == "測試描述"
            assert rule.rule_conditions == {"metric": "cpu_usage"}
            assert rule.created_by == "admin@example.com"
        finally:
            db.close()

    def test_create_alert_rule_with_conditions(self, prepare_database):
        """測試帶條件的告警規則創建"""
        from app.db import SessionLocal
        import uuid
        db = SessionLocal()
        try:
            unique_name = f"條件規則_{uuid.uuid4().hex[:8]}"
            rule_data = AlertRuleCreate(
                name=unique_name,
                rule_type="metric",
                alert_level="warning",
                threshold_value=50.0,
                threshold_operator="<",
                enabled=True,
                notification_method="email",
                notification_target="admin@example.com",
                rule_conditions={"metric": "memory_usage", "duration": 300}
            )
            
            rule = create_alert_rule(db, rule=rule_data)
            
            assert rule.rule_conditions == {"metric": "memory_usage", "duration": 300}
        finally:
            db.close()


class TestGetAlertRule:
    """獲取告警規則測試"""

    def test_get_alert_rule_by_id(self, prepare_database):
        """測試根據ID獲取告警規則"""
        from app.db import SessionLocal
        import uuid
        db = SessionLocal()
        try:
            unique_name = f"測試規則_{uuid.uuid4().hex[:8]}"
            rule_data = AlertRuleCreate(
                name=unique_name,
                rule_type="metric",
                alert_level="warning",
                threshold_value=100.0,
                threshold_operator=">",
                enabled=True,
                notification_method="email",
                notification_target="admin@example.com"
            )
            
            created = create_alert_rule(db, rule=rule_data)
            
            found = get_alert_rule(db, rule_id=created.id)
            
            assert found is not None
            assert found.id == created.id
            assert found.name == created.name
        finally:
            db.close()

    def test_get_alert_rule_by_id_not_exists(self, prepare_database):
        """測試獲取不存在的規則"""
        from app.db import SessionLocal
        db = SessionLocal()
        try:
            rule = get_alert_rule(db, rule_id="nonexistent_id")
            assert rule is None
        finally:
            db.close()

    def test_get_alert_rule_by_name(self, prepare_database):
        """測試根據名稱獲取告警規則"""
        from app.db import SessionLocal
        import uuid
        db = SessionLocal()
        try:
            unique_name = f"測試規則_{uuid.uuid4().hex[:8]}"
            rule_data = AlertRuleCreate(
                name=unique_name,
                rule_type="metric",
                alert_level="warning",
                threshold_value=100.0,
                threshold_operator=">",
                enabled=True,
                notification_method="email",
                notification_target="admin@example.com"
            )
            
            created = create_alert_rule(db, rule=rule_data)
            
            found = get_alert_rule_by_name(db, name=unique_name)
            
            assert found is not None
            assert found.id == created.id
            assert found.name == unique_name
        finally:
            db.close()

    def test_get_alert_rule_by_name_not_exists(self, prepare_database):
        """測試獲取不存在的規則（按名稱）"""
        from app.db import SessionLocal
        db = SessionLocal()
        try:
            rule = get_alert_rule_by_name(db, name="nonexistent_rule")
            assert rule is None
        finally:
            db.close()


class TestListAlertRules:
    """列出告警規則測試"""

    def test_list_alert_rules_basic(self, prepare_database):
        """測試基本列表查詢"""
        from app.db import SessionLocal
        import uuid
        db = SessionLocal()
        try:
            # 創建多個規則
            for i in range(3):
                unique_name = f"規則_{uuid.uuid4().hex[:8]}"
                rule_data = AlertRuleCreate(
                    name=unique_name,
                    rule_type="metric",
                    alert_level="warning",
                    threshold_value=100.0 + i,
                    threshold_operator=">",
                    enabled=True,
                    notification_method="email",
                    notification_target="admin@example.com"
                )
                create_alert_rule(db, rule=rule_data)
            
            rules, total = list_alert_rules(db)
            
            assert total >= 3
            assert len(rules) >= 3
        finally:
            db.close()

    def test_list_alert_rules_with_pagination(self, prepare_database):
        """測試分頁查詢"""
        from app.db import SessionLocal
        import uuid
        db = SessionLocal()
        try:
            # 創建多個規則
            for i in range(10):
                unique_name = f"規則_{uuid.uuid4().hex[:8]}"
                rule_data = AlertRuleCreate(
                    name=unique_name,
                    rule_type="metric",
                    alert_level="warning",
                    threshold_value=100.0,
                    threshold_operator=">",
                    enabled=True,
                    notification_method="email",
                    notification_target="admin@example.com"
                )
                create_alert_rule(db, rule=rule_data)
            
            # 第一頁
            rules1, total1 = list_alert_rules(db, skip=0, limit=5)
            assert len(rules1) <= 5
            assert total1 >= 10
            
            # 第二頁
            rules2, total2 = list_alert_rules(db, skip=5, limit=5)
            assert len(rules2) <= 5
            assert total2 == total1
        finally:
            db.close()

    def test_list_alert_rules_filter_enabled(self, prepare_database):
        """測試過濾啟用的規則"""
        from app.db import SessionLocal
        import uuid
        db = SessionLocal()
        try:
            # 創建啟用和禁用的規則
            enabled_name = f"啟用規則_{uuid.uuid4().hex[:8]}"
            disabled_name = f"禁用規則_{uuid.uuid4().hex[:8]}"
            
            rule_data1 = AlertRuleCreate(
                name=enabled_name,
                rule_type="metric",
                alert_level="warning",
                threshold_value=100.0,
                threshold_operator=">",
                enabled=True,
                notification_method="email",
                notification_target="admin@example.com"
            )
            create_alert_rule(db, rule=rule_data1)
            
            rule_data2 = AlertRuleCreate(
                name=disabled_name,
                rule_type="metric",
                alert_level="warning",
                threshold_value=100.0,
                threshold_operator=">",
                enabled=False,
                notification_method="email",
                notification_target="admin@example.com"
            )
            create_alert_rule(db, rule=rule_data2)
            
            enabled_rules, _ = list_alert_rules(db, enabled=True)
            assert all(r.enabled is True for r in enabled_rules)
            
            disabled_rules, _ = list_alert_rules(db, enabled=False)
            assert all(r.enabled is False for r in disabled_rules)
        finally:
            db.close()

    def test_list_alert_rules_filter_by_type(self, prepare_database):
        """測試按類型過濾"""
        from app.db import SessionLocal
        import uuid
        db = SessionLocal()
        try:
            # 創建不同類型的規則
            metric_name = f"指標規則_{uuid.uuid4().hex[:8]}"
            event_name = f"事件規則_{uuid.uuid4().hex[:8]}"
            
            rule_data1 = AlertRuleCreate(
                name=metric_name,
                rule_type="metric",
                alert_level="warning",
                threshold_value=100.0,
                threshold_operator=">",
                enabled=True,
                notification_method="email",
                notification_target="admin@example.com"
            )
            create_alert_rule(db, rule=rule_data1)
            
            rule_data2 = AlertRuleCreate(
                name=event_name,
                rule_type="event",
                alert_level="warning",
                threshold_value=100.0,
                threshold_operator=">",
                enabled=True,
                notification_method="email",
                notification_target="admin@example.com"
            )
            create_alert_rule(db, rule=rule_data2)
            
            metric_rules, _ = list_alert_rules(db, rule_type="metric")
            assert all(r.rule_type == "metric" for r in metric_rules)
            
            event_rules, _ = list_alert_rules(db, rule_type="event")
            assert all(r.rule_type == "event" for r in event_rules)
        finally:
            db.close()


class TestGetEnabledAlertRules:
    """獲取啟用的告警規則測試"""

    def test_get_enabled_alert_rules(self, prepare_database):
        """測試獲取所有啟用的規則"""
        from app.db import SessionLocal
        import uuid
        db = SessionLocal()
        try:
            # 創建啟用和禁用的規則
            enabled_name = f"啟用規則_{uuid.uuid4().hex[:8]}"
            disabled_name = f"禁用規則_{uuid.uuid4().hex[:8]}"
            
            rule_data1 = AlertRuleCreate(
                name=enabled_name,
                rule_type="metric",
                alert_level="warning",
                threshold_value=100.0,
                threshold_operator=">",
                enabled=True,
                notification_method="email",
                notification_target="admin@example.com"
            )
            create_alert_rule(db, rule=rule_data1)
            
            rule_data2 = AlertRuleCreate(
                name=disabled_name,
                rule_type="metric",
                alert_level="warning",
                threshold_value=100.0,
                threshold_operator=">",
                enabled=False,
                notification_method="email",
                notification_target="admin@example.com"
            )
            create_alert_rule(db, rule=rule_data2)
            
            enabled_rules = get_enabled_alert_rules(db)
            assert all(r.enabled is True for r in enabled_rules)
            assert len(enabled_rules) >= 1
        finally:
            db.close()

    def test_get_enabled_alert_rules_by_type(self, prepare_database):
        """測試按類型獲取啟用的規則"""
        from app.db import SessionLocal
        import uuid
        db = SessionLocal()
        try:
            metric_name = f"指標規則_{uuid.uuid4().hex[:8]}"
            rule_data = AlertRuleCreate(
                name=metric_name,
                rule_type="metric",
                alert_level="warning",
                threshold_value=100.0,
                threshold_operator=">",
                enabled=True,
                notification_method="email",
                notification_target="admin@example.com"
            )
            create_alert_rule(db, rule=rule_data)
            
            metric_rules = get_enabled_alert_rules(db, rule_type="metric")
            assert all(r.rule_type == "metric" and r.enabled is True for r in metric_rules)
        finally:
            db.close()


class TestUpdateAlertRule:
    """更新告警規則測試"""

    def test_update_alert_rule(self, prepare_database):
        """測試更新告警規則"""
        from app.db import SessionLocal
        import uuid
        db = SessionLocal()
        try:
            unique_name = f"原始規則_{uuid.uuid4().hex[:8]}"
            rule_data = AlertRuleCreate(
                name=unique_name,
                rule_type="metric",
                alert_level="warning",
                threshold_value=100.0,
                threshold_operator=">",
                enabled=True,
                notification_method="email",
                notification_target="admin@example.com"
            )
            
            created = create_alert_rule(db, rule=rule_data)
            
            update_data = AlertRuleUpdate(
                threshold_value=200.0,
                enabled=False,
                description="更新後的描述"
            )
            
            updated = update_alert_rule(db, rule_id=created.id, rule_update=update_data)
            
            assert updated is not None
            assert updated.threshold_value == 200.0
            assert updated.enabled is False
            assert updated.description == "更新後的描述"
        finally:
            db.close()

    def test_update_alert_rule_not_exists(self, prepare_database):
        """測試更新不存在的規則"""
        from app.db import SessionLocal
        db = SessionLocal()
        try:
            update_data = AlertRuleUpdate(threshold_value=200.0)
            updated = update_alert_rule(db, rule_id="nonexistent_id", rule_update=update_data)
            assert updated is None
        finally:
            db.close()

    def test_update_alert_rule_partial(self, prepare_database):
        """測試部分更新"""
        from app.db import SessionLocal
        import uuid
        db = SessionLocal()
        try:
            unique_name = f"規則_{uuid.uuid4().hex[:8]}"
            rule_data = AlertRuleCreate(
                name=unique_name,
                rule_type="metric",
                alert_level="warning",
                threshold_value=100.0,
                threshold_operator=">",
                enabled=True,
                notification_method="email",
                notification_target="admin@example.com"
            )
            
            created = create_alert_rule(db, rule=rule_data)
            
            # 只更新一個字段
            update_data = AlertRuleUpdate(threshold_value=150.0)
            updated = update_alert_rule(db, rule_id=created.id, rule_update=update_data)
            
            assert updated.threshold_value == 150.0
            # 其他字段應該保持不變
            assert updated.name == unique_name
            assert updated.enabled is True
        finally:
            db.close()


class TestDeleteAlertRule:
    """刪除告警規則測試"""

    def test_delete_alert_rule(self, prepare_database):
        """測試刪除告警規則"""
        from app.db import SessionLocal
        import uuid
        db = SessionLocal()
        try:
            unique_name = f"待刪除規則_{uuid.uuid4().hex[:8]}"
            rule_data = AlertRuleCreate(
                name=unique_name,
                rule_type="metric",
                alert_level="warning",
                threshold_value=100.0,
                threshold_operator=">",
                enabled=True,
                notification_method="email",
                notification_target="admin@example.com"
            )
            
            created = create_alert_rule(db, rule=rule_data)
            
            result = delete_alert_rule(db, rule_id=created.id)
            assert result is True
            
            # 驗證已刪除
            found = get_alert_rule(db, rule_id=created.id)
            assert found is None
        finally:
            db.close()

    def test_delete_alert_rule_not_exists(self, prepare_database):
        """測試刪除不存在的規則"""
        from app.db import SessionLocal
        db = SessionLocal()
        try:
            result = delete_alert_rule(db, rule_id="nonexistent_id")
            assert result is False
        finally:
            db.close()

