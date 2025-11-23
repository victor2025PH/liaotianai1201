"""
AccountManager 單元測試
"""
import os
import asyncio
import pytest
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch

from group_ai_service.account_manager import AccountManager, AccountInstance
from group_ai_service.models.account import AccountConfig, AccountStatusEnum


@pytest.fixture
def account_manager():
    """創建 AccountManager 實例"""
    return AccountManager()


@pytest.fixture
def mock_client():
    """創建模擬 Client"""
    client = Mock()
    client.is_connected = False
    client.start = AsyncMock()
    client.stop = AsyncMock()
    return client


@pytest.fixture
def session_file(tmp_path):
    """創建臨時 session 文件"""
    session_path = tmp_path / "test.session"
    session_path.write_text("dummy")
    return session_path


@pytest.fixture(autouse=True)
def mock_api_env(monkeypatch):
    """設置必需的 API 環境變量"""
    monkeypatch.setenv("TELEGRAM_API_ID", "123456")
    monkeypatch.setenv("TELEGRAM_API_HASH", "abc123")


@pytest.fixture
def sample_config(session_file):
    """創建示例配置"""
    return AccountConfig(
        account_id="test_account",
        session_file=str(session_file),
        script_id="default",
        group_ids=[123456789],
        active=True
    )


@pytest.mark.asyncio
async def test_add_account(account_manager, mock_client, sample_config):
    """測試添加賬號"""
    with patch('group_ai_service.account_manager.Client', return_value=mock_client):
        account = await account_manager.add_account(
            account_id=sample_config.account_id,
            session_file=sample_config.session_file,
            config=sample_config
        )
        
        assert account is not None
        assert account.account_id == sample_config.account_id
        assert account_manager.accounts[sample_config.account_id] == account


@pytest.mark.asyncio
async def test_remove_account(account_manager, mock_client, sample_config):
    """測試移除賬號"""
    with patch('group_ai_service.account_manager.Client', return_value=mock_client):
        # 先添加賬號
        account = await account_manager.add_account(
            account_id=sample_config.account_id,
            session_file=sample_config.session_file,
            config=sample_config
        )
        
        # 移除賬號
        result = await account_manager.remove_account(sample_config.account_id)
        
        assert result is True
        assert sample_config.account_id not in account_manager.accounts


@pytest.mark.asyncio
async def test_start_account(account_manager, mock_client, sample_config):
    """測試啟動賬號"""
    with patch('group_ai_service.account_manager.Client', return_value=mock_client):
        # 添加賬號
        account = await account_manager.add_account(
            account_id=sample_config.account_id,
            session_file=sample_config.session_file,
            config=sample_config
        )
        
        # 啟動賬號
        mock_client.start.return_value = None
        result = await account_manager.start_account(sample_config.account_id)
        
        assert result is True
        assert account.status == AccountStatusEnum.ONLINE


@pytest.mark.asyncio
async def test_stop_account(account_manager, mock_client, sample_config):
    """測試停止賬號"""
    with patch('group_ai_service.account_manager.Client', return_value=mock_client):
        # 添加並啟動賬號
        account = await account_manager.add_account(
            account_id=sample_config.account_id,
            session_file=sample_config.session_file,
            config=sample_config
        )
        account.status = AccountStatusEnum.ONLINE
        mock_client.is_connected = True
        
        # 停止賬號
        result = await account_manager.stop_account(sample_config.account_id)
        
        assert result is True
        assert account.status == AccountStatusEnum.OFFLINE


def test_get_account_status(account_manager, mock_client, sample_config):
    """測試獲取賬號狀態"""
    # 添加賬號
    account = AccountInstance(
        account_id=sample_config.account_id,
        client=mock_client,
        config=sample_config
    )
    account.status = AccountStatusEnum.ONLINE
    account_manager.accounts[sample_config.account_id] = account
    
    # 獲取狀態
    status = account_manager.get_account_status(sample_config.account_id)
    
    assert status is not None
    assert status.account_id == sample_config.account_id
    assert status.status == AccountStatusEnum.ONLINE


def test_list_accounts(account_manager, mock_client, sample_config):
    """測試列出所有賬號"""
    # 添加賬號
    account = AccountInstance(
        account_id=sample_config.account_id,
        client=mock_client,
        config=sample_config
    )
    account.status = AccountStatusEnum.ONLINE
    account_manager.accounts[sample_config.account_id] = account
    
    # 列出賬號
    accounts = account_manager.list_accounts()
    
    assert len(accounts) == 1
    assert accounts[0].account_id == sample_config.account_id


@pytest.mark.asyncio
async def test_add_account_session_file_not_found(account_manager, mock_client, sample_config, tmp_path):
    """測試添加賬號時 session 文件不存在"""
    missing_file = tmp_path / "missing.session"
    with patch('group_ai_service.account_manager.Client', return_value=mock_client):
        with pytest.raises(FileNotFoundError):
            await account_manager.add_account(
                account_id="missing_account",
                session_file=str(missing_file),
                config=AccountConfig(
                    account_id="missing_account",
                    session_file=str(missing_file),
                    script_id="default",
                    group_ids=[]
                )
            )


@pytest.mark.asyncio
async def test_add_account_missing_api_credentials(account_manager, mock_client, sample_config, monkeypatch):
    """測試缺少 API 憑證時的報錯"""
    monkeypatch.delenv("TELEGRAM_API_ID", raising=False)
    monkeypatch.delenv("TELEGRAM_API_HASH", raising=False)
    
    with patch('group_ai_service.account_manager.Client', return_value=mock_client):
        with pytest.raises(ValueError):
            await account_manager.add_account(
                account_id=sample_config.account_id,
                session_file=sample_config.session_file,
                config=sample_config
            )


@pytest.mark.asyncio
async def test_start_account_already_online(account_manager, mock_client, sample_config):
    """測試啟動賬號（已在線）"""
    with patch('group_ai_service.account_manager.Client', return_value=mock_client):
        account = await account_manager.add_account(
            account_id=sample_config.account_id,
            session_file=sample_config.session_file,
            config=sample_config
        )
        account.status = AccountStatusEnum.ONLINE
        
        result = await account_manager.start_account(sample_config.account_id)
        
        assert result is True
        account.client.start.assert_not_called()


@pytest.mark.asyncio
async def test_stop_account_not_found(account_manager):
    """測試停止不存在的賬號"""
    result = await account_manager.stop_account("missing")
    assert result is False


def test_get_account_status_not_found(account_manager):
    """測試獲取不存在賬號狀態"""
    status = account_manager.get_account_status("missing")
    assert status is None


def test_list_accounts_empty(account_manager):
    """測試列出賬號（空）"""
    accounts = account_manager.list_accounts()
    assert accounts == []


@pytest.mark.asyncio
async def test_load_accounts_from_directory(account_manager, mock_client, tmp_path):
    """測試從目錄加載賬號"""
    sessions_dir = tmp_path / "sessions"
    sessions_dir.mkdir()
    session_file = sessions_dir / "acc1.session"
    session_file.write_text("dummy")
    
    with patch('group_ai_service.account_manager.Client', return_value=mock_client):
        loaded = await account_manager.load_accounts_from_directory(str(sessions_dir))
    
    assert loaded == ["acc1"]
    assert "acc1" in account_manager.accounts


@pytest.mark.asyncio
async def test_load_accounts_from_directory_missing(account_manager, tmp_path):
    """測試加載賬號（目錄不存在）"""
    missing_dir = tmp_path / "missing"
    loaded = await account_manager.load_accounts_from_directory(str(missing_dir))
    assert loaded == []


@pytest.mark.asyncio
async def test_account_instance_start_and_stop(sample_config, monkeypatch):
    """測試 AccountInstance 啟動及停止"""
    mock_client = AsyncMock()
    mock_client.is_connected = True
    mock_client.start = AsyncMock()
    mock_client.stop = AsyncMock()
    
    account = AccountInstance("acc", mock_client, sample_config)
    
    class DummyConfig:
        account_health_check_interval = 0
        account_max_reconnect_attempts = 1
        account_reconnect_delay = 0
    
    monkeypatch.setattr('group_ai_service.account_manager.get_group_ai_config', lambda: DummyConfig())
    
    original_sleep = asyncio.sleep
    
    async def fast_sleep(*args, **kwargs):
        account.status = AccountStatusEnum.OFFLINE
        await original_sleep(0)
    
    with patch('group_ai_service.account_manager.asyncio.sleep', side_effect=fast_sleep):
        result = await account.start()
        assert result is True
        assert account.status == AccountStatusEnum.ONLINE
        assert mock_client.stop.await_count == 1
        assert account._health_check_task is not None
        
        stop_result = await account.stop()
        assert stop_result is True
        assert account.status == AccountStatusEnum.OFFLINE


@pytest.mark.asyncio
async def test_account_instance_reconnect_success(sample_config, monkeypatch):
    """測試 AccountInstance 重連流程"""
    mock_client = AsyncMock()
    account = AccountInstance("acc", mock_client, sample_config)
    
    class DummyConfig:
        account_health_check_interval = 0
        account_max_reconnect_attempts = 2
        account_reconnect_delay = 0
    
    monkeypatch.setattr('group_ai_service.account_manager.get_group_ai_config', lambda: DummyConfig())
    
    original_sleep = asyncio.sleep
    
    async def fast_sleep(*args, **kwargs):
        await original_sleep(0)
    
    with patch('group_ai_service.account_manager.asyncio.sleep', side_effect=fast_sleep):
        account.start = AsyncMock(side_effect=[False, True])
        await account._reconnect()
        await account._reconnect_task
        assert account.start.await_count == 2


@pytest.mark.asyncio
async def test_start_account_retry(account_manager, mock_client, sample_config):
    """測試啟動賬號失敗後重新嘗試"""
    with patch('group_ai_service.account_manager.Client', return_value=mock_client):
        account = await account_manager.add_account(
            account_id=sample_config.account_id,
            session_file=sample_config.session_file,
            config=sample_config
        )
        account.start = AsyncMock(side_effect=[False, True])
        with patch('group_ai_service.account_manager.asyncio.sleep', new_callable=AsyncMock) as mock_sleep:
            result = await account_manager.start_account(sample_config.account_id)
    
    assert result is True
    mock_sleep.assert_called()


@pytest.mark.asyncio
async def test_load_accounts_handles_errors(tmp_path):
    """測試批量加載時的錯誤處理"""
    sessions_dir = tmp_path / "sessions"
    sessions_dir.mkdir()
    (sessions_dir / "bad.session").write_text("dummy")
    
    manager = AccountManager()
    manager.add_account = AsyncMock(side_effect=RuntimeError("boom"))
    
    loaded = await manager.load_accounts_from_directory(str(sessions_dir))
    assert loaded == []


@pytest.mark.asyncio
async def test_add_account_resolves_relative_path(mock_client, tmp_path, monkeypatch):
    """測試從 sessions 目錄解析相對路徑"""
    sessions_dir = tmp_path / "sessions"
    sessions_dir.mkdir()
    session_file = sessions_dir / "rel.session"
    session_file.write_text("dummy")
    
    class DummyConfig:
        session_files_directory = str(sessions_dir)
        account_health_check_interval = 0
        account_max_reconnect_attempts = 1
        account_reconnect_delay = 0
    
    dummy_config = DummyConfig()
    monkeypatch.setattr('group_ai_service.account_manager.get_group_ai_config', lambda: dummy_config)
    monkeypatch.setattr('group_ai_service.config.get_group_ai_config', lambda: dummy_config)
    
    manager = AccountManager()
    config = AccountConfig(
        account_id="rel",
        session_file="rel.session",
        script_id="default",
        group_ids=[]
    )
    
    with patch('group_ai_service.account_manager.Client', return_value=mock_client) as mock_client_cls:
        account = await manager.add_account("rel", "rel.session", config)
    
    assert account.account_id == "rel"
    mock_client_cls.assert_called_once()
    _, kwargs = mock_client_cls.call_args
    assert kwargs["workdir"] == str(session_file.parent)

