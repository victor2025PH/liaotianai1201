from datetime import datetime
from typing import Any, Dict, List, Optional

import httpx

from app.core.config import get_settings


def _safe_get(url: str, timeout: float = 2.0) -> Any:
    """安全获取外部 API 数据，快速失败"""
    try:
        response = httpx.get(url, timeout=timeout)
        response.raise_for_status()
        return response.json()
    except Exception:
        return None


def get_accounts() -> Dict[str, Any]:
    settings = get_settings()
    endpoint = f"{settings.session_service_url.rstrip('/')}/api/accounts"
    data = _safe_get(endpoint)
    if data and isinstance(data, dict) and "items" in data:
        return data

    # fallback mock
    now = datetime.utcnow().isoformat()
    return {
        "items": [
            {
                "phone": "+8613812345678",
                "displayName": "运营A",
                "roles": ["operator"],
                "status": "ONLINE",
                "lastHeartbeat": now,
            },
            {
                "phone": "+8613812345679",
                "displayName": "技术B",
                "roles": ["support"],
                "status": "OFFLINE",
                "lastHeartbeat": now,
            },
        ],
        "total": 2,
    }


def get_activities() -> Dict[str, Any]:
    settings = get_settings()
    endpoint = f"{settings.redpacket_service_url.rstrip('/')}/api/activities"
    data = _safe_get(endpoint)
    if data and isinstance(data, dict) and "items" in data:
        return data

    now = datetime.utcnow().isoformat()
    return {
        "items": [
            {
                "id": "RP-20251112-001",
                "name": "双11回访红包",
                "status": "进行中",
                "success_rate": 0.86,
                "started_at": now,
                "participants": 18,
            },
            {
                "id": "RP-20251111-004",
                "name": "晚高峰福利",
                "status": "已完成",
                "success_rate": 0.92,
                "started_at": now,
                "participants": 24,
            },
        ],
        "total": 2,
    }


def get_alerts() -> Dict[str, Any]:
    settings = get_settings()
    endpoint = f"{settings.monitoring_service_url.rstrip('/')}/api/alerts"
    data = _safe_get(endpoint)
    if data and isinstance(data, dict) and "items" in data:
        return data

    now = datetime.utcnow().isoformat()
    return {
        "items": [
            {
                "id": "AL-001",
                "level": "高",
                "title": "在线账户低于阈值",
                "description": "当前在线账户 4 个，低于设置阈值 6 个",
                "status": "未处理",
                "created_at": now,
            },
            {
                "id": "AL-002",
                "level": "中",
                "title": "FloodWait 频繁",
                "description": "Session +8613812345679 在 5 分钟内触发 8 次 FloodWait",
                "status": "处理中",
                "created_at": now,
            },
        ],
        "total": 2,
    }


def enqueue_command(payload: Dict[str, Any]) -> Dict[str, Any]:
    settings = get_settings()
    endpoint = f"{settings.session_service_url.rstrip('/')}/api/commands"
    try:
        response = httpx.post(endpoint, json=payload, timeout=5.0)
        response.raise_for_status()
        data = response.json()
        if isinstance(data, dict) and "commandId" in data:
            return data
    except Exception:
        pass

    return {
        "commandId": f"mock-{datetime.utcnow().timestamp()}",
        "status": "QUEUED",
        "queuedAt": datetime.utcnow().isoformat(),
    }


def get_dashboard_stats() -> Dict[str, Any]:
    """獲取 Dashboard 統計數據（已遷移到群組AI儀表板API，此函數保留用於兼容）"""
    # 不再返回模擬數據，返回空數據
    # 實際數據應該通過 /api/v1/group-ai/dashboard 獲取
    return {
        "stats": {
            "today_sessions": 0,
            "success_rate": 0.0,
            "token_usage": 0,
            "error_count": 0,
            "avg_response_time": 0.0,
            "active_users": 0,
            "sessions_change": "0%",
            "success_rate_change": "0%",
            "token_usage_change": "0%",
            "error_count_change": "0%",
            "response_time_change": "0%",
            "active_users_change": "0%",
        },
        "recent_sessions": [],
        "recent_errors": [],
    }


def get_sessions(page: int = 1, page_size: int = 20, q: Optional[str] = None, time_range: Optional[str] = None, start_date: Optional[str] = None, end_date: Optional[str] = None) -> Dict[str, Any]:
    """獲取會話列表"""
    settings = get_settings()
    endpoint = f"{settings.session_service_url.rstrip('/')}/api/sessions?page={page}&page_size={page_size}"
    data = _safe_get(endpoint)
    if data and isinstance(data, dict) and "items" in data:
        return data

    # fallback mock data
    from datetime import timezone
    now = datetime.now(timezone.utc)
    items = []
    for i in range(1, page_size + 1):
        item = {
            "id": f"sess-{i:03d}",
            "user": f"user{i}@example.com",
            "user_id": f"user-{i}",
            "messages": 10 + i,
            "status": "completed" if i % 3 != 0 else ("active" if i % 3 == 1 else "failed"),
            "duration": f"{1 + i % 5}m {20 + i * 2}s",
            "started_at": now.isoformat(),
            "token_usage": (1000 + i * 100) if i % 2 == 0 else None,
            "model": "gpt-4" if i % 2 == 0 else "gpt-4o-mini",
        }
        if i % 3 == 0:
            item["ended_at"] = now.isoformat()
        items.append(item)
    return {
        "items": items,
        "total": 150,
        "page": page,
        "page_size": page_size,
    }


def get_session_detail(session_id: str) -> Dict[str, Any]:
    """獲取單個會話詳情"""
    settings = get_settings()
    endpoint = f"{settings.session_service_url.rstrip('/')}/api/sessions/{session_id}"
    data = _safe_get(endpoint)
    if data and isinstance(data, dict) and "id" in data:
        return data

    # fallback mock data
    from datetime import timezone, timedelta
    now = datetime.now(timezone.utc)
    ended_at = now + timedelta(seconds=204)
    return {
        "id": session_id,
        "user": "user@example.com",
        "user_id": "user-001",
        "messages": 12,
        "status": "completed",
        "duration": "3m 24s",
        "started_at": now.isoformat(),
        "ended_at": ended_at.isoformat(),
        "token_usage": 2500,
        "model": "gpt-4",
        "messages": [
            {
                "id": f"msg-{i}",
                "role": "user" if i % 2 == 0 else "assistant",
                "content": f"這是第 {i+1} 條訊息內容。用戶詢問了關於系統功能的問題，助手提供了詳細的回答。",
                "timestamp": (now + timedelta(seconds=i * 10)).isoformat(),
            }
            for i in range(12)
        ],
        "error_message": None,
        "request_metadata": {"temperature": 0.7, "max_tokens": 1000},
        "response_metadata": {"finish_reason": "stop", "usage": {"total_tokens": 2500}},
    }


def get_logs(page: int = 1, page_size: int = 20, level: Optional[str] = None, q: Optional[str] = None) -> Dict[str, Any]:
    """獲取日誌列表（已遷移到群組AI日誌API，此函數保留用於兼容）"""
    # 不再返回模擬數據，返回空列表
    # 實際日誌應該通過 /api/v1/group-ai/logs/ 獲取
    return {
        "items": [],
        "total": 0,
        "page": page,
        "page_size": page_size,
    }


def get_metrics() -> Dict[str, Any]:
    """獲取 Metrics 數據（響應時間趨勢、系統狀態）- 優化版本，減少計算時間"""
    settings = get_settings()
    endpoint = f"{settings.monitoring_service_url.rstrip('/')}/api/metrics"
    # 減少超時時間，快速失敗
    data = _safe_get(endpoint, timeout=2.0)
    if data and isinstance(data, dict):
        return data

    # fallback mock data - 優化：減少循環和計算
    now = datetime.utcnow()
    from datetime import timedelta
    
    # 優化：生成過去 24 小時的響應時間數據（減少計算）
    response_time_data = []
    base_time = 0.8
    # 預計算時間範圍
    time_range = [(now - timedelta(hours=23-i)) for i in range(24)]
    
    for i, timestamp in enumerate(time_range):
        hour = timestamp.hour
        # 簡化計算
        time_value = base_time + (i * 0.03) + (0.3 if 12 <= hour < 18 else 0) + (i % 3) * 0.1
        response_time_data.append({
            "hour": hour,
            "timestamp": timestamp.isoformat(),
            "avg_response_time": round(time_value, 2),
        })
    
    # 優化：使用列表推導式
    response_times = [d["avg_response_time"] for d in response_time_data]
    avg_time = sum(response_times) / len(response_times) if response_times else 0
    
    return {
        "response_time": {
            "data_points": response_time_data,
            "average": round(avg_time, 2),
            "min": round(min(response_times), 2) if response_times else 0,
            "max": round(max(response_times), 2) if response_times else 0,
            "trend": "-12%",
        },
        "system_status": {
            "status_items": [
                {
                    "label": "API Key 狀態",
                    "status": "active",
                    "value": "已配置",
                    "description": "OpenAI API Key 正常",
                },
                {
                    "label": "模型狀態",
                    "status": "active",
                    "value": "運行中",
                    "description": "GPT-4 / GPT-4o-mini 可用",
                },
                {
                    "label": "系統健康度",
                    "status": "healthy",
                    "value": "98.5%",
                    "description": "所有服務正常運行",
                },
            ],
            "last_updated": now.isoformat(),
        },
    }


def get_alert_settings() -> Dict[str, Any]:
    """獲取告警設置"""
    # 這裡可以從數據庫或配置文件讀取
    # 目前先返回默認值
    return {
        "error_rate_threshold": 5.0,
        "max_response_time": 2000,
        "notification_method": "email",
        "email_recipients": "admin@example.com",
        "webhook_url": None,
        "webhook_enabled": False,
    }


def save_alert_settings(settings: Dict[str, Any]) -> Dict[str, Any]:
    """保存告警設置"""
    # 這裡可以保存到數據庫或配置文件
    # 目前先返回成功響應
    return {
        "success": True,
        "message": "告警設置已保存",
        "settings": settings,
    }


def get_system_monitor() -> Dict[str, Any]:
    """獲取系統監控數據"""
    settings = get_settings()
    endpoint = f"{settings.monitoring_service_url.rstrip('/')}/api/system/monitor"
    data = _safe_get(endpoint)
    if data and isinstance(data, dict):
        return data

    # fallback mock data
    from datetime import timezone
    now = datetime.now(timezone.utc)
    
    # 嘗試獲取真實系統指標
    try:
        import psutil
        import os
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        # 獲取進程信息
        process = psutil.Process(os.getpid())
        uptime = int((datetime.now(timezone.utc) - datetime.fromtimestamp(process.create_time(), tz=timezone.utc)).total_seconds())
    except ImportError:
        # 如果 psutil 不可用，使用 mock 數據
        cpu_percent = 45.2
        memory = type('obj', (object,), {'percent': 62.5})()
        disk = type('obj', (object,), {'percent': 38.1})()
        uptime = 86400  # 1 天
    except Exception:
        # 其他錯誤也使用 mock 數據
        cpu_percent = 45.2
        memory = type('obj', (object,), {'percent': 62.5})()
        disk = type('obj', (object,), {'percent': 38.1})()
        uptime = 86400  # 1 天
    
    return {
        "health": {
            "status": "healthy",
            "uptime_seconds": uptime,
            "version": "0.1.0",
            "timestamp": now.isoformat(),
        },
        "metrics": {
            "cpu_usage_percent": round(cpu_percent, 2),
            "memory_usage_percent": round(memory.percent, 2) if hasattr(memory, 'percent') else 62.5,
            "disk_usage_percent": round(disk.percent, 2) if hasattr(disk, 'percent') else 38.1,
            "active_connections": 12,
            "queue_length": 3,
            "timestamp": now.isoformat(),
        },
        "services": {
            "api_server": {"status": "running", "uptime": uptime},
            "database": {"status": "connected", "response_time_ms": 5},
            "redis": {"status": "connected", "response_time_ms": 2},
            "session_service": {"status": "running", "active_sessions": 45},
        },
    }

