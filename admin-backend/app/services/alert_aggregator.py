"""
告警聚合服务
提供告警聚合、去重、级别管理、静默功能
"""
import logging
from typing import Dict, List, Optional, Set, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class AlertSeverity(str, Enum):
    """告警严重程度"""
    CRITICAL = "critical"  # 严重：需要立即处理
    HIGH = "high"  # 高：需要尽快处理
    MEDIUM = "medium"  # 中：需要关注
    LOW = "low"  # 低：信息性告警


class AlertStatus(str, Enum):
    """告警状态"""
    ACTIVE = "active"  # 活跃
    RESOLVED = "resolved"  # 已解决
    SUPPRESSED = "suppressed"  # 已抑制（静默）
    ACKNOWLEDGED = "acknowledged"  # 已确认


@dataclass
class AggregatedAlert:
    """聚合后的告警"""
    alert_key: str
    alert_type: str
    severity: AlertSeverity
    message: str
    account_id: Optional[str] = None
    count: int = 1  # 相同告警的数量
    first_occurrence: datetime = field(default_factory=datetime.now)
    last_occurrence: datetime = field(default_factory=datetime.now)
    status: AlertStatus = AlertStatus.ACTIVE
    resolved_at: Optional[datetime] = None
    suppressed_until: Optional[datetime] = None
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None
    related_alerts: List[str] = field(default_factory=list)  # 相关告警 ID


class AlertAggregator:
    """告警聚合器"""
    
    def __init__(
        self,
        deduplication_window: int = 300,  # 5分钟内相同告警视为重复
        aggregation_window: int = 3600,  # 1小时内聚合相同告警
        max_alerts_per_key: int = 100  # 每个告警键最多保留的告警数
    ):
        """
        初始化告警聚合器
        
        Args:
            deduplication_window: 去重时间窗口（秒）
            aggregation_window: 聚合时间窗口（秒）
            max_alerts_per_key: 每个告警键最多保留的告警数
        """
        self.deduplication_window = deduplication_window
        self.aggregation_window = aggregation_window
        self.max_alerts_per_key = max_alerts_per_key
        
        # 告警存储：key -> AggregatedAlert
        self.aggregated_alerts: Dict[str, AggregatedAlert] = {}
        
        # 静默规则：key -> 静默截止时间
        self.suppression_rules: Dict[str, datetime] = {}
        
        # 确认记录：key -> (确认人, 确认时间)
        self.acknowledgments: Dict[str, Tuple[str, datetime]] = {}
        
        # 统计信息
        self.stats = {
            "total_alerts": 0,
            "deduplicated": 0,
            "aggregated": 0,
            "suppressed": 0,
            "resolved": 0,
        }
    
    def _generate_alert_key(
        self,
        alert_type: str,
        account_id: Optional[str],
        message: str,
        severity: Optional[AlertSeverity] = None
    ) -> str:
        """
        生成告警唯一键
        
        Args:
            alert_type: 告警类型
            account_id: 账号ID
            message: 告警消息
            severity: 告警严重程度
        
        Returns:
            告警唯一键
        """
        # 使用消息的前100个字符作为键的一部分（避免过长）
        message_hash = hash(message[:100])
        key_parts = [
            alert_type,
            account_id or "system",
            str(message_hash),
        ]
        if severity:
            key_parts.append(severity.value)
        
        return ":".join(key_parts)
    
    def _determine_severity(self, alert_type: str, message: str) -> AlertSeverity:
        """
        根据告警类型和消息确定严重程度
        
        Args:
            alert_type: 告警类型
            message: 告警消息
        
        Returns:
            告警严重程度
        """
        # 错误类型告警通常是高优先级
        if alert_type == "error":
            # 检查消息中的关键词
            critical_keywords = ["critical", "fatal", "crash", "down", "offline"]
            if any(keyword in message.lower() for keyword in critical_keywords):
                return AlertSeverity.CRITICAL
            return AlertSeverity.HIGH
        
        # 警告类型告警通常是中等优先级
        if alert_type == "warning":
            return AlertSeverity.MEDIUM
        
        # 信息类型告警通常是低优先级
        if alert_type == "info":
            return AlertSeverity.LOW
        
        # 默认中等优先级
        return AlertSeverity.MEDIUM
    
    def _is_duplicate(
        self,
        alert_key: str,
        timestamp: datetime
    ) -> bool:
        """
        检查告警是否为重复（在去重时间窗口内）
        
        Args:
            alert_key: 告警键
            timestamp: 告警时间戳
        
        Returns:
            是否为重复告警
        """
        if alert_key not in self.aggregated_alerts:
            return False
        
        aggregated = self.aggregated_alerts[alert_key]
        
        # 检查是否在去重时间窗口内
        time_diff = (timestamp - aggregated.last_occurrence).total_seconds()
        return time_diff < self.deduplication_window
    
    def _should_suppress(self, alert_key: str, timestamp: datetime) -> bool:
        """
        检查告警是否应该被抑制（静默）
        
        Args:
            alert_key: 告警键
            timestamp: 告警时间戳
        
        Returns:
            是否应该被抑制
        """
        # 检查静默规则
        if alert_key in self.suppression_rules:
            suppress_until = self.suppression_rules[alert_key]
            if timestamp < suppress_until:
                return True
        
        # 检查聚合告警的静默状态
        if alert_key in self.aggregated_alerts:
            aggregated = self.aggregated_alerts[alert_key]
            if aggregated.suppressed_until and timestamp < aggregated.suppressed_until:
                return True
        
        return False
    
    def add_alert(
        self,
        alert_type: str,
        message: str,
        account_id: Optional[str] = None,
        timestamp: Optional[datetime] = None,
        severity: Optional[AlertSeverity] = None
    ) -> Tuple[bool, Optional[AggregatedAlert]]:
        """
        添加告警（自动聚合和去重）
        
        Args:
            alert_type: 告警类型
            message: 告警消息
            account_id: 账号ID
            timestamp: 告警时间戳
            severity: 告警严重程度（可选，自动确定）
        
        Returns:
            (是否为新告警, 聚合后的告警对象)
        """
        if timestamp is None:
            timestamp = datetime.now()
        
        if severity is None:
            severity = self._determine_severity(alert_type, message)
        
        alert_key = self._generate_alert_key(alert_type, account_id, message, severity)
        
        # 检查是否应该被抑制
        if self._should_suppress(alert_key, timestamp):
            self.stats["suppressed"] += 1
            logger.debug(f"告警被抑制: {alert_key}")
            return False, None
        
        # 检查是否为重复告警
        if self._is_duplicate(alert_key, timestamp):
            # 更新聚合告警
            aggregated = self.aggregated_alerts[alert_key]
            aggregated.count += 1
            aggregated.last_occurrence = timestamp
            self.stats["deduplicated"] += 1
            logger.debug(f"告警去重: {alert_key} (计数: {aggregated.count})")
            return False, aggregated
        
        # 检查是否在聚合时间窗口内
        if alert_key in self.aggregated_alerts:
            aggregated = self.aggregated_alerts[alert_key]
            time_diff = (timestamp - aggregated.last_occurrence).total_seconds()
            
            if time_diff < self.aggregation_window:
                # 在聚合窗口内，更新现有告警
                aggregated.count += 1
                aggregated.last_occurrence = timestamp
                self.stats["aggregated"] += 1
                logger.debug(f"告警聚合: {alert_key} (计数: {aggregated.count})")
                return False, aggregated
        
        # 创建新的聚合告警
        aggregated = AggregatedAlert(
            alert_key=alert_key,
            alert_type=alert_type,
            severity=severity,
            message=message,
            account_id=account_id,
            count=1,
            first_occurrence=timestamp,
            last_occurrence=timestamp,
            status=AlertStatus.ACTIVE
        )
        
        self.aggregated_alerts[alert_key] = aggregated
        self.stats["total_alerts"] += 1
        
        logger.info(f"新告警: {alert_key} (严重程度: {severity.value})")
        return True, aggregated
    
    def suppress_alert(
        self,
        alert_key: str,
        duration_seconds: int = 3600,
        reason: Optional[str] = None
    ) -> bool:
        """
        静默告警（抑制一段时间）
        
        Args:
            alert_key: 告警键
            duration_seconds: 静默持续时间（秒）
            reason: 静默原因
        
        Returns:
            是否成功静默
        """
        suppress_until = datetime.now() + timedelta(seconds=duration_seconds)
        self.suppression_rules[alert_key] = suppress_until
        
        if alert_key in self.aggregated_alerts:
            aggregated = self.aggregated_alerts[alert_key]
            aggregated.suppressed_until = suppress_until
            aggregated.status = AlertStatus.SUPPRESSED
        
        logger.info(f"告警已静默: {alert_key} (直到: {suppress_until}, 原因: {reason})")
        return True
    
    def acknowledge_alert(
        self,
        alert_key: str,
        acknowledged_by: str,
        timestamp: Optional[datetime] = None
    ) -> bool:
        """
        确认告警
        
        Args:
            alert_key: 告警键
            acknowledged_by: 确认人
            timestamp: 确认时间
        
        Returns:
            是否成功确认
        """
        if timestamp is None:
            timestamp = datetime.now()
        
        self.acknowledgments[alert_key] = (acknowledged_by, timestamp)
        
        if alert_key in self.aggregated_alerts:
            aggregated = self.aggregated_alerts[alert_key]
            aggregated.acknowledged_by = acknowledged_by
            aggregated.acknowledged_at = timestamp
            aggregated.status = AlertStatus.ACKNOWLEDGED
        
        logger.info(f"告警已确认: {alert_key} (确认人: {acknowledged_by})")
        return True
    
    def resolve_alert(self, alert_key: str, timestamp: Optional[datetime] = None) -> bool:
        """
        解决告警
        
        Args:
            alert_key: 告警键
            timestamp: 解决时间
        
        Returns:
            是否成功解决
        """
        if timestamp is None:
            timestamp = datetime.now()
        
        if alert_key in self.aggregated_alerts:
            aggregated = self.aggregated_alerts[alert_key]
            aggregated.status = AlertStatus.RESOLVED
            aggregated.resolved_at = timestamp
            self.stats["resolved"] += 1
            logger.info(f"告警已解决: {alert_key}")
            return True
        
        return False
    
    def get_active_alerts(
        self,
        severity: Optional[AlertSeverity] = None,
        account_id: Optional[str] = None,
        limit: int = 100
    ) -> List[AggregatedAlert]:
        """
        获取活跃告警列表
        
        Args:
            severity: 过滤严重程度
            account_id: 过滤账号ID
            limit: 返回数量限制
        
        Returns:
            活跃告警列表
        """
        alerts = []
        
        for aggregated in self.aggregated_alerts.values():
            # 只返回活跃状态的告警
            if aggregated.status != AlertStatus.ACTIVE:
                continue
            
            # 检查静默状态
            if aggregated.suppressed_until and datetime.now() < aggregated.suppressed_until:
                continue
            
            # 过滤严重程度
            if severity and aggregated.severity != severity:
                continue
            
            # 过滤账号ID
            if account_id and aggregated.account_id != account_id:
                continue
            
            alerts.append(aggregated)
        
        # 按严重程度和最后发生时间排序
        alerts.sort(
            key=lambda x: (
                x.severity.value,  # 严重程度优先
                x.last_occurrence  # 然后按时间
            ),
            reverse=True
        )
        
        return alerts[:limit]
    
    def get_alert_statistics(self) -> Dict[str, any]:
        """
        获取告警统计信息
        
        Returns:
            统计信息字典
        """
        active_by_severity = defaultdict(int)
        total_by_severity = defaultdict(int)
        
        for aggregated in self.aggregated_alerts.values():
            severity = aggregated.severity.value
            total_by_severity[severity] += 1
            
            if aggregated.status == AlertStatus.ACTIVE:
                # 检查是否在静默期
                if not (aggregated.suppressed_until and datetime.now() < aggregated.suppressed_until):
                    active_by_severity[severity] += 1
        
        return {
            "total_alerts": self.stats["total_alerts"],
            "deduplicated": self.stats["deduplicated"],
            "aggregated": self.stats["aggregated"],
            "suppressed": self.stats["suppressed"],
            "resolved": self.stats["resolved"],
            "active_by_severity": dict(active_by_severity),
            "total_by_severity": dict(total_by_severity),
            "total_active": sum(active_by_severity.values()),
            "total_aggregated": len(self.aggregated_alerts),
        }
    
    def cleanup_old_alerts(self, max_age_hours: int = 24):
        """
        清理旧告警（已解决且超过指定时间的告警）
        
        Args:
            max_age_hours: 最大保留时间（小时）
        """
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        
        keys_to_remove = []
        for key, aggregated in self.aggregated_alerts.items():
            # 只清理已解决的告警
            if aggregated.status == AlertStatus.RESOLVED:
                if aggregated.resolved_at and aggregated.resolved_at < cutoff_time:
                    keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del self.aggregated_alerts[key]
            logger.debug(f"清理旧告警: {key}")
        
        # 清理过期的静默规则
        expired_suppressions = [
            k for k, v in self.suppression_rules.items()
            if v < datetime.now()
        ]
        for k in expired_suppressions:
            del self.suppression_rules[k]
        
        logger.info(f"清理了 {len(keys_to_remove)} 个旧告警")


# 全局告警聚合器实例
_alert_aggregator: Optional[AlertAggregator] = None


def get_alert_aggregator() -> AlertAggregator:
    """获取全局告警聚合器实例"""
    global _alert_aggregator
    if _alert_aggregator is None:
        _alert_aggregator = AlertAggregator()
    return _alert_aggregator

