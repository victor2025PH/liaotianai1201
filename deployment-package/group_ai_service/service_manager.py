"""
服務管理器 - 統一管理劇本引擎、對話管理器和會話池
"""
import logging
import asyncio
from typing import Dict, Optional
from pathlib import Path

from group_ai_service.account_manager import AccountManager, AccountInstance
from group_ai_service.script_engine import ScriptEngine
from group_ai_service.script_parser import ScriptParser, Script
from group_ai_service.dialogue_manager import DialogueManager
from group_ai_service.session_pool import ExtendedSessionPool
from group_ai_service.models.account import AccountConfig, AccountStatusEnum

logger = logging.getLogger(__name__)


class ServiceManager:
    """服務管理器 - 統一管理所有服務"""
    
    _instance: Optional['ServiceManager'] = None
    
    def __init__(self):
        try:
            logger.info("開始初始化 ServiceManager...")
            self.account_manager = AccountManager()
            logger.debug("AccountManager 初始化成功")
            
            self.script_parser = ScriptParser()
            logger.debug("ScriptParser 初始化成功")
            
            self.script_engines: Dict[str, ScriptEngine] = {}
            logger.debug("script_engines 初始化成功")
            
            # 初始化遊戲系統 API 客戶端（如果配置了）
            self.game_api_client = None
            self._init_game_api_client()
            
            # DialogueManager 初始化可能失敗，添加錯誤處理
            try:
                # 傳入遊戲 API 客戶端給 RedpacketHandler
                from group_ai_service.redpacket_handler import RedpacketHandler
                redpacket_handler = RedpacketHandler(game_api_client=self.game_api_client)
                
                self.dialogue_manager = DialogueManager(redpacket_handler=redpacket_handler)
                logger.debug("DialogueManager 初始化成功")
            except Exception as e:
                logger.error(f"DialogueManager 初始化失敗: {e}", exc_info=True)
                raise  # 暫時還是拋出異常，讓調用者知道
            
            # 初始化遊戲引導服務
            try:
                from group_ai_service.game_guide_service import GameGuideService
                self.game_guide_service = GameGuideService(
                    dialogue_manager=self.dialogue_manager,
                    account_manager=self.account_manager
                )
                logger.debug("GameGuideService 初始化成功")
                
                # 註冊遊戲事件處理器（如果配置了遊戲API客戶端）
                if self.game_api_client:
                    # 注意：GameAPIClient 需要支持事件註冊
                    # 這裡先記錄，後續可以擴展 GameAPIClient 支持事件回調
                    logger.info("遊戲引導服務已就緒，等待遊戲事件")
            except Exception as e:
                logger.warning(f"初始化遊戲引導服務失敗: {e}，遊戲引導功能將不可用")
                self.game_guide_service = None
            
            self.session_pool: Optional[ExtendedSessionPool] = None
            self._scripts_cache: Dict[str, Script] = {}  # 緩存已加載的劇本
            logger.info("ServiceManager 初始化完成")
        except Exception as e:
            logger.exception(f"ServiceManager 初始化過程中發生錯誤: {e}", exc_info=True)
            raise
    
    @classmethod
    def get_instance(cls) -> 'ServiceManager':
        """獲取 ServiceManager 單例"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def _init_game_api_client(self):
        """初始化遊戲系統 API 客戶端"""
        try:
            from group_ai_service.config import get_group_ai_config
            config = get_group_ai_config()
            
            # 優先使用數據庫對接（如果配置了）
            if config.game_database_url:
                from group_ai_service.game_api_client import GameAPIClient
                self.game_api_client = GameAPIClient(
                    base_url=config.game_api_base_url,
                    api_key=config.game_api_key,
                    timeout=config.game_api_timeout,
                    database_url=config.game_database_url
                )
                logger.info(f"遊戲系統 API 客戶端已初始化（數據庫模式）: {config.game_database_url}")
            elif config.game_api_enabled and config.game_api_base_url:
                from group_ai_service.game_api_client import GameAPIClient
                self.game_api_client = GameAPIClient(
                    base_url=config.game_api_base_url,
                    api_key=config.game_api_key,
                    timeout=config.game_api_timeout
                )
                logger.info(f"遊戲系統 API 客戶端已初始化（HTTP API 模式）: {config.game_api_base_url}")
            else:
                logger.info("遊戲系統 API 未啟用或未配置，將使用 Telegram API 檢測")
                self.game_api_client = None
        except Exception as e:
            logger.warning(f"初始化遊戲系統 API 客戶端失敗: {e}，將使用 Telegram API 檢測")
            self.game_api_client = None
    
    async def handle_game_start(self, game_event):
        """處理遊戲開始事件"""
        logger.info(f"遊戲開始: group_id={game_event.group_id}, game_id={game_event.game_id}")
        # 觸發遊戲開始引導
        if self.game_guide_service:
            await self.game_guide_service.on_game_start(game_event)
    
    async def handle_redpacket_sent(self, game_event):
        """處理紅包發放事件"""
        logger.info(f"紅包發放: group_id={game_event.group_id}, payload={game_event.payload}")
        # 觸發紅包發送引導
        if self.game_guide_service:
            await self.game_guide_service.on_redpacket_sent(game_event)
    
    async def handle_redpacket_claimed(self, game_event):
        """處理紅包被領取事件"""
        logger.info(f"紅包被領取: group_id={game_event.group_id}, payload={game_event.payload}")
        # 觸發紅包被領取引導
        if self.game_guide_service:
            await self.game_guide_service.on_redpacket_claimed(game_event)
    
    async def handle_game_end(self, game_event):
        """處理遊戲結束事件"""
        logger.info(f"遊戲結束: group_id={game_event.group_id}, game_id={game_event.game_id}")
        # 觸發遊戲結束引導
        if self.game_guide_service:
            await self.game_guide_service.on_game_end(game_event)
    
    async def handle_result_announced(self, game_event):
        """處理結果公布事件"""
        logger.info(f"結果公布: group_id={game_event.group_id}, payload={game_event.payload}")
        # 觸發結果公布引導
        if self.game_guide_service:
            await self.game_guide_service.on_result_announced(game_event)
    
    def get_script(self, script_id: str, yaml_content: Optional[str] = None) -> Optional[Script]:
        """獲取劇本（從緩存、文件系統或數據庫）"""
        # 先從緩存獲取
        if script_id in self._scripts_cache:
            return self._scripts_cache[script_id]
        
        # 如果提供了 YAML 內容，直接解析
        if yaml_content:
            try:
                import tempfile
                with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False, encoding='utf-8') as f:
                    f.write(yaml_content)
                    temp_path = f.name
                
                try:
                    script = self.script_parser.load_script(temp_path)
                    self._scripts_cache[script_id] = script
                    logger.info(f"從 YAML 內容加載劇本: {script_id}")
                    return script
                finally:
                    Path(temp_path).unlink(missing_ok=True)
            except Exception as e:
                logger.error(f"從 YAML 內容加載劇本失敗 ({script_id}): {e}")
        
        # 嘗試從文件系統加載
        script_path = Path(f"ai_models/group_scripts/{script_id}.yaml")
        if script_path.exists():
            try:
                script = self.script_parser.load_script(str(script_path))
                self._scripts_cache[script_id] = script
                logger.info(f"從文件加載劇本: {script_id}")
                return script
            except Exception as e:
                logger.error(f"從文件加載劇本失敗 ({script_id}): {e}")
        
        logger.warning(f"劇本 {script_id} 未找到")
        return None
    
    def initialize_account_services(
        self,
        account_id: str,
        account_config: AccountConfig,
        script_yaml_content: Optional[str] = None
    ) -> bool:
        """初始化帳號的服務（劇本引擎和對話管理器）"""
        try:
            # 1. 加載劇本
            script = self.get_script(account_config.script_id, script_yaml_content)
            if not script:
                logger.error(f"帳號 {account_id} 無法加載劇本: {account_config.script_id}")
                return False
            
            # 2. 創建或獲取劇本引擎
            if account_id not in self.script_engines:
                script_engine = ScriptEngine()
                script_engine.initialize_account(account_id, script)
                self.script_engines[account_id] = script_engine
                logger.info(f"帳號 {account_id} 劇本引擎已初始化")
            else:
                script_engine = self.script_engines[account_id]
            
            # 3. 初始化對話管理器
            self.dialogue_manager.initialize_account(
                account_id=account_id,
                script_engine=script_engine,
                group_ids=account_config.group_ids or []
            )
            
            logger.info(f"帳號 {account_id} 服務初始化完成")
            return True
            
        except Exception as e:
            logger.error(f"初始化帳號 {account_id} 服務失敗: {e}", exc_info=True)
            return False
    
    async def start_account(self, account_id: str, script_yaml_content: Optional[str] = None) -> bool:
        """啟動帳號（包括初始化服務）"""
        if account_id not in self.account_manager.accounts:
            logger.error(f"帳號 {account_id} 不存在於 AccountManager 中")
            return False
        
        account = self.account_manager.accounts[account_id]
        
        # 檢查 session 文件是否存在
        from pathlib import Path
        session_path = Path(account.config.session_file)
        if not session_path.exists():
            logger.error(f"帳號 {account_id} 的 Session 文件不存在: {account.config.session_file}")
            return False
        
        # 1. 初始化服務（劇本引擎和對話管理器）
        if not self.initialize_account_services(account_id, account.config, script_yaml_content):
            logger.error(f"帳號 {account_id} 服務初始化失敗（可能是劇本無法加載）")
            return False
        
        # 2. 啟動帳號（連接 Telegram）
        try:
            success = await self.account_manager.start_account(account_id)
            if not success:
                # 檢查賬號狀態，獲取更多錯誤信息
                account_status = account.status
                error_msg = f"帳號 {account_id} 啟動失敗"
                if account_status == AccountStatusEnum.ERROR:
                    error_msg += "（狀態為 ERROR，可能是 Telegram 連接失敗）"
                elif account.error_count > 0:
                    error_msg += f"（已嘗試 {account.error_count} 次）"
                logger.error(error_msg)
                return False
        except Exception as e:
            logger.error(f"帳號 {account_id} 啟動時發生異常: {e}", exc_info=True)
            return False
        
        # 3. 確保會話池已啟動並監聽消息
        if not self.session_pool:
            try:
                self.session_pool = ExtendedSessionPool(
                    account_manager=self.account_manager,
                    dialogue_manager=self.dialogue_manager
                )
                await self.session_pool.start()
                logger.info("會話池已啟動")
            except Exception as e:
                logger.error(f"啟動會話池失敗: {e}", exc_info=True)
                # 會話池啟動失敗不應該阻止賬號啟動，只是消息監聽不可用
                logger.warning(f"帳號 {account_id} 已啟動，但會話池未啟動，消息監聽不可用")
        
        # 為新啟動的帳號啟動消息監聽
        if self.session_pool:
            try:
                await self.session_pool.start_monitoring_account(account_id)
            except Exception as e:
                logger.warning(f"為帳號 {account_id} 啟動消息監聽失敗: {e}，但賬號已啟動")
        
        logger.info(f"帳號 {account_id} 已完全啟動（劇本引擎、對話管理器和消息監聽已初始化）")
        return True
    
    async def stop_account(self, account_id: str) -> bool:
        """停止帳號"""
        # 停止帳號連接
        success = await self.account_manager.stop_account(account_id)
        
        # 清理服務（可選，保留狀態以便重啟）
        # self.dialogue_manager.remove_account(account_id)
        # if account_id in self.script_engines:
        #     self.script_engines[account_id].remove_account(account_id)
        
        return success
    
    def remove_account(self, account_id: str):
        """移除帳號（清理所有相關服務）"""
        # 停止帳號
        if account_id in self.account_manager.accounts:
            account = self.account_manager.accounts[account_id]
            if account.status.value == "online":
                asyncio.create_task(self.stop_account(account_id))
        
        # 清理對話管理器
        self.dialogue_manager.remove_account(account_id)
        
        # 清理劇本引擎
        if account_id in self.script_engines:
            self.script_engines[account_id].remove_account(account_id)
            del self.script_engines[account_id]
        
        # 從帳號管理器移除
        asyncio.create_task(self.account_manager.remove_account(account_id))
        
        logger.info(f"帳號 {account_id} 已完全移除")
    
    async def start_session_pool(self):
        """啟動會話池"""
        if not self.session_pool:
            self.session_pool = ExtendedSessionPool(
                account_manager=self.account_manager,
                dialogue_manager=self.dialogue_manager
            )
        
        await self.session_pool.start()
        logger.info("會話池已啟動")
    
    async def stop_session_pool(self):
        """停止會話池"""
        if self.session_pool:
            await self.session_pool.stop()
            logger.info("會話池已停止")

