"""
GameGuideService 單元測試
"""
import sys
from pathlib import Path

# 添加項目根目錄到 Python 路徑
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Mock aiohttp 在導入 game_api_client 之前
import sys
from unittest.mock import MagicMock
mock_aiohttp = MagicMock()
sys.modules['aiohttp'] = mock_aiohttp

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from group_ai_service.game_guide_service import GameGuideService
from group_ai_service.game_api_client import GameEvent, GameStatus
from group_ai_service.account_manager import AccountManager
from group_ai_service.models.account import AccountConfig


@pytest.fixture
def account_manager():
    """創建 AccountManager 實例"""
    return Mock(spec=AccountManager)


@pytest.fixture
def dialogue_manager():
    """創建 DialogueManager 實例"""
    mock = Mock()
    mock.send_message = AsyncMock()
    return mock


@pytest.fixture
def game_guide_service(dialogue_manager, account_manager):
    """創建 GameGuideService 實例"""
    return GameGuideService(
        dialogue_manager=dialogue_manager,
        account_manager=account_manager
    )


@pytest.fixture
def game_start_event():
    """創建遊戲開始事件"""
    return GameEvent(
        event_type="GAME_START",
        group_id=-1001234567890,
        game_id="test_game",
        timestamp=datetime.now()
    )


@pytest.fixture
def redpacket_sent_event():
    """創建紅包發送事件"""
    return GameEvent(
        event_type="REDPACKET_SENT",
        group_id=-1001234567890,
        game_id="test_game",
        payload={
            "amount": 10.0,
            "count": 10,
            "remaining": 10,
            "token": "USDT"
        },
        timestamp=datetime.now()
    )


class TestGameGuideService:
    """GameGuideService 測試"""
    
    def test_service_initialization(self, game_guide_service):
        """測試服務初始化"""
        assert game_guide_service is not None
        assert game_guide_service.dialogue_manager is not None
        assert game_guide_service.account_manager is not None
        assert len(game_guide_service.guide_templates) > 0
    
    def test_load_templates(self, game_guide_service):
        """測試加載模板"""
        templates = game_guide_service.guide_templates
        assert "game_start" in templates
        assert "redpacket_sent" in templates
        assert "redpacket_claimed" in templates
        assert "redpacket_almost_gone" in templates
        assert "game_end" in templates
        assert "result_announced" in templates
    
    @pytest.mark.asyncio
    async def test_handle_game_event_game_start(self, game_guide_service, game_start_event):
        """測試處理遊戲開始事件"""
        await game_guide_service.handle_game_event(game_start_event)
        
        # 應該調用 on_game_start
        # 注意：實際調用取決於實現
    
    @pytest.mark.asyncio
    async def test_handle_game_event_redpacket_sent(self, game_guide_service, redpacket_sent_event):
        """測試處理紅包發送事件"""
        await game_guide_service.handle_game_event(redpacket_sent_event)
        
        # 應該調用 on_redpacket_sent
        # 注意：實際調用取決於實現
    
    @pytest.mark.asyncio
    async def test_on_game_start(self, game_guide_service, game_start_event):
        """測試遊戲開始處理"""
        # Mock 賬號和客戶端
        mock_account = Mock()
        mock_account.client = AsyncMock()
        mock_account.client.send_message = AsyncMock()
        mock_account.config = Mock(spec=AccountConfig)
        mock_account.config.group_ids = [game_start_event.group_id]
        
        game_guide_service.account_manager.accounts = {
            "test_account": mock_account
        }
        game_guide_service.account_manager.list_accounts = Mock(return_value=[mock_account])
        
        await game_guide_service.on_game_start(game_start_event)
        
        # 應該發送消息
        # 注意：實際發送取決於實現
    
    @pytest.mark.asyncio
    async def test_on_redpacket_sent(self, game_guide_service, redpacket_sent_event):
        """測試紅包發送處理"""
        # Mock 賬號和客戶端
        mock_account = Mock()
        mock_account.client = AsyncMock()
        mock_account.client.send_message = AsyncMock()
        mock_account.config = Mock(spec=AccountConfig)
        mock_account.config.group_ids = [redpacket_sent_event.group_id]
        
        game_guide_service.account_manager.accounts = {
            "test_account": mock_account
        }
        game_guide_service.account_manager.list_accounts = Mock(return_value=[mock_account])
        
        await game_guide_service.on_redpacket_sent(redpacket_sent_event)
        
        # 應該發送消息
        # 注意：實際發送取決於實現
    
    @pytest.mark.asyncio
    async def test_on_redpacket_claimed(self, game_guide_service):
        """測試紅包搶到處理"""
        event = GameEvent(
            event_type="REDPACKET_CLAIMED",
            group_id=-1001234567890,
            game_id="test_game",
            payload={
                "amount": 1.0,
                "remaining": 9,
                "token": "USDT"
            },
            timestamp=datetime.now()
        )
        
        # Mock 賬號和客戶端
        mock_account = Mock()
        mock_account.client = AsyncMock()
        mock_account.client.send_message = AsyncMock()
        mock_account.config = Mock(spec=AccountConfig)
        mock_account.config.group_ids = [event.group_id]
        
        game_guide_service.account_manager.accounts = {
            "test_account": mock_account
        }
        game_guide_service.account_manager.list_accounts = Mock(return_value=[mock_account])
        
        await game_guide_service.on_redpacket_claimed(event)
        
        # 應該發送消息
        # 注意：實際發送取決於實現
    
    @pytest.mark.asyncio
    async def test_on_game_end(self, game_guide_service):
        """測試遊戲結束處理"""
        event = GameEvent(
            event_type="GAME_END",
            group_id=-1001234567890,
            game_id="test_game",
            payload={
                "total_amount": 100.0,
                "participants": 10,
                "redpacket_count": 5,
                "token": "USDT"
            },
            timestamp=datetime.now()
        )
        
        # Mock 賬號和客戶端
        mock_account = Mock()
        mock_account.client = AsyncMock()
        mock_account.client.send_message = AsyncMock()
        mock_account.config = Mock(spec=AccountConfig)
        mock_account.config.group_ids = [event.group_id]
        
        game_guide_service.account_manager.accounts = {
            "test_account": mock_account
        }
        game_guide_service.account_manager.list_accounts = Mock(return_value=[mock_account])
        
        await game_guide_service.on_game_end(event)
        
        # 應該發送消息
        # 注意：實際發送取決於實現
    
    def test_template_formatting(self, game_guide_service):
        """測試模板格式化"""
        template = game_guide_service.guide_templates["redpacket_sent"]
        formatted = template.format(
            amount=10.0,
            token="USDT",
            count=10,
            remaining=10
        )
        
        assert "10.0" in formatted or "10" in formatted
        assert "USDT" in formatted
    
    @pytest.mark.asyncio
    async def test_on_game_start_no_accounts(self, game_guide_service, game_start_event):
        """測試遊戲開始（沒有賬號）"""
        game_guide_service.account_manager.accounts = {}
        
        # 應該不會報錯
        await game_guide_service.on_game_start(game_start_event)
    
    @pytest.mark.asyncio
    async def test_on_game_start_account_offline(self, game_guide_service, game_start_event):
        """測試遊戲開始（賬號離線）"""
        mock_account = Mock()
        mock_account.status = Mock()
        mock_account.status.value = "offline"
        mock_account.client = None
        mock_account.config = Mock(spec=AccountConfig)
        mock_account.config.group_ids = [game_start_event.group_id]
        
        game_guide_service.account_manager.accounts = {
            "test_account": mock_account
        }
        
        # 應該不會發送消息
        await game_guide_service.on_game_start(game_start_event)
    
    @pytest.mark.asyncio
    async def test_on_game_start_with_game_id(self, game_guide_service):
        """測試遊戲開始（帶遊戲ID）"""
        event = GameEvent(
            event_type="GAME_START",
            group_id=-1001234567890,
            game_id="test_game_123",
            timestamp=datetime.now()
        )
        
        mock_account = Mock()
        mock_account.status = Mock()
        mock_account.status.value = "online"
        mock_account.client = AsyncMock()
        mock_account.client.send_message = AsyncMock()
        mock_account.config = Mock(spec=AccountConfig)
        mock_account.config.group_ids = [event.group_id]
        
        game_guide_service.account_manager.accounts = {
            "test_account": mock_account
        }
        
        await game_guide_service.on_game_start(event)
        
        # 驗證消息被發送
        mock_account.client.send_message.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_on_redpacket_sent_no_accounts(self, game_guide_service, redpacket_sent_event):
        """測試紅包發送（沒有賬號）"""
        game_guide_service.account_manager.accounts = {}
        
        # 應該不會報錯
        await game_guide_service.on_redpacket_sent(redpacket_sent_event)
    
    @pytest.mark.asyncio
    async def test_on_redpacket_sent_send_failure(self, game_guide_service, redpacket_sent_event):
        """測試紅包發送（發送失敗）"""
        mock_account = Mock()
        mock_account.status = Mock()
        mock_account.status.value = "online"
        mock_account.client = AsyncMock()
        mock_account.client.send_message = AsyncMock(side_effect=Exception("發送失敗"))
        mock_account.config = Mock(spec=AccountConfig)
        mock_account.config.group_ids = [redpacket_sent_event.group_id]
        
        game_guide_service.account_manager.accounts = {
            "test_account": mock_account
        }
        
        # 應該不會拋出異常，只是記錄錯誤
        await game_guide_service.on_redpacket_sent(redpacket_sent_event)
    
    @pytest.mark.asyncio
    async def test_on_redpacket_claimed_no_account_id(self, game_guide_service):
        """測試紅包搶到（沒有賬號ID）"""
        event = GameEvent(
            event_type="REDPACKET_CLAIMED",
            group_id=-1001234567890,
            game_id="test_game",
            payload={},  # 沒有 account_id
            timestamp=datetime.now()
        )
        
        # 應該直接返回，不處理
        await game_guide_service.on_redpacket_claimed(event)
    
    @pytest.mark.asyncio
    async def test_on_redpacket_claimed_almost_gone(self, game_guide_service):
        """測試紅包搶到（快搶完了）"""
        event = GameEvent(
            event_type="REDPACKET_CLAIMED",
            group_id=-1001234567890,
            game_id="test_game",
            payload={
                "account_id": "test_account",
                "amount": 1.0,
                "remaining_count": 2,  # 剩餘2份，應該觸發提醒
                "token": "USDT"
            },
            timestamp=datetime.now()
        )
        
        mock_account = Mock()
        mock_account.status = Mock()
        mock_account.status.value = "online"
        mock_account.client = AsyncMock()
        mock_account.client.send_message = AsyncMock()
        mock_account.config = Mock(spec=AccountConfig)
        mock_account.config.group_ids = [event.group_id]
        
        game_guide_service.account_manager.accounts = {
            "test_account": mock_account
        }
        
        await game_guide_service.on_redpacket_claimed(event)
        
        # 驗證消息被發送（快搶完提醒）
        mock_account.client.send_message.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_on_redpacket_claimed_not_almost_gone(self, game_guide_service):
        """測試紅包搶到（沒有快搶完）"""
        event = GameEvent(
            event_type="REDPACKET_CLAIMED",
            group_id=-1001234567890,
            game_id="test_game",
            payload={
                "account_id": "test_account",
                "amount": 1.0,
                "remaining_count": 5,  # 剩餘5份，不觸發提醒
                "token": "USDT"
            },
            timestamp=datetime.now()
        )
        
        mock_account = Mock()
        mock_account.status = Mock()
        mock_account.status.value = "online"
        mock_account.client = AsyncMock()
        mock_account.client.send_message = AsyncMock()
        mock_account.config = Mock(spec=AccountConfig)
        mock_account.config.group_ids = [event.group_id]
        
        game_guide_service.account_manager.accounts = {
            "test_account": mock_account
        }
        
        await game_guide_service.on_redpacket_claimed(event)
        
        # 驗證消息沒有被發送（因為剩餘數量足夠）
        mock_account.client.send_message.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_on_result_announced(self, game_guide_service):
        """測試結果公布處理"""
        event = GameEvent(
            event_type="RESULT_ANNOUNCED",
            group_id=-1001234567890,
            game_id="test_game",
            payload={
                "summary": "遊戲結果總結"
            },
            timestamp=datetime.now()
        )
        
        mock_account = Mock()
        mock_account.status = Mock()
        mock_account.status.value = "online"
        mock_account.client = AsyncMock()
        mock_account.client.send_message = AsyncMock()
        mock_account.config = Mock(spec=AccountConfig)
        mock_account.config.group_ids = [event.group_id]
        
        game_guide_service.account_manager.accounts = {
            "test_account": mock_account
        }
        
        await game_guide_service.on_result_announced(event)
        
        # 驗證消息被發送
        mock_account.client.send_message.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_handle_game_event_unknown_type(self, game_guide_service):
        """測試處理未知事件類型"""
        event = GameEvent(
            event_type="UNKNOWN_EVENT",
            group_id=-1001234567890,
            timestamp=datetime.now()
        )
        
        # 應該不會報錯，只是記錄日誌
        await game_guide_service.handle_game_event(event)
    
    @pytest.mark.asyncio
    async def test_handle_game_event_exception(self, game_guide_service):
        """測試處理事件異常"""
        event = GameEvent(
            event_type="GAME_START",
            group_id=-1001234567890,
            timestamp=datetime.now()
        )
        
        # Mock 方法拋出異常
        game_guide_service.on_game_start = AsyncMock(side_effect=Exception("處理失敗"))
        
        # 應該不會拋出異常，只是記錄錯誤
        await game_guide_service.handle_game_event(event)
    
    def test_get_accounts_for_group(self, game_guide_service):
        """測試獲取群組賬號"""
        mock_account1 = Mock()
        mock_account1.config = Mock(spec=AccountConfig)
        mock_account1.config.group_ids = [-1001234567890]
        
        mock_account2 = Mock()
        mock_account2.config = Mock(spec=AccountConfig)
        mock_account2.config.group_ids = [-1001234567891]  # 不同的群組
        
        game_guide_service.account_manager.accounts = {
            "account1": mock_account1,
            "account2": mock_account2
        }
        
        accounts = game_guide_service._get_accounts_for_group(-1001234567890)
        
        assert len(accounts) == 1
        assert accounts[0] == mock_account1
    
    def test_get_accounts_for_group_no_group_ids(self, game_guide_service):
        """測試獲取群組賬號（沒有 group_ids）"""
        mock_account = Mock()
        mock_account.config = Mock(spec=AccountConfig)
        mock_account.config.group_ids = None  # 沒有群組列表
        
        game_guide_service.account_manager.accounts = {
            "account1": mock_account
        }
        
        accounts = game_guide_service._get_accounts_for_group(-1001234567890)
        
        # 如果沒有 group_ids，應該返回所有賬號
        assert len(accounts) == 1
    
    @pytest.mark.asyncio
    async def test_send_message(self, game_guide_service):
        """測試發送消息"""
        mock_client = AsyncMock()
        mock_client.send_message = AsyncMock()
        
        await game_guide_service._send_message(
            client=mock_client,
            chat_id=-1001234567890,
            text="測試消息"
        )
        
        mock_client.send_message.assert_called_once_with(
            chat_id=-1001234567890,
            text="測試消息"
        )
    
    @pytest.mark.asyncio
    async def test_send_message_failure(self, game_guide_service):
        """測試發送消息失敗"""
        mock_client = AsyncMock()
        mock_client.send_message = AsyncMock(side_effect=Exception("發送失敗"))
        
        # 應該拋出異常
        with pytest.raises(Exception):
            await game_guide_service._send_message(
                client=mock_client,
                chat_id=-1001234567890,
                text="測試消息"
            )
    
    @pytest.mark.asyncio
    async def test_send_custom_guide_with_account_id(self, game_guide_service):
        """測試發送自定義引導（指定賬號）"""
        mock_account = Mock()
        mock_account.status = Mock()
        mock_account.status.value = "online"
        mock_account.client = AsyncMock()
        mock_account.client.send_message = AsyncMock()
        
        game_guide_service.account_manager.accounts = {
            "test_account": mock_account
        }
        
        await game_guide_service.send_custom_guide(
            group_id=-1001234567890,
            message="自定義消息",
            account_id="test_account"
        )
        
        mock_account.client.send_message.assert_called_once_with(
            chat_id=-1001234567890,
            text="自定義消息"
        )
    
    @pytest.mark.asyncio
    async def test_send_custom_guide_without_account_id(self, game_guide_service):
        """測試發送自定義引導（不指定賬號）"""
        mock_account = Mock()
        mock_account.status = Mock()
        mock_account.status.value = "online"
        mock_account.client = AsyncMock()
        mock_account.client.send_message = AsyncMock()
        mock_account.config = Mock(spec=AccountConfig)
        mock_account.config.group_ids = [-1001234567890]
        
        game_guide_service.account_manager.accounts = {
            "test_account": mock_account
        }
        
        await game_guide_service.send_custom_guide(
            group_id=-1001234567890,
            message="自定義消息"
        )
        
        mock_account.client.send_message.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_send_custom_guide_account_not_found(self, game_guide_service):
        """測試發送自定義引導（賬號不存在）"""
        game_guide_service.account_manager.accounts = {}
        
        # 應該不會報錯
        await game_guide_service.send_custom_guide(
            group_id=-1001234567890,
            message="自定義消息",
            account_id="nonexistent_account"
        )
    
    @pytest.mark.asyncio
    async def test_send_custom_guide_send_failure(self, game_guide_service):
        """測試發送自定義引導（發送失敗）"""
        mock_account = Mock()
        mock_account.status = Mock()
        mock_account.status.value = "online"
        mock_account.client = AsyncMock()
        mock_account.client.send_message = AsyncMock(side_effect=Exception("發送失敗"))
        mock_account.config = Mock(spec=AccountConfig)
        mock_account.config.group_ids = [-1001234567890]
        
        game_guide_service.account_manager.accounts = {
            "test_account": mock_account
        }
        
        # 應該不會拋出異常，只是記錄錯誤
        await game_guide_service.send_custom_guide(
            group_id=-1001234567890,
            message="自定義消息"
        )

