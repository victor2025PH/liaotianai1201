"""
群組管理增強功能
支持自動加入群組、群組監控、自動管理等
"""
import logging
import asyncio
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger(__name__)


class JoinType(Enum):
    """加入類型"""
    INVITE_LINK = "invite_link"
    USERNAME = "username"
    GROUP_ID = "group_id"
    SEARCH = "search"


@dataclass
class GroupJoinConfig:
    """群組加入配置"""
    id: str
    name: str
    enabled: bool = True
    join_type: JoinType = JoinType.INVITE_LINK
    invite_link: Optional[str] = None
    username: Optional[str] = None
    group_id: Optional[int] = None
    search_keywords: List[str] = field(default_factory=list)
    account_ids: List[str] = field(default_factory=list)
    priority: int = 0
    conditions: Dict[str, Any] = field(default_factory=dict)  # min_members, max_members, group_types等
    post_join_actions: List[Dict[str, Any]] = field(default_factory=list)  # 加入後動作


@dataclass
class GroupActivityMetrics:
    """群組活動指標"""
    group_id: int
    message_count_24h: int = 0
    active_members_24h: int = 0
    new_members_24h: int = 0
    redpacket_count_24h: int = 0
    last_activity: Optional[datetime] = None
    health_score: float = 0.0  # 0-1


@dataclass
class GroupMonitorConfig:
    """群組監控配置"""
    group_id: int
    enabled: bool = True
    metrics: List[str] = field(default_factory=list)  # 監控的指標
    alert_thresholds: Dict[str, float] = field(default_factory=dict)  # 告警閾值
    check_interval: int = 300  # 檢查間隔（秒）


class GroupManager:
    """群組管理器 - 增強功能"""
    
    def __init__(self, account_manager=None, action_executor=None):
        """
        初始化群組管理器
        
        Args:
            account_manager: AccountManager 實例
            action_executor: ActionExecutor 實例
        """
        self.logger = logging.getLogger(__name__)
        self.account_manager = account_manager
        self.action_executor = action_executor
        
        # 群組加入配置
        self.join_configs: Dict[str, GroupJoinConfig] = {}  # config_id -> config
        
        # 群組監控配置
        self.monitor_configs: Dict[int, GroupMonitorConfig] = {}  # group_id -> config
        
        # 群組活動指標
        self.activity_metrics: Dict[int, GroupActivityMetrics] = {}  # group_id -> metrics
        
        # 已加入的群組記錄
        self.joined_groups: Dict[int, Dict[str, Any]] = {}  # group_id -> info
        
        # 從數據庫加載配置
        self._load_configs()
        
        self.logger.info("GroupManager 初始化完成")
    
    def _load_configs(self):
        """從數據庫加載配置"""
        # 嘗試從數據庫加載配置
        try:
            # 動態導入，避免循環依賴
            import sys
            from pathlib import Path
            
            # 檢查是否在 admin-backend 環境中
            admin_backend_path = Path(__file__).parent.parent.parent / "admin-backend"
            if admin_backend_path.exists() and str(admin_backend_path) not in sys.path:
                sys.path.insert(0, str(admin_backend_path))
            
            try:
                from app.db import SessionLocal
                from app.models.unified_features import GroupJoinConfig as DBGroupJoinConfig
                
                db = SessionLocal()
                try:
                    db_configs = db.query(DBGroupJoinConfig).filter(
                        DBGroupJoinConfig.enabled == True
                    ).all()
                    
                    for db_config in db_configs:
                        # 轉換數據庫模型為處理器配置
                        config = GroupJoinConfig(
                            id=db_config.config_id,
                            name=db_config.name,
                            enabled=db_config.enabled,
                            join_type=JoinType(db_config.join_type) if db_config.join_type else JoinType.INVITE_LINK,
                            invite_link=db_config.invite_link,
                            username=db_config.username,
                            group_id=db_config.group_id,
                            search_keywords=db_config.search_keywords or [],
                            account_ids=db_config.account_ids or [],
                            min_members=db_config.min_members,
                            max_members=db_config.max_members,
                            group_types=db_config.group_types or [],
                            post_join_actions=db_config.post_join_actions or [],
                            priority=db_config.priority,
                        )
                        self.join_configs[config.id] = config
                    
                    if db_configs:
                        self.logger.info(f"從數據庫加載了 {len(db_configs)} 個群組加入配置")
                finally:
                    db.close()
            except ImportError:
                # 數據庫模組不可用（可能在 worker 節點環境）
                self.logger.debug("數據庫模組不可用，跳過從數據庫加載配置")
            except Exception as e:
                self.logger.warning(f"從數據庫加載配置失敗: {e}")
        except Exception as e:
            self.logger.warning(f"加載群組管理配置失敗: {e}")
    
    def add_join_config(self, config: GroupJoinConfig):
        """添加群組加入配置"""
        self.join_configs[config.id] = config
        self.logger.info(f"已添加群組加入配置: {config.name} ({config.id})")
    
    def remove_join_config(self, config_id: str):
        """移除群組加入配置"""
        if config_id in self.join_configs:
            del self.join_configs[config_id]
            self.logger.info(f"已移除群組加入配置: {config_id}")
    
    async def auto_join_groups(self, account_id: str) -> Dict[str, Any]:
        """
        自動加入配置的群組
        
        Args:
            account_id: 賬號 ID
            
        Returns:
            加入結果統計
        """
        if not self.account_manager:
            self.logger.error("AccountManager 未提供，無法自動加入群組")
            return {"success": False, "error": "AccountManager 未提供"}
        
        results = {
            "success": True,
            "total": 0,
            "success_count": 0,
            "failed_count": 0,
            "details": []
        }
        
        # 獲取該賬號需要加入的群組配置
        for config in self.join_configs.values():
            if not config.enabled:
                continue
            
            if account_id not in config.account_ids:
                continue
            
            results["total"] += 1
            
            try:
                # 檢查是否已加入
                if config.group_id and config.group_id in self.joined_groups:
                    self.logger.debug(f"賬號 {account_id} 已加入群組 {config.group_id}，跳過")
                    results["success_count"] += 1
                    continue
                
                # 執行加入
                success = await self._join_group(account_id, config)
                
                if success:
                    results["success_count"] += 1
                    # 記錄已加入
                    if config.group_id:
                        self.joined_groups[config.group_id] = {
                            "account_id": account_id,
                            "joined_at": datetime.now(),
                            "config_id": config.id
                        }
                    
                    # 執行加入後動作
                    await self._execute_post_join_actions(account_id, config)
                else:
                    results["failed_count"] += 1
                
                results["details"].append({
                    "config_id": config.id,
                    "group_name": config.name,
                    "success": success
                })
                
            except Exception as e:
                self.logger.error(f"自動加入群組失敗: {config.name}: {e}", exc_info=True)
                results["failed_count"] += 1
                results["details"].append({
                    "config_id": config.id,
                    "group_name": config.name,
                    "success": False,
                    "error": str(e)
                })
        
        return results
    
    async def _join_group(self, account_id: str, config: GroupJoinConfig) -> bool:
        """執行加入群組"""
        if not self.action_executor:
            return False
        
        action_data = {
            "account_id": account_id
        }
        
        if config.join_type == JoinType.INVITE_LINK:
            if not config.invite_link:
                return False
            action_data["invite_link"] = config.invite_link
        elif config.join_type == JoinType.USERNAME:
            if not config.username:
                return False
            action_data["username"] = config.username
        elif config.join_type == JoinType.GROUP_ID:
            if not config.group_id:
                return False
            
            # 優化：先獲取群組信息驗證
            if self.account_manager:
                account = self.account_manager.accounts.get(account_id)
                if account and account.client and account.client.is_connected:
                    try:
                        # 嘗試獲取群組信息
                        chat = await account.client.get_chat(config.group_id)
                        
                        # 驗證群組類型
                        if not hasattr(chat, 'type') or chat.type not in ['group', 'supergroup']:
                            self.logger.warning(
                                f"群組 {config.group_id} 不是有效的群組類型，"
                                f"類型: {getattr(chat, 'type', 'unknown')}"
                            )
                            return False
                        
                        # 檢查是否已經在群組中
                        if hasattr(chat, 'members_count') and chat.members_count is not None:
                            # 如果能夠獲取成員數，說明已經在群組中
                            self.logger.info(
                                f"賬號 {account_id} 已經在群組 {config.group_id} 中 "
                                f"(成員數: {chat.members_count})"
                            )
                            # 記錄已加入
                            self.joined_groups[config.group_id] = {
                                "account_id": account_id,
                                "joined_at": datetime.now(),
                                "config_id": config.id
                            }
                            return True
                        
                        # 檢查群組是否可加入（公開群組可以通過 ID 加入）
                        if hasattr(chat, 'username') and chat.username:
                            # 有用戶名的公開群組，使用用戶名加入更可靠
                            action_data["username"] = chat.username
                            action_data["group_id"] = None  # 清除 group_id，使用 username
                            self.logger.info(
                                f"群組 {config.group_id} 是公開群組 (username: {chat.username})，"
                                f"將使用用戶名加入"
                            )
                        else:
                            # 私有群組，需要邀請鏈接
                            self.logger.warning(
                                f"群組 {config.group_id} 是私有群組，無法通過 ID 直接加入，"
                                f"需要邀請鏈接"
                            )
                            return False
                            
                    except Exception as e:
                        # 如果獲取群組信息失敗，可能是群組不存在或無權限
                        self.logger.warning(
                            f"無法獲取群組 {config.group_id} 信息: {e}，"
                            f"將嘗試直接通過 ID 加入"
                        )
                        # 繼續嘗試直接加入
                        action_data["group_id"] = config.group_id
                else:
                    # 賬號或客戶端不可用，直接使用 group_id
                    action_data["group_id"] = config.group_id
            else:
                # 沒有 account_manager，直接使用 group_id
                action_data["group_id"] = config.group_id
        elif config.join_type == JoinType.SEARCH:
            # 實現關鍵詞搜索加入
            if not config.search_keywords:
                self.logger.warning("搜索類型需要提供 search_keywords")
                return False
            
            return await self._search_and_join_group(account_id, config)
        else:
            return False
        
        # 使用 ActionExecutor 加入群組
        return await self.action_executor.execute_action(
            "join_group",
            MessageContext(account_id=account_id),
            action_data,
            self.account_manager
        )
    
    async def _search_and_join_group(self, account_id: str, config: GroupJoinConfig) -> bool:
        """
        通過關鍵詞搜索並加入群組
        
        注意：Telegram API 的搜索功能有限，此實現主要支持：
        1. 通過用戶名搜索（如果關鍵詞是 @username 格式）
        2. 嘗試直接通過關鍵詞作為用戶名搜索
        """
        if not self.account_manager:
            return False
        
        account = self.account_manager.accounts.get(account_id)
        if not account or not account.client or not account.client.is_connected:
            self.logger.error(f"賬號 {account_id} 不可用或未連接")
            return False
        
        # 遍歷搜索關鍵詞
        for keyword in config.search_keywords:
            try:
                # 清理關鍵詞（移除 @ 符號和空格）
                clean_keyword = keyword.strip().lstrip('@')
                
                if not clean_keyword:
                    continue
                
                self.logger.info(f"嘗試搜索群組: {clean_keyword}")
                
                # 方法1: 嘗試作為用戶名直接獲取
                try:
                    chat = await account.client.get_chat(clean_keyword)
                    
                    # 驗證是群組類型
                    if not hasattr(chat, 'type') or chat.type not in ['group', 'supergroup']:
                        self.logger.debug(f"{clean_keyword} 不是群組類型: {chat.type}")
                        continue
                    
                    # 檢查條件
                    if not self._check_group_conditions(chat, config):
                        self.logger.debug(f"群組 {clean_keyword} 不滿足條件")
                        continue
                    
                    # 嘗試加入
                    try:
                        # 如果有用戶名，使用用戶名加入
                        if hasattr(chat, 'username') and chat.username:
                            action_data = {
                                "account_id": account_id,
                                "username": chat.username
                            }
                        else:
                            # 沒有用戶名，嘗試通過 ID 加入（可能需要邀請鏈接）
                            action_data = {
                                "account_id": account_id,
                                "group_id": chat.id
                            }
                        
                        success = await self.action_executor.execute_action(
                            "join_group",
                            MessageContext(account_id=account_id),
                            action_data,
                            self.account_manager
                        )
                        
                        if success:
                            # 記錄已加入
                            self.joined_groups[chat.id] = {
                                "account_id": account_id,
                                "joined_at": datetime.now(),
                                "config_id": config.id,
                                "search_keyword": keyword
                            }
                            
                            # 執行加入後動作
                            await self._execute_post_join_actions(account_id, config)
                            
                            self.logger.info(f"成功通過搜索加入群組: {clean_keyword} (ID: {chat.id})")
                            return True
                        else:
                            self.logger.warning(f"加入群組失敗: {clean_keyword}")
                            
                    except Exception as e:
                        self.logger.warning(f"加入群組 {clean_keyword} 時出錯: {e}")
                        continue
                        
                except Exception as e:
                    self.logger.debug(f"無法獲取群組 {clean_keyword}: {e}")
                    continue
                    
            except Exception as e:
                self.logger.error(f"搜索關鍵詞 {keyword} 時出錯: {e}", exc_info=True)
                continue
        
        self.logger.warning(f"無法通過關鍵詞搜索加入群組: {config.search_keywords}")
        return False
    
    def _check_group_conditions(self, chat, config: GroupJoinConfig) -> bool:
        """檢查群組是否滿足配置的條件"""
        # 檢查成員數
        if hasattr(chat, 'members_count') and chat.members_count is not None:
            min_members = config.conditions.get('min_members') or config.min_members
            max_members = config.conditions.get('max_members') or config.max_members
            
            if min_members and chat.members_count < min_members:
                return False
            if max_members and chat.members_count > max_members:
                return False
        
        # 檢查群組類型
        group_types = config.conditions.get('group_types') or config.group_types or []
        if group_types:
            chat_type = getattr(chat, 'type', None)
            if chat_type not in group_types:
                return False
        
        return True
    
    async def _execute_post_join_actions(self, account_id: str, config: GroupJoinConfig):
        """執行加入後動作"""
        if not config.post_join_actions:
            return
        
        for action in config.post_join_actions:
            action_type = action.get("type")
            if action_type == "send_message":
                # 發送歡迎消息
                message = action.get("message", "大家好！我是新成員，請多關照～")
                delay = action.get("delay", [5, 10])  # 默認延遲 5-10 秒
                
                if self.action_executor and config.group_id:
                    await asyncio.sleep(delay[0] if isinstance(delay, list) else delay)
                    await self.action_executor.execute_action(
                        "send_message",
                        MessageContext(account_id=account_id, group_id=config.group_id),
                        {
                            "message": message,
                            "group_id": config.group_id,
                            "account_id": account_id,
                            "delay": delay
                        },
                        self.account_manager
                    )
    
    def update_activity_metrics(self, group_id: int, metrics: GroupActivityMetrics):
        """更新群組活動指標"""
        self.activity_metrics[group_id] = metrics
    
    def get_activity_metrics(self, group_id: int) -> Optional[GroupActivityMetrics]:
        """獲取群組活動指標"""
        return self.activity_metrics.get(group_id)
    
    def calculate_health_score(self, metrics: GroupActivityMetrics, total_members: Optional[int] = None) -> float:
        """
        計算群組健康度評分
        
        Args:
            metrics: 群組活動指標
            total_members: 總成員數（可選，如果提供則計算參與度）
        """
        # 簡單的評分算法
        score = 0.0
        
        # 活動度（40%）
        if metrics.message_count_24h > 0:
            activity_score = min(metrics.message_count_24h / 100, 1.0)  # 100 條消息為滿分
            score += activity_score * 0.4
        
        # 成員穩定性（30%）
        if metrics.active_members_24h > 0:
            stability_score = min(metrics.active_members_24h / 50, 1.0)  # 50 個活躍成員為滿分
            score += stability_score * 0.3
        
        # 參與度（30%）
        engagement_score = self._calculate_engagement_score(metrics, total_members)
        score += engagement_score * 0.3
        
        return min(score, 1.0)
    
    def _calculate_engagement_score(self, metrics: GroupActivityMetrics, total_members: Optional[int] = None) -> float:
        """
        計算參與度評分
        
        參與度 = 活躍成員數 / 總成員數
        
        Args:
            metrics: 群組活動指標
            total_members: 總成員數
            
        Returns:
            參與度評分 (0-1)
        """
        if not total_members or total_members <= 0:
            # 如果沒有總成員數，使用活躍成員數作為代理指標
            # 假設活躍成員數越多，參與度越高
            if metrics.active_members_24h > 0:
                # 使用活躍成員數的對數函數來估算參與度
                # 10個活躍成員 = 0.5, 50個 = 0.8, 100個 = 1.0
                engagement_score = min(metrics.active_members_24h / 100, 1.0)
                return engagement_score
            else:
                return 0.0
        
        # 計算實際參與度
        if metrics.active_members_24h <= 0:
            return 0.0
        
        engagement_ratio = metrics.active_members_24h / total_members
        
        # 參與度評分：
        # - 10% 以上 = 優秀 (1.0)
        # - 5-10% = 良好 (0.8)
        # - 2-5% = 一般 (0.6)
        # - 1-2% = 較低 (0.4)
        # - 1% 以下 = 很低 (0.2)
        if engagement_ratio >= 0.10:
            return 1.0
        elif engagement_ratio >= 0.05:
            return 0.8
        elif engagement_ratio >= 0.02:
            return 0.6
        elif engagement_ratio >= 0.01:
            return 0.4
        else:
            return 0.2
    
    def detect_anomalies(self, group_id: int) -> List[Dict[str, Any]]:
        """檢測群組異常"""
        anomalies = []
        metrics = self.activity_metrics.get(group_id)
        
        if not metrics:
            return anomalies
        
        # 檢測低活躍度
        if metrics.message_count_24h < 5:
            anomalies.append({
                "type": "low_activity",
                "severity": "warning",
                "message": f"群組 {group_id} 24小時內消息數少於 5 條",
                "value": metrics.message_count_24h
            })
        
        # 檢測健康度低
        if metrics.health_score < 0.3:
            anomalies.append({
                "type": "low_health",
                "severity": "critical",
                "message": f"群組 {group_id} 健康度低於 0.3",
                "value": metrics.health_score
            })
        
        return anomalies
