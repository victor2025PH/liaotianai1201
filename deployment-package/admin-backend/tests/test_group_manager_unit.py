"""
GroupManager 單元測試
"""
import sys
from pathlib import Path

# 添加項目根目錄到 Python 路徑
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import pytest
from unittest.mock import Mock, AsyncMock, patch
from pyrogram.errors import FloodWait, ChatAdminRequired, UserNotParticipant

from group_ai_service.group_manager import GroupManager
from group_ai_service.account_manager import AccountManager
from group_ai_service.models.account import AccountConfig, AccountStatusEnum


@pytest.fixture
def account_manager():
    """創建 AccountManager 實例"""
    return Mock(spec=AccountManager)


@pytest.fixture
def group_manager(account_manager):
    """創建 GroupManager 實例"""
    return GroupManager(account_manager=account_manager)


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


@pytest.fixture
def mock_account_instance(account_config):
    """創建模擬 AccountInstance"""
    mock_client = AsyncMock()
    mock_client.is_connected = True
    mock_client.create_group = AsyncMock()
    mock_client.set_chat_description = AsyncMock()
    mock_client.join_chat = AsyncMock()
    mock_client.get_chat_members_count = AsyncMock(return_value=10)
    mock_client.get_chat_members = AsyncMock()
    mock_client.leave_chat = AsyncMock()
    
    instance = Mock()
    instance.account_id = account_config.account_id
    instance.client = mock_client
    instance.config = account_config
    instance.status = AccountStatusEnum.ONLINE
    
    return instance


class TestGroupManager:
    """GroupManager 測試"""
    
    def test_manager_initialization(self, group_manager):
        """測試管理器初始化"""
        assert group_manager is not None
        assert group_manager.account_manager is not None
    
    @pytest.mark.asyncio
    async def test_create_group_success(self, group_manager, account_config, mock_account_instance):
        """測試創建群組（成功）"""
        # Mock 賬號
        group_manager.account_manager.accounts = {
            account_config.account_id: mock_account_instance
        }
        
        # Mock 創建群組返回
        mock_chat = Mock()
        mock_chat.id = -1001234567891
        mock_account_instance.client.create_group.return_value = mock_chat
        
        group_id = await group_manager.create_group(
            account_id=account_config.account_id,
            title="測試群組",
            description="測試描述"
        )
        
        assert group_id == -1001234567891
        mock_account_instance.client.create_group.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_group_with_members(self, group_manager, account_config, mock_account_instance):
        """測試創建群組（帶成員）"""
        # Mock 賬號
        group_manager.account_manager.accounts = {
            account_config.account_id: mock_account_instance
        }
        
        # Mock 創建群組返回
        mock_chat = Mock()
        mock_chat.id = -1001234567891
        mock_account_instance.client.create_group.return_value = mock_chat
        
        member_ids = [123456789, 987654321]
        group_id = await group_manager.create_group(
            account_id=account_config.account_id,
            title="測試群組",
            member_ids=member_ids
        )
        
        assert group_id == -1001234567891
        mock_account_instance.client.create_group.assert_called_once_with(
            title="測試群組",
            users=member_ids
        )
    
    @pytest.mark.asyncio
    async def test_create_group_account_not_found(self, group_manager):
        """測試創建群組（賬號不存在）"""
        group_manager.account_manager.accounts = {}
        
        group_id = await group_manager.create_group(
            account_id="nonexistent_account",
            title="測試群組"
        )
        
        assert group_id is None
    
    @pytest.mark.asyncio
    async def test_create_group_flood_wait(self, group_manager, account_config, mock_account_instance):
        """測試創建群組（FloodWait）"""
        # Mock 賬號
        group_manager.account_manager.accounts = {
            account_config.account_id: mock_account_instance
        }
        
        # Mock FloodWait 錯誤
        mock_account_instance.client.create_group.side_effect = [
            FloodWait(value=5),
            Mock(id=-1001234567891)  # 重試成功
        ]
        
        with patch('asyncio.sleep', new_callable=AsyncMock):
            group_id = await group_manager.create_group(
                account_id=account_config.account_id,
                title="測試群組"
            )
            
            assert group_id == -1001234567891
    
    @pytest.mark.asyncio
    async def test_join_group_by_username(self, group_manager, account_config, mock_account_instance):
        """測試加入群組（通過用戶名）"""
        # Mock 賬號
        group_manager.account_manager.accounts = {
            account_config.account_id: mock_account_instance
        }
        
        # Mock 加入群組返回
        mock_chat = Mock()
        mock_chat.id = -1001234567891
        mock_account_instance.client.join_chat.return_value = mock_chat
        
        result = await group_manager.join_group(
            account_id=account_config.account_id,
            group_username="test_group"
        )
        
        assert result is True
        mock_account_instance.client.join_chat.assert_called_once_with("test_group")
    
    @pytest.mark.asyncio
    async def test_join_group_by_id(self, group_manager, account_config, mock_account_instance):
        """測試加入群組（通過ID）"""
        # Mock 賬號
        group_manager.account_manager.accounts = {
            account_config.account_id: mock_account_instance
        }
        
        # Mock 獲取群組返回
        mock_chat = Mock()
        mock_chat.id = -1001234567891
        mock_chat.type.name = "SUPERGROUP"  # 不是私人群組
        mock_account_instance.client.get_chat.return_value = mock_chat
        
        result = await group_manager.join_group(
            account_id=account_config.account_id,
            group_id=-1001234567891
        )
        
        assert result is True
        mock_account_instance.client.get_chat.assert_called_once_with(-1001234567891)
    
    @pytest.mark.asyncio
    async def test_join_group_by_invite_link(self, group_manager, account_config, mock_account_instance):
        """測試加入群組（通過邀請鏈接）"""
        # Mock 賬號
        group_manager.account_manager.accounts = {
            account_config.account_id: mock_account_instance
        }
        
        # Mock 加入群組返回
        mock_chat = Mock()
        mock_chat.id = -1001234567891
        mock_account_instance.client.join_chat.return_value = mock_chat
        
        invite_link = "https://t.me/joinchat/test"
        result = await group_manager.join_group(
            account_id=account_config.account_id,
            invite_link=invite_link
        )
        
        assert result is True
        mock_account_instance.client.join_chat.assert_called_once_with(invite_link)
    
    @pytest.mark.asyncio
    async def test_join_group_failure(self, group_manager, account_config, mock_account_instance):
        """測試加入群組（失敗）"""
        # Mock 賬號
        group_manager.account_manager.accounts = {
            account_config.account_id: mock_account_instance
        }
        
        # Mock 加入群組失敗
        mock_account_instance.client.join_chat.side_effect = Exception("Join failed")
        
        result = await group_manager.join_group(
            account_id=account_config.account_id,
            group_username="test_group"
        )
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_start_group_chat(self, group_manager, account_config, mock_account_instance):
        """測試啟動群組聊天"""
        # Mock 賬號
        group_manager.account_manager.accounts = {
            account_config.account_id: mock_account_instance
        }
        
        result = await group_manager.start_group_chat(
            account_id=account_config.account_id,
            group_id=-1001234567890,
            auto_reply=True
        )
        
        assert result is True
        # 群組應該被添加到監聽列表
        assert -1001234567890 in mock_account_instance.config.group_ids
    
    @pytest.mark.asyncio
    async def test_create_and_start_group(self, group_manager, account_config, mock_account_instance):
        """測試創建並啟動群組"""
        # Mock 賬號
        group_manager.account_manager.accounts = {
            account_config.account_id: mock_account_instance
        }
        
        # Mock 創建群組返回
        mock_chat = Mock()
        mock_chat.id = -1001234567891
        mock_account_instance.client.create_group.return_value = mock_chat
        
        group_id = await group_manager.create_and_start_group(
            account_id=account_config.account_id,
            title="測試群組",
            description="測試描述",
            auto_reply=True
        )
        
        assert group_id == -1001234567891
        mock_account_instance.client.create_group.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_group_not_connected(self, group_manager, account_config, mock_account_instance):
        """測試創建群組（賬號未連接）"""
        # Mock 賬號（未連接）
        mock_account_instance.client.is_connected = False
        mock_account_instance.client.start = AsyncMock()
        
        group_manager.account_manager.accounts = {
            account_config.account_id: mock_account_instance
        }
        
        # Mock 創建群組返回
        mock_chat = Mock()
        mock_chat.id = -1001234567891
        mock_account_instance.client.create_group.return_value = mock_chat
        
        group_id = await group_manager.create_group(
            account_id=account_config.account_id,
            title="測試群組"
        )
        
        assert group_id == -1001234567891
        mock_account_instance.client.start.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_group_set_description_failure(self, group_manager, account_config, mock_account_instance):
        """測試創建群組（設置描述失敗）"""
        # Mock 賬號
        group_manager.account_manager.accounts = {
            account_config.account_id: mock_account_instance
        }
        
        # Mock 創建群組返回
        mock_chat = Mock()
        mock_chat.id = -1001234567891
        mock_account_instance.client.create_group.return_value = mock_chat
        
        # Mock 設置描述失敗
        mock_account_instance.client.set_chat_description.side_effect = Exception("設置失敗")
        
        group_id = await group_manager.create_group(
            account_id=account_config.account_id,
            title="測試群組",
            description="測試描述"
        )
        
        # 應該仍然成功創建群組
        assert group_id == -1001234567891
        mock_account_instance.client.set_chat_description.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_group_exception(self, group_manager, account_config, mock_account_instance):
        """測試創建群組（異常處理）"""
        # Mock 賬號
        group_manager.account_manager.accounts = {
            account_config.account_id: mock_account_instance
        }
        
        # Mock 創建群組失敗（非FloodWait異常）
        mock_account_instance.client.create_group.side_effect = Exception("創建失敗")
        
        group_id = await group_manager.create_group(
            account_id=account_config.account_id,
            title="測試群組"
        )
        
        assert group_id is None
    
    @pytest.mark.asyncio
    async def test_join_group_not_connected(self, group_manager, account_config, mock_account_instance):
        """測試加入群組（賬號未連接）"""
        # Mock 賬號（未連接）
        mock_account_instance.client.is_connected = False
        mock_account_instance.client.start = AsyncMock()
        
        group_manager.account_manager.accounts = {
            account_config.account_id: mock_account_instance
        }
        
        # Mock 加入群組返回
        mock_chat = Mock()
        mock_chat.id = -1001234567891
        mock_account_instance.client.join_chat.return_value = mock_chat
        
        result = await group_manager.join_group(
            account_id=account_config.account_id,
            group_username="test_group"
        )
        
        assert result is True
        mock_account_instance.client.start.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_join_group_private_chat(self, group_manager, account_config, mock_account_instance):
        """測試加入群組（私人群組）"""
        # Mock 賬號
        group_manager.account_manager.accounts = {
            account_config.account_id: mock_account_instance
        }
        
        # Mock 獲取群組返回（私人群組）
        mock_chat = Mock()
        mock_chat.id = -1001234567891
        mock_chat.type.name = "PRIVATE"
        mock_account_instance.client.get_chat.return_value = mock_chat
        
        result = await group_manager.join_group(
            account_id=account_config.account_id,
            group_id=-1001234567891
        )
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_join_group_no_params(self, group_manager, account_config, mock_account_instance):
        """測試加入群組（無參數）"""
        # Mock 賬號
        group_manager.account_manager.accounts = {
            account_config.account_id: mock_account_instance
        }
        
        result = await group_manager.join_group(
            account_id=account_config.account_id
        )
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_join_group_flood_wait_retry(self, group_manager, account_config, mock_account_instance):
        """測試加入群組（FloodWait重試）"""
        # Mock 賬號
        group_manager.account_manager.accounts = {
            account_config.account_id: mock_account_instance
        }
        
        # Mock FloodWait 錯誤，然後成功
        mock_chat = Mock()
        mock_chat.id = -1001234567891
        mock_account_instance.client.join_chat.side_effect = [
            FloodWait(value=5),
            mock_chat  # 重試成功
        ]
        
        with patch('asyncio.sleep', new_callable=AsyncMock):
            result = await group_manager.join_group(
                account_id=account_config.account_id,
                group_username="test_group"
            )
            
            assert result is True
            assert mock_account_instance.client.join_chat.call_count == 2
    
    @pytest.mark.asyncio
    async def test_join_group_user_not_participant(self, group_manager, account_config, mock_account_instance):
        """測試加入群組（UserNotParticipant）"""
        # Mock 賬號
        group_manager.account_manager.accounts = {
            account_config.account_id: mock_account_instance
        }
        
        # Mock UserNotParticipant 錯誤
        mock_account_instance.client.join_chat.side_effect = UserNotParticipant()
        
        result = await group_manager.join_group(
            account_id=account_config.account_id,
            group_username="test_group"
        )
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_start_group_chat_add_to_list(self, group_manager, account_config, mock_account_instance):
        """測試啟動群組聊天（添加群組到監聽列表）"""
        # Mock 賬號
        mock_account_instance.config.group_ids = []  # 空列表
        group_manager.account_manager.accounts = {
            account_config.account_id: mock_account_instance
        }
        
        # Mock 獲取群組
        mock_chat = Mock()
        mock_chat.id = -1001234567891
        mock_chat.title = "測試群組"
        mock_account_instance.client.get_chat.return_value = mock_chat
        
        # Mock ServiceManager
        with patch('group_ai_service.service_manager.ServiceManager') as mock_service_manager:
            mock_service_instance = Mock()
            mock_service_instance.start_account = AsyncMock(return_value=True)
            mock_service_instance.session_pool = None
            mock_service_manager.get_instance.return_value = mock_service_instance
            
            result = await group_manager.start_group_chat(
                account_id=account_config.account_id,
                group_id=-1001234567891,
                auto_reply=False
            )
            
            assert result is True
            assert -1001234567891 in mock_account_instance.config.group_ids
    
    @pytest.mark.asyncio
    async def test_start_group_chat_account_not_started(self, group_manager, account_config, mock_account_instance):
        """測試啟動群組聊天（賬號未啟動）"""
        # Mock 賬號（未啟動）
        mock_account_instance.status = AccountStatusEnum.OFFLINE
        mock_account_instance.config.group_ids = [-1001234567891]
        group_manager.account_manager.accounts = {
            account_config.account_id: mock_account_instance
        }
        
        # Mock 獲取群組
        mock_chat = Mock()
        mock_chat.id = -1001234567891
        mock_chat.title = "測試群組"
        mock_account_instance.client.get_chat.return_value = mock_chat
        
        # Mock ServiceManager
        with patch('group_ai_service.service_manager.ServiceManager') as mock_service_manager:
            mock_service_instance = Mock()
            mock_service_instance.start_account = AsyncMock(return_value=True)
            mock_service_instance.session_pool = None
            mock_service_manager.get_instance.return_value = mock_service_instance
            
            result = await group_manager.start_group_chat(
                account_id=account_config.account_id,
                group_id=-1001234567891,
                auto_reply=False
            )
            
            assert result is True
            mock_service_instance.start_account.assert_called_once_with(account_config.account_id)
    
    @pytest.mark.asyncio
    async def test_start_group_chat_account_start_failed(self, group_manager, account_config, mock_account_instance):
        """測試啟動群組聊天（啟動賬號失敗）"""
        # Mock 賬號（未啟動）
        mock_account_instance.status = AccountStatusEnum.OFFLINE
        mock_account_instance.config.group_ids = [-1001234567891]
        group_manager.account_manager.accounts = {
            account_config.account_id: mock_account_instance
        }
        
        # Mock ServiceManager（啟動失敗）
        with patch('group_ai_service.service_manager.ServiceManager') as mock_service_manager:
            mock_service_instance = Mock()
            mock_service_instance.start_account = AsyncMock(return_value=False)
            mock_service_manager.get_instance.return_value = mock_service_instance
            
            result = await group_manager.start_group_chat(
                account_id=account_config.account_id,
                group_id=-1001234567891,
                auto_reply=False
            )
            
            assert result is False
    
    @pytest.mark.asyncio
    async def test_start_group_chat_not_connected(self, group_manager, account_config, mock_account_instance):
        """測試啟動群組聊天（賬號未連接）"""
        # Mock 賬號（未連接）
        mock_account_instance.status = AccountStatusEnum.ONLINE
        mock_account_instance.client.is_connected = False
        mock_account_instance.client.start = AsyncMock()
        mock_account_instance.config.group_ids = [-1001234567891]
        group_manager.account_manager.accounts = {
            account_config.account_id: mock_account_instance
        }
        
        # Mock 獲取群組
        mock_chat = Mock()
        mock_chat.id = -1001234567891
        mock_chat.title = "測試群組"
        mock_account_instance.client.get_chat.return_value = mock_chat
        
        # Mock ServiceManager
        with patch('group_ai_service.service_manager.ServiceManager') as mock_service_manager:
            mock_service_instance = Mock()
            mock_service_instance.session_pool = None
            mock_service_manager.get_instance.return_value = mock_service_instance
            
            result = await group_manager.start_group_chat(
                account_id=account_config.account_id,
                group_id=-1001234567891,
                auto_reply=False
            )
            
            assert result is True
            mock_account_instance.client.start.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_start_group_chat_cannot_access(self, group_manager, account_config, mock_account_instance):
        """測試啟動群組聊天（無法訪問群組）"""
        # Mock 賬號
        mock_account_instance.config.group_ids = [-1001234567891]
        group_manager.account_manager.accounts = {
            account_config.account_id: mock_account_instance
        }
        
        # Mock 獲取群組失敗
        mock_account_instance.client.get_chat.side_effect = Exception("無法訪問")
        
        result = await group_manager.start_group_chat(
            account_id=account_config.account_id,
            group_id=-1001234567891,
            auto_reply=False
        )
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_start_group_chat_exception(self, group_manager, account_config, mock_account_instance):
        """測試啟動群組聊天（異常處理）"""
        # Mock 賬號
        group_manager.account_manager.accounts = {
            account_config.account_id: mock_account_instance
        }
        
        # Mock 異常（通過設置無效的group_ids）
        mock_account_instance.config.group_ids = None
        
        result = await group_manager.start_group_chat(
            account_id=account_config.account_id,
            group_id=-1001234567891,
            auto_reply=False
        )
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_create_and_start_group_start_failed(self, group_manager, account_config, mock_account_instance):
        """測試創建並啟動群組（啟動失敗）"""
        # Mock 賬號
        group_manager.account_manager.accounts = {
            account_config.account_id: mock_account_instance
        }
        
        # Mock 創建群組返回
        mock_chat = Mock()
        mock_chat.id = -1001234567891
        mock_account_instance.client.create_group.return_value = mock_chat
        
        # Mock 啟動群組聊天失敗
        with patch.object(group_manager, 'start_group_chat', return_value=False):
            group_id = await group_manager.create_and_start_group(
                account_id=account_config.account_id,
                title="測試群組"
            )
            
            # 應該仍然返回群組ID（因為群組已創建）
            assert group_id == -1001234567891

