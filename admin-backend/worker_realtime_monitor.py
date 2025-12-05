"""
🖥️ 實時監控面板模組
支持：
- WebSocket 實時推送
- 群組狀態監控
- AI 帳號狀態監控
- 活動日誌流
- 告警通知
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any, Set, Callable
from dataclasses import dataclass, field, asdict
from enum import Enum
from collections import deque
import weakref

logger = logging.getLogger(__name__)


# ==================== 事件類型 ====================

class EventType(Enum):
    """事件類型"""
    # 群組事件
    GROUP_CREATED = "group_created"
    GROUP_STATUS_CHANGED = "group_status_changed"
    GROUP_MESSAGE = "group_message"
    
    # 用戶事件
    USER_JOINED = "user_joined"
    USER_LEFT = "user_left"
    USER_MESSAGE = "user_message"
    
    # AI 事件
    AI_ONLINE = "ai_online"
    AI_OFFLINE = "ai_offline"
    AI_ASSIGNED = "ai_assigned"
    AI_MESSAGE_SENT = "ai_message_sent"
    
    # 紅包事件
    REDPACKET_SENT = "redpacket_sent"
    REDPACKET_CLAIMED = "redpacket_claimed"
    
    # 系統事件
    SYSTEM_STATUS = "system_status"
    ALERT = "alert"
    ERROR = "error"


class AlertLevel(Enum):
    """告警級別"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


# ==================== 數據結構 ====================

@dataclass
class MonitorEvent:
    """監控事件"""
    event_type: EventType
    timestamp: datetime = field(default_factory=datetime.now)
    data: Dict[str, Any] = field(default_factory=dict)
    group_id: Optional[int] = None
    user_id: Optional[int] = None
    
    def to_dict(self) -> dict:
        return {
            "event_type": self.event_type.value,
            "timestamp": self.timestamp.isoformat(),
            "data": self.data,
            "group_id": self.group_id,
            "user_id": self.user_id
        }
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False)


@dataclass
class Alert:
    """告警"""
    level: AlertLevel
    title: str
    message: str
    timestamp: datetime = field(default_factory=datetime.now)
    group_id: Optional[int] = None
    resolved: bool = False
    
    def to_dict(self) -> dict:
        return {
            "level": self.level.value,
            "title": self.title,
            "message": self.message,
            "timestamp": self.timestamp.isoformat(),
            "group_id": self.group_id,
            "resolved": self.resolved
        }


@dataclass
class GroupMetrics:
    """群組指標"""
    group_id: int
    group_name: str
    status: str
    
    # 實時指標
    ai_count: int = 0
    user_count: int = 0
    online_users: int = 0
    
    # 活動指標（最近 1 小時）
    messages_1h: int = 0
    user_joins_1h: int = 0
    redpackets_1h: int = 0
    
    # 轉化指標
    engagement_rate: float = 0.0
    game_participation_rate: float = 0.0
    
    last_update: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> dict:
        return {
            "group_id": self.group_id,
            "group_name": self.group_name,
            "status": self.status,
            "ai_count": self.ai_count,
            "user_count": self.user_count,
            "online_users": self.online_users,
            "messages_1h": self.messages_1h,
            "user_joins_1h": self.user_joins_1h,
            "redpackets_1h": self.redpackets_1h,
            "engagement_rate": round(self.engagement_rate, 2),
            "game_participation_rate": round(self.game_participation_rate, 2),
            "last_update": self.last_update.isoformat()
        }


@dataclass
class SystemMetrics:
    """系統指標"""
    # 群組統計
    total_groups: int = 0
    active_groups: int = 0
    full_groups: int = 0
    
    # AI 統計
    total_ais: int = 0
    online_ais: int = 0
    busy_ais: int = 0
    
    # 用戶統計
    total_users: int = 0
    active_users_1h: int = 0
    new_users_24h: int = 0
    
    # 消息統計
    messages_1h: int = 0
    messages_24h: int = 0
    
    # 紅包統計
    redpackets_sent_24h: int = 0
    redpackets_claimed_24h: int = 0
    total_amount_24h: float = 0.0
    
    # 系統狀態
    uptime_seconds: int = 0
    error_count_1h: int = 0
    
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> dict:
        return {
            "groups": {
                "total": self.total_groups,
                "active": self.active_groups,
                "full": self.full_groups
            },
            "ais": {
                "total": self.total_ais,
                "online": self.online_ais,
                "busy": self.busy_ais
            },
            "users": {
                "total": self.total_users,
                "active_1h": self.active_users_1h,
                "new_24h": self.new_users_24h
            },
            "messages": {
                "count_1h": self.messages_1h,
                "count_24h": self.messages_24h
            },
            "redpackets": {
                "sent_24h": self.redpackets_sent_24h,
                "claimed_24h": self.redpackets_claimed_24h,
                "amount_24h": round(self.total_amount_24h, 2)
            },
            "system": {
                "uptime_seconds": self.uptime_seconds,
                "error_count_1h": self.error_count_1h
            },
            "timestamp": self.timestamp.isoformat()
        }


# ==================== WebSocket 連接管理 ====================

class WebSocketConnection:
    """WebSocket 連接"""
    
    def __init__(self, connection_id: str, send_func: Callable):
        self.connection_id = connection_id
        self.send_func = send_func
        self.subscriptions: Set[str] = set()  # 訂閱的事件類型
        self.connected_at = datetime.now()
        self.last_activity = datetime.now()
    
    async def send(self, data: dict):
        """發送數據"""
        try:
            await self.send_func(json.dumps(data, ensure_ascii=False))
            self.last_activity = datetime.now()
        except Exception as e:
            logger.error(f"WebSocket 發送失敗: {e}")
    
    def subscribe(self, event_types: List[str]):
        """訂閱事件"""
        self.subscriptions.update(event_types)
    
    def unsubscribe(self, event_types: List[str]):
        """取消訂閱"""
        self.subscriptions -= set(event_types)


class ConnectionManager:
    """WebSocket 連接管理器"""
    
    def __init__(self):
        self.connections: Dict[str, WebSocketConnection] = {}
        self._lock = asyncio.Lock()
    
    async def add_connection(
        self,
        connection_id: str,
        send_func: Callable
    ) -> WebSocketConnection:
        """添加連接"""
        async with self._lock:
            conn = WebSocketConnection(connection_id, send_func)
            self.connections[connection_id] = conn
            logger.info(f"WebSocket 連接: {connection_id}")
            return conn
    
    async def remove_connection(self, connection_id: str):
        """移除連接"""
        async with self._lock:
            if connection_id in self.connections:
                del self.connections[connection_id]
                logger.info(f"WebSocket 斷開: {connection_id}")
    
    async def broadcast(self, data: dict, event_type: str = None):
        """廣播消息"""
        for conn in list(self.connections.values()):
            # 如果有訂閱過濾，只發送給訂閱了該事件的連接
            if event_type and conn.subscriptions and event_type not in conn.subscriptions:
                continue
            
            try:
                await conn.send(data)
            except Exception as e:
                logger.error(f"廣播失敗 {conn.connection_id}: {e}")
    
    def get_connection_count(self) -> int:
        return len(self.connections)


# ==================== 實時監控器 ====================

class RealtimeMonitor:
    """實時監控器"""
    
    def __init__(self):
        self.connection_manager = ConnectionManager()
        
        # 事件歷史（最近 1000 條）
        self.event_history: deque = deque(maxlen=1000)
        
        # 告警列表
        self.alerts: List[Alert] = []
        
        # 群組指標
        self.group_metrics: Dict[int, GroupMetrics] = {}
        
        # 系統指標
        self.system_metrics = SystemMetrics()
        self._start_time = datetime.now()
        
        # 統計計數器
        self._message_counts: deque = deque(maxlen=3600)  # 每秒計數，保留 1 小時
        self._user_joins: deque = deque(maxlen=86400)  # 每秒計數，保留 24 小時
        
        # 後台任務
        self._tasks: List[asyncio.Task] = []
    
    async def start(self):
        """啟動監控器"""
        # 啟動定期更新任務
        self._tasks.append(asyncio.create_task(self._periodic_update()))
        self._tasks.append(asyncio.create_task(self._cleanup_old_data()))
        logger.info("實時監控器已啟動")
    
    async def stop(self):
        """停止監控器"""
        for task in self._tasks:
            task.cancel()
        self._tasks.clear()
        logger.info("實時監控器已停止")
    
    async def _periodic_update(self):
        """定期更新並推送系統狀態"""
        while True:
            try:
                # 更新系統指標
                self._update_system_metrics()
                
                # 推送系統狀態
                await self.broadcast_event(MonitorEvent(
                    event_type=EventType.SYSTEM_STATUS,
                    data=self.system_metrics.to_dict()
                ))
                
                await asyncio.sleep(5)  # 每 5 秒更新一次
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"定期更新失敗: {e}")
                await asyncio.sleep(5)
    
    async def _cleanup_old_data(self):
        """清理舊數據"""
        while True:
            try:
                # 清理已解決的告警（超過 24 小時）
                cutoff = datetime.now() - timedelta(hours=24)
                self.alerts = [a for a in self.alerts 
                              if not a.resolved or a.timestamp > cutoff]
                
                await asyncio.sleep(3600)  # 每小時清理一次
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"清理失敗: {e}")
                await asyncio.sleep(3600)
    
    def _update_system_metrics(self):
        """更新系統指標"""
        self.system_metrics.uptime_seconds = int(
            (datetime.now() - self._start_time).total_seconds()
        )
        self.system_metrics.timestamp = datetime.now()
    
    # ==================== 事件處理 ====================
    
    async def record_event(self, event: MonitorEvent):
        """記錄事件"""
        self.event_history.append(event)
        
        # 更新統計
        self._update_statistics(event)
        
        # 廣播事件
        await self.broadcast_event(event)
    
    async def broadcast_event(self, event: MonitorEvent):
        """廣播事件"""
        await self.connection_manager.broadcast(
            event.to_dict(),
            event.event_type.value
        )
    
    def _update_statistics(self, event: MonitorEvent):
        """更新統計數據"""
        now = datetime.now()
        
        if event.event_type == EventType.GROUP_MESSAGE:
            self._message_counts.append((now, 1))
            self.system_metrics.messages_1h = self._count_recent(
                self._message_counts, hours=1
            )
            
            if event.group_id and event.group_id in self.group_metrics:
                self.group_metrics[event.group_id].messages_1h += 1
        
        elif event.event_type == EventType.USER_JOINED:
            self._user_joins.append((now, 1))
            self.system_metrics.new_users_24h = self._count_recent(
                self._user_joins, hours=24
            )
            self.system_metrics.total_users += 1
            
            if event.group_id and event.group_id in self.group_metrics:
                self.group_metrics[event.group_id].user_joins_1h += 1
                self.group_metrics[event.group_id].user_count += 1
        
        elif event.event_type == EventType.REDPACKET_CLAIMED:
            amount = event.data.get("amount", 0)
            self.system_metrics.redpackets_claimed_24h += 1
            self.system_metrics.total_amount_24h += amount
    
    def _count_recent(self, data: deque, hours: int) -> int:
        """計算最近 N 小時的數量"""
        cutoff = datetime.now() - timedelta(hours=hours)
        return sum(count for ts, count in data if ts > cutoff)
    
    # ==================== 群組監控 ====================
    
    def register_group(
        self,
        group_id: int,
        group_name: str,
        status: str,
        ai_count: int = 0
    ):
        """註冊群組監控"""
        self.group_metrics[group_id] = GroupMetrics(
            group_id=group_id,
            group_name=group_name,
            status=status,
            ai_count=ai_count
        )
        self.system_metrics.total_groups += 1
        
        if status == "active":
            self.system_metrics.active_groups += 1
    
    def update_group_status(self, group_id: int, status: str):
        """更新群組狀態"""
        if group_id in self.group_metrics:
            old_status = self.group_metrics[group_id].status
            self.group_metrics[group_id].status = status
            self.group_metrics[group_id].last_update = datetime.now()
            
            # 更新計數
            if old_status == "active" and status != "active":
                self.system_metrics.active_groups -= 1
            elif old_status != "active" and status == "active":
                self.system_metrics.active_groups += 1
    
    def get_group_metrics(self, group_id: int) -> Optional[dict]:
        """獲取群組指標"""
        metrics = self.group_metrics.get(group_id)
        return metrics.to_dict() if metrics else None
    
    def get_all_group_metrics(self) -> List[dict]:
        """獲取所有群組指標"""
        return [m.to_dict() for m in self.group_metrics.values()]
    
    # ==================== AI 監控 ====================
    
    def record_ai_status(self, user_id: int, is_online: bool):
        """記錄 AI 狀態"""
        if is_online:
            self.system_metrics.online_ais += 1
        else:
            self.system_metrics.online_ais = max(0, self.system_metrics.online_ais - 1)
    
    # ==================== 告警 ====================
    
    async def create_alert(
        self,
        level: AlertLevel,
        title: str,
        message: str,
        group_id: int = None
    ):
        """創建告警"""
        alert = Alert(
            level=level,
            title=title,
            message=message,
            group_id=group_id
        )
        self.alerts.append(alert)
        
        if level in [AlertLevel.ERROR, AlertLevel.CRITICAL]:
            self.system_metrics.error_count_1h += 1
        
        # 廣播告警
        await self.record_event(MonitorEvent(
            event_type=EventType.ALERT,
            data=alert.to_dict(),
            group_id=group_id
        ))
        
        logger.warning(f"告警 [{level.value}] {title}: {message}")
    
    def resolve_alert(self, alert_index: int):
        """解決告警"""
        if 0 <= alert_index < len(self.alerts):
            self.alerts[alert_index].resolved = True
    
    def get_active_alerts(self) -> List[dict]:
        """獲取活躍告警"""
        return [a.to_dict() for a in self.alerts if not a.resolved]
    
    # ==================== API 接口 ====================
    
    def get_dashboard_data(self) -> dict:
        """獲取儀表板數據"""
        return {
            "system": self.system_metrics.to_dict(),
            "groups": self.get_all_group_metrics(),
            "alerts": self.get_active_alerts(),
            "recent_events": [e.to_dict() for e in list(self.event_history)[-50:]],
            "connections": self.connection_manager.get_connection_count()
        }
    
    def get_event_history(
        self,
        event_type: str = None,
        group_id: int = None,
        limit: int = 100
    ) -> List[dict]:
        """獲取事件歷史"""
        events = list(self.event_history)
        
        if event_type:
            events = [e for e in events if e.event_type.value == event_type]
        
        if group_id:
            events = [e for e in events if e.group_id == group_id]
        
        return [e.to_dict() for e in events[-limit:]]


# ==================== FastAPI 路由（示例） ====================

def create_monitor_routes(monitor: RealtimeMonitor):
    """創建監控 API 路由（FastAPI）"""
    from fastapi import APIRouter, WebSocket, WebSocketDisconnect
    import uuid
    
    router = APIRouter(prefix="/api/v1/monitor", tags=["monitor"])
    
    @router.get("/dashboard")
    async def get_dashboard():
        """獲取儀表板數據"""
        return monitor.get_dashboard_data()
    
    @router.get("/groups")
    async def get_groups():
        """獲取所有群組指標"""
        return monitor.get_all_group_metrics()
    
    @router.get("/groups/{group_id}")
    async def get_group(group_id: int):
        """獲取單個群組指標"""
        metrics = monitor.get_group_metrics(group_id)
        if not metrics:
            return {"error": "Group not found"}
        return metrics
    
    @router.get("/alerts")
    async def get_alerts():
        """獲取活躍告警"""
        return monitor.get_active_alerts()
    
    @router.get("/events")
    async def get_events(
        event_type: str = None,
        group_id: int = None,
        limit: int = 100
    ):
        """獲取事件歷史"""
        return monitor.get_event_history(event_type, group_id, limit)
    
    @router.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket):
        """WebSocket 實時推送"""
        await websocket.accept()
        connection_id = str(uuid.uuid4())
        
        conn = await monitor.connection_manager.add_connection(
            connection_id,
            websocket.send_text
        )
        
        try:
            # 發送初始數據
            await conn.send(monitor.get_dashboard_data())
            
            # 保持連接並處理消息
            while True:
                data = await websocket.receive_text()
                
                # 處理訂閱請求
                try:
                    msg = json.loads(data)
                    if msg.get("action") == "subscribe":
                        conn.subscribe(msg.get("events", []))
                    elif msg.get("action") == "unsubscribe":
                        conn.unsubscribe(msg.get("events", []))
                except json.JSONDecodeError:
                    pass
                    
        except WebSocketDisconnect:
            await monitor.connection_manager.remove_connection(connection_id)
    
    return router


# 導出
__all__ = [
    "EventType",
    "AlertLevel",
    "MonitorEvent",
    "Alert",
    "GroupMetrics",
    "SystemMetrics",
    "WebSocketConnection",
    "ConnectionManager",
    "RealtimeMonitor",
    "create_monitor_routes"
]
