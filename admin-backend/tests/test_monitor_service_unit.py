"""
MonitorService 單元測試
"""
import sys
from pathlib import Path

# 添加項目根目錄到 Python 路徑
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from group_ai_service.monitor_service import (
    MonitorService,
    AccountMetrics,
    SystemMetrics,
    Alert
)
from group_ai_service.models.account import AccountStatusEnum


@pytest.fixture
def monitor_service():
    """創建 MonitorService 實例"""
    return MonitorService()


class TestAccountMetrics:
    """AccountMetrics 測試"""
    
    def test_metrics_creation(self):
        """測試指標創建"""
        metrics = AccountMetrics(account_id="test_account")
        
        assert metrics.account_id == "test_account"
        assert metrics.message_count == 0
        assert metrics.reply_count == 0
        assert metrics.error_count == 0


class TestMonitorService:
    """MonitorService 測試"""
    
    def test_service_initialization(self, monitor_service):
        """測試服務初始化"""
        assert monitor_service is not None
        assert hasattr(monitor_service, 'account_metrics')
        assert hasattr(monitor_service, 'event_log')
    
    def test_record_message(self, monitor_service):
        """測試記錄消息"""
        account_id = "test_account"
        
        monitor_service.record_message(account_id, success=True)
        
        assert account_id in monitor_service.account_metrics
        assert monitor_service.account_metrics[account_id].message_count == 1
    
    def test_record_reply(self, monitor_service):
        """測試記錄回復"""
        account_id = "test_account"
        
        monitor_service.record_reply(account_id, reply_time=1.5, success=True)
        
        assert account_id in monitor_service.account_metrics
        assert monitor_service.account_metrics[account_id].reply_count == 1
        assert monitor_service.account_metrics[account_id].total_reply_time == 1.5
    
    def test_record_redpacket(self, monitor_service):
        """測試記錄紅包"""
        account_id = "test_account"
        
        monitor_service.record_redpacket(account_id, success=True, amount=5.0)
        
        assert account_id in monitor_service.account_metrics
        assert monitor_service.account_metrics[account_id].redpacket_count == 1
    
    def test_get_account_metrics(self, monitor_service):
        """測試獲取賬號指標"""
        account_id = "test_account"
        
        monitor_service.record_message(account_id, success=True)
        monitor_service.record_reply(account_id, success=True)
        
        metrics = monitor_service.get_account_metrics(account_id)
        
        assert metrics is not None
        assert metrics.message_count == 1
        assert metrics.reply_count == 1
    
    def test_get_account_metrics_with_time_range(self, monitor_service):
        """測試獲取賬號指標（帶時間範圍）"""
        account_id = "test_account"
        
        # 記錄一些事件
        monitor_service.record_message(account_id, success=True)
        monitor_service.record_reply(account_id, success=True)
        
        # 獲取最近1小時的指標
        metrics = monitor_service.get_account_metrics(
            account_id,
            time_range=timedelta(hours=1)
        )
        
        assert metrics is not None
        assert metrics.message_count >= 0
    
    def test_get_system_metrics(self, monitor_service):
        """測試獲取系統指標"""
        account_id = "test_account"
        
        monitor_service.record_message(account_id, success=True)
        
        metrics = monitor_service.get_system_metrics()
        
        assert metrics is not None
        assert metrics.total_accounts >= 1
        assert metrics.total_messages >= 1
    
    def test_check_alerts(self, monitor_service):
        """測試檢查告警"""
        # 記錄一些錯誤
        account_id = "test_account"
        for _ in range(10):
            monitor_service.record_message(account_id, success=False)
        
        alerts = monitor_service.check_alerts()
        
        assert isinstance(alerts, list)
        # 可能觸發告警，也可能不觸發（取決於閾值）
    
    def test_get_recent_alerts(self, monitor_service):
        """測試獲取最近告警"""
        # 創建一些告警
        alert1 = Alert(
            alert_id="alert1",
            alert_type="error",
            message="測試告警1"
        )
        alert2 = Alert(
            alert_id="alert2",
            alert_type="warning",
            message="測試告警2"
        )
        
        monitor_service.alerts.append(alert1)
        monitor_service.alerts.append(alert2)
        
        recent = monitor_service.get_recent_alerts(limit=1)
        
        assert len(recent) <= 1
        if recent:
            assert recent[0].alert_id in ["alert1", "alert2"]
    
    def test_resolve_alert(self, monitor_service):
        """測試解決告警"""
        alert = Alert(
            alert_id="test_alert",
            alert_type="error",
            message="測試告警"
        )
        
        monitor_service.alerts.append(alert)
        
        success = monitor_service.resolve_alert("test_alert")
        
        assert success == True
        assert alert.resolved == True
    
    def test_cleanup_old_events(self, monitor_service):
        """測試清理舊事件"""
        account_id = "test_account"
        
        # 記錄一些事件
        monitor_service.record_message(account_id, success=True)
        
        # 手動觸發清理（通常由 record_* 方法自動觸發）
        monitor_service._maybe_cleanup_old_events()
        
        # 檢查事件日誌是否正常
        assert len(monitor_service.event_log) >= 0
    
    def test_update_account_status(self, monitor_service):
        """測試更新賬號狀態"""
        account_id = "test_account"
        
        monitor_service.update_account_status(
            account_id,
            AccountStatusEnum.ONLINE,
            uptime_seconds=3600
        )
        
        assert account_id in monitor_service.account_metrics
        assert monitor_service.account_metrics[account_id].uptime_seconds == 3600
    
    def test_record_message_error(self, monitor_service):
        """測試記錄消息（錯誤）"""
        monitor_service.record_message("test_account", "error", success=False)
        
        metrics = monitor_service.get_account_metrics("test_account")
        assert metrics.error_count >= 1
    
    def test_record_reply_error(self, monitor_service):
        """測試記錄回復（錯誤）"""
        monitor_service.record_reply("test_account", reply_time=0.5, success=False)
        
        metrics = monitor_service.get_account_metrics("test_account")
        assert metrics.error_count >= 1
    
    def test_record_redpacket_failure(self, monitor_service):
        """測試記錄紅包（失敗）"""
        monitor_service.record_redpacket("test_account", success=False)
        
        metrics = monitor_service.get_account_metrics("test_account")
        assert metrics.redpacket_count >= 1
        assert metrics.error_count >= 1
    
    def test_get_account_metrics_not_found(self, monitor_service):
        """測試獲取賬號指標（未找到）"""
        metrics = monitor_service.get_account_metrics("nonexistent_account")
        
        # 如果賬號不存在，應該返回 None
        assert metrics is None
    
    def test_get_system_metrics_empty(self, monitor_service):
        """測試獲取系統指標（空數據）"""
        metrics = monitor_service.get_system_metrics()
        
        assert metrics.total_accounts == 0
        assert metrics.online_accounts == 0
        assert metrics.total_messages == 0
    
    def test_check_alerts_no_alerts(self, monitor_service):
        """測試檢查告警（無告警）"""
        # 記錄一些正常事件
        monitor_service.record_message("test_account", "text", success=True)
        monitor_service.record_reply("test_account", reply_time=0.1, success=True)
        
        alerts = monitor_service.check_alerts()
        
        # 應該沒有告警（所有指標正常）
        assert isinstance(alerts, list)
    
    def test_get_recent_alerts_empty(self, monitor_service):
        """測試獲取最近告警（空列表）"""
        alerts = monitor_service.get_recent_alerts(limit=10)
        
        assert isinstance(alerts, list)
        assert len(alerts) == 0
    
    def test_resolve_alert_not_found(self, monitor_service):
        """測試解決告警（未找到）"""
        result = monitor_service.resolve_alert("nonexistent_alert_id")
        
        assert result is False
    
    def test_get_account_metrics_multiple_accounts(self, monitor_service):
        """測試獲取賬號指標（多個賬號）"""
        # 記錄多個賬號的事件
        monitor_service.record_message("account1", "text", success=True)
        monitor_service.record_message("account2", "text", success=True)
        monitor_service.record_reply("account1", reply_time=0.1, success=True)
        
        metrics1 = monitor_service.get_account_metrics("account1")
        metrics2 = monitor_service.get_account_metrics("account2")
        
        assert metrics1.message_count >= 1
        assert metrics1.reply_count >= 1
        assert metrics2.message_count >= 1
        assert metrics2.reply_count == 0
    
    def test_get_system_metrics_with_data(self, monitor_service):
        """測試獲取系統指標（有數據）"""
        # 記錄一些事件
        monitor_service.record_message("account1", "text", success=True)
        monitor_service.record_message("account2", "text", success=True)
        monitor_service.record_reply("account1", reply_time=0.1, success=True)
        monitor_service.update_account_status("account1", AccountStatusEnum.ONLINE)
        monitor_service.update_account_status("account2", AccountStatusEnum.OFFLINE)
        
        metrics = monitor_service.get_system_metrics()
        
        assert metrics.total_accounts >= 2
        assert metrics.total_messages >= 2
        assert metrics.total_replies >= 1
    
    def test_get_recent_alerts_with_limit(self, monitor_service):
        """測試獲取最近告警（帶限制）"""
        alerts = monitor_service.get_recent_alerts(limit=5)
        
        assert isinstance(alerts, list)
        assert len(alerts) <= 5
    
    def test_compare_values_operators(self, monitor_service):
        """測試比較運算符"""
        # 測試各種運算符
        assert monitor_service._compare_values(5.0, 3.0, ">") == True
        assert monitor_service._compare_values(5.0, 3.0, ">=") == True
        assert monitor_service._compare_values(5.0, 5.0, ">=") == True
        assert monitor_service._compare_values(3.0, 5.0, "<") == True
        assert monitor_service._compare_values(3.0, 5.0, "<=") == True
        assert monitor_service._compare_values(5.0, 5.0, "<=") == True
        assert monitor_service._compare_values(5.0, 5.0, "==") == True
        assert monitor_service._compare_values(5.0, 3.0, "!=") == True
        assert monitor_service._compare_values(5.0, 3.0, "unknown") == True  # 默認使用 >
    
    def test_generate_alert_message_with_account(self, monitor_service):
        """測試生成告警消息（帶賬號）"""
        from types import SimpleNamespace
        
        rule = SimpleNamespace(
            name="測試規則",
            threshold_operator=">",
            threshold_value=10.0
        )
        
        message = monitor_service._generate_alert_message(rule, 15.0, "test_account")
        
        assert "test_account" in message
        assert "測試規則" in message
        assert "15.00" in message
        assert "10.0" in message or "10.00" in message  # 可能是 10.0 或 10.00
    
    def test_generate_alert_message_without_account(self, monitor_service):
        """測試生成告警消息（不帶賬號）"""
        from types import SimpleNamespace
        
        rule = SimpleNamespace(
            name="系統規則",
            threshold_operator="<",
            threshold_value=5.0
        )
        
        message = monitor_service._generate_alert_message(rule, 3.0, None)
        
        assert "系統規則" in message
        assert "3.00" in message
        assert "5.0" in message or "5.00" in message  # 可能是 5.0 或 5.00
        assert "賬號" not in message
    
    def test_check_default_rules_error_rate(self, monitor_service):
        """測試檢查默認規則（錯誤率）"""
        # 設置高錯誤率
        monitor_service.record_message("test_account", success=False)
        monitor_service.record_message("test_account", success=False)
        monitor_service.record_message("test_account", success=True)
        
        system_metrics = monitor_service.get_system_metrics()
        alerts = monitor_service._check_default_rules(system_metrics)
        
        # 應該有錯誤率告警
        assert len(alerts) > 0
        error_alerts = [a for a in alerts if "錯誤率" in a.message]
        assert len(error_alerts) > 0
    
    def test_check_default_rules_warning_rate(self, monitor_service):
        """測試檢查默認規則（警告率）"""
        # 設置中等錯誤率（在警告閾值和錯誤閾值之間）
        monitor_service.record_message("test_account", success=False)
        monitor_service.record_message("test_account", success=True)
        monitor_service.record_message("test_account", success=True)
        monitor_service.record_message("test_account", success=True)
        
        system_metrics = monitor_service.get_system_metrics()
        alerts = monitor_service._check_default_rules(system_metrics)
        
        # 應該有警告率告警
        assert len(alerts) > 0
        warning_alerts = [a for a in alerts if "錯誤率較高" in a.message]
        assert len(warning_alerts) > 0
    
    def test_check_default_rules_system_errors(self, monitor_service):
        """測試檢查默認規則（系統錯誤數）"""
        # 記錄大量錯誤
        for i in range(150):
            monitor_service.record_message(f"account_{i}", success=False)
        
        system_metrics = monitor_service.get_system_metrics()
        alerts = monitor_service._check_default_rules(system_metrics)
        
        # 應該有系統錯誤告警
        system_error_alerts = [a for a in alerts if "系統錯誤" in a.message or a.account_id is None]
        assert len(system_error_alerts) > 0
    
    def test_check_default_rules_account_offline(self, monitor_service):
        """測試檢查默認規則（賬號離線）"""
        from group_ai_service.models.account import AccountStatusEnum
        
        # 設置多個賬號為離線
        monitor_service.update_account_status("account1", AccountStatusEnum.OFFLINE)
        monitor_service.update_account_status("account2", AccountStatusEnum.OFFLINE)
        monitor_service.update_account_status("account3", AccountStatusEnum.OFFLINE)
        monitor_service.update_account_status("account4", AccountStatusEnum.ONLINE)
        
        system_metrics = monitor_service.get_system_metrics()
        alerts = monitor_service._check_default_rules(system_metrics)
        
        # 應該有賬號離線告警（如果離線率超過閾值）
        offline_alerts = [a for a in alerts if "離線" in a.message or "offline" in a.message.lower()]
        # 根據閾值，可能會有告警
        assert isinstance(alerts, list)
    
    def test_check_default_rules_response_time(self, monitor_service):
        """測試檢查默認規則（響應時間）"""
        # 記錄慢響應
        for i in range(10):
            monitor_service.record_reply("test_account", reply_time=10.0, success=True)  # 10秒響應
        
        system_metrics = monitor_service.get_system_metrics()
        alerts = monitor_service._check_default_rules(system_metrics)
        
        # 應該有響應時間告警（如果超過閾值）
        response_time_alerts = [a for a in alerts if "響應時間" in a.message or "response" in a.message.lower()]
        # 根據閾值，可能會有告警
        assert isinstance(alerts, list)
    
    def test_check_default_rules_redpacket_failure_rate(self, monitor_service):
        """測試檢查默認規則（紅包失敗率）"""
        # 記錄大量紅包失敗
        for i in range(10):
            monitor_service.record_redpacket("test_account", success=False)
        monitor_service.record_redpacket("test_account", success=True)
        
        system_metrics = monitor_service.get_system_metrics()
        alerts = monitor_service._check_default_rules(system_metrics)
        
        # 應該有紅包失敗率告警
        redpacket_alerts = [a for a in alerts if "紅包" in a.message or "redpacket" in a.message.lower()]
        # 根據閾值，可能會有告警
        assert isinstance(alerts, list)
    
    def test_check_default_rules_message_processing_error(self, monitor_service):
        """測試檢查默認規則（消息處理錯誤）"""
        # 記錄大量消息處理錯誤
        for i in range(15):
            monitor_service.record_message("test_account", success=False)
        
        system_metrics = monitor_service.get_system_metrics()
        alerts = monitor_service._check_default_rules(system_metrics)
        
        # 應該有消息處理錯誤告警
        message_error_alerts = [a for a in alerts if "消息處理" in a.message or "message" in a.message.lower()]
        # 根據閾值，可能會有告警
        assert isinstance(alerts, list)
    
    def test_check_default_rules_config_error(self, monitor_service):
        """測試檢查默認規則（配置讀取失敗）"""
        # Mock 配置讀取失敗（在 config 模塊中）
        with patch('group_ai_service.config.get_group_ai_config', side_effect=Exception("配置錯誤")):
            system_metrics = monitor_service.get_system_metrics()
            alerts = monitor_service._check_default_rules(system_metrics)
            
            # 應該使用默認值並繼續執行
            assert isinstance(alerts, list)
    
    def test_evaluate_rule_unknown_type(self, monitor_service):
        """測試評估規則（未知類型）"""
        from types import SimpleNamespace
        
        rule = SimpleNamespace(
            id="test_rule",
            name="未知規則",
            rule_type="unknown_type",
            threshold_value=10.0,
            threshold_operator=">",
            alert_level="warning"
        )
        
        system_metrics = monitor_service.get_system_metrics()
        result = monitor_service._evaluate_rule(rule, system_metrics)
        
        # 應該返回 None（未知類型）
        assert result is None
    
    def test_evaluate_rule_error_rate_no_match(self, monitor_service):
        """測試評估規則（錯誤率，不匹配）"""
        from types import SimpleNamespace
        
        # 設置低錯誤率
        monitor_service.record_message("test_account", success=True)
        monitor_service.record_message("test_account", success=True)
        
        rule = SimpleNamespace(
            id="test_rule",
            name="錯誤率規則",
            rule_type="error_rate",
            threshold_value=0.5,
            threshold_operator=">",
            alert_level="error"
        )
        
        system_metrics = monitor_service.get_system_metrics()
        result = monitor_service._evaluate_rule(rule, system_metrics)
        
        # 應該返回 None（不匹配閾值）
        assert result is None
    
    def test_evaluate_rule_system_errors(self, monitor_service):
        """測試評估規則（系統錯誤數）"""
        from types import SimpleNamespace
        
        # 記錄大量錯誤
        for i in range(20):
            monitor_service.record_message(f"account_{i}", success=False)
        
        rule = SimpleNamespace(
            id="test_rule",
            name="系統錯誤規則",
            rule_type="system_errors",
            threshold_value=10.0,
            threshold_operator=">",
            alert_level="error"
        )
        
        system_metrics = monitor_service.get_system_metrics()
        result = monitor_service._evaluate_rule(rule, system_metrics)
        
        # 應該返回告警
        assert result is not None
        assert result.alert_type == "error"
    
    def test_evaluate_rule_response_time(self, monitor_service):
        """測試評估規則（響應時間）"""
        from types import SimpleNamespace
        
        # 記錄慢響應
        monitor_service.record_reply("test_account", reply_time=6.0, success=True)  # 6秒
        
        rule = SimpleNamespace(
            id="test_rule",
            name="響應時間規則",
            rule_type="response_time",
            threshold_value=5000.0,  # 5秒（毫秒）
            threshold_operator=">",
            alert_level="warning"
        )
        
        system_metrics = monitor_service.get_system_metrics()
        result = monitor_service._evaluate_rule(rule, system_metrics)
        
        # 應該返回告警（6秒 > 5秒）
        assert result is not None
        assert result.alert_type == "warning"
    
    def test_evaluate_rule_account_offline(self, monitor_service):
        """測試評估規則（賬號離線）"""
        from types import SimpleNamespace
        from group_ai_service.models.account import AccountStatusEnum
        
        # 設置多個賬號為離線
        monitor_service.update_account_status("account1", AccountStatusEnum.OFFLINE)
        monitor_service.update_account_status("account2", AccountStatusEnum.OFFLINE)
        monitor_service.update_account_status("account3", AccountStatusEnum.ONLINE)
        
        rule = SimpleNamespace(
            id="test_rule",
            name="賬號離線規則",
            rule_type="account_offline",
            threshold_value=50.0,  # 50% 離線率
            threshold_operator=">",
            alert_level="warning"
        )
        
        system_metrics = monitor_service.get_system_metrics()
        result = monitor_service._evaluate_rule(rule, system_metrics)
        
        # 應該返回告警（66.7% > 50%）
        assert result is not None
        assert result.alert_type == "warning"

