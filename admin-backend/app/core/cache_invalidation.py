"""
智能缓存失效策略
提供基于事件和时间的缓存失效机制
"""
import logging
from typing import List, Set, Optional, Callable
from datetime import datetime, timedelta
from app.core.cache import get_cache_manager, invalidate_cache

logger = logging.getLogger(__name__)


class CacheInvalidationStrategy:
    """缓存失效策略管理器"""
    
    def __init__(self):
        self.cache_manager = get_cache_manager()
        self.invalidation_rules: List[dict] = []
        self.event_handlers: dict = {}
    
    def register_invalidation_rule(
        self,
        pattern: str,
        on_events: List[str],
        ttl_override: Optional[int] = None
    ):
        """
        注册缓存失效规则
        
        Args:
            pattern: 缓存键模式（支持通配符，如 "accounts_list:*"）
            on_events: 触发失效的事件列表（如 ["account.created", "account.updated"]）
            ttl_override: 可选的TTL覆盖值
        """
        rule = {
            "pattern": pattern,
            "on_events": on_events,
            "ttl_override": ttl_override
        }
        self.invalidation_rules.append(rule)
        logger.info(f"注册缓存失效规则: {pattern} -> {on_events}")
    
    def register_event_handler(self, event: str, handler: Callable):
        """注册事件处理器"""
        if event not in self.event_handlers:
            self.event_handlers[event] = []
        self.event_handlers[event].append(handler)
        logger.info(f"注册事件处理器: {event}")
    
    def trigger_event(self, event: str, **kwargs):
        """
        触发事件，自动失效相关缓存
        
        Args:
            event: 事件名称（如 "account.created", "account.updated"）
            **kwargs: 事件参数
        """
        logger.debug(f"触发事件: {event}")
        
        # 执行事件处理器
        if event in self.event_handlers:
            for handler in self.event_handlers[event]:
                try:
                    handler(event, **kwargs)
                except Exception as e:
                    logger.error(f"事件处理器执行失败: {e}", exc_info=True)
        
        # 查找匹配的失效规则
        for rule in self.invalidation_rules:
            if event in rule["on_events"]:
                pattern = rule["pattern"]
                try:
                    invalidate_cache(pattern)
                    logger.info(f"缓存失效: {pattern} (事件: {event})")
                except Exception as e:
                    logger.error(f"缓存失效失败: {e}", exc_info=True)
    
    def invalidate_by_pattern(self, pattern: str):
        """按模式失效缓存"""
        try:
            invalidate_cache(pattern)
            logger.info(f"手动缓存失效: {pattern}")
        except Exception as e:
            logger.error(f"缓存失效失败: {e}", exc_info=True)
    
    def invalidate_all(self):
        """失效所有缓存（谨慎使用）"""
        try:
            # 失效所有已知的缓存模式
            patterns = [
                "accounts_list:*",
                "account_detail:*",
                "scripts_list:*",
                "script_detail:*",
                "servers_list:*",
                "automation_tasks_list:*",
                "users_list:*",
                "notification_configs_list:*",
                "role_assignment_schemes_list:*",
                "dashboard_stats:*",
                "account_metrics:*",
                "system_statistics:*",
                "dialogue_contexts:*",
                "redpacket_stats:*"
            ]
            for pattern in patterns:
                try:
                    invalidate_cache(pattern)
                except Exception:
                    pass
            logger.warning("所有缓存已失效")
        except Exception as e:
            logger.error(f"失效所有缓存失败: {e}", exc_info=True)


# 全局实例
_invalidation_strategy: Optional[CacheInvalidationStrategy] = None


def get_invalidation_strategy() -> CacheInvalidationStrategy:
    """获取缓存失效策略管理器实例"""
    global _invalidation_strategy
    if _invalidation_strategy is None:
        _invalidation_strategy = CacheInvalidationStrategy()
        # 注册默认规则
        _setup_default_rules(_invalidation_strategy)
    return _invalidation_strategy


def _setup_default_rules(strategy: CacheInvalidationStrategy):
    """设置默认的缓存失效规则"""
    # 账号相关事件
    strategy.register_invalidation_rule(
        pattern="accounts_list:*",
        on_events=["account.created", "account.updated", "account.deleted", "account.started", "account.stopped"]
    )
    strategy.register_invalidation_rule(
        pattern="account_detail:*",
        on_events=["account.updated", "account.deleted", "account.started", "account.stopped"]
    )
    
    # 脚本相关事件
    strategy.register_invalidation_rule(
        pattern="scripts_list:*",
        on_events=["script.created", "script.updated", "script.deleted", "script.published"]
    )
    strategy.register_invalidation_rule(
        pattern="script_detail:*",
        on_events=["script.updated", "script.deleted"]
    )
    
    # 服务器相关事件
    strategy.register_invalidation_rule(
        pattern="servers_list:*",
        on_events=["server.updated", "server.deleted"]
    )
    
    # 自动化任务相关事件
    strategy.register_invalidation_rule(
        pattern="automation_tasks_list:*",
        on_events=["automation_task.created", "automation_task.updated", "automation_task.deleted", "automation_task.enabled", "automation_task.disabled"]
    )
    
    # 用户相关事件
    strategy.register_invalidation_rule(
        pattern="users_list:*",
        on_events=["user.created", "user.updated", "user.deleted"]
    )
    
    # 通知配置相关事件
    strategy.register_invalidation_rule(
        pattern="notification_configs_list:*",
        on_events=["notification_config.created", "notification_config.updated", "notification_config.deleted"]
    )
    
    # 角色分配方案相关事件
    strategy.register_invalidation_rule(
        pattern="role_assignment_schemes_list:*",
        on_events=["role_assignment_scheme.created", "role_assignment_scheme.updated", "role_assignment_scheme.deleted"]
    )
    
    # 仪表板统计（需要更频繁的更新）
    strategy.register_invalidation_rule(
        pattern="dashboard_stats:*",
        on_events=["account.created", "account.deleted", "script.created", "script.deleted", "message.sent", "reply.sent"]
    )
    
    # 账号指标
    strategy.register_invalidation_rule(
        pattern="account_metrics:*",
        on_events=["message.sent", "reply.sent", "error.occurred"]
    )
    
    # 系统统计
    strategy.register_invalidation_rule(
        pattern="system_statistics:*",
        on_events=["account.created", "account.deleted", "message.sent", "reply.sent"]
    )
    
    logger.info("默认缓存失效规则已设置")


# 便捷函数
def trigger_cache_invalidation(event: str, **kwargs):
    """触发缓存失效事件（便捷函数）"""
    strategy = get_invalidation_strategy()
    strategy.trigger_event(event, **kwargs)

