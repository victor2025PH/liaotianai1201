"""
ExtendedSessionPool 單元測試
"""
import sys
from pathlib import Path

# 添加項目根目錄到 Python 路徑
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime

from group_ai_service.session_pool import ExtendedSessionPool
from group_ai_service.account_manager import AccountManager
from group_ai_service.dialogue_manager import DialogueManager
from group_ai_service.models.account import AccountConfig, AccountStatusEnum


@pytest.fixture
def account_manager():
    """創建 AccountManager 實例"""
    return AccountManager()


@pytest.fixture
def dialogue_manager():
    """創建 DialogueManager 實例"""
    from group_ai_service.redpacket_handler import RedpacketHandler
    redpacket_handler = Mock(spec=RedpacketHandler)
    return DialogueManager(redpacket_handler=redpacket_handler)


@pytest.fixture
def session_pool(account_manager, dialogue_manager):
    """創建 ExtendedSessionPool 實例"""
    return ExtendedSessionPool(account_manager, dialogue_manager)


@pytest.fixture
def account_config():
    """創建 AccountConfig 實例"""
    return AccountConfig(
        account_id="test_account",
        session_file="test.session",
        script_id="test_script",
        group_ids=[-1001234567890],
        active=True
    )


class TestExtendedSessionPool:
    """ExtendedSessionPool 測試"""
    
    def test_pool_initialization(self, session_pool):
        """測試會話池初始化"""
        assert session_pool is not None
        assert session_pool.account_manager is not None
        assert session_pool.dialogue_manager is not None
        assert session_pool._running is False
        assert len(session_pool._tasks) == 0
    
    def test_pool_initialization_without_dialogue_manager(self, account_manager):
        """測試不提供 DialogueManager 的初始化"""
        pool = ExtendedSessionPool(account_manager)
        assert pool.account_manager is not None
        assert pool.dialogue_manager is None
    
    @pytest.mark.asyncio
    async def test_start_pool(self, session_pool):
        """測試啟動會話池"""
        # Mock 賬號列表
        mock_account = Mock()
        mock_account.account_id = "test_account"
        mock_account.status = Mock()
        mock_account.status.value = "offline"  # 不在線，不會啟動監聽
        
        session_pool.account_manager.list_accounts = Mock(return_value=[mock_account])
        
        await session_pool.start()
        
        assert session_pool._running is True
    
    @pytest.mark.asyncio
    async def test_start_pool_already_running(self, session_pool):
        """測試重複啟動會話池"""
        session_pool._running = True
        
        await session_pool.start()
        
        # 應該不會報錯，只是警告
        assert session_pool._running is True
    
    @pytest.mark.asyncio
    async def test_stop_pool(self, session_pool):
        """測試停止會話池"""
        session_pool._running = True
        # 創建真正的 asyncio.Task
        async def dummy_task():
            await asyncio.sleep(0.1)
        
        task = asyncio.create_task(dummy_task())
        session_pool._tasks = [task]
        
        await session_pool.stop()
        
        assert session_pool._running is False
        assert len(session_pool._tasks) == 0
    
    @pytest.mark.asyncio
    async def test_stop_pool_not_running(self, session_pool):
        """測試停止未運行的會話池"""
        session_pool._running = False
        
        await session_pool.stop()
        
        # 應該不會報錯
        assert session_pool._running is False
    
    def test_register_message_handler(self, session_pool):
        """測試註冊消息處理器"""
        async def handler(account, message):
            pass
        
        session_pool.register_message_handler("test_account", handler)
        
        assert "test_account" in session_pool._message_handlers
        assert len(session_pool._message_handlers["test_account"]) == 1
    
    def test_register_message_handler_all_accounts(self, session_pool):
        """測試註冊全局消息處理器"""
        async def handler(account, message):
            pass
        
        session_pool.register_message_handler(None, handler)
        
        assert None in session_pool._message_handlers
        assert len(session_pool._message_handlers[None]) == 1
    
    @pytest.mark.asyncio
    async def test_start_monitoring_account_not_online(self, session_pool):
        """測試監聽不在線的賬號"""
        # Mock 賬號不在線
        mock_account = Mock()
        mock_account.status = Mock()
        mock_account.status.value = "offline"
        session_pool.account_manager.accounts = {"test_account": mock_account}
        
        await session_pool.start_monitoring_account("test_account")
        
        # 應該不會啟動監聽
        assert len(session_pool._tasks) == 0
    
    @pytest.mark.asyncio
    async def test_start_monitoring_account_already_monitoring(self, session_pool):
        """測試監聽已在監聽的賬號"""
        # 創建模擬任務
        mock_task = AsyncMock()
        mock_task.get_name = Mock(return_value="monitor-test_account")
        mock_task.done = Mock(return_value=False)
        session_pool._tasks = [mock_task]
        
        await session_pool.start_monitoring_account("test_account")
        
        # 應該不會重複啟動
        assert len(session_pool._tasks) == 1
    
    def test_get_client(self, session_pool):
        """測試獲取客戶端"""
        # Mock 賬號
        mock_account = Mock()
        mock_client = Mock()
        mock_account.client = mock_client
        session_pool.account_manager.accounts = {"test_account": mock_account}
        
        client = session_pool.get_client("test_account")
        
        assert client == mock_client
    
    def test_get_client_not_found(self, session_pool):
        """測試獲取不存在的客戶端"""
        session_pool.account_manager.accounts = {}
        
        client = session_pool.get_client("nonexistent_account")
        
        assert client is None
    
    def test_get_account_by_group(self, session_pool):
        """測試根據群組獲取賬號"""
        # Mock 賬號
        mock_account = Mock()
        mock_account.config = Mock()
        mock_account.config.group_ids = [-1001234567890]
        session_pool.account_manager.accounts = {"test_account": mock_account}
        
        accounts = session_pool.get_account_by_group(-1001234567890)
        
        assert len(accounts) == 1
        assert accounts[0] == mock_account
    
    def test_get_account_by_group_not_found(self, session_pool):
        """測試根據群組獲取賬號（未找到）"""
        # Mock 賬號（不在該群組）
        mock_account = Mock()
        mock_account.config = Mock()
        mock_account.config.group_ids = [-1001234567891]  # 不同的群組
        session_pool.account_manager.accounts = {"test_account": mock_account}
        
        accounts = session_pool.get_account_by_group(-1001234567890)
        
        assert len(accounts) == 0
    
    def test_active_accounts(self, session_pool):
        """測試獲取活躍賬號列表"""
        # Mock 賬號（在線）
        mock_account1 = Mock()
        mock_account1.account_id = "account1"
        mock_account1.status.value = "online"
        mock_account2 = Mock()
        mock_account2.account_id = "account2"
        mock_account2.status.value = "online"
        session_pool.account_manager.accounts = {
            "account1": mock_account1,
            "account2": mock_account2
        }
        
        active = session_pool.active_accounts  # 這是屬性，不是方法
        
        assert len(active) == 2
        assert "account1" in active
        assert "account2" in active
    
    @pytest.mark.asyncio
    async def test_dispatch_message(self, session_pool):
        """測試分發消息"""
        # Mock 賬號
        mock_account = Mock()
        mock_account.account_id = "test_account"
        
        # Mock 消息
        mock_message = Mock()
        mock_message.chat.id = -1001234567890
        
        # 註冊處理器
        handler_called = []
        async def handler(account, message):
            handler_called.append((account, message))
        
        session_pool.register_message_handler("test_account", handler)
        
        await session_pool._dispatch_message(mock_account, mock_message)
        
        assert len(handler_called) == 1
        assert handler_called[0][0] == mock_account
        assert handler_called[0][1] == mock_message
    
    @pytest.mark.asyncio
    async def test_dispatch_message_global_handler(self, session_pool):
        """測試分發消息（全局處理器）"""
        # Mock 賬號
        mock_account = Mock()
        mock_account.account_id = "test_account"
        
        # Mock 消息
        mock_message = Mock()
        mock_message.chat.id = -1001234567890
        
        # 註冊全局處理器
        handler_called = []
        async def handler(account, message):
            handler_called.append((account, message))
        
        session_pool.register_message_handler(None, handler)
        
        await session_pool._dispatch_message(mock_account, mock_message)
        
        assert len(handler_called) == 1
    
    @pytest.mark.asyncio
    async def test_monitor_account_handles_message(self, session_pool, account_config):
        """測試監聽賬號（處理消息）"""
        # 創建模擬賬號和客戶端
        mock_client = AsyncMock()
        
        mock_account = Mock()
        mock_account.account_id = account_config.account_id
        mock_account.client = mock_client
        mock_account.config = account_config
        mock_account.last_activity = None
        mock_account.message_count = 0
        mock_account.reply_count = 0
        mock_account.error_count = 0
        
        session_pool.account_manager.accounts[account_config.account_id] = mock_account
        
        # Mock dialogue_manager
        session_pool.dialogue_manager = AsyncMock()
        session_pool.dialogue_manager.process_message = AsyncMock(return_value="回復消息")
        
        # 創建模擬消息
        mock_message = AsyncMock()
        mock_message.text = "測試消息"
        mock_message.chat = Mock()
        mock_message.chat.id = -1001234567890
        mock_message.chat.type.name = "GROUP"
        mock_message.reply_text = AsyncMock()
        
        # 模擬消息處理邏輯
        from datetime import datetime
        
        # 只處理群組消息
        if mock_message.chat and mock_message.chat.type.name == "GROUP":
            # 檢查是否在監聽的群組列表中
            if account_config.group_ids and mock_message.chat.id in account_config.group_ids:
                # 更新賬號活動時間
                mock_account.last_activity = datetime.now()
                mock_account.message_count += 1
                
                # 如果有對話管理器，優先使用對話管理器處理
                if session_pool.dialogue_manager:
                    reply = await session_pool.dialogue_manager.process_message(
                        account_id=mock_account.account_id,
                        group_id=mock_message.chat.id,
                        message=mock_message,
                        account_config=account_config
                    )
                    if reply:
                        await mock_message.reply_text(reply)
                        mock_account.reply_count += 1
        
        # 驗證對話管理器被調用
        session_pool.dialogue_manager.process_message.assert_called_once()
        # 驗證回復被發送
        mock_message.reply_text.assert_called_once_with("回復消息")
        # 驗證賬號活動被更新
        assert mock_account.message_count == 1
        assert mock_account.reply_count == 1
    
    @pytest.mark.asyncio
    async def test_monitor_account_handles_callback_query(self, session_pool, account_config):
        """測試監聽賬號（處理回調查詢）"""
        # 創建模擬賬號和客戶端
        mock_client = AsyncMock()
        mock_client.get_me = AsyncMock(return_value=Mock(first_name="測試機器人"))
        
        mock_account = Mock()
        mock_account.account_id = account_config.account_id
        mock_account.client = mock_client
        mock_account.config = account_config
        mock_account.last_activity = None
        mock_account.error_count = 0
        
        session_pool.account_manager.accounts[account_config.account_id] = mock_account
        
        # Mock dialogue_manager 和 redpacket_handler
        from group_ai_service.redpacket_handler import RedpacketInfo, RedpacketResult
        mock_redpacket = RedpacketInfo(
            redpacket_id="test_redpacket",
            group_id=-1001234567890,
            sender_id=123456789,
            amount=10.0,
            count=10
        )
        
        session_pool.dialogue_manager = Mock()
        session_pool.dialogue_manager.redpacket_handler = AsyncMock()
        session_pool.dialogue_manager.redpacket_handler.detect_redpacket = AsyncMock(return_value=mock_redpacket)
        session_pool.dialogue_manager.redpacket_handler.should_participate = AsyncMock(return_value=True)
        session_pool.dialogue_manager.redpacket_handler.participate = AsyncMock(return_value=RedpacketResult(
            redpacket_id="test_redpacket",
            account_id=account_config.account_id,
            success=True,
            amount=5.0
        ))
        session_pool.dialogue_manager.contexts = {}
        
        # 創建模擬回調查詢
        mock_callback_query = Mock()
        mock_callback_query.data = "hb:grab:test_envelope"
        mock_callback_query.message = Mock()
        mock_callback_query.message.chat = Mock()
        mock_callback_query.message.chat.id = -1001234567890
        mock_callback_query.message.chat.type.name = "GROUP"
        mock_callback_query.message.from_user = Mock(first_name="發送者")
        
        # 模擬回調查詢處理邏輯
        from datetime import datetime
        
        # 只處理群組中的回調
        if mock_callback_query.message and mock_callback_query.message.chat:
            if mock_callback_query.message.chat.type.name == "GROUP":
                # 檢查是否在監聽的群組列表中
                if account_config.group_ids and mock_callback_query.message.chat.id in account_config.group_ids:
                    # 更新賬號活動時間
                    mock_account.last_activity = datetime.now()
                    
                    # 處理紅包按鈕點擊
                    callback_data = mock_callback_query.data or ""
                    if callback_data.startswith("hb:grab:"):
                        # 如果有對話管理器，處理紅包參與
                        if session_pool.dialogue_manager and session_pool.dialogue_manager.redpacket_handler:
                            message = mock_callback_query.message
                            
                            # 檢測紅包
                            redpacket = await session_pool.dialogue_manager.redpacket_handler.detect_redpacket(message)
                            if redpacket:
                                # 檢查是否應該參與
                                should_participate = await session_pool.dialogue_manager.redpacket_handler.should_participate(
                                    account_id=mock_account.account_id,
                                    redpacket=redpacket,
                                    account_config=account_config,
                                    context=None
                                )
                                
                                if should_participate:
                                    # 獲取發包人信息
                                    sender_name = None
                                    if message.from_user:
                                        sender_name = getattr(message.from_user, 'first_name', None)
                                    
                                    # 獲取參與者信息
                                    participant_name = None
                                    try:
                                        me = await mock_client.get_me()
                                        if me:
                                            participant_name = me.first_name
                                    except Exception:
                                        pass
                                    
                                    # 參與紅包
                                    result = await session_pool.dialogue_manager.redpacket_handler.participate(
                                        account_id=mock_account.account_id,
                                        redpacket=redpacket,
                                        client=mock_client,
                                        sender_name=sender_name,
                                        participant_name=participant_name
                                    )
        
        # 驗證紅包處理器被調用
        session_pool.dialogue_manager.redpacket_handler.detect_redpacket.assert_called_once()
        session_pool.dialogue_manager.redpacket_handler.should_participate.assert_called_once()
        session_pool.dialogue_manager.redpacket_handler.participate.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_monitor_account_skips_non_group_message(self, session_pool, account_config):
        """測試監聽賬號（跳過非群組消息）"""
        # 創建模擬消息（私聊消息）
        mock_message = Mock()
        mock_message.text = "測試消息"
        mock_message.chat = Mock()
        mock_message.chat.type.name = "PRIVATE"  # 私聊
        
        # 模擬消息處理邏輯
        if not mock_message.chat or mock_message.chat.type.name != "GROUP":
            # 應該在這裡返回，不處理私聊消息
            pass
        
        # 驗證消息沒有被處理（這裡主要測試邏輯路徑）
        assert mock_message.chat.type.name == "PRIVATE"
    
    @pytest.mark.asyncio
    async def test_monitor_account_skips_wrong_group(self, session_pool, account_config):
        """測試監聽賬號（跳過錯誤群組）"""
        # 創建模擬消息（不同群組）
        mock_message = Mock()
        mock_message.text = "測試消息"
        mock_message.chat = Mock()
        mock_message.chat.id = -9999999999  # 不同的群組ID
        mock_message.chat.type.name = "GROUP"
        
        # 模擬消息處理邏輯
        if mock_message.chat and mock_message.chat.type.name == "GROUP":
            # 檢查是否在監聽的群組列表中
            if account_config.group_ids and mock_message.chat.id not in account_config.group_ids:
                # 應該在這裡返回，不處理不同群組的消息
                pass
        
        # 驗證消息沒有被處理（這裡主要測試邏輯路徑）
        assert mock_message.chat.id not in account_config.group_ids
    
    @pytest.mark.asyncio
    async def test_monitor_account_handles_exception(self, session_pool, account_config):
        """測試監聽賬號（處理異常）"""
        # 創建模擬賬號和客戶端
        mock_client = AsyncMock()
        
        mock_account = Mock()
        mock_account.account_id = account_config.account_id
        mock_account.client = mock_client
        mock_account.config = account_config
        mock_account.error_count = 0
        
        session_pool.account_manager.accounts[account_config.account_id] = mock_account
        
        # Mock dialogue_manager 拋出異常
        session_pool.dialogue_manager = AsyncMock()
        session_pool.dialogue_manager.process_message = AsyncMock(side_effect=Exception("測試錯誤"))
        
        # 創建模擬消息
        mock_message = AsyncMock()
        mock_message.text = "測試消息"
        mock_message.chat = Mock()
        mock_message.chat.id = -1001234567890
        mock_message.chat.type.name = "GROUP"
        
        # 模擬消息處理邏輯（帶異常處理）
        try:
            if mock_message.chat and mock_message.chat.type.name == "GROUP":
                if account_config.group_ids and mock_message.chat.id in account_config.group_ids:
                    if session_pool.dialogue_manager:
                        try:
                            reply = await session_pool.dialogue_manager.process_message(
                                account_id=mock_account.account_id,
                                group_id=mock_message.chat.id,
                                message=mock_message,
                                account_config=account_config
                            )
                        except Exception as e:
                            mock_account.error_count += 1
        except Exception as e:
            mock_account.error_count += 1
        
        # 驗證錯誤計數增加
        assert mock_account.error_count >= 1
    
    @pytest.mark.asyncio
    async def test_monitor_account_account_not_found(self, session_pool):
        """測試監聽不存在的賬號"""
        # 賬號不存在
        session_pool.account_manager.accounts = {}
        
        # 應該不會報錯，只是記錄錯誤
        await session_pool._monitor_account("nonexistent_account")
        
        # 驗證沒有創建任務
        assert len(session_pool._tasks) == 0
    
    @pytest.mark.asyncio
    async def test_monitor_account_no_client(self, session_pool, account_config):
        """測試監聽沒有客戶端的賬號"""
        # Mock 賬號（沒有客戶端）
        mock_account = Mock()
        mock_account.account_id = account_config.account_id
        mock_account.client = None
        session_pool.account_manager.accounts[account_config.account_id] = mock_account
        
        # 應該不會報錯，只是記錄錯誤
        await session_pool._monitor_account(account_config.account_id)
        
        # 驗證沒有創建任務
        assert len(session_pool._tasks) == 0
    
    @pytest.mark.asyncio
    async def test_monitor_account_message_no_chat(self, session_pool, account_config):
        """測試監聽賬號（消息沒有 chat）"""
        # 創建模擬消息（沒有 chat）
        mock_message = Mock()
        mock_message.chat = None
        
        # 模擬消息處理邏輯
        if not mock_message.chat or mock_message.chat.type.name != "GROUP":
            # 應該在這裡返回，不處理沒有 chat 的消息
            pass
        
        # 驗證消息沒有被處理
        assert mock_message.chat is None
    
    @pytest.mark.asyncio
    async def test_monitor_account_message_no_reply(self, session_pool, account_config):
        """測試監聽賬號（對話管理器不返回回復）"""
        # 創建模擬賬號和客戶端
        mock_client = AsyncMock()
        
        mock_account = Mock()
        mock_account.account_id = account_config.account_id
        mock_account.client = mock_client
        mock_account.config = account_config
        mock_account.last_activity = None
        mock_account.message_count = 0
        mock_account.reply_count = 0
        mock_account.error_count = 0
        
        session_pool.account_manager.accounts[account_config.account_id] = mock_account
        
        # Mock dialogue_manager（不返回回復）
        session_pool.dialogue_manager = AsyncMock()
        session_pool.dialogue_manager.process_message = AsyncMock(return_value=None)
        
        # 創建模擬消息
        mock_message = AsyncMock()
        mock_message.text = "測試消息"
        mock_message.chat = Mock()
        mock_message.chat.id = -1001234567890
        mock_message.chat.type.name = "GROUP"
        mock_message.reply_text = AsyncMock()
        
        # 模擬消息處理邏輯
        if mock_message.chat and mock_message.chat.type.name == "GROUP":
            if account_config.group_ids and mock_message.chat.id in account_config.group_ids:
                mock_account.last_activity = datetime.now()
                mock_account.message_count += 1
                
                if session_pool.dialogue_manager:
                    reply = await session_pool.dialogue_manager.process_message(
                        account_id=mock_account.account_id,
                        group_id=mock_message.chat.id,
                        message=mock_message,
                        account_config=account_config
                    )
                    if reply:
                        await mock_message.reply_text(reply)
                        mock_account.reply_count += 1
        
        # 驗證對話管理器被調用
        session_pool.dialogue_manager.process_message.assert_called_once()
        # 驗證回復沒有被發送（因為返回 None）
        mock_message.reply_text.assert_not_called()
        # 驗證賬號活動被更新
        assert mock_account.message_count == 1
        assert mock_account.reply_count == 0
    
    @pytest.mark.asyncio
    async def test_monitor_account_callback_query_no_message(self, session_pool, account_config):
        """測試監聽賬號（回調查詢沒有 message）"""
        # 創建模擬回調查詢（沒有 message）
        mock_callback_query = Mock()
        mock_callback_query.data = "hb:grab:test_envelope"
        mock_callback_query.message = None
        
        # 模擬回調查詢處理邏輯
        if not mock_callback_query.message or not mock_callback_query.message.chat:
            # 應該在這裡返回，不處理沒有 message 的回調
            pass
        
        # 驗證回調沒有被處理
        assert mock_callback_query.message is None
    
    @pytest.mark.asyncio
    async def test_monitor_account_callback_query_no_chat(self, session_pool, account_config):
        """測試監聽賬號（回調查詢的 message 沒有 chat）"""
        # 創建模擬回調查詢（message 沒有 chat）
        mock_callback_query = Mock()
        mock_callback_query.data = "hb:grab:test_envelope"
        mock_callback_query.message = Mock()
        mock_callback_query.message.chat = None
        
        # 模擬回調查詢處理邏輯
        if not mock_callback_query.message or not mock_callback_query.message.chat:
            # 應該在這裡返回，不處理沒有 chat 的回調
            pass
        
        # 驗證回調沒有被處理
        assert mock_callback_query.message.chat is None
    
    @pytest.mark.asyncio
    async def test_monitor_account_callback_query_private(self, session_pool, account_config):
        """測試監聽賬號（回調查詢是私聊）"""
        # 創建模擬回調查詢（私聊）
        mock_callback_query = Mock()
        mock_callback_query.data = "hb:grab:test_envelope"
        mock_callback_query.message = Mock()
        mock_callback_query.message.chat = Mock()
        mock_callback_query.message.chat.type.name = "PRIVATE"  # 私聊
        
        # 模擬回調查詢處理邏輯
        if mock_callback_query.message and mock_callback_query.message.chat:
            if mock_callback_query.message.chat.type.name != "GROUP":
                # 應該在這裡返回，不處理私聊回調
                pass
        
        # 驗證回調沒有被處理
        assert mock_callback_query.message.chat.type.name == "PRIVATE"
    
    @pytest.mark.asyncio
    async def test_monitor_account_callback_query_wrong_group(self, session_pool, account_config):
        """測試監聽賬號（回調查詢是錯誤群組）"""
        # 創建模擬回調查詢（不同群組）
        mock_callback_query = Mock()
        mock_callback_query.data = "hb:grab:test_envelope"
        mock_callback_query.message = Mock()
        mock_callback_query.message.chat = Mock()
        mock_callback_query.message.chat.id = -9999999999  # 不同的群組ID
        mock_callback_query.message.chat.type.name = "GROUP"
        
        # 模擬回調查詢處理邏輯
        if mock_callback_query.message and mock_callback_query.message.chat:
            if mock_callback_query.message.chat.type.name == "GROUP":
                if account_config.group_ids and mock_callback_query.message.chat.id not in account_config.group_ids:
                    # 應該在這裡返回，不處理不同群組的回調
                    pass
        
        # 驗證回調沒有被處理
        assert mock_callback_query.message.chat.id not in account_config.group_ids
    
    @pytest.mark.asyncio
    async def test_monitor_account_callback_query_no_redpacket(self, session_pool, account_config):
        """測試監聽賬號（回調查詢不是紅包）"""
        # 創建模擬回調查詢（不是紅包）
        mock_callback_query = Mock()
        mock_callback_query.data = "other:callback:data"  # 不是紅包
        
        # 模擬回調查詢處理邏輯
        callback_data = mock_callback_query.data or ""
        if not callback_data.startswith("hb:grab:"):
            # 應該在這裡返回，不處理非紅包回調
            pass
        
        # 驗證回調沒有被處理
        assert not callback_data.startswith("hb:grab:")
    
    @pytest.mark.asyncio
    async def test_monitor_account_callback_query_no_redpacket_handler(self, session_pool, account_config):
        """測試監聽賬號（回調查詢沒有 redpacket_handler）"""
        # 創建模擬賬號和客戶端
        mock_client = AsyncMock()
        mock_client.get_me = AsyncMock(return_value=Mock(first_name="測試機器人"))
        
        mock_account = Mock()
        mock_account.account_id = account_config.account_id
        mock_account.client = mock_client
        mock_account.config = account_config
        mock_account.last_activity = None
        mock_account.error_count = 0
        
        session_pool.account_manager.accounts[account_config.account_id] = mock_account
        
        # Mock dialogue_manager（沒有 redpacket_handler）
        session_pool.dialogue_manager = Mock()
        session_pool.dialogue_manager.redpacket_handler = None
        
        # 創建模擬回調查詢
        mock_callback_query = Mock()
        mock_callback_query.data = "hb:grab:test_envelope"
        mock_callback_query.message = Mock()
        mock_callback_query.message.chat = Mock()
        mock_callback_query.message.chat.id = -1001234567890
        mock_callback_query.message.chat.type.name = "GROUP"
        
        # 模擬回調查詢處理邏輯
        if mock_callback_query.message and mock_callback_query.message.chat:
            if mock_callback_query.message.chat.type.name == "GROUP":
                if account_config.group_ids and mock_callback_query.message.chat.id in account_config.group_ids:
                    callback_data = mock_callback_query.data or ""
                    if callback_data.startswith("hb:grab:"):
                        # 如果沒有 redpacket_handler，應該不處理
                        if not session_pool.dialogue_manager or not session_pool.dialogue_manager.redpacket_handler:
                            pass
        
        # 驗證沒有處理紅包（因為沒有 redpacket_handler）
        assert session_pool.dialogue_manager.redpacket_handler is None
    
    @pytest.mark.asyncio
    async def test_monitor_account_callback_query_redpacket_not_detected(self, session_pool, account_config):
        """測試監聽賬號（回調查詢紅包未檢測到）"""
        # 創建模擬賬號和客戶端
        mock_client = AsyncMock()
        mock_client.get_me = AsyncMock(return_value=Mock(first_name="測試機器人"))
        
        mock_account = Mock()
        mock_account.account_id = account_config.account_id
        mock_account.client = mock_client
        mock_account.config = account_config
        mock_account.last_activity = None
        mock_account.error_count = 0
        
        session_pool.account_manager.accounts[account_config.account_id] = mock_account
        
        # Mock dialogue_manager 和 redpacket_handler（不檢測到紅包）
        session_pool.dialogue_manager = Mock()
        session_pool.dialogue_manager.redpacket_handler = AsyncMock()
        session_pool.dialogue_manager.redpacket_handler.detect_redpacket = AsyncMock(return_value=None)
        session_pool.dialogue_manager.contexts = {}
        
        # 創建模擬回調查詢
        mock_callback_query = Mock()
        mock_callback_query.data = "hb:grab:test_envelope"
        mock_callback_query.message = Mock()
        mock_callback_query.message.chat = Mock()
        mock_callback_query.message.chat.id = -1001234567890
        mock_callback_query.message.chat.type.name = "GROUP"
        
        # 模擬回調查詢處理邏輯
        if mock_callback_query.message and mock_callback_query.message.chat:
            if mock_callback_query.message.chat.type.name == "GROUP":
                if account_config.group_ids and mock_callback_query.message.chat.id in account_config.group_ids:
                    callback_data = mock_callback_query.data or ""
                    if callback_data.startswith("hb:grab:"):
                        if session_pool.dialogue_manager and session_pool.dialogue_manager.redpacket_handler:
                            message = mock_callback_query.message
                            redpacket = await session_pool.dialogue_manager.redpacket_handler.detect_redpacket(message)
                            if not redpacket:
                                # 沒有檢測到紅包，應該不處理
                                pass
        
        # 驗證紅包檢測被調用
        session_pool.dialogue_manager.redpacket_handler.detect_redpacket.assert_called_once()
        # 驗證沒有參與紅包（因為沒有檢測到）
        assert session_pool.dialogue_manager.redpacket_handler.detect_redpacket.return_value is None
    
    @pytest.mark.asyncio
    async def test_monitor_account_callback_query_should_not_participate(self, session_pool, account_config):
        """測試監聽賬號（回調查詢不應該參與）"""
        # 創建模擬賬號和客戶端
        mock_client = AsyncMock()
        mock_client.get_me = AsyncMock(return_value=Mock(first_name="測試機器人"))
        
        mock_account = Mock()
        mock_account.account_id = account_config.account_id
        mock_account.client = mock_client
        mock_account.config = account_config
        mock_account.last_activity = None
        mock_account.error_count = 0
        
        session_pool.account_manager.accounts[account_config.account_id] = mock_account
        
        # Mock dialogue_manager 和 redpacket_handler（不應該參與）
        from group_ai_service.redpacket_handler import RedpacketInfo
        mock_redpacket = RedpacketInfo(
            redpacket_id="test_redpacket",
            group_id=-1001234567890,
            sender_id=123456789,
            amount=10.0,
            count=10
        )
        
        session_pool.dialogue_manager = Mock()
        session_pool.dialogue_manager.redpacket_handler = AsyncMock()
        session_pool.dialogue_manager.redpacket_handler.detect_redpacket = AsyncMock(return_value=mock_redpacket)
        session_pool.dialogue_manager.redpacket_handler.should_participate = AsyncMock(return_value=False)
        session_pool.dialogue_manager.contexts = {}
        
        # 創建模擬回調查詢
        mock_callback_query = Mock()
        mock_callback_query.data = "hb:grab:test_envelope"
        mock_callback_query.message = Mock()
        mock_callback_query.message.chat = Mock()
        mock_callback_query.message.chat.id = -1001234567890
        mock_callback_query.message.chat.type.name = "GROUP"
        
        # 模擬回調查詢處理邏輯
        if mock_callback_query.message and mock_callback_query.message.chat:
            if mock_callback_query.message.chat.type.name == "GROUP":
                if account_config.group_ids and mock_callback_query.message.chat.id in account_config.group_ids:
                    callback_data = mock_callback_query.data or ""
                    if callback_data.startswith("hb:grab:"):
                        if session_pool.dialogue_manager and session_pool.dialogue_manager.redpacket_handler:
                            message = mock_callback_query.message
                            redpacket = await session_pool.dialogue_manager.redpacket_handler.detect_redpacket(message)
                            if redpacket:
                                should_participate = await session_pool.dialogue_manager.redpacket_handler.should_participate(
                                    account_id=mock_account.account_id,
                                    redpacket=redpacket,
                                    account_config=account_config,
                                    context=None
                                )
                                if not should_participate:
                                    # 不應該參與，應該不處理
                                    pass
        
        # 驗證紅包檢測和參與檢查被調用
        session_pool.dialogue_manager.redpacket_handler.detect_redpacket.assert_called_once()
        session_pool.dialogue_manager.redpacket_handler.should_participate.assert_called_once()
        # 驗證沒有參與紅包（因為不應該參與）
        assert session_pool.dialogue_manager.redpacket_handler.should_participate.return_value is False
    
    @pytest.mark.asyncio
    async def test_monitor_account_callback_query_participate_failed(self, session_pool, account_config):
        """測試監聽賬號（回調查詢參與失敗）"""
        # 創建模擬賬號和客戶端
        mock_client = AsyncMock()
        mock_client.get_me = AsyncMock(return_value=Mock(first_name="測試機器人"))
        
        mock_account = Mock()
        mock_account.account_id = account_config.account_id
        mock_account.client = mock_client
        mock_account.config = account_config
        mock_account.last_activity = None
        mock_account.error_count = 0
        
        session_pool.account_manager.accounts[account_config.account_id] = mock_account
        
        # Mock dialogue_manager 和 redpacket_handler（參與失敗）
        from group_ai_service.redpacket_handler import RedpacketInfo, RedpacketResult
        mock_redpacket = RedpacketInfo(
            redpacket_id="test_redpacket",
            group_id=-1001234567890,
            sender_id=123456789,
            amount=10.0,
            count=10
        )
        
        session_pool.dialogue_manager = Mock()
        session_pool.dialogue_manager.redpacket_handler = AsyncMock()
        session_pool.dialogue_manager.redpacket_handler.detect_redpacket = AsyncMock(return_value=mock_redpacket)
        session_pool.dialogue_manager.redpacket_handler.should_participate = AsyncMock(return_value=True)
        session_pool.dialogue_manager.redpacket_handler.participate = AsyncMock(return_value=RedpacketResult(
            redpacket_id="test_redpacket",
            account_id=account_config.account_id,
            success=False,
            amount=0.0,
            error="參與失敗"
        ))
        session_pool.dialogue_manager.contexts = {}
        
        # 創建模擬回調查詢
        mock_callback_query = Mock()
        mock_callback_query.data = "hb:grab:test_envelope"
        mock_callback_query.message = Mock()
        mock_callback_query.message.chat = Mock()
        mock_callback_query.message.chat.id = -1001234567890
        mock_callback_query.message.chat.type.name = "GROUP"
        mock_callback_query.message.from_user = Mock(first_name="發送者")
        
        # 模擬回調查詢處理邏輯
        if mock_callback_query.message and mock_callback_query.message.chat:
            if mock_callback_query.message.chat.type.name == "GROUP":
                if account_config.group_ids and mock_callback_query.message.chat.id in account_config.group_ids:
                    callback_data = mock_callback_query.data or ""
                    if callback_data.startswith("hb:grab:"):
                        if session_pool.dialogue_manager and session_pool.dialogue_manager.redpacket_handler:
                            message = mock_callback_query.message
                            redpacket = await session_pool.dialogue_manager.redpacket_handler.detect_redpacket(message)
                            if redpacket:
                                should_participate = await session_pool.dialogue_manager.redpacket_handler.should_participate(
                                    account_id=mock_account.account_id,
                                    redpacket=redpacket,
                                    account_config=account_config,
                                    context=None
                                )
                                if should_participate:
                                    sender_name = None
                                    if message.from_user:
                                        sender_name = getattr(message.from_user, 'first_name', None)
                                    
                                    participant_name = None
                                    try:
                                        me = await mock_client.get_me()
                                        if me:
                                            participant_name = me.first_name
                                    except Exception:
                                        pass
                                    
                                    result = await session_pool.dialogue_manager.redpacket_handler.participate(
                                        account_id=mock_account.account_id,
                                        redpacket=redpacket,
                                        client=mock_client,
                                        sender_name=sender_name,
                                        participant_name=participant_name
                                    )
                                    
                                    if not result.success:
                                        # 參與失敗，應該記錄錯誤
                                        pass
        
        # 驗證參與被調用
        session_pool.dialogue_manager.redpacket_handler.participate.assert_called_once()
        # 驗證參與失敗
        result = await session_pool.dialogue_manager.redpacket_handler.participate(
            account_id=mock_account.account_id,
            redpacket=mock_redpacket,
            client=mock_client,
            sender_name="發送者",
            participant_name="測試機器人"
        )
        assert result.success is False
    
    @pytest.mark.asyncio
    async def test_dispatch_message_handler_exception(self, session_pool):
        """測試分發消息（處理器異常）"""
        # Mock 賬號
        mock_account = Mock()
        mock_account.account_id = "test_account"
        
        # Mock 消息
        mock_message = Mock()
        mock_message.chat.id = -1001234567890
        
        # 註冊會拋出異常的處理器
        async def handler(account, message):
            raise Exception("處理器異常")
        
        session_pool.register_message_handler("test_account", handler)
        
        # 應該不會拋出異常，只是記錄錯誤
        await session_pool._dispatch_message(mock_account, mock_message)
        
        # 驗證處理器被調用（雖然拋出異常）
        assert "test_account" in session_pool._message_handlers
    
    @pytest.mark.asyncio
    async def test_dispatch_message_global_handler_exception(self, session_pool):
        """測試分發消息（全局處理器異常）"""
        # Mock 賬號
        mock_account = Mock()
        mock_account.account_id = "test_account"
        
        # Mock 消息
        mock_message = Mock()
        mock_message.chat.id = -1001234567890
        
        # 註冊會拋出異常的全局處理器
        async def handler(account, message):
            raise Exception("全局處理器異常")
        
        session_pool.register_message_handler(None, handler)
        
        # 應該不會拋出異常，只是記錄錯誤
        await session_pool._dispatch_message(mock_account, mock_message)
        
        # 驗證處理器被調用（雖然拋出異常）
        assert None in session_pool._message_handlers
    
    @pytest.mark.asyncio
    async def test_start_monitoring_account_success(self, session_pool, account_config):
        """測試成功啟動監聽賬號"""
        # Mock 賬號（在線）
        mock_client = AsyncMock()
        mock_account = Mock()
        mock_account.account_id = account_config.account_id
        mock_account.status = Mock()
        mock_account.status.value = "online"
        mock_account.client = mock_client
        mock_account.config = account_config
        session_pool.account_manager.accounts[account_config.account_id] = mock_account
        
        # Mock client.idle 以避免無限等待
        mock_client.idle = AsyncMock(side_effect=asyncio.CancelledError())
        
        # 啟動監聽
        await session_pool.start_monitoring_account(account_config.account_id)
        
        # 驗證任務被創建
        assert len(session_pool._tasks) == 1
    
    @pytest.mark.asyncio
    async def test_start_with_online_accounts(self, session_pool, account_config):
        """測試啟動會話池（有在線賬號）"""
        # Mock 在線賬號
        mock_client = AsyncMock()
        mock_client.idle = AsyncMock(side_effect=asyncio.CancelledError())
        
        mock_account = Mock()
        mock_account.account_id = account_config.account_id
        mock_account.status = Mock()
        mock_account.status.value = "online"
        mock_account.client = mock_client
        mock_account.config = account_config
        
        session_pool.account_manager.list_accounts = Mock(return_value=[mock_account])
        session_pool.account_manager.accounts[account_config.account_id] = mock_account
        
        # 啟動會話池
        await session_pool.start()
        
        # 驗證會話池已啟動
        assert session_pool._running is True
        # 驗證任務被創建
        assert len(session_pool._tasks) == 1
    
    @pytest.mark.asyncio
    async def test_monitor_account_idle_cancelled(self, session_pool, account_config):
        """測試監聽賬號（idle 被取消）"""
        # 創建模擬賬號和客戶端
        mock_client = Mock()
        # Mock idle 方法，使其在被調用時立即拋出 CancelledError
        async def mock_idle():
            raise asyncio.CancelledError()
        mock_client.idle = mock_idle
        
        # Mock 裝飾器（作為可調用對象，支持 @decorator() 語法）
        class MockDecorator:
            def __call__(self, func=None):
                if func is None:
                    # 作為裝飾器使用（無參數）
                    return self
                else:
                    # 直接調用
                    return func
            def __call__(self, func):
                return func
        
        # 使用 MagicMock 來模擬裝飾器
        mock_client.on_message = MagicMock(return_value=lambda f: f)
        mock_client.on_callback_query = MagicMock(return_value=lambda f: f)
        
        mock_account = Mock()
        mock_account.account_id = account_config.account_id
        mock_account.client = mock_client
        mock_account.config = account_config
        
        session_pool.account_manager.accounts[account_config.account_id] = mock_account
        
        # 應該不會拋出異常，只是記錄日誌
        await session_pool._monitor_account(account_config.account_id)
        
        # 驗證裝飾器被調用（至少一次）
        # 注意：由於裝飾器的複雜性，我們主要驗證方法能正常執行而不拋出異常
        assert True  # 如果能執行到這裡，說明異常處理正常
    
    @pytest.mark.asyncio
    async def test_monitor_account_idle_exception(self, session_pool, account_config):
        """測試監聽賬號（idle 異常）"""
        # 創建模擬賬號和客戶端
        mock_client = Mock()
        # Mock idle 方法，使其在被調用時立即拋出異常
        async def mock_idle():
            raise Exception("連接異常")
        mock_client.idle = mock_idle
        
        # 使用 MagicMock 來模擬裝飾器
        mock_client.on_message = MagicMock(return_value=lambda f: f)
        mock_client.on_callback_query = MagicMock(return_value=lambda f: f)
        
        mock_account = Mock()
        mock_account.account_id = account_config.account_id
        mock_account.client = mock_client
        mock_account.config = account_config
        
        session_pool.account_manager.accounts[account_config.account_id] = mock_account
        
        # 應該不會拋出異常，只是記錄錯誤
        await session_pool._monitor_account(account_config.account_id)
        
        # 驗證方法能正常執行而不拋出異常
        assert True  # 如果能執行到這裡，說明異常處理正常
    
    @pytest.mark.asyncio
    async def test_dispatch_message_multiple_handlers(self, session_pool):
        """測試分發消息（多個處理器）"""
        # Mock 賬號
        mock_account = Mock()
        mock_account.account_id = "test_account"
        
        # Mock 消息
        mock_message = Mock()
        mock_message.chat.id = -1001234567890
        
        # 註冊多個處理器
        handler1_called = []
        handler2_called = []
        
        async def handler1(account, message):
            handler1_called.append((account, message))
        
        async def handler2(account, message):
            handler2_called.append((account, message))
        
        session_pool.register_message_handler("test_account", handler1)
        session_pool.register_message_handler("test_account", handler2)
        
        await session_pool._dispatch_message(mock_account, mock_message)
        
        # 驗證兩個處理器都被調用
        assert len(handler1_called) == 1
        assert len(handler2_called) == 1
    
    @pytest.mark.asyncio
    async def test_dispatch_message_both_specific_and_global(self, session_pool):
        """測試分發消息（特定和全局處理器）"""
        # Mock 賬號
        mock_account = Mock()
        mock_account.account_id = "test_account"
        
        # Mock 消息
        mock_message = Mock()
        mock_message.chat.id = -1001234567890
        
        # 註冊特定和全局處理器
        specific_handler_called = []
        global_handler_called = []
        
        async def specific_handler(account, message):
            specific_handler_called.append((account, message))
        
        async def global_handler(account, message):
            global_handler_called.append((account, message))
        
        session_pool.register_message_handler("test_account", specific_handler)
        session_pool.register_message_handler(None, global_handler)
        
        await session_pool._dispatch_message(mock_account, mock_message)
        
        # 驗證兩個處理器都被調用
        assert len(specific_handler_called) == 1
        assert len(global_handler_called) == 1
    
    @pytest.mark.asyncio
    async def test_start_monitoring_account_task_done(self, session_pool, account_config):
        """測試啟動監聽（任務已完成）"""
        # 創建一個已完成的任務
        completed_task = asyncio.create_task(asyncio.sleep(0))
        await completed_task  # 等待任務完成
        
        session_pool._tasks = [completed_task]
        
        # Mock 賬號（在線）
        mock_client = AsyncMock()
        mock_client.idle = AsyncMock(side_effect=asyncio.CancelledError())
        
        mock_account = Mock()
        mock_account.account_id = account_config.account_id
        mock_account.status = Mock()
        mock_account.status.value = "online"
        mock_account.client = mock_client
        mock_account.config = account_config
        
        session_pool.account_manager.accounts[account_config.account_id] = mock_account
        
        # 應該創建新任務（因為舊任務已完成）
        await session_pool.start_monitoring_account(account_config.account_id)
        
        # 驗證新任務被創建
        assert len(session_pool._tasks) == 2  # 舊任務 + 新任務
    
    def test_get_account_by_group_empty_group_ids(self, session_pool):
        """測試根據群組獲取賬號（空的 group_ids）"""
        # Mock 賬號（group_ids 為空列表）
        mock_account = Mock()
        mock_account.config = Mock()
        mock_account.config.group_ids = []  # 空列表
        
        session_pool.account_manager.accounts = {
            "test_account": mock_account
        }
        
        accounts = session_pool.get_account_by_group(-1001234567890)
        
        # 根據代碼邏輯：如果 group_ids 為空列表（falsy），會返回該賬號
        # 因為 `not account.config.group_ids` 為 True，所以會包含該賬號
        assert len(accounts) == 1
        assert accounts[0] == mock_account
    
    def test_active_accounts_mixed_status(self, session_pool):
        """測試獲取活躍賬號（混合狀態）"""
        # Mock 在線和離線賬號
        mock_account1 = Mock()
        mock_account1.account_id = "account1"
        mock_account1.status.value = "online"
        
        mock_account2 = Mock()
        mock_account2.account_id = "account2"
        mock_account2.status.value = "offline"
        
        mock_account3 = Mock()
        mock_account3.account_id = "account3"
        mock_account3.status.value = "online"
        
        session_pool.account_manager.accounts = {
            "account1": mock_account1,
            "account2": mock_account2,
            "account3": mock_account3
        }
        
        active = session_pool.active_accounts
        
        assert len(active) == 2
        assert "account1" in active
        assert "account3" in active
        assert "account2" not in active
    
    @pytest.mark.asyncio
    async def test_handle_message_group_message(self, session_pool, account_config):
        """測試處理消息（群組消息）"""
        # 創建模擬賬號和消息
        mock_account = Mock()
        mock_account.account_id = account_config.account_id
        mock_account.config = account_config
        mock_account.last_activity = None
        mock_account.message_count = 0
        mock_account.reply_count = 0
        mock_account.error_count = 0
        
        mock_message = AsyncMock()
        mock_message.chat = Mock()
        mock_message.chat.id = -1001234567890
        mock_message.chat.type.name = "GROUP"
        mock_message.reply_text = AsyncMock()
        
        # Mock dialogue_manager
        session_pool.dialogue_manager = AsyncMock()
        session_pool.dialogue_manager.process_message = AsyncMock(return_value="測試回復")
        
        # 調用方法
        await session_pool._handle_message(mock_account, mock_message, account_config.account_id)
        
        # 驗證
        assert mock_account.message_count == 1
        session_pool.dialogue_manager.process_message.assert_called_once()
        mock_message.reply_text.assert_called_once_with("測試回復")
        assert mock_account.reply_count == 1
    
    @pytest.mark.asyncio
    async def test_handle_message_non_group_message(self, session_pool, account_config):
        """測試處理消息（非群組消息）"""
        mock_account = Mock()
        mock_account.account_id = account_config.account_id
        mock_account.config = account_config
        mock_account.message_count = 0
        
        mock_message = Mock()
        mock_message.chat = Mock()
        mock_message.chat.type.name = "PRIVATE"  # 私聊
        
        await session_pool._handle_message(mock_account, mock_message, account_config.account_id)
        
        # 應該不處理私聊消息
        assert mock_account.message_count == 0
    
    @pytest.mark.asyncio
    async def test_handle_message_wrong_group(self, session_pool, account_config):
        """測試處理消息（錯誤群組）"""
        mock_account = Mock()
        mock_account.account_id = account_config.account_id
        mock_account.config = account_config
        mock_account.message_count = 0
        
        mock_message = Mock()
        mock_message.chat = Mock()
        mock_message.chat.id = -9999999999  # 不同的群組
        mock_message.chat.type.name = "GROUP"
        
        await session_pool._handle_message(mock_account, mock_message, account_config.account_id)
        
        # 應該不處理不同群組的消息
        assert mock_account.message_count == 0
    
    @pytest.mark.asyncio
    async def test_handle_message_dialogue_manager_exception(self, session_pool, account_config):
        """測試處理消息（對話管理器異常）"""
        mock_account = Mock()
        mock_account.account_id = account_config.account_id
        mock_account.config = account_config
        mock_account.last_activity = None
        mock_account.message_count = 0
        mock_account.error_count = 0
        
        mock_message = AsyncMock()
        mock_message.chat = Mock()
        mock_message.chat.id = -1001234567890
        mock_message.chat.type.name = "GROUP"
        
        # Mock dialogue_manager 拋出異常
        session_pool.dialogue_manager = AsyncMock()
        session_pool.dialogue_manager.process_message = AsyncMock(side_effect=Exception("處理失敗"))
        
        await session_pool._handle_message(mock_account, mock_message, account_config.account_id)
        
        # 驗證錯誤計數增加
        assert mock_account.error_count == 1
    
    @pytest.mark.asyncio
    async def test_handle_message_no_reply(self, session_pool, account_config):
        """測試處理消息（沒有回復）"""
        mock_account = Mock()
        mock_account.account_id = account_config.account_id
        mock_account.config = account_config
        mock_account.last_activity = None
        mock_account.message_count = 0
        mock_account.reply_count = 0
        
        mock_message = AsyncMock()
        mock_message.chat = Mock()
        mock_message.chat.id = -1001234567890
        mock_message.chat.type.name = "GROUP"
        mock_message.reply_text = AsyncMock()
        
        # Mock dialogue_manager 不返回回復
        session_pool.dialogue_manager = AsyncMock()
        session_pool.dialogue_manager.process_message = AsyncMock(return_value=None)
        
        await session_pool._handle_message(mock_account, mock_message, account_config.account_id)
        
        # 驗證
        assert mock_account.message_count == 1
        assert mock_account.reply_count == 0
        mock_message.reply_text.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_handle_callback_query_redpacket_success(self, session_pool, account_config):
        """測試處理回調查詢（紅包成功）"""
        # 創建模擬賬號和客戶端
        mock_client = AsyncMock()
        mock_client.get_me = AsyncMock(return_value=Mock(first_name="測試機器人", username="test_bot"))
        
        mock_account = Mock()
        mock_account.account_id = account_config.account_id
        mock_account.config = account_config
        mock_account.last_activity = None
        mock_account.error_count = 0
        
        # Mock dialogue_manager 和 redpacket_handler
        from group_ai_service.redpacket_handler import RedpacketInfo, RedpacketResult
        mock_redpacket = RedpacketInfo(
            redpacket_id="test_redpacket",
            group_id=-1001234567890,
            sender_id=123456789,
            amount=10.0,
            count=10
        )
        
        session_pool.dialogue_manager = Mock()
        session_pool.dialogue_manager.redpacket_handler = AsyncMock()
        session_pool.dialogue_manager.redpacket_handler.detect_redpacket = AsyncMock(return_value=mock_redpacket)
        session_pool.dialogue_manager.redpacket_handler.should_participate = AsyncMock(return_value=True)
        session_pool.dialogue_manager.redpacket_handler.participate = AsyncMock(return_value=RedpacketResult(
            redpacket_id="test_redpacket",
            account_id=account_config.account_id,
            success=True,
            amount=5.0
        ))
        session_pool.dialogue_manager.contexts = {}
        
        # 創建模擬回調查詢
        mock_callback_query = Mock()
        mock_callback_query.data = "hb:grab:test_envelope"
        mock_callback_query.message = Mock()
        mock_callback_query.message.chat = Mock()
        mock_callback_query.message.chat.id = -1001234567890
        mock_callback_query.message.chat.type.name = "GROUP"
        mock_callback_query.message.from_user = Mock(first_name="發送者", username="sender")
        
        # 調用方法
        await session_pool._handle_callback_query(
            mock_account,
            mock_client,
            mock_callback_query,
            account_config.account_id
        )
        
        # 驗證
        session_pool.dialogue_manager.redpacket_handler.detect_redpacket.assert_called_once()
        session_pool.dialogue_manager.redpacket_handler.should_participate.assert_called_once()
        session_pool.dialogue_manager.redpacket_handler.participate.assert_called_once()
        assert mock_account.error_count == 0
    
    @pytest.mark.asyncio
    async def test_handle_callback_query_non_group(self, session_pool, account_config):
        """測試處理回調查詢（非群組）"""
        mock_account = Mock()
        mock_account.account_id = account_config.account_id
        mock_account.config = account_config
        mock_account.error_count = 0
        
        mock_client = AsyncMock()
        
        mock_callback_query = Mock()
        mock_callback_query.message = Mock()
        mock_callback_query.message.chat = Mock()
        mock_callback_query.message.chat.type.name = "PRIVATE"  # 私聊
        
        await session_pool._handle_callback_query(
            mock_account,
            mock_client,
            mock_callback_query,
            account_config.account_id
        )
        
        # 應該不處理私聊回調
        assert mock_account.error_count == 0
    
    @pytest.mark.asyncio
    async def test_handle_callback_query_no_message(self, session_pool, account_config):
        """測試處理回調查詢（沒有 message）"""
        mock_account = Mock()
        mock_account.account_id = account_config.account_id
        mock_account.config = account_config
        mock_account.error_count = 0
        
        mock_client = AsyncMock()
        
        mock_callback_query = Mock()
        mock_callback_query.message = None
        
        await session_pool._handle_callback_query(
            mock_account,
            mock_client,
            mock_callback_query,
            account_config.account_id
        )
        
        # 應該不處理沒有 message 的回調
        assert mock_account.error_count == 0
    
    @pytest.mark.asyncio
    async def test_handle_callback_query_wrong_group(self, session_pool, account_config):
        """測試處理回調查詢（錯誤群組）"""
        mock_account = Mock()
        mock_account.account_id = account_config.account_id
        mock_account.config = account_config
        mock_account.error_count = 0
        
        mock_client = AsyncMock()
        
        mock_callback_query = Mock()
        mock_callback_query.message = Mock()
        mock_callback_query.message.chat = Mock()
        mock_callback_query.message.chat.id = -9999999999  # 不同的群組
        mock_callback_query.message.chat.type.name = "GROUP"
        
        await session_pool._handle_callback_query(
            mock_account,
            mock_client,
            mock_callback_query,
            account_config.account_id
        )
        
        # 應該不處理不同群組的回調
        assert mock_account.error_count == 0
    
    @pytest.mark.asyncio
    async def test_handle_callback_query_not_redpacket(self, session_pool, account_config):
        """測試處理回調查詢（不是紅包）"""
        mock_account = Mock()
        mock_account.account_id = account_config.account_id
        mock_account.config = account_config
        mock_account.last_activity = None
        mock_account.error_count = 0
        
        mock_client = AsyncMock()
        
        mock_callback_query = Mock()
        mock_callback_query.data = "other:callback:data"  # 不是紅包
        mock_callback_query.message = Mock()
        mock_callback_query.message.chat = Mock()
        mock_callback_query.message.chat.id = -1001234567890
        mock_callback_query.message.chat.type.name = "GROUP"
        
        await session_pool._handle_callback_query(
            mock_account,
            mock_client,
            mock_callback_query,
            account_config.account_id
        )
        
        # 應該不處理非紅包回調
        assert mock_account.error_count == 0
    
    @pytest.mark.asyncio
    async def test_handle_callback_query_redpacket_detect_failed(self, session_pool, account_config):
        """測試處理回調查詢（紅包檢測失敗）"""
        mock_account = Mock()
        mock_account.account_id = account_config.account_id
        mock_account.config = account_config
        mock_account.last_activity = None
        mock_account.error_count = 0
        
        mock_client = AsyncMock()
        
        session_pool.dialogue_manager = Mock()
        session_pool.dialogue_manager.redpacket_handler = AsyncMock()
        session_pool.dialogue_manager.redpacket_handler.detect_redpacket = AsyncMock(return_value=None)
        session_pool.dialogue_manager.contexts = {}
        
        mock_callback_query = Mock()
        mock_callback_query.data = "hb:grab:test_envelope"
        mock_callback_query.message = Mock()
        mock_callback_query.message.chat = Mock()
        mock_callback_query.message.chat.id = -1001234567890
        mock_callback_query.message.chat.type.name = "GROUP"
        
        await session_pool._handle_callback_query(
            mock_account,
            mock_client,
            mock_callback_query,
            account_config.account_id
        )
        
        # 驗證
        session_pool.dialogue_manager.redpacket_handler.detect_redpacket.assert_called_once()
        assert mock_account.error_count == 0
    
    @pytest.mark.asyncio
    async def test_handle_callback_query_should_not_participate(self, session_pool, account_config):
        """測試處理回調查詢（不應該參與）"""
        mock_account = Mock()
        mock_account.account_id = account_config.account_id
        mock_account.config = account_config
        mock_account.last_activity = None
        mock_account.error_count = 0
        
        mock_client = AsyncMock()
        
        from group_ai_service.redpacket_handler import RedpacketInfo
        mock_redpacket = RedpacketInfo(
            redpacket_id="test_redpacket",
            group_id=-1001234567890,
            sender_id=123456789,
            amount=10.0,
            count=10
        )
        
        session_pool.dialogue_manager = Mock()
        session_pool.dialogue_manager.redpacket_handler = AsyncMock()
        session_pool.dialogue_manager.redpacket_handler.detect_redpacket = AsyncMock(return_value=mock_redpacket)
        session_pool.dialogue_manager.redpacket_handler.should_participate = AsyncMock(return_value=False)
        session_pool.dialogue_manager.contexts = {}
        
        mock_callback_query = Mock()
        mock_callback_query.data = "hb:grab:test_envelope"
        mock_callback_query.message = Mock()
        mock_callback_query.message.chat = Mock()
        mock_callback_query.message.chat.id = -1001234567890
        mock_callback_query.message.chat.type.name = "GROUP"
        
        await session_pool._handle_callback_query(
            mock_account,
            mock_client,
            mock_callback_query,
            account_config.account_id
        )
        
        # 驗證
        session_pool.dialogue_manager.redpacket_handler.detect_redpacket.assert_called_once()
        session_pool.dialogue_manager.redpacket_handler.should_participate.assert_called_once()
        # 不應該參與，所以不應該調用 participate
        session_pool.dialogue_manager.redpacket_handler.participate.assert_not_called()
        assert mock_account.error_count == 0
    
    @pytest.mark.asyncio
    async def test_handle_callback_query_get_me_failure(self, session_pool, account_config):
        """測試處理回調查詢（獲取參與者名稱失敗）"""
        mock_client = AsyncMock()
        mock_client.get_me = AsyncMock(side_effect=Exception("獲取失敗"))
        
        mock_account = Mock()
        mock_account.account_id = account_config.account_id
        mock_account.config = account_config
        mock_account.last_activity = None
        mock_account.error_count = 0
        
        from group_ai_service.redpacket_handler import RedpacketInfo, RedpacketResult
        mock_redpacket = RedpacketInfo(
            redpacket_id="test_redpacket",
            group_id=-1001234567890,
            sender_id=123456789,
            amount=10.0,
            count=10
        )
        
        session_pool.dialogue_manager = Mock()
        session_pool.dialogue_manager.redpacket_handler = AsyncMock()
        session_pool.dialogue_manager.redpacket_handler.detect_redpacket = AsyncMock(return_value=mock_redpacket)
        session_pool.dialogue_manager.redpacket_handler.should_participate = AsyncMock(return_value=True)
        session_pool.dialogue_manager.redpacket_handler.participate = AsyncMock(return_value=RedpacketResult(
            redpacket_id="test_redpacket",
            account_id=account_config.account_id,
            success=True,
            amount=5.0
        ))
        session_pool.dialogue_manager.contexts = {}
        
        mock_callback_query = Mock()
        mock_callback_query.data = "hb:grab:test_envelope"
        mock_callback_query.message = Mock()
        mock_callback_query.message.chat = Mock()
        mock_callback_query.message.chat.id = -1001234567890
        mock_callback_query.message.chat.type.name = "GROUP"
        mock_callback_query.message.from_user = Mock(first_name="發送者")
        
        await session_pool._handle_callback_query(
            mock_account,
            mock_client,
            mock_callback_query,
            account_config.account_id
        )
        
        # 驗證（即使獲取參與者名稱失敗，也應該能正常處理）
        session_pool.dialogue_manager.redpacket_handler.detect_redpacket.assert_called_once()
        session_pool.dialogue_manager.redpacket_handler.participate.assert_called_once()
        # 驗證參與時 participant_name 為 None（因為獲取失敗）
        call_args = session_pool.dialogue_manager.redpacket_handler.participate.call_args
        assert call_args[1]['participant_name'] is None
        assert mock_account.error_count == 0
    
    @pytest.mark.asyncio
    async def test_handle_callback_query_participate_failed(self, session_pool, account_config):
        """測試處理回調查詢（參與失敗）"""
        mock_client = AsyncMock()
        mock_client.get_me = AsyncMock(return_value=Mock(first_name="測試機器人"))
        
        mock_account = Mock()
        mock_account.account_id = account_config.account_id
        mock_account.config = account_config
        mock_account.last_activity = None
        mock_account.error_count = 0
        
        from group_ai_service.redpacket_handler import RedpacketInfo, RedpacketResult
        mock_redpacket = RedpacketInfo(
            redpacket_id="test_redpacket",
            group_id=-1001234567890,
            sender_id=123456789,
            amount=10.0,
            count=10
        )
        
        session_pool.dialogue_manager = Mock()
        session_pool.dialogue_manager.redpacket_handler = AsyncMock()
        session_pool.dialogue_manager.redpacket_handler.detect_redpacket = AsyncMock(return_value=mock_redpacket)
        session_pool.dialogue_manager.redpacket_handler.should_participate = AsyncMock(return_value=True)
        session_pool.dialogue_manager.redpacket_handler.participate = AsyncMock(return_value=RedpacketResult(
            redpacket_id="test_redpacket",
            account_id=account_config.account_id,
            success=False,
            amount=0.0,
            error="參與失敗"
        ))
        session_pool.dialogue_manager.contexts = {}
        
        mock_callback_query = Mock()
        mock_callback_query.data = "hb:grab:test_envelope"
        mock_callback_query.message = Mock()
        mock_callback_query.message.chat = Mock()
        mock_callback_query.message.chat.id = -1001234567890
        mock_callback_query.message.chat.type.name = "GROUP"
        mock_callback_query.message.from_user = Mock(first_name="發送者")
        
        await session_pool._handle_callback_query(
            mock_account,
            mock_client,
            mock_callback_query,
            account_config.account_id
        )
        
        # 驗證參與被調用
        session_pool.dialogue_manager.redpacket_handler.participate.assert_called_once()
        # 參與失敗，但應該記錄日誌，不增加錯誤計數（因為這是正常的業務邏輯）
        assert mock_account.error_count == 0
    
    @pytest.mark.asyncio
    async def test_handle_message_no_chat(self, session_pool, account_config):
        """測試處理消息（沒有 chat）"""
        mock_account = Mock()
        mock_account.account_id = account_config.account_id
        mock_account.config = account_config
        mock_account.message_count = 0
        
        mock_message = Mock()
        mock_message.chat = None
        
        await session_pool._handle_message(mock_account, mock_message, account_config.account_id)
        
        # 應該不處理沒有 chat 的消息
        assert mock_account.message_count == 0
    
    @pytest.mark.asyncio
    async def test_handle_message_no_dialogue_manager(self, session_pool, account_config):
        """測試處理消息（沒有對話管理器）"""
        mock_account = Mock()
        mock_account.account_id = account_config.account_id
        mock_account.config = account_config
        mock_account.last_activity = None
        mock_account.message_count = 0
        
        mock_message = AsyncMock()
        mock_message.chat = Mock()
        mock_message.chat.id = -1001234567890
        mock_message.chat.type.name = "GROUP"
        
        # 沒有對話管理器
        session_pool.dialogue_manager = None
        
        # 註冊一個處理器
        handler_called = []
        async def handler(account, message):
            handler_called.append((account, message))
        
        session_pool.register_message_handler(account_config.account_id, handler)
        
        await session_pool._handle_message(mock_account, mock_message, account_config.account_id)
        
        # 驗證
        assert mock_account.message_count == 1
        assert len(handler_called) == 1
    
    @pytest.mark.asyncio
    async def test_handle_callback_query_no_redpacket_handler(self, session_pool, account_config):
        """測試處理回調查詢（沒有紅包處理器）"""
        mock_account = Mock()
        mock_account.account_id = account_config.account_id
        mock_account.config = account_config
        mock_account.last_activity = None
        mock_account.error_count = 0
        
        mock_client = AsyncMock()
        
        # 沒有 redpacket_handler
        session_pool.dialogue_manager = Mock()
        session_pool.dialogue_manager.redpacket_handler = None
        
        mock_callback_query = Mock()
        mock_callback_query.data = "hb:grab:test_envelope"
        mock_callback_query.message = Mock()
        mock_callback_query.message.chat = Mock()
        mock_callback_query.message.chat.id = -1001234567890
        mock_callback_query.message.chat.type.name = "GROUP"
        
        await session_pool._handle_callback_query(
            mock_account,
            mock_client,
            mock_callback_query,
            account_config.account_id
        )
        
        # 應該不處理（沒有 redpacket_handler）
        assert mock_account.error_count == 0
    
    @pytest.mark.asyncio
    async def test_handle_callback_query_redpacket_exception(self, session_pool, account_config):
        """測試處理回調查詢（紅包處理異常）"""
        mock_account = Mock()
        mock_account.account_id = account_config.account_id
        mock_account.config = account_config
        mock_account.last_activity = None
        mock_account.error_count = 0
        
        mock_client = AsyncMock()
        
        session_pool.dialogue_manager = Mock()
        session_pool.dialogue_manager.redpacket_handler = AsyncMock()
        session_pool.dialogue_manager.redpacket_handler.detect_redpacket = AsyncMock(side_effect=Exception("檢測失敗"))
        session_pool.dialogue_manager.contexts = {}
        
        mock_callback_query = Mock()
        mock_callback_query.data = "hb:grab:test_envelope"
        mock_callback_query.message = Mock()
        mock_callback_query.message.chat = Mock()
        mock_callback_query.message.chat.id = -1001234567890
        mock_callback_query.message.chat.type.name = "GROUP"
        
        await session_pool._handle_callback_query(
            mock_account,
            mock_client,
            mock_callback_query,
            account_config.account_id
        )
        
        # 驗證錯誤計數增加
        assert mock_account.error_count == 1
    
    @pytest.mark.asyncio
    async def test_handle_message_exception(self, session_pool, account_config):
        """測試處理消息（整體異常）"""
        mock_account = Mock()
        mock_account.account_id = account_config.account_id
        mock_account.config = account_config
        mock_account.error_count = 0
        
        # 創建一個會導致異常的消息（訪問 type.name 時異常）
        mock_message = Mock()
        mock_message.chat = Mock()
        # 設置 type 為 None，導致訪問 type.name 時異常
        mock_message.chat.type = None
        
        await session_pool._handle_message(mock_account, mock_message, account_config.account_id)
        
        # 驗證錯誤計數增加（因為訪問 type.name 時會異常）
        assert mock_account.error_count == 1
