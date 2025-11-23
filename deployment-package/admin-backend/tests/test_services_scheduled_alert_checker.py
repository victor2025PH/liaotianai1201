"""
定時告警檢查服務測試
"""
import pytest
import asyncio
from unittest.mock import MagicMock, patch, AsyncMock

from app.services.scheduled_alert_checker import ScheduledAlertChecker


class TestScheduledAlertChecker:
    """定時告警檢查服務測試"""
    
    @pytest.fixture
    def checker(self):
        """創建定時告警檢查服務實例"""
        return ScheduledAlertChecker(interval_seconds=60)
    
    def test_init(self, checker):
        """測試初始化"""
        assert checker.interval_seconds == 60
        assert checker.task is None
        assert checker.stop_event is None
        assert checker.is_running is False
    
    @pytest.mark.asyncio
    async def test_check_alerts_no_rules(self, checker):
        """測試告警檢查（無規則）"""
        with patch('app.db.SessionLocal') as mock_session:
            mock_db = MagicMock()
            mock_session.return_value = mock_db
            
            # Mock crud.alert_rule module
            with patch('app.crud.alert_rule.get_enabled_alert_rules') as mock_get_rules:
                mock_get_rules.return_value = []
                
                await checker._check_alerts()
                
                mock_get_rules.assert_called_once_with(mock_db)
                mock_db.close.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_check_alerts_with_rules(self, checker):
        """測試告警檢查（有規則）"""
        mock_rule = MagicMock()
        mock_rule.id = 1
        mock_rule.name = "Test Rule"
        
        with patch('app.db.SessionLocal') as mock_session:
            mock_db = MagicMock()
            mock_session.return_value = mock_db
            
            # Mock crud.alert_rule and monitor_service
            with patch('app.crud.alert_rule.get_enabled_alert_rules') as mock_get_rules, \
                 patch('app.api.group_ai.monitor.monitor_service') as mock_monitor:
                mock_get_rules.return_value = [mock_rule]
                
                mock_alert = MagicMock()
                mock_alert.alert_type = "test"
                mock_alert.message = "Test alert"
                mock_monitor.check_alerts.return_value = [mock_alert]
                
                await checker._check_alerts()
                
                mock_get_rules.assert_called_once_with(mock_db)
                mock_monitor.check_alerts.assert_called_once_with(alert_rules=[mock_rule])
                mock_db.close.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_check_alerts_exception_handling(self, checker):
        """測試告警檢查異常處理"""
        with patch('app.db.SessionLocal') as mock_session:
            mock_db = MagicMock()
            mock_session.return_value = mock_db
            
            # Mock crud.alert_rule and simulate exception
            with patch('app.crud.alert_rule.get_enabled_alert_rules') as mock_get_rules:
                mock_get_rules.side_effect = Exception("Database error")
                
                # 不應該拋出異常，應該被內部捕獲
                await checker._check_alerts()
                
                mock_db.close.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_start_and_stop(self, checker):
        """測試啟動和停止"""
        assert checker.is_running is False
        
        # 啟動服務
        checker.start()
        
        # 等待一小段時間確保任務已創建
        await asyncio.sleep(0.1)
        
        assert checker.is_running is True
        assert checker.task is not None
        assert checker.stop_event is not None
        
        # 停止服務
        checker.stop()
        
        # 等待任務停止
        await asyncio.sleep(0.1)
        
        assert checker.is_running is False
    
    @pytest.mark.asyncio
    async def test_start_already_running(self, checker):
        """測試重複啟動（已運行）"""
        checker.is_running = True
        
        # 不應該拋出異常
        checker.start()
        
        # 狀態應該保持不變
        assert checker.is_running is True
    
    @pytest.mark.asyncio
    async def test_stop_when_not_running(self, checker):
        """測試停止（未運行）"""
        assert checker.is_running is False
        
        # 不應該拋出異常
        checker.stop()
        
        assert checker.is_running is False
    
    @pytest.mark.asyncio
    async def test_run_periodic_executes_check(self, checker):
        """測試週期性執行告警檢查"""
        checker.stop_event = asyncio.Event()
        
        # 模擬 _check_alerts
        check_calls = []
        original_check = checker._check_alerts
        
        async def mock_check():
            check_calls.append(1)
            await original_check()
        
        checker._check_alerts = mock_check
        
        # 創建任務
        task = asyncio.create_task(checker._run_periodic())
        
        # 等待一小段時間，應該立即執行一次檢查
        await asyncio.sleep(0.2)
        
        # 停止服務
        checker.stop_event.set()
        await task
        
        # 應該至少執行了一次檢查
        assert len(check_calls) >= 1
    
    @pytest.mark.asyncio
    async def test_run_periodic_with_interval(self, checker):
        """測試週期性執行（間隔時間）"""
        checker.interval_seconds = 1  # 1 秒間隔
        checker.stop_event = asyncio.Event()
        
        check_calls = []
        original_check = checker._check_alerts
        
        async def mock_check():
            check_calls.append(1)
            await original_check()
        
        checker._check_alerts = mock_check
        
        # 創建任務
        task = asyncio.create_task(checker._run_periodic())
        
        # 等待間隔時間
        await asyncio.sleep(1.5)
        
        # 停止服務
        checker.stop_event.set()
        await task
        
        # 應該執行多次檢查（立即執行 + 間隔後執行）
        assert len(check_calls) >= 2

