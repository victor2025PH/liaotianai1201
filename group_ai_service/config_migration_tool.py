"""
配置遷移工具
將現有的 AccountConfig 遷移到統一配置管理系統
"""
import logging
from typing import List, Optional
from datetime import datetime

from group_ai_service.models.account import AccountConfig
from group_ai_service.unified_config_manager import ConfigManager, UnifiedConfig, ChatConfig, RedpacketConfig, KeywordConfig

logger = logging.getLogger(__name__)


class ConfigMigrationTool:
    """配置遷移工具"""
    
    def __init__(self, config_manager: ConfigManager):
        """
        初始化配置遷移工具
        
        Args:
            config_manager: ConfigManager 實例
        """
        self.config_manager = config_manager
        self.logger = logging.getLogger(__name__)
    
    def migrate_account_config(self, account_id: str, account_config: AccountConfig) -> UnifiedConfig:
        """
        遷移單個賬號配置
        
        Args:
            account_id: 賬號 ID
            account_config: 現有的 AccountConfig
            
        Returns:
            遷移後的 UnifiedConfig
        """
        unified_config = self.config_manager.convert_from_account_config(account_config)
        self.config_manager.set_account_config(account_id, unified_config)
        
        self.logger.info(f"已遷移賬號 {account_id} 的配置")
        return unified_config
    
    def migrate_all_accounts(self, account_configs: dict) -> dict:
        """
        批量遷移所有賬號配置
        
        Args:
            account_configs: 賬號配置字典 {account_id: AccountConfig}
            
        Returns:
            遷移結果字典 {account_id: UnifiedConfig}
        """
        results = {}
        
        for account_id, account_config in account_configs.items():
            try:
                unified_config = self.migrate_account_config(account_id, account_config)
                results[account_id] = unified_config
            except Exception as e:
                self.logger.error(f"遷移賬號 {account_id} 配置失敗: {e}", exc_info=True)
                results[account_id] = None
        
        self.logger.info(f"已遷移 {len([r for r in results.values() if r])}/{len(account_configs)} 個賬號配置")
        return results
    
    def export_config_hierarchy(
        self,
        account_id: str,
        group_id: Optional[int] = None,
        role_id: Optional[str] = None
    ) -> dict:
        """
        導出配置層級（用於調試和驗證）
        
        Args:
            account_id: 賬號 ID
            group_id: 群組 ID（可選）
            role_id: 角色 ID（可選）
            
        Returns:
            配置層級字典
        """
        final_config = self.config_manager.get_config(
            account_id=account_id,
            group_id=group_id,
            role_id=role_id
        )
        
        hierarchy = {
            "account_id": account_id,
            "group_id": group_id,
            "role_id": role_id,
            "final_config": {
                "chat": {
                    "enabled": final_config.chat.enabled,
                    "interval_min": final_config.chat.interval_min,
                    "interval_max": final_config.chat.interval_max,
                    "reply_rate": final_config.chat.reply_rate,
                },
                "redpacket": {
                    "enabled": final_config.redpacket.enabled,
                    "probability": final_config.redpacket.probability,
                },
            },
            "global_config": {
                "chat": {
                    "enabled": self.config_manager.global_config.chat.enabled if self.config_manager.global_config else None,
                    "interval_min": self.config_manager.global_config.chat.interval_min if self.config_manager.global_config else None,
                } if self.config_manager.global_config else None,
            },
            "account_config": {
                "chat": {
                    "enabled": self.config_manager.account_configs.get(account_id).chat.enabled if account_id in self.config_manager.account_configs else None,
                } if account_id in self.config_manager.account_configs else None,
            },
            "group_config": {
                "chat": {
                    "enabled": self.config_manager.group_configs.get(group_id).chat.enabled if group_id and group_id in self.config_manager.group_configs else None,
                } if group_id and group_id in self.config_manager.group_configs else None,
            },
        }
        
        return hierarchy
