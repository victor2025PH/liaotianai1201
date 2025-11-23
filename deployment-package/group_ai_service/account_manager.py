"""
賬號管理器 - 批量加載和管理 AI 賬號
"""
import asyncio
import logging
from pathlib import Path
from typing import Dict, List, Optional

from pyrogram import Client
from pyrogram.errors import SessionPasswordNeeded

from group_ai_service.config import get_group_ai_config
from group_ai_service.models.account import (
    AccountConfig,
    AccountInfo,
    AccountStatus as AccountStatusData,
    AccountStatusEnum
)

logger = logging.getLogger(__name__)


class AccountInstance:
    """賬號實例（封裝 Pyrogram Client）"""
    
    def __init__(self, account_id: str, client: Client, config: AccountConfig):
        self.account_id = account_id
        self.client = client
        self.config = config
        self.status = AccountStatusEnum.OFFLINE
        self.message_count = 0
        self.reply_count = 0
        self.redpacket_count = 0
        self.error_count = 0
        self.last_activity = None
        self.start_time = None
        self._reconnect_task: Optional[asyncio.Task] = None
        self._health_check_task: Optional[asyncio.Task] = None
    
    async def start(self) -> bool:
        """啟動賬號"""
        try:
            self.status = AccountStatusEnum.STARTING
            
            # 如果已經連接，先停止
            if self.client.is_connected:
                await self.client.stop()
            
            # 檢查 session 文件是否存在（支持加密文件）
            from pathlib import Path
            import tempfile
            from utils.session_encryption import get_session_manager
            
            session_path = Path(self.config.session_file)
            session_manager = get_session_manager()
            
            # 檢查是否為加密文件
            if session_manager.encryptor and session_manager.encryptor.is_encrypted_file(session_path):
                # 解密到臨時文件供 Pyrogram 使用
                temp_dir = Path(tempfile.gettempdir()) / "telegram_sessions" / self.account_id
                temp_dir.mkdir(parents=True, exist_ok=True)
                try:
                    decrypted_data = session_manager.encryptor.decrypt_session(session_path)
                    temp_path = session_manager.encryptor.get_decrypted_path(session_path, temp_dir)
                    temp_path.write_bytes(decrypted_data)
                    # 更新 client 的 workdir 和 session_name
                    session_name = temp_path.stem
                    workdir = temp_dir
                    logger.info(f"已解密 Session 文件到臨時位置: {temp_path}")
                except Exception as e:
                    logger.error(f"解密 Session 文件失敗: {e}")
                    self.status = AccountStatusEnum.ERROR
                    self.error_count += 1
                    return False
            else:
                if not session_path.exists():
                    logger.error(f"賬號 {self.account_id} 的 Session 文件不存在: {self.config.session_file}")
                    self.status = AccountStatusEnum.ERROR
                    self.error_count += 1
                    return False
                session_name = session_path.stem
                workdir = session_path.parent
            
            # 如果使用臨時解密文件，需要重新創建 Client
            if session_manager.encryptor and session_manager.encryptor.is_encrypted_file(session_path):
                from pyrogram import Client
                self.client = Client(
                    session_name,
                    api_id=self.config.api_id,
                    api_hash=self.config.api_hash,
                    workdir=str(workdir.resolve()),
                )
            
            await self.client.start()
            self.status = AccountStatusEnum.ONLINE
            self.start_time = asyncio.get_event_loop().time()
            self.error_count = 0  # 重置錯誤計數
            
            # 更新 Prometheus 指標
            try:
                from app.monitoring.prometheus_metrics import update_account_metrics
                update_account_metrics(
                    account_id=self.account_id,
                    status="online"
                )
            except Exception as e:
                logger.debug(f"更新 Prometheus 指標失敗: {e}")
            
            # 啟動健康檢查
            self._start_health_check()
            
            logger.info(f"賬號 {self.account_id} 已啟動")
            return True
        except SessionPasswordNeeded:
            # 需要 2FA 密碼
            self.status = AccountStatusEnum.ERROR
            self.error_count += 1
            error_msg = f"賬號 {self.account_id} 需要兩步驗證密碼（2FA），請先手動登錄"
            logger.error(error_msg)
            return False
        except Exception as e:
            self.status = AccountStatusEnum.ERROR
            self.error_count += 1
            error_type = type(e).__name__
            error_msg = f"賬號 {self.account_id} 啟動失敗 ({error_type}): {str(e)}"
            logger.error(error_msg, exc_info=True)
            return False
    
    def _start_health_check(self):
        """啟動健康檢查任務"""
        if self._health_check_task and not self._health_check_task.done():
            return
        
        async def health_check():
            from group_ai_service.config import get_group_ai_config
            config = get_group_ai_config()
            
            while self.status == AccountStatusEnum.ONLINE:
                try:
                    await asyncio.sleep(config.account_health_check_interval)
                    
                    # 檢查連接狀態
                    if not self.client.is_connected:
                        logger.warning(f"賬號 {self.account_id} 連接斷開，嘗試重連...")
                        await self._reconnect()
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.exception(f"健康檢查異常 (account={self.account_id}): {e}")
        
        self._health_check_task = asyncio.create_task(health_check())
    
    async def _reconnect(self):
        """重連賬號（增強版，支持智能重試）"""
        if self._reconnect_task and not self._reconnect_task.done():
            return
        
        async def reconnect_loop():
            from group_ai_service.config import get_group_ai_config
            from utils.retry_handler import retry_async, SESSION_RETRY_CONFIG, SessionError, NetworkError, NonRetryableError
            from pyrogram.errors import AuthKeyUnregistered, SessionPasswordNeeded
            
            config = get_group_ai_config()
            
            # 创建自定义重试配置
            retry_config = SESSION_RETRY_CONFIG
            retry_config.max_attempts = config.account_max_reconnect_attempts
            retry_config.initial_delay = config.account_reconnect_delay
            
            def on_retry(attempt: int, exception: Exception):
                """重试回调"""
                error_type = type(exception).__name__
                logger.warning(
                    f"賬號 {self.account_id} 重連嘗試 {attempt}/{retry_config.max_attempts} "
                    f"失敗 ({error_type}): {exception}"
                )
            
            def on_failure(exception: Exception):
                """失败回调"""
                logger.error(
                    f"賬號 {self.account_id} 重連失敗，已達最大嘗試次數: {exception}"
                )
                self.status = AccountStatusEnum.ERROR
                self.error_count += 1
            
            retry_config.on_retry = on_retry
            retry_config.on_failure = on_failure
            
            async def attempt_reconnect():
                """尝试重连"""
                try:
                    # 先停止现有连接
                    if self.client.is_connected:
                        await self.client.stop()
                    
                    # 等待一小段时间
                    await asyncio.sleep(1)
                    
                    # 尝试启动
                    if await self.start():
                        logger.info(f"賬號 {self.account_id} 重連成功")
                        return True
                    else:
                        raise SessionError("啟動失敗")
                except (AuthKeyUnregistered, SessionPasswordNeeded) as e:
                    # Session 失效，不可重试
                    raise NonRetryableError(f"Session 失效: {e}")
                except Exception as e:
                    # 检查是否为网络错误
                    error_str = str(e).lower()
                    if any(keyword in error_str for keyword in ["connection", "network", "timeout", "unreachable"]):
                        raise NetworkError(f"網絡錯誤: {e}") from e
                    else:
                        raise SessionError(f"重連錯誤: {e}") from e
            
            try:
                await retry_async(attempt_reconnect, retry_config)
            except Exception as e:
                # 最终失败处理已在 on_failure 中完成
                pass
        
        self._reconnect_task = asyncio.create_task(reconnect_loop())
    
    async def stop(self) -> bool:
        """停止賬號"""
        try:
            self.status = AccountStatusEnum.STOPPING
            
            # 取消健康檢查任務
            if self._health_check_task and not self._health_check_task.done():
                self._health_check_task.cancel()
                try:
                    await self._health_check_task
                except asyncio.CancelledError:
                    pass
            
            # 取消重連任務
            if self._reconnect_task and not self._reconnect_task.done():
                self._reconnect_task.cancel()
                try:
                    await self._reconnect_task
                except asyncio.CancelledError:
                    pass
            
            # 停止客戶端
            if self.client.is_connected:
                await self.client.stop()
            
            self.status = AccountStatusEnum.OFFLINE
            
            # 更新 Prometheus 指標
            try:
                from app.monitoring.prometheus_metrics import update_account_metrics
                update_account_metrics(
                    account_id=self.account_id,
                    status="offline"
                )
            except Exception as e:
                logger.debug(f"更新 Prometheus 指標失敗: {e}")
            
            logger.info(f"賬號 {self.account_id} 已停止")
            return True
        except Exception as e:
            logger.error(f"賬號 {self.account_id} 停止失敗: {e}")
            return False


class AccountManager:
    """賬號管理器"""
    
    def __init__(self):
        self.config = get_group_ai_config()
        self.accounts: Dict[str, AccountInstance] = {}
        self._lock = asyncio.Lock()
        logger.info("AccountManager 初始化完成")
    
    async def load_accounts_from_directory(
        self,
        directory: str,
        script_id: str = "default",
        group_ids: Optional[List[int]] = None
    ) -> List[str]:
        """從目錄批量加載 .session 文件"""
        session_dir = Path(directory)
        if not session_dir.exists():
            logger.error(f"Session 目錄不存在: {directory}")
            return []
        
        session_files = list(session_dir.glob("*.session"))
        logger.info(f"找到 {len(session_files)} 個 session 文件")
        
        loaded_accounts = []
        for session_file in session_files:
            account_id = session_file.stem
            try:
                await self.add_account(
                    account_id=account_id,
                    session_file=str(session_file),
                    config=AccountConfig(
                        account_id=account_id,
                        session_file=str(session_file),
                        script_id=script_id,
                        group_ids=group_ids or []
                    )
                )
                loaded_accounts.append(account_id)
            except Exception as e:
                logger.error(f"加載賬號 {account_id} 失敗: {e}")
        
        logger.info(f"成功加載 {len(loaded_accounts)} 個賬號")
        return loaded_accounts
    
    async def add_account(
        self,
        account_id: str,
        session_file: str,
        config: AccountConfig
    ) -> AccountInstance:
        """添加單個賬號"""
        async with self._lock:
            if account_id in self.accounts:
                logger.warning(f"賬號 {account_id} 已存在，跳過添加")
                return self.accounts[account_id]
            
            # 驗證 session 文件
            session_path = Path(session_file)
            
            # 如果是相對路徑，嘗試從sessions目錄查找
            if not session_path.is_absolute():
                # 先嘗試當前目錄
                if not session_path.exists():
                    # 嘗試從sessions目錄查找
                    from group_ai_service.config import get_group_ai_config
                    config = get_group_ai_config()
                    sessions_dir = Path(config.session_files_directory)
                    if sessions_dir.exists():
                        session_path = sessions_dir / session_path.name
                        if session_path.exists():
                            session_file = str(session_path)
            
            # 最終檢查
            if not Path(session_file).exists():
                raise FileNotFoundError(f"Session 文件不存在: {session_file}。請確保文件位於 sessions 文件夾內，或提供完整路徑。")
            
            # 創建 Pyrogram Client
            # 嘗試從多個來源獲取 API_ID 和 API_HASH
            import os
            api_id = None
            api_hash = None
            
            # 方法1: 從環境變量獲取（優先）
            api_id_str = os.getenv("TELEGRAM_API_ID") or os.getenv("API_ID")
            if api_id_str:
                try:
                    api_id = int(api_id_str)
                except (ValueError, TypeError):
                    logger.warning(f"API_ID 格式無效: {api_id_str}")
            
            api_hash = os.getenv("TELEGRAM_API_HASH") or os.getenv("API_HASH")
            
            # 方法2: 如果環境變量沒有，嘗試從 config 模塊導入（向後兼容）
            if not api_id or not api_hash:
                try:
                    import sys
                    # 嘗試從項目根目錄導入 config
                    project_root = Path(__file__).parent.parent.parent
                    config_path = project_root / "config.py"
                    if config_path.exists() and str(project_root) not in sys.path:
                        sys.path.insert(0, str(project_root))
                    from config import API_ID as CONFIG_API_ID, API_HASH as CONFIG_API_HASH
                    if not api_id:
                        api_id = CONFIG_API_ID
                    if not api_hash:
                        api_hash = CONFIG_API_HASH
                except (ImportError, ValueError) as e:
                    logger.warning(f"無法從 config 模塊導入 API_ID/API_HASH: {e}")
            
            if not api_id or not api_hash:
                raise ValueError(
                    "無法獲取 Telegram API_ID 和 API_HASH。"
                    "請設置環境變量 TELEGRAM_API_ID 和 TELEGRAM_API_HASH，"
                    "或在項目根目錄的 config.py 中定義 API_ID 和 API_HASH。"
                )
            
            client = Client(
                name=session_path.stem,
                api_id=api_id,
                api_hash=api_hash,
                workdir=str(session_path.parent),
            )
            
            # 創建 AccountInstance
            account = AccountInstance(account_id, client, config)
            self.accounts[account_id] = account
            
            logger.info(f"賬號 {account_id} 已添加（未啟動）")
            return account
    
    async def remove_account(self, account_id: str) -> bool:
        """移除賬號"""
        async with self._lock:
            if account_id not in self.accounts:
                logger.warning(f"賬號 {account_id} 不存在")
                return False
            
            account = self.accounts[account_id]
            if account.status == AccountStatusEnum.ONLINE:
                await account.stop()
            
            del self.accounts[account_id]
            logger.info(f"賬號 {account_id} 已移除")
            return True
    
    async def start_account(self, account_id: str) -> bool:
        """啟動賬號"""
        if account_id not in self.accounts:
            logger.error(f"賬號 {account_id} 不存在")
            return False
        
        account = self.accounts[account_id]
        
        # 如果已經在線，直接返回
        if account.status == AccountStatusEnum.ONLINE:
            logger.info(f"賬號 {account_id} 已在線")
            return True
        
        # 嘗試啟動
        success = await account.start()
        
        # 如果啟動失敗，嘗試重連
        if not success and account.error_count < self.config.account_max_reconnect_attempts:
            logger.info(f"賬號 {account_id} 啟動失敗，嘗試重連...")
            await asyncio.sleep(self.config.account_reconnect_delay)
            success = await account.start()
        
        return success
    
    async def stop_account(self, account_id: str) -> bool:
        """停止賬號"""
        if account_id not in self.accounts:
            logger.error(f"賬號 {account_id} 不存在")
            return False
        
        account = self.accounts[account_id]
        return await account.stop()
    
    def get_account_status(self, account_id: str) -> Optional[AccountStatusData]:
        """獲取賬號狀態"""
        if account_id not in self.accounts:
            return None
        
        account = self.accounts[account_id]
        from datetime import datetime
        import time
        
        uptime = 0
        if account.start_time:
            uptime = int(time.time() - account.start_time)
        
        return AccountStatusData(
            account_id=account.account_id,
            status=account.status,
            online=account.status == AccountStatusEnum.ONLINE,
            last_activity=account.last_activity,
            message_count=account.message_count,
            reply_count=account.reply_count,
            redpacket_count=account.redpacket_count,
            error_count=account.error_count,
            uptime_seconds=uptime
        )
    
    def list_accounts(self) -> List[AccountInfo]:
        """列出所有賬號"""
        result = []
        for account_id, account in self.accounts.items():
            result.append(AccountInfo(
                account_id=account.account_id,
                session_file=account.config.session_file,
                script_id=account.config.script_id,
                status=account.status,
                group_count=len(account.config.group_ids),
                message_count=account.message_count,
                reply_count=account.reply_count,
                last_activity=account.last_activity
            ))
        return result

