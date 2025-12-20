"""
統一配置管理系統
分層配置管理，解決配置衝突問題
"""
import logging
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from enum import Enum

from group_ai_service.models.account import AccountConfig

logger = logging.getLogger(__name__)


class ConfigLevel(Enum):
    """配置層級"""
    GLOBAL = "global"      # 全局配置（最低優先級）
    GROUP = "group"        # 群組配置
    ACCOUNT = "account"    # 賬號配置
    ROLE = "role"         # 角色配置
    TASK = "task"         # 任務配置（最高優先級）


@dataclass
class ChatConfig:
    """聊天配置"""
    enabled: bool = True
    interval_min: int = 30  # 秒
    interval_max: int = 120  # 秒
    reply_rate: float = 0.3
    max_replies_per_hour: int = 50
    min_reply_interval: int = 3  # 秒


@dataclass
class RedpacketConfig:
    """紅包配置"""
    enabled: bool = True
    auto_grab: bool = True
    interval: int = 300  # 秒
    probability: float = 0.5
    max_per_hour: int = 10
    cooldown_seconds: int = 300
    min_amount: float = 0.01


@dataclass
class KeywordConfig:
    """關鍵詞配置"""
    enabled: bool = True
    keywords: List[str] = field(default_factory=list)
    match_type: str = "any"  # any/all/regex
    case_sensitive: bool = False


@dataclass
class UnifiedConfig:
    """統一配置"""
    chat: ChatConfig = field(default_factory=ChatConfig)
    redpacket: RedpacketConfig = field(default_factory=RedpacketConfig)
    keywords: KeywordConfig = field(default_factory=KeywordConfig)
    metadata: Dict[str, Any] = field(default_factory=dict)


class ConfigManager:
    """統一配置管理器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # 分層配置存儲
        self.global_config: Optional[UnifiedConfig] = None
        self.group_configs: Dict[int, UnifiedConfig] = {}  # group_id -> config
        self.account_configs: Dict[str, UnifiedConfig] = {}  # account_id -> config
        self.role_configs: Dict[str, UnifiedConfig] = {}  # role_id -> config
        self.task_configs: Dict[str, UnifiedConfig] = {}  # task_id -> config
        
        # 初始化全局默認配置
        self.global_config = UnifiedConfig()
        
        self.logger.info("ConfigManager 初始化完成")
    
    def set_global_config(self, config: UnifiedConfig):
        """設置全局配置"""
        self.global_config = config
        self.logger.info("全局配置已更新")
    
    def set_group_config(self, group_id: int, config: UnifiedConfig):
        """設置群組配置"""
        self.group_configs[group_id] = config
        self.logger.info(f"群組 {group_id} 配置已更新")
    
    def set_account_config(self, account_id: str, config: UnifiedConfig):
        """設置賬號配置"""
        self.account_configs[account_id] = config
        self.logger.info(f"賬號 {account_id} 配置已更新")
    
    def set_role_config(self, role_id: str, config: UnifiedConfig):
        """設置角色配置"""
        self.role_configs[role_id] = config
        self.logger.info(f"角色 {role_id} 配置已更新")
    
    def set_task_config(self, task_id: str, config: UnifiedConfig):
        """設置任務配置"""
        self.task_configs[task_id] = config
        self.logger.info(f"任務 {task_id} 配置已更新")
    
    def get_config(
        self,
        account_id: str,
        group_id: Optional[int] = None,
        role_id: Optional[str] = None,
        task_id: Optional[str] = None
    ) -> UnifiedConfig:
        """
        獲取最終配置（合併所有層級的配置）
        
        優先級（從高到低）:
        1. 任務配置 (task_id)
        2. 賬號配置 (account_id)
        3. 角色配置 (role_id)
        4. 群組配置 (group_id)
        5. 全局配置
        
        Args:
            account_id: 賬號 ID
            group_id: 群組 ID（可選）
            role_id: 角色 ID（可選）
            task_id: 任務 ID（可選）
            
        Returns:
            合併後的 UnifiedConfig
        """
        # 從全局配置開始
        result = UnifiedConfig()
        
        if self.global_config:
            result = self._merge_config(result, self.global_config)
        
        # 合併群組配置
        if group_id and group_id in self.group_configs:
            result = self._merge_config(result, self.group_configs[group_id])
        
        # 合併角色配置
        if role_id and role_id in self.role_configs:
            result = self._merge_config(result, self.role_configs[role_id])
        
        # 合併賬號配置
        if account_id in self.account_configs:
            result = self._merge_config(result, self.account_configs[account_id])
        
        # 合併任務配置（最高優先級）
        if task_id and task_id in self.task_configs:
            result = self._merge_config(result, self.task_configs[task_id])
        
        return result
    
    def _merge_config(self, base: UnifiedConfig, override: UnifiedConfig) -> UnifiedConfig:
        """合併配置（override 覆蓋 base）"""
        # 合併聊天配置
        merged_chat = ChatConfig(
            enabled=override.chat.enabled if override.chat.enabled != base.chat.enabled else base.chat.enabled,
            interval_min=override.chat.interval_min if override.chat.interval_min != base.chat.interval_min else base.chat.interval_min,
            interval_max=override.chat.interval_max if override.chat.interval_max != base.chat.interval_max else base.chat.interval_max,
            reply_rate=override.chat.reply_rate if override.chat.reply_rate != base.chat.reply_rate else base.chat.reply_rate,
            max_replies_per_hour=override.chat.max_replies_per_hour if override.chat.max_replies_per_hour != base.chat.max_replies_per_hour else base.chat.max_replies_per_hour,
            min_reply_interval=override.chat.min_reply_interval if override.chat.min_reply_interval != base.chat.min_reply_interval else base.chat.min_reply_interval,
        )
        
        # 合併紅包配置
        merged_redpacket = RedpacketConfig(
            enabled=override.redpacket.enabled if override.redpacket.enabled != base.redpacket.enabled else base.redpacket.enabled,
            auto_grab=override.redpacket.auto_grab if override.redpacket.auto_grab != base.redpacket.auto_grab else base.redpacket.auto_grab,
            interval=override.redpacket.interval if override.redpacket.interval != base.redpacket.interval else base.redpacket.interval,
            probability=override.redpacket.probability if override.redpacket.probability != base.redpacket.probability else base.redpacket.probability,
            max_per_hour=override.redpacket.max_per_hour if override.redpacket.max_per_hour != base.redpacket.max_per_hour else base.redpacket.max_per_hour,
            cooldown_seconds=override.redpacket.cooldown_seconds if override.redpacket.cooldown_seconds != base.redpacket.cooldown_seconds else base.redpacket.cooldown_seconds,
            min_amount=override.redpacket.min_amount if override.redpacket.min_amount != base.redpacket.min_amount else base.redpacket.min_amount,
        )
        
        # 合併關鍵詞配置
        merged_keywords = KeywordConfig(
            enabled=override.keywords.enabled if override.keywords.enabled != base.keywords.enabled else base.keywords.enabled,
            keywords=override.keywords.keywords if override.keywords.keywords else base.keywords.keywords,
            match_type=override.keywords.match_type if override.keywords.match_type != base.keywords.match_type else base.keywords.match_type,
            case_sensitive=override.keywords.case_sensitive if override.keywords.case_sensitive != base.keywords.case_sensitive else base.keywords.case_sensitive,
        )
        
        # 合併元數據
        merged_metadata = {**base.metadata, **override.metadata}
        
        return UnifiedConfig(
            chat=merged_chat,
            redpacket=merged_redpacket,
            keywords=merged_keywords,
            metadata=merged_metadata
        )
    
    def convert_from_account_config(self, account_config: AccountConfig) -> UnifiedConfig:
        """從 AccountConfig 轉換為 UnifiedConfig"""
        return UnifiedConfig(
            chat=ChatConfig(
                enabled=account_config.active,
                interval_min=account_config.min_reply_interval or 30,
                interval_max=account_config.max_replies_per_hour or 120,
                reply_rate=account_config.reply_rate or 0.3,
                max_replies_per_hour=account_config.max_replies_per_hour or 50,
                min_reply_interval=account_config.min_reply_interval or 3,
            ),
            redpacket=RedpacketConfig(
                enabled=account_config.redpacket_enabled,
                auto_grab=account_config.redpacket_enabled,
                probability=account_config.redpacket_probability or 0.5,
                max_per_hour=10,
                cooldown_seconds=300,
                min_amount=0.01,
            ),
            keywords=KeywordConfig(
                enabled=True,
                keywords=[],
                match_type="any",
                case_sensitive=False,
            ),
            metadata=account_config.config if isinstance(account_config.config, dict) else {}
        )
    
    def update_account_config_from_unified(
        self,
        account_config: AccountConfig,
        unified_config: UnifiedConfig
    ) -> AccountConfig:
        """從 UnifiedConfig 更新 AccountConfig"""
        account_config.active = unified_config.chat.enabled
        account_config.min_reply_interval = unified_config.chat.min_reply_interval
        account_config.max_replies_per_hour = unified_config.chat.max_replies_per_hour
        account_config.reply_rate = unified_config.chat.reply_rate
        account_config.redpacket_enabled = unified_config.redpacket.enabled
        account_config.redpacket_probability = unified_config.redpacket.probability
        
        return account_config
