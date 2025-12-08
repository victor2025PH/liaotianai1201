"""
監控服務 API
"""
import logging
import sys
import asyncio
import json
from pathlib import Path
from typing import List, Optional, Set
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from sqlalchemy.orm import Session

# 導入緩存功能
from app.core.cache import cached

# 添加項目根目錄到路徑
project_root = Path(__file__).parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from group_ai_service import AccountManager
from group_ai_service.monitor_service import MonitorService, AccountMetrics, SystemMetrics, Alert
from app.db import get_db

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Group AI Monitor"])

# 全局實例（應該通過依賴注入管理）
account_manager = AccountManager()
monitor_service = MonitorService()

# WebSocket 連接管理
class ConnectionManager:
    """WebSocket 連接管理器"""
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self.metrics_task: Optional[asyncio.Task] = None
    
    async def connect(self, websocket: WebSocket):
        """接受 WebSocket 連接"""
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info(f"WebSocket 連接已建立，當前連接數: {len(self.active_connections)}")
        
        # 如果這是第一個連接，啟動指標推送任務
        if len(self.active_connections) == 1:
            self.start_metrics_broadcast()
    
    def disconnect(self, websocket: WebSocket):
        """斷開 WebSocket 連接"""
        self.active_connections.discard(websocket)
        logger.info(f"WebSocket 連接已斷開，當前連接數: {len(self.active_connections)}")
        
        # 如果沒有連接了，停止指標推送任務
        if len(self.active_connections) == 0 and self.metrics_task:
            self.metrics_task.cancel()
            self.metrics_task = None
    
    def start_metrics_broadcast(self):
        """啟動指標廣播任務"""
        if self.metrics_task and not self.metrics_task.done():
            return
        
        async def broadcast_metrics():
            """定期廣播指標"""
            while True:
                try:
                    if not self.active_connections:
                        await asyncio.sleep(1)
                        continue
                    
                    # 獲取系統指標
                    system_metrics = monitor_service.get_system_metrics()
                    
                    # 獲取賬號指標
                    account_metrics_list = []
                    for account_id, metrics in monitor_service.account_metrics.items():
                        account_metrics_list.append({
                            "account_id": metrics.account_id,
                            "message_count": metrics.message_count,
                            "reply_count": metrics.reply_count,
                            "redpacket_count": metrics.redpacket_count,
                            "error_count": metrics.error_count,
                            "last_activity": metrics.last_activity.isoformat() if metrics.last_activity else None
                        })
                    
                    # 構建推送消息
                    message = {
                        "type": "metrics_update",
                        "timestamp": datetime.now().isoformat(),
                        "system_metrics": {
                            "total_accounts": system_metrics.total_accounts,
                            "online_accounts": system_metrics.online_accounts,
                            "total_messages": system_metrics.total_messages,
                            "total_replies": system_metrics.total_replies,
                            "total_redpackets": system_metrics.total_redpackets,
                            "total_errors": system_metrics.total_errors,
                            "average_reply_time": system_metrics.average_reply_time
                        },
                        "account_metrics": account_metrics_list
                    }
                    
                    # 發送給所有連接的客戶端
                    disconnected = []
                    for connection in self.active_connections:
                        try:
                            await connection.send_json(message)
                        except Exception as e:
                            logger.warning(f"發送指標到客戶端失敗: {e}")
                            disconnected.append(connection)
                    
                    # 清理斷開的連接
                    for conn in disconnected:
                        self.disconnect(conn)
                    
                    # 每 5 秒推送一次
                    await asyncio.sleep(5)
                
                except asyncio.CancelledError:
                    logger.info("指標廣播任務已取消")
                    break
                except Exception as e:
                    logger.error(f"指標廣播任務出錯: {e}", exc_info=True)
                    await asyncio.sleep(5)
        
        self.metrics_task = asyncio.create_task(broadcast_metrics())
        logger.info("指標廣播任務已啟動")
    
    async def broadcast_alert(self, alert: dict):
        """廣播告警消息"""
        if not self.active_connections:
            return
        
        message = {
            "type": "alert",
            "timestamp": datetime.now().isoformat(),
            "alert": alert
        }
        
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.warning(f"發送告警到客戶端失敗: {e}")
                disconnected.append(connection)
        
        # 清理斷開的連接
        for conn in disconnected:
            self.disconnect(conn)


# 全局連接管理器
connection_manager = ConnectionManager()


class AccountMetricsResponse(BaseModel):
    """賬號指標響應"""
    account_id: str
    message_count: int
    reply_count: int
    redpacket_count: int
    error_count: int
    last_activity: Optional[str] = None
    
    class Config:
        from_attributes = True


class SystemMetricsResponse(BaseModel):
    """系統指標響應"""
    total_accounts: int
    online_accounts: int
    total_messages: int
    total_replies: int
    total_redpackets: int
    total_errors: int
    average_reply_time: float
    timestamp: str


class AlertResponse(BaseModel):
    """告警響應"""
    alert_id: str
    alert_type: str
    account_id: Optional[str] = None
    message: str
    timestamp: str
    resolved: bool = False


@router.get("/accounts/metrics", response_model=List[AccountMetricsResponse])
@cached(prefix="accounts_metrics", ttl=30)  # 緩存 30 秒（賬號指標更新頻率中等）
async def get_accounts_metrics(
    account_id: Optional[str] = Query(None, description="賬號 ID（可選）"),
    db: Session = Depends(get_db)
):
    """獲取賬號指標"""
    try:
        if account_id:
            if account_id in monitor_service.account_metrics:
                metrics = monitor_service.account_metrics[account_id]
                return [AccountMetricsResponse(
                    account_id=metrics.account_id,
                    message_count=metrics.message_count,
                    reply_count=metrics.reply_count,
                    redpacket_count=metrics.redpacket_count,
                    error_count=metrics.error_count,
                    last_activity=metrics.last_activity.isoformat() if metrics.last_activity else None
                )]
            else:
                return []
        else:
            metrics_list = []
            for acc_id, metrics in monitor_service.account_metrics.items():
                metrics_list.append(AccountMetricsResponse(
                    account_id=metrics.account_id,
                    message_count=metrics.message_count,
                    reply_count=metrics.reply_count,
                    redpacket_count=metrics.redpacket_count,
                    error_count=metrics.error_count,
                    last_activity=metrics.last_activity.isoformat() if metrics.last_activity else None
                ))
            return metrics_list
    
    except Exception as e:
        logger.error(f"獲取賬號指標失敗: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"獲取賬號指標失敗: {str(e)}"
        )


@router.get("/system", response_model=SystemMetricsResponse)
async def get_system_metrics(
    db: Session = Depends(get_db)
):
    """獲取系統指標（實時數據，不緩存）"""
    try:
        metrics = monitor_service.get_system_metrics()
        
        return SystemMetricsResponse(
            total_accounts=metrics.total_accounts,
            online_accounts=metrics.online_accounts,
            total_messages=metrics.total_messages,
            total_replies=metrics.total_replies,
            total_redpackets=metrics.total_redpackets,
            total_errors=metrics.total_errors,
            average_reply_time=metrics.average_reply_time,
            timestamp=metrics.timestamp.isoformat()
        )
    
    except Exception as e:
        logger.error(f"獲取系統指標失敗: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"獲取系統指標失敗: {str(e)}"
        )


class MetricsHistoryResponse(BaseModel):
    """指標歷史數據響應"""
    metric_type: str  # messages, replies, errors, redpackets
    data_points: List[dict]  # [{timestamp, value}, ...]
    period: str  # 1h, 24h, 7d, 30d


@router.get("/system/history", response_model=MetricsHistoryResponse)
async def get_system_metrics_history(
    metric_type: str = Query("messages", description="指標類型（messages, replies, errors, redpackets）"),
    period: str = Query("24h", description="時間範圍（1h, 24h, 7d, 30d）"),
    db: Session = Depends(get_db)
):
    """獲取系統指標歷史數據"""
    try:
        # 計算時間範圍
        from datetime import timedelta
        now = datetime.now()
        
        if period == "1h":
            start_time = now - timedelta(hours=1)
            interval_minutes = 5
        elif period == "24h":
            start_time = now - timedelta(hours=24)
            interval_minutes = 30
        elif period == "7d":
            start_time = now - timedelta(days=7)
            interval_minutes = 240  # 4小時
        elif period == "30d":
            start_time = now - timedelta(days=30)
            interval_minutes = 1440  # 1天
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"不支持的時間範圍: {period}"
            )
        
        # 從事件日誌中提取歷史數據
        data_points = []
        events = list(monitor_service.event_log)
        
        # 過濾時間範圍內的事件
        filtered_events = [
            e for e in events
            if "timestamp" in e and e["timestamp"] >= start_time
        ]
        
        # 按時間間隔聚合數據
        current_time = start_time
        while current_time <= now:
            next_time = current_time + timedelta(minutes=interval_minutes)
            
            # 統計該時間段內的事件
            period_events = [
                e for e in filtered_events
                if current_time <= e.get("timestamp", datetime.min) < next_time
            ]
            
            value = 0
            if metric_type == "messages":
                value = len([e for e in period_events if e.get("type") == "message"])
            elif metric_type == "replies":
                value = len([e for e in period_events if e.get("type") == "reply"])
            elif metric_type == "errors":
                value = len([e for e in period_events if e.get("type") == "error"])
            elif metric_type == "redpackets":
                value = len([e for e in period_events if e.get("type") == "redpacket"])
            
            data_points.append({
                "timestamp": current_time.isoformat(),
                "value": value
            })
            
            current_time = next_time
        
        return MetricsHistoryResponse(
            metric_type=metric_type,
            data_points=data_points,
            period=period
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"獲取系統指標歷史數據失敗: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"獲取系統指標歷史數據失敗: {str(e)}"
        )


class AccountMetricsHistoryResponse(BaseModel):
    """賬號指標歷史數據響應"""
    account_id: str
    metric_type: str
    data_points: List[dict]
    period: str


@router.get("/accounts/{account_id}/history", response_model=AccountMetricsHistoryResponse)
async def get_account_metrics_history(
    account_id: str,
    metric_type: str = Query("messages", description="指標類型（messages, replies, errors, redpackets）"),
    period: str = Query("24h", description="時間範圍（1h, 24h, 7d, 30d）"),
    db: Session = Depends(get_db)
):
    """獲取賬號指標歷史數據"""
    try:
        # 計算時間範圍
        from datetime import timedelta
        now = datetime.now()
        
        if period == "1h":
            start_time = now - timedelta(hours=1)
            interval_minutes = 5
        elif period == "24h":
            start_time = now - timedelta(hours=24)
            interval_minutes = 30
        elif period == "7d":
            start_time = now - timedelta(days=7)
            interval_minutes = 240
        elif period == "30d":
            start_time = now - timedelta(days=30)
            interval_minutes = 1440
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"不支持的時間範圍: {period}"
            )
        
        # 從事件日誌中提取該賬號的歷史數據
        data_points = []
        events = list(monitor_service.event_log)
        
        # 過濾該賬號和時間範圍內的事件
        filtered_events = [
            e for e in events
            if e.get("account_id") == account_id
            and "timestamp" in e
            and e["timestamp"] >= start_time
        ]
        
        # 按時間間隔聚合數據
        current_time = start_time
        while current_time <= now:
            next_time = current_time + timedelta(minutes=interval_minutes)
            
            period_events = [
                e for e in filtered_events
                if current_time <= e.get("timestamp", datetime.min) < next_time
            ]
            
            value = 0
            if metric_type == "messages":
                value = len([e for e in period_events if e.get("type") == "message"])
            elif metric_type == "replies":
                value = len([e for e in period_events if e.get("type") == "reply"])
            elif metric_type == "errors":
                value = len([e for e in period_events if e.get("type") == "error"])
            elif metric_type == "redpackets":
                value = len([e for e in period_events if e.get("type") == "redpacket"])
            
            data_points.append({
                "timestamp": current_time.isoformat(),
                "value": value
            })
            
            current_time = next_time
        
        return AccountMetricsHistoryResponse(
            account_id=account_id,
            metric_type=metric_type,
            data_points=data_points,
            period=period
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"獲取賬號指標歷史數據失敗: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"獲取賬號指標歷史數據失敗: {str(e)}"
        )


class MetricsStatisticsResponse(BaseModel):
    """指標統計響應"""
    total_messages: int
    total_replies: int
    total_errors: int
    total_redpackets: int
    reply_rate: float
    error_rate: float
    average_reply_time: float
    period: str
    start_time: str
    end_time: str


@router.get("/system/statistics", response_model=MetricsStatisticsResponse)
async def get_system_statistics(
    period: str = Query("24h", description="時間範圍（1h, 24h, 7d, 30d）"),
    db: Session = Depends(get_db)
):
    """獲取系統指標統計"""
    try:
        from datetime import timedelta
        now = datetime.now()
        
        if period == "1h":
            start_time = now - timedelta(hours=1)
        elif period == "24h":
            start_time = now - timedelta(hours=24)
        elif period == "7d":
            start_time = now - timedelta(days=7)
        elif period == "30d":
            start_time = now - timedelta(days=30)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"不支持的時間範圍: {period}"
            )
        
        # 從事件日誌中統計
        events = list(monitor_service.event_log)
        filtered_events = [
            e for e in events
            if "timestamp" in e and e["timestamp"] >= start_time
        ]
        
        total_messages = len([e for e in filtered_events if e.get("type") == "message"])
        total_replies = len([e for e in filtered_events if e.get("type") == "reply"])
        total_errors = len([e for e in filtered_events if e.get("type") == "error"])
        total_redpackets = len([e for e in filtered_events if e.get("type") == "redpacket"])
        
        reply_rate = (total_replies / total_messages * 100) if total_messages > 0 else 0.0
        error_rate = (total_errors / total_messages * 100) if total_messages > 0 else 0.0
        
        # 計算平均回復時間（從事件中提取）
        reply_times = [
            e.get("reply_time", 0) for e in filtered_events
            if e.get("type") == "reply" and "reply_time" in e
        ]
        average_reply_time = sum(reply_times) / len(reply_times) if reply_times else 0.0
        
        return MetricsStatisticsResponse(
            total_messages=total_messages,
            total_replies=total_replies,
            total_errors=total_errors,
            total_redpackets=total_redpackets,
            reply_rate=reply_rate,
            error_rate=error_rate,
            average_reply_time=average_reply_time,
            period=period,
            start_time=start_time.isoformat(),
            end_time=now.isoformat()
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"獲取系統指標統計失敗: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"獲取系統指標統計失敗: {str(e)}"
        )


@router.get("/alerts", response_model=List[AlertResponse])
async def get_alerts(
    limit: int = Query(50, ge=1, le=500, description="返回數量"),
    alert_type: Optional[str] = Query(None, description="告警類型（error, warning, info）"),
    resolved: Optional[bool] = Query(None, description="是否已解決"),
    check_rules: bool = Query(False, description="是否執行告警規則檢查"),
    use_aggregation: bool = Query(True, description="是否使用告警聚合"),
    severity: Optional[str] = Query(None, description="告警嚴重程度（critical, high, medium, low）"),
    db: Session = Depends(get_db)
):
    """獲取告警列表（支持聚合和去重）"""
    try:
        # 如果請求執行告警規則檢查，先檢查規則
        if check_rules:
            try:
                from app.crud import alert_rule as crud_alert_rule
                # 從數據庫讀取啟用的告警規則
                enabled_rules = crud_alert_rule.get_enabled_alert_rules(db)
                if enabled_rules:
                    # 使用規則進行告警檢查
                    new_alerts = monitor_service.check_alerts(alert_rules=enabled_rules)
                    if new_alerts:
                        logger.info(f"告警規則檢查觸發了 {len(new_alerts)} 個新告警")
                        
                        # 如果啟用聚合，將新告警添加到聚合器
                        if use_aggregation:
                            from app.services.alert_aggregator import get_alert_aggregator, AlertSeverity
                            aggregator = get_alert_aggregator()
                            
                            for alert in new_alerts:
                                # 確定嚴重程度
                                alert_severity = None
                                if severity:
                                    try:
                                        alert_severity = AlertSeverity(severity)
                                    except ValueError:
                                        pass
                                
                                aggregator.add_alert(
                                    alert_type=alert.alert_type,
                                    message=alert.message,
                                    account_id=alert.account_id,
                                    timestamp=alert.timestamp,
                                    severity=alert_severity
                                )
                else:
                    # 沒有啟用的規則，使用默認規則（向後兼容）
                    monitor_service.check_alerts()
            except Exception as e:
                logger.warning(f"執行告警規則檢查失敗，使用默認規則: {e}")
                monitor_service.check_alerts()
        
        # 如果使用聚合，從聚合器獲取告警
        if use_aggregation:
            from app.services.alert_aggregator import get_alert_aggregator, AlertSeverity
            aggregator = get_alert_aggregator()
            
            # 清理舊告警
            aggregator.cleanup_old_alerts()
            
            # 獲取活躍告警
            alert_severity = None
            if severity:
                try:
                    alert_severity = AlertSeverity(severity)
                except ValueError:
                    pass
            
            aggregated_alerts = aggregator.get_active_alerts(
                severity=alert_severity,
                limit=limit
            )
            
            # 轉換為 AlertResponse
            result = []
            for agg in aggregated_alerts:
                # 過濾告警類型
                if alert_type and agg.alert_type != alert_type:
                    continue
                
                # 過濾已解決/未解決
                if resolved is not None:
                    is_resolved = agg.status.value == "resolved"
                    if resolved != is_resolved:
                        continue
                
                result.append(AlertResponse(
                    alert_id=agg.alert_key,
                    alert_type=agg.alert_type,
                    account_id=agg.account_id,
                    message=f"{agg.message} (出现 {agg.count} 次)" if agg.count > 1 else agg.message,
                    timestamp=agg.last_occurrence.isoformat(),
                    resolved=agg.status.value == "resolved"
                ))
            
            return result[:limit]
        
        # 不使用聚合，返回原始告警列表
        alerts = monitor_service.get_recent_alerts(limit=limit, alert_type=alert_type)
        
        # 過濾已解決/未解決
        if resolved is not None:
            alerts = [a for a in alerts if a.resolved == resolved]
        
        return [
            AlertResponse(
                alert_id=alert.alert_id,
                alert_type=alert.alert_type,
                account_id=alert.account_id,
                message=alert.message,
                timestamp=alert.timestamp.isoformat(),
                resolved=alert.resolved
            )
            for alert in alerts
        ]
    
    except Exception as e:
        logger.error(f"獲取告警列表失敗: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"獲取告警列表失敗: {str(e)}"
        )


@router.post("/alerts/check", status_code=status.HTTP_200_OK)
async def check_alerts(
    db: Session = Depends(get_db)
):
    """執行告警規則檢查"""
    try:
        from app.crud import alert_rule as crud_alert_rule
        # 從數據庫讀取啟用的告警規則
        enabled_rules = crud_alert_rule.get_enabled_alert_rules(db)
        
        if enabled_rules:
            # 使用規則進行告警檢查
            new_alerts = monitor_service.check_alerts(alert_rules=enabled_rules)
            
            # 發送通知（如果有新告警）
            if new_alerts:
                try:
                    from app.services.notification_service import NotificationService
                    from app.services.telegram_alert_service import get_telegram_alert_service
                    from app.monitoring.prometheus_metrics import alerts_total, alerts_active
                    
                    notification_service = NotificationService(db)
                    telegram_service = get_telegram_alert_service()
                    
                    # 轉換告警格式
                    alert_dicts = []
                    for alert in new_alerts:
                        # 確定告警級別
                        alert_level = "error" if alert.alert_type == "error" else "warning" if alert.alert_type == "warning" else "info"
                        
                        alert_dict = {
                            "alert_type": alert.alert_type,
                            "alert_level": alert_level,
                            "message": alert.message,
                            "account_id": alert.account_id,
                            "timestamp": alert.timestamp,
                        }
                        alert_dicts.append(alert_dict)
                        
                        # 更新 Prometheus 指標
                        try:
                            alerts_total.labels(level=alert_level, type=alert.alert_type).inc()
                            alerts_active.labels(level=alert_level, type=alert.alert_type).inc()
                        except Exception as e:
                            logger.debug(f"更新 Prometheus 指標失敗: {e}")
                        
                        # 發送標準通知（郵件、Webhook等）
                        await notification_service.send_alert_notification(
                            alert_level=alert_level,
                            alert_title=f"告警: {alert.alert_type}",
                            alert_message=alert.message,
                            resource_type="account" if alert.account_id else "system",
                            resource_id=alert.account_id,
                        )
                    
                    # 發送 Telegram 告警（批量發送，避免消息過多）
                    if telegram_service.enabled:
                        await telegram_service.send_batch_alerts(alert_dicts)
                except Exception as e:
                    logger.warning(f"發送告警通知失敗: {e}", exc_info=True)
            
            return {
                "message": "告警規則檢查完成",
                "rules_checked": len(enabled_rules),
                "new_alerts": len(new_alerts),
                "alerts": [
                    {
                        "alert_id": alert.alert_id,
                        "alert_type": alert.alert_type,
                        "account_id": alert.account_id,
                        "message": alert.message,
                        "timestamp": alert.timestamp.isoformat()
                    }
                    for alert in new_alerts
                ]
            }
        else:
            # 沒有啟用的規則，使用默認規則（向後兼容）
            new_alerts = monitor_service.check_alerts()
            return {
                "message": "告警檢查完成（使用默認規則）",
                "rules_checked": 0,
                "new_alerts": len(new_alerts),
                "alerts": [
                    {
                        "alert_id": alert.alert_id,
                        "alert_type": alert.alert_type,
                        "account_id": alert.account_id,
                        "message": alert.message,
                        "timestamp": alert.timestamp.isoformat()
                    }
                    for alert in new_alerts
                ]
            }
    
    except Exception as e:
        logger.error(f"執行告警規則檢查失敗: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"執行告警規則檢查失敗: {str(e)}"
        )


@router.post("/alerts/{alert_id}/resolve", status_code=status.HTTP_200_OK)
async def resolve_alert(
    alert_id: str,
    db: Session = Depends(get_db)
):
    """解決告警"""
    try:
        success = monitor_service.resolve_alert(alert_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"告警 {alert_id} 不存在"
            )
        
        return {"message": "告警已解決", "alert_id": alert_id}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"解決告警失敗: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"解決告警失敗: {str(e)}"
        )


@router.get("/events", response_model=List[dict])
async def get_events(
    account_id: Optional[str] = Query(None, description="賬號 ID（可選）"),
    event_type: Optional[str] = Query(None, description="事件類型（message, reply, redpacket）"),
    limit: int = Query(100, ge=1, le=1000, description="返回數量"),
    db: Session = Depends(get_db)
):
    """獲取事件日誌"""
    try:
        events = list(monitor_service.event_log)
        
        # 過濾
        if account_id:
            events = [e for e in events if e.get("account_id") == account_id]
        if event_type:
            events = [e for e in events if e.get("type") == event_type]
        
        # 限制數量
        events = events[-limit:] if len(events) > limit else events
        
        # 格式化時間戳
        for event in events:
            if "timestamp" in event and hasattr(event["timestamp"], "isoformat"):
                event["timestamp"] = event["timestamp"].isoformat()
        
        return events
    
    except Exception as e:
        logger.error(f"獲取事件日誌失敗: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"獲取事件日誌失敗: {str(e)}"
        )


@router.get("/scheduled-checker/status", status_code=status.HTTP_200_OK)
async def get_scheduled_checker_status():
    """獲取定時告警檢查服務狀態"""
    try:
        from app.services.scheduled_alert_checker import get_scheduled_checker
        checker = get_scheduled_checker()
        
        return {
            "enabled": checker.is_running,
            "interval_seconds": checker.interval_seconds,
            "status": "running" if checker.is_running else "stopped"
        }
    except Exception as e:
        logger.error(f"獲取定時告警檢查服務狀態失敗: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"獲取定時告警檢查服務狀態失敗: {str(e)}"
        )


@router.post("/scheduled-checker/start", status_code=status.HTTP_200_OK)
async def start_scheduled_checker():
    """啟動定時告警檢查服務"""
    try:
        from app.services.scheduled_alert_checker import get_scheduled_checker
        checker = get_scheduled_checker()
        
        if checker.is_running:
            return {
                "message": "定時告警檢查服務已經在運行中",
                "status": "running"
            }
        
        checker.start()
        return {
            "message": "定時告警檢查服務已啟動",
            "status": "running",
            "interval_seconds": checker.interval_seconds
        }
    except Exception as e:
        logger.error(f"啟動定時告警檢查服務失敗: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"啟動定時告警檢查服務失敗: {str(e)}"
        )


@router.post("/scheduled-checker/stop", status_code=status.HTTP_200_OK)
async def stop_scheduled_checker():
    """停止定時告警檢查服務"""
    try:
        from app.services.scheduled_alert_checker import get_scheduled_checker
        checker = get_scheduled_checker()
        
        if not checker.is_running:
            return {
                "message": "定時告警檢查服務未運行",
                "status": "stopped"
            }
        
        checker.stop()
        return {
            "message": "定時告警檢查服務已停止",
            "status": "stopped"
        }
    except Exception as e:
        logger.error(f"停止定時告警檢查服務失敗: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"停止定時告警檢查服務失敗: {str(e)}"
        )


@router.websocket("/ws/metrics")
async def websocket_metrics(websocket: WebSocket):
    """
    WebSocket 實時指標推送
    
    客戶端連接後，每 5 秒自動推送系統指標和賬號指標更新
    支持推送告警消息
    """
    await connection_manager.connect(websocket)
    try:
        # 發送初始指標
        system_metrics = monitor_service.get_system_metrics()
        account_metrics_list = []
        for account_id, metrics in monitor_service.account_metrics.items():
            account_metrics_list.append({
                "account_id": metrics.account_id,
                "message_count": metrics.message_count,
                "reply_count": metrics.reply_count,
                "redpacket_count": metrics.redpacket_count,
                "error_count": metrics.error_count,
                "last_activity": metrics.last_activity.isoformat() if metrics.last_activity else None
            })
        
        initial_message = {
            "type": "metrics_update",
            "timestamp": datetime.now().isoformat(),
            "system_metrics": {
                "total_accounts": system_metrics.total_accounts,
                "online_accounts": system_metrics.online_accounts,
                "total_messages": system_metrics.total_messages,
                "total_replies": system_metrics.total_replies,
                "total_redpackets": system_metrics.total_redpackets,
                "total_errors": system_metrics.total_errors,
                "average_reply_time": system_metrics.average_reply_time
            },
            "account_metrics": account_metrics_list
        }
        await websocket.send_json(initial_message)
        
        # 保持連接，等待客戶端斷開
        while True:
            try:
                # 接收客戶端消息（用於心跳檢測）
                data = await websocket.receive_text()
                # 可以處理客戶端發送的消息（如訂閱特定賬號的指標）
                try:
                    message = json.loads(data)
                    if message.get("type") == "ping":
                        await websocket.send_json({"type": "pong", "timestamp": datetime.now().isoformat()})
                except json.JSONDecodeError:
                    pass
            except WebSocketDisconnect:
                break
    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.error(f"WebSocket 連接錯誤: {e}", exc_info=True)
    finally:
        connection_manager.disconnect(websocket)


@router.websocket("/ws/alerts")
async def websocket_alerts(websocket: WebSocket):
    """
    WebSocket 實時告警推送
    
    客戶端連接後，實時推送新觸發的告警
    """
    await connection_manager.connect(websocket)
    try:
        # 發送最近的告警
        recent_alerts = monitor_service.get_recent_alerts(limit=10)
        for alert in recent_alerts:
            alert_message = {
                "type": "alert",
                "timestamp": alert.timestamp.isoformat(),
                "alert": {
                    "alert_id": alert.alert_id,
                    "alert_type": alert.alert_type,
                    "account_id": alert.account_id,
                    "message": alert.message,
                    "resolved": alert.resolved
                }
            }
            await websocket.send_json(alert_message)
        
        # 保持連接，等待客戶端斷開
        while True:
            try:
                data = await websocket.receive_text()
                try:
                    message = json.loads(data)
                    if message.get("type") == "ping":
                        await websocket.send_json({"type": "pong", "timestamp": datetime.now().isoformat()})
                except json.JSONDecodeError:
                    pass
            except WebSocketDisconnect:
                break
    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.error(f"WebSocket 告警連接錯誤: {e}", exc_info=True)
    finally:
        connection_manager.disconnect(websocket)
