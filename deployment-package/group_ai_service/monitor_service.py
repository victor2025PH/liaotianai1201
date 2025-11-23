"""
監控服務 - 收集和統計系統運行指標
"""
import logging
import asyncio
import concurrent.futures
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict, deque
from dataclasses import dataclass, field

from group_ai_service.models.account import AccountStatusEnum

logger = logging.getLogger(__name__)


@dataclass
class AccountMetrics:
    """賬號指標"""
    account_id: str
    message_count: int = 0
    reply_count: int = 0
    redpacket_count: int = 0
    success_count: int = 0
    error_count: int = 0
    total_reply_time: float = 0.0  # 總回復時間（秒）
    last_activity: Optional[datetime] = None
    uptime_seconds: int = 0


@dataclass
class SystemMetrics:
    """系統指標"""
    total_accounts: int = 0
    online_accounts: int = 0
    total_messages: int = 0
    total_replies: int = 0
    total_redpackets: int = 0
    total_errors: int = 0
    average_reply_time: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class Alert:
    """告警"""
    alert_id: str
    alert_type: str  # error, warning, info
    account_id: Optional[str] = None
    message: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    resolved: bool = False


class MonitorService:
    """監控服務"""
    
    def __init__(self):
        self.account_metrics: Dict[str, AccountMetrics] = {}
        self.system_metrics_history: deque = deque(maxlen=1000)  # 最近 1000 條系統指標
        self.alerts: List[Alert] = []
        self.event_log: deque = deque(maxlen=10000)  # 最近 10000 條事件
        
        # 事件日誌清理配置
        self.event_log_retention_hours = 24  # 保留 24 小時的事件
        self.last_cleanup_time = datetime.now()
        self.cleanup_interval_seconds = 3600  # 每小時清理一次
        
        logger.info("MonitorService 初始化完成")
    
    def record_message(
        self,
        account_id: str,
        message_type: str = "received",
        success: bool = True
    ):
        """記錄消息事件"""
        if account_id not in self.account_metrics:
            self.account_metrics[account_id] = AccountMetrics(account_id=account_id)
        
        metrics = self.account_metrics[account_id]
        metrics.message_count += 1
        metrics.last_activity = datetime.now()
        
        if not success:
            metrics.error_count += 1
        
        self.event_log.append({
            "type": "message",
            "account_id": account_id,
            "message_type": message_type,
            "success": success,
            "timestamp": datetime.now()
        })
        
        # 定期清理舊事件（非阻塞）
        self._maybe_cleanup_old_events()
    
    def record_reply(
        self,
        account_id: str,
        reply_time: float = 0.0,
        success: bool = True
    ):
        """記錄回復事件"""
        if account_id not in self.account_metrics:
            self.account_metrics[account_id] = AccountMetrics(account_id=account_id)
        
        metrics = self.account_metrics[account_id]
        metrics.reply_count += 1
        metrics.total_reply_time += reply_time
        
        if success:
            metrics.success_count += 1
        else:
            metrics.error_count += 1
        
        self.event_log.append({
            "type": "reply",
            "account_id": account_id,
            "reply_time": reply_time,
            "success": success,
            "timestamp": datetime.now()
        })
        
        # 定期清理舊事件（非阻塞）
        self._maybe_cleanup_old_events()
    
    def record_redpacket(
        self,
        account_id: str,
        success: bool = True,
        amount: Optional[float] = None
    ):
        """記錄紅包事件"""
        if account_id not in self.account_metrics:
            self.account_metrics[account_id] = AccountMetrics(account_id=account_id)
        
        metrics = self.account_metrics[account_id]
        metrics.redpacket_count += 1
        
        if success:
            metrics.success_count += 1
        else:
            metrics.error_count += 1
        
        self.event_log.append({
            "type": "redpacket",
            "account_id": account_id,
            "success": success,
            "amount": amount,
            "timestamp": datetime.now()
        })
        
        # 定期清理舊事件（非阻塞）
        self._maybe_cleanup_old_events()
    
    def get_account_metrics(
        self,
        account_id: str,
        time_range: Optional[timedelta] = None
    ) -> Optional[AccountMetrics]:
        """獲取賬號指標"""
        if account_id not in self.account_metrics:
            return None
        
        metrics = self.account_metrics[account_id]
        
        # 如果指定了時間範圍，過濾事件並重新計算指標
        if time_range:
            cutoff = datetime.now() - time_range
            
            # 從事件日誌中過濾該賬號在時間範圍內的事件
            filtered_events = [
                event for event in self.event_log
                if (event.get("account_id") == account_id and
                    event.get("timestamp") and
                    isinstance(event.get("timestamp"), datetime) and
                    event.get("timestamp") >= cutoff)
            ]
            
            # 重新計算指標
            filtered_metrics = AccountMetrics(account_id=account_id)
            filtered_metrics.last_activity = metrics.last_activity
            filtered_metrics.uptime_seconds = metrics.uptime_seconds
            
            for event in filtered_events:
                event_type = event.get("type")
                timestamp = event.get("timestamp")
                
                if event_type == "message":
                    filtered_metrics.message_count += 1
                    if not event.get("success", True):
                        filtered_metrics.error_count += 1
                    if timestamp and (not filtered_metrics.last_activity or timestamp > filtered_metrics.last_activity):
                        filtered_metrics.last_activity = timestamp
                
                elif event_type == "reply":
                    filtered_metrics.reply_count += 1
                    filtered_metrics.total_reply_time += event.get("reply_time", 0.0)
                    if event.get("success", True):
                        filtered_metrics.success_count += 1
                    else:
                        filtered_metrics.error_count += 1
                    if timestamp and (not filtered_metrics.last_activity or timestamp > filtered_metrics.last_activity):
                        filtered_metrics.last_activity = timestamp
                
                elif event_type == "redpacket":
                    filtered_metrics.redpacket_count += 1
                    if event.get("success", True):
                        filtered_metrics.success_count += 1
                    else:
                        filtered_metrics.error_count += 1
                    if timestamp and (not filtered_metrics.last_activity or timestamp > filtered_metrics.last_activity):
                        filtered_metrics.last_activity = timestamp
            
            return filtered_metrics
        
        return metrics
    
    def get_system_metrics(
        self,
        time_range: Optional[timedelta] = None
    ) -> SystemMetrics:
        """獲取系統指標"""
        # 從賬號指標聚合
        total_accounts = len(self.account_metrics)
        online_accounts = sum(
            1 for m in self.account_metrics.values()
            if m.last_activity and (datetime.now() - m.last_activity).total_seconds() < 300
        )
        
        total_messages = sum(m.message_count for m in self.account_metrics.values())
        total_replies = sum(m.reply_count for m in self.account_metrics.values())
        total_redpackets = sum(m.redpacket_count for m in self.account_metrics.values())
        total_errors = sum(m.error_count for m in self.account_metrics.values())
        
        total_reply_time = sum(m.total_reply_time for m in self.account_metrics.values())
        average_reply_time = (
            total_reply_time / total_replies
            if total_replies > 0 else 0.0
        )
        
        metrics = SystemMetrics(
            total_accounts=total_accounts,
            online_accounts=online_accounts,
            total_messages=total_messages,
            total_replies=total_replies,
            total_redpackets=total_redpackets,
            total_errors=total_errors,
            average_reply_time=average_reply_time,
            timestamp=datetime.now()
        )
        
        # 記錄到歷史
        self.system_metrics_history.append(metrics)
        
        return metrics
    
    def check_alerts(self, alert_rules: Optional[List[Any]] = None) -> List[Alert]:
        """
        檢查告警
        
        Args:
            alert_rules: 告警規則列表（從數據庫讀取）。如果為 None，使用默認硬編碼規則（向後兼容）
        
        Returns:
            新觸發的告警列表
        """
        alerts = []
        system_metrics = self.get_system_metrics()
        
        # 如果提供了規則，使用規則進行檢查
        if alert_rules:
            for rule in alert_rules:
                # 跳過未啟用的規則
                if not rule.enabled:
                    continue
                
                # 根據規則類型進行檢查
                alert = self._evaluate_rule(rule, system_metrics)
                if alert:
                    alerts.append(alert)
                    self.alerts.append(alert)
        else:
            # 向後兼容：使用默認硬編碼規則
            alerts.extend(self._check_default_rules(system_metrics))
        
        return alerts
    
    def _evaluate_rule(self, rule: Any, system_metrics: SystemMetrics) -> Optional[Alert]:
        """
        評估單個告警規則
        
        Args:
            rule: 告警規則對象（從數據庫讀取）
            system_metrics: 系統指標
        
        Returns:
            如果觸發告警，返回 Alert 對象；否則返回 None
        """
        rule_type = rule.rule_type
        threshold_value = rule.threshold_value
        threshold_operator = rule.threshold_operator
        alert_level = rule.alert_level
        
        # 根據規則類型計算實際值
        actual_value = None
        account_id = None
        
        if rule_type == "error_rate":
            # 錯誤率告警：檢查所有賬號
            for acc_id, metrics in self.account_metrics.items():
                total_events = metrics.message_count + metrics.reply_count + metrics.redpacket_count
                if total_events > 0:
                    error_rate = metrics.error_count / total_events
                    if self._compare_values(error_rate, threshold_value, threshold_operator):
                        account_id = acc_id
                        actual_value = error_rate
                        break
        
        elif rule_type == "system_errors":
            # 系統錯誤數告警
            actual_value = system_metrics.total_errors
            if not self._compare_values(actual_value, threshold_value, threshold_operator):
                return None
        
        elif rule_type == "response_time":
            # 響應時間告警
            actual_value = system_metrics.average_reply_time * 1000  # 轉換為毫秒
            if not self._compare_values(actual_value, threshold_value, threshold_operator):
                return None
        
        elif rule_type == "account_offline":
            # 賬號離線告警
            online_rate = system_metrics.online_accounts / system_metrics.total_accounts if system_metrics.total_accounts > 0 else 0.0
            actual_value = (1.0 - online_rate) * 100  # 離線率百分比
            if not self._compare_values(actual_value, threshold_value, threshold_operator):
                return None
        
        else:
            # 未知規則類型，跳過
            logger.warning(f"未知的告警規則類型: {rule_type}")
            return None
        
        # 如果規則被觸發，創建告警
        if actual_value is not None:
            alert_id = f"{rule_type}_{rule.id}_{datetime.now().timestamp()}"
            message = self._generate_alert_message(rule, actual_value, account_id)
            
            alert = Alert(
                alert_id=alert_id,
                alert_type=alert_level,
                account_id=account_id,
                message=message
            )
            
            # 發送通知（異步，不阻塞）
            self._send_alert_notification(alert, rule)
            
            return alert
        
        return None
    
    def _send_alert_notification(self, alert: Alert, rule: Any = None):
        """
        發送告警通知（異步，不阻塞）
        
        Args:
            alert: 告警對象
            rule: 告警規則對象（可選，用於自定義規則的通知方式）
        """
        try:
            # 優先使用本地通知服務
            try:
                from group_ai_service.notification_service import get_notification_service
                notification_service = get_notification_service()
                
                # 構建告警信息字典
                alert_dict = {
                    "alert_type": alert.alert_type,
                    "alert_level": alert.alert_type,  # 使用 alert_type 作為 level
                    "message": alert.message,
                    "account_id": alert.account_id,
                    "timestamp": alert.timestamp
                }
                
                # 如果規則存在，使用規則的通知方式
                notification_method = None
                notification_target = None
                if rule and hasattr(rule, 'notification_method'):
                    notification_method = rule.notification_method
                if rule and hasattr(rule, 'notification_target'):
                    notification_target = rule.notification_target
                
                # 異步發送通知（不阻塞主流程）
                def send_notification():
                    """在線程池中執行異步通知發送"""
                    try:
                        asyncio.run(
                            notification_service.send_alert_notification(
                                alert_dict,
                                notification_method=notification_method,
                                notification_target=notification_target
                            )
                        )
                    except Exception as e:
                        logger.error(f"線程池中發送通知失敗: {e}", exc_info=True)
                
                # 使用線程池執行，不阻塞主流程
                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                    executor.submit(send_notification)
                
            except ImportError:
                # 降級：嘗試使用 admin-backend 的通知服務（如果可用）
                try:
                    import sys
                    from pathlib import Path
                    
                    admin_backend_path = Path(__file__).parent.parent / "admin-backend"
                    if str(admin_backend_path) not in sys.path:
                        sys.path.insert(0, str(admin_backend_path))
                    
                    from app.services.notification import get_notification_service
                    notification_service = get_notification_service()
                    
                    alert_dict = {
                        "name": getattr(rule, 'name', '告警') if rule else '告警',
                        "alert_level": alert.alert_type,
                        "alert_type": alert.alert_type,
                        "message": alert.message,
                        "account_id": alert.account_id,
                        "timestamp": alert.timestamp
                    }
                    
                    def send_notification():
                        try:
                            asyncio.run(
                                notification_service.send_alert_notification(
                                    alert_dict,
                                    notification_method=getattr(rule, 'notification_method', None) if rule else None,
                                    notification_target=getattr(rule, 'notification_target', None) if rule else None
                                )
                            )
                        except Exception as e:
                            logger.error(f"線程池中發送通知失敗: {e}", exc_info=True)
                    
                    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                        executor.submit(send_notification)
                except ImportError:
                    logger.warning("通知服務模組不可用，跳過發送通知")
            except Exception as e:
                logger.warning(f"發送告警通知失敗: {e}", exc_info=True)
        
        except Exception as e:
            logger.warning(f"發送告警通知失敗: {e}", exc_info=True)
    
    def _compare_values(self, actual: float, threshold: float, operator: str) -> bool:
        """比較實際值和閾值"""
        if operator == ">":
            return actual > threshold
        elif operator == ">=":
            return actual >= threshold
        elif operator == "<":
            return actual < threshold
        elif operator == "<=":
            return actual <= threshold
        elif operator == "==":
            return actual == threshold
        elif operator == "!=":
            return actual != threshold
        else:
            logger.warning(f"未知的比較運算符: {operator}，使用 >")
            return actual > threshold
    
    def _generate_alert_message(self, rule: Any, actual_value: float, account_id: Optional[str] = None) -> str:
        """生成告警消息"""
        if account_id:
            return f"賬號 {account_id}: {rule.name} - 當前值 {actual_value:.2f} {rule.threshold_operator} 閾值 {rule.threshold_value}"
        else:
            return f"{rule.name} - 當前值 {actual_value:.2f} {rule.threshold_operator} 閾值 {rule.threshold_value}"
    
    def _check_default_rules(self, system_metrics: SystemMetrics) -> List[Alert]:
        """檢查默認硬編碼規則（向後兼容，使用配置文件中的閾值）"""
        alerts = []
        
        # 從配置文件讀取閾值
        try:
            from group_ai_service.config import get_group_ai_config
            config = get_group_ai_config()
            error_rate_threshold = config.alert_error_rate_threshold
            warning_rate_threshold = config.alert_warning_rate_threshold
            system_errors_threshold = config.alert_system_errors_threshold
            account_offline_threshold = config.alert_account_offline_threshold
            account_inactive_seconds = config.alert_account_inactive_seconds
            response_time_threshold = config.alert_response_time_threshold
            redpacket_failure_rate_threshold = config.alert_redpacket_failure_rate_threshold
            message_processing_error_threshold = config.alert_message_processing_error_threshold
        except Exception as e:
            logger.warning(f"讀取告警配置失敗，使用默認值: {e}")
            # 使用默認值
            error_rate_threshold = 0.5
            warning_rate_threshold = 0.2
            system_errors_threshold = 100
            account_offline_threshold = 0.3
            account_inactive_seconds = 300
            response_time_threshold = 5000.0
            redpacket_failure_rate_threshold = 0.3
            message_processing_error_threshold = 10
        
        # 1. 檢查賬號錯誤率
        for account_id, metrics in self.account_metrics.items():
            total_events = metrics.message_count + metrics.reply_count + metrics.redpacket_count
            if total_events > 0:
                error_rate = metrics.error_count / total_events
                
                if error_rate > error_rate_threshold:
                    alert = Alert(
                        alert_id=f"error_rate_{account_id}_{datetime.now().timestamp()}",
                        alert_type="error",
                        account_id=account_id,
                        message=f"賬號 {account_id} 錯誤率過高: {error_rate:.2%} (閾值: {error_rate_threshold:.2%})"
                    )
                    alerts.append(alert)
                    self.alerts.append(alert)
                    self._send_alert_notification(alert)
                
                elif error_rate > warning_rate_threshold:
                    alert = Alert(
                        alert_id=f"warning_rate_{account_id}_{datetime.now().timestamp()}",
                        alert_type="warning",
                        account_id=account_id,
                        message=f"賬號 {account_id} 錯誤率較高: {error_rate:.2%} (閾值: {warning_rate_threshold:.2%})"
                    )
                    alerts.append(alert)
                    self.alerts.append(alert)
                    self._send_alert_notification(alert)
        
        # 2. 檢查賬號離線
        if system_metrics.total_accounts > 0:
            offline_rate = 1.0 - (system_metrics.online_accounts / system_metrics.total_accounts)
            if offline_rate > account_offline_threshold:
                offline_count = system_metrics.total_accounts - system_metrics.online_accounts
                alert = Alert(
                    alert_id=f"account_offline_{datetime.now().timestamp()}",
                    alert_type="warning",
                    message=f"賬號離線率過高: {offline_rate:.2%} ({offline_count}/{system_metrics.total_accounts} 個賬號離線，閾值: {account_offline_threshold:.2%})"
                )
                alerts.append(alert)
                self.alerts.append(alert)
                self._send_alert_notification(alert)
        
        # 3. 檢查系統級錯誤數
        if system_metrics.total_errors > system_errors_threshold:
            alert = Alert(
                alert_id=f"system_errors_{datetime.now().timestamp()}",
                alert_type="error",
                message=f"系統錯誤數過多: {system_metrics.total_errors} (閾值: {system_errors_threshold})"
            )
            alerts.append(alert)
            self.alerts.append(alert)
            self._send_alert_notification(alert)
        
        # 4. 檢查響應時間
        if system_metrics.average_reply_time > 0:
            response_time_ms = system_metrics.average_reply_time * 1000
            if response_time_ms > response_time_threshold:
                alert = Alert(
                    alert_id=f"response_time_{datetime.now().timestamp()}",
                    alert_type="warning",
                    message=f"平均響應時間過長: {response_time_ms:.2f}ms (閾值: {response_time_threshold:.2f}ms)"
                )
                alerts.append(alert)
                self.alerts.append(alert)
                self._send_alert_notification(alert)
        
        # 5. 檢查紅包參與失敗率
        for account_id, metrics in self.account_metrics.items():
            if metrics.redpacket_count > 0:
                # 從事件日誌中計算紅包失敗率
                redpacket_events = [
                    e for e in self.event_log
                    if e.get("account_id") == account_id and e.get("type") == "redpacket"
                ]
                if redpacket_events:
                    failed_count = sum(1 for e in redpacket_events if not e.get("success", True))
                    failure_rate = failed_count / len(redpacket_events)
                    
                    if failure_rate > redpacket_failure_rate_threshold:
                        alert = Alert(
                            alert_id=f"redpacket_failure_{account_id}_{datetime.now().timestamp()}",
                            alert_type="warning",
                            account_id=account_id,
                            message=f"賬號 {account_id} 紅包參與失敗率過高: {failure_rate:.2%} ({failed_count}/{len(redpacket_events)} 次失敗，閾值: {redpacket_failure_rate_threshold:.2%})"
                        )
                        alerts.append(alert)
                        self.alerts.append(alert)
                        self._send_alert_notification(alert)
        
        # 6. 檢查消息處理異常（每小時錯誤數）
        one_hour_ago = datetime.now() - timedelta(hours=1)
        for account_id, metrics in self.account_metrics.items():
            # 從事件日誌中統計最近1小時的消息處理錯誤
            recent_errors = [
                e for e in self.event_log
                if (e.get("account_id") == account_id and
                    e.get("type") == "message" and
                    not e.get("success", True) and
                    e.get("timestamp") and
                    isinstance(e.get("timestamp"), datetime) and
                    e.get("timestamp") >= one_hour_ago)
            ]
            
            if len(recent_errors) > message_processing_error_threshold:
                alert = Alert(
                    alert_id=f"message_processing_error_{account_id}_{datetime.now().timestamp()}",
                    alert_type="warning",
                    account_id=account_id,
                    message=f"賬號 {account_id} 消息處理異常: 最近1小時內 {len(recent_errors)} 次錯誤 (閾值: {message_processing_error_threshold})"
                )
                alerts.append(alert)
                self.alerts.append(alert)
                self._send_alert_notification(alert)
        
        return alerts
    
    def get_recent_alerts(
        self,
        limit: int = 50,
        alert_type: Optional[str] = None
    ) -> List[Alert]:
        """獲取最近的告警"""
        alerts = self.alerts
        
        if alert_type:
            alerts = [a for a in alerts if a.alert_type == alert_type]
        
        # 按時間排序，返回最近的
        alerts.sort(key=lambda x: x.timestamp, reverse=True)
        return alerts[:limit]
    
    def resolve_alert(self, alert_id: str) -> bool:
        """解決告警"""
        for alert in self.alerts:
            if alert.alert_id == alert_id:
                alert.resolved = True
                logger.info(f"告警已解決: {alert_id}")
                return True
        return False
    
    def get_event_log(
        self,
        account_id: Optional[str] = None,
        event_type: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """獲取事件日誌"""
        events = list(self.event_log)
        
        # 過濾
        if account_id:
            events = [e for e in events if e.get("account_id") == account_id]
        
        if event_type:
            events = [e for e in events if e.get("type") == event_type]
        
        # 按時間排序
        events.sort(key=lambda x: x.get("timestamp", datetime.min), reverse=True)
        
        return events[:limit]
    
    def _maybe_cleanup_old_events(self):
        """定期清理舊事件（非阻塞，避免頻繁清理）"""
        try:
            now = datetime.now()
            # 檢查是否需要清理（每小時清理一次）
            if (now - self.last_cleanup_time).total_seconds() < self.cleanup_interval_seconds:
                return
            
            self.last_cleanup_time = now
            cutoff = now - timedelta(hours=self.event_log_retention_hours)
            
            # 清理超過保留時間的事件
            # 注意：deque 不支持直接過濾，需要轉換為列表再轉回
            original_size = len(self.event_log)
            filtered_events = [
                event for event in self.event_log
                if (event.get("timestamp") and
                    isinstance(event.get("timestamp"), datetime) and
                    event.get("timestamp") >= cutoff)
            ]
            
            # 重建 deque（保留 maxlen）
            maxlen = self.event_log.maxlen
            self.event_log.clear()
            for event in filtered_events:
                self.event_log.append(event)
            
            cleaned_count = original_size - len(self.event_log)
            if cleaned_count > 0:
                logger.debug(f"清理了 {cleaned_count} 個舊事件（保留 {len(self.event_log)} 個）")
        
        except Exception as e:
            # 清理失敗不應該影響主流程
            logger.warning(f"清理舊事件失敗: {e}")
    
    def update_account_status(
        self,
        account_id: str,
        status: AccountStatusEnum,
        uptime_seconds: int = 0
    ):
        """更新賬號狀態"""
        if account_id not in self.account_metrics:
            self.account_metrics[account_id] = AccountMetrics(account_id=account_id)
        
        metrics = self.account_metrics[account_id]
        metrics.uptime_seconds = uptime_seconds
        
        if status == AccountStatusEnum.ERROR:
            metrics.error_count += 1
            # 創建告警
            alert = Alert(
                alert_id=f"account_error_{account_id}_{datetime.now().timestamp()}",
                alert_type="error",
                account_id=account_id,
                message=f"賬號 {account_id} 狀態異常"
            )
            self.alerts.append(alert)

