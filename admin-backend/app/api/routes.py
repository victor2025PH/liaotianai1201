from fastapi import APIRouter, Depends, Query, status
from typing import Optional

# 導入緩存功能
from app.core.cache import cached

from app.schemas import (
    Account,
    AccountList,
    Activity,
    ActivityList,
    Alert,
    AlertList,
    CommandCreate,
    CommandResult,
    DashboardData,
    SessionList,
    LogList,
    MetricsData,
    AlertSettings,
    SystemMonitorData,
)
from app.api.deps import get_current_active_user
from app.services import data_sources
from app.middleware.performance import get_performance_stats

router = APIRouter()

@router.get("/accounts", response_model=AccountList, tags=["accounts"], dependencies=[Depends(get_current_active_user)])
async def list_accounts() -> AccountList:
    data = data_sources.get_accounts()
    items = [Account(**item) for item in data.get("items", [])]
    return AccountList(items=items, total=data.get("total", len(items)))


@router.get("/activities", response_model=ActivityList, tags=["activities"], dependencies=[Depends(get_current_active_user)])
async def list_activities() -> ActivityList:
    data = data_sources.get_activities()
    items = [Activity(**item) for item in data.get("items", [])]
    return ActivityList(items=items, total=data.get("total", len(items)))


@router.post(
    "/commands",
    response_model=CommandResult,
    status_code=status.HTTP_202_ACCEPTED,
    tags=["commands"],
    dependencies=[Depends(get_current_active_user)],
)
async def create_command(payload: CommandCreate) -> CommandResult:
    result = data_sources.enqueue_command(payload.dict(exclude_none=True))
    return CommandResult(**result)


@router.get("/alerts", response_model=AlertList, tags=["alerts"], dependencies=[Depends(get_current_active_user)])
async def list_alerts() -> AlertList:
    data = data_sources.get_alerts()
    items = [Alert(**item) for item in data.get("items", [])]
    return AlertList(items=items, total=data.get("total", len(items)))


@router.get("/dashboard", response_model=DashboardData, tags=["dashboard"], dependencies=[Depends(get_current_active_user)])
async def get_dashboard() -> DashboardData:
    """獲取 Dashboard 統計數據（從群組AI系統，帶緩存）"""
    import logging
    logger = logging.getLogger(__name__)
    from app.schemas.dashboard import DashboardStats, RecentSession, RecentError, DashboardData
    
    try:
        # 優先使用群組AI儀表板API（真實數據）
        from app.api.group_ai.dashboard import get_dashboard_stats
        data = get_dashboard_stats()
        
        # 確保 data 是字典類型
        if not isinstance(data, dict):
            logger.error(f"get_dashboard_stats 返回的不是字典: {type(data)}")
            raise ValueError("Invalid data type from get_dashboard_stats")
        
        # 確保數據結構正確
        stats_data = data.get("stats", {})
        # 如果 stats_data 是字符串，嘗試解析
        if isinstance(stats_data, str):
            logger.warning(f"stats_data 是字符串，嘗試解析: {stats_data[:100]}")
            import json
            try:
                stats_data = json.loads(stats_data)
            except:
                stats_data = {}
        
        # 確保 stats_data 是字典
        if not isinstance(stats_data, dict):
            logger.error(f"stats_data 不是字典: {type(stats_data)}")
            stats_data = {}
        
        recent_sessions_data = data.get("recent_sessions", [])
        recent_errors_data = data.get("recent_errors", [])
        
        # 處理stats，確保所有字段都有默認值
        stats = DashboardStats(
            today_sessions=stats_data.get("today_sessions", 0),
            success_rate=stats_data.get("success_rate", 0.0),
            token_usage=stats_data.get("token_usage", 0),
            error_count=stats_data.get("error_count", 0),
            avg_response_time=stats_data.get("avg_response_time", 0.0),
            active_users=stats_data.get("active_users", 0),
            sessions_change=stats_data.get("sessions_change", "0%"),
            success_rate_change=stats_data.get("success_rate_change", "0%"),
            token_usage_change=stats_data.get("token_usage_change", "0%"),
            error_count_change=stats_data.get("error_count_change", "0%"),
            response_time_change=stats_data.get("response_time_change", "0%"),
            active_users_change=stats_data.get("active_users_change", "0%"),
        )
        
        # 確保 recent_sessions_data 和 recent_errors_data 是列表
        if not isinstance(recent_sessions_data, list):
            recent_sessions_data = []
        if not isinstance(recent_errors_data, list):
            recent_errors_data = []
        
        # 验证并创建 RecentSession 对象，确保所有必需字段都有值
        recent_sessions = []
        for item in recent_sessions_data:
            if isinstance(item, dict):
                # 确保所有必需字段都有默认值，特别是 timestamp
                from datetime import datetime
                timestamp = item.get("timestamp") or item.get("started_at") or datetime.now().isoformat()
                session_data = {
                    "id": item.get("id", "unknown"),
                    "user": item.get("user", "unknown"),
                    "messages": item.get("messages", 0),
                    "status": item.get("status", "unknown"),
                    "duration": item.get("duration", "0s"),
                    "timestamp": timestamp
                }
                try:
                    recent_sessions.append(RecentSession(**session_data))
                except Exception as e:
                    logger.warning(f"创建 RecentSession 失败: {e}, 数据: {item}")
        
        # 验证并创建 RecentError 对象，确保所有必需字段都有值
        recent_errors = []
        for item in recent_errors_data:
            if isinstance(item, dict):
                # 确保所有必需字段都有默认值
                # 确保 timestamp 不为空
                error_timestamp = item.get("timestamp") or datetime.now().isoformat()
                error_data = {
                    "id": item.get("id", "unknown"),
                    "type": item.get("type", "error"),
                    "message": item.get("message", "未知错误"),
                    "severity": item.get("severity", "medium"),
                    "timestamp": error_timestamp
                }
                try:
                    recent_errors.append(RecentError(**error_data))
                except Exception as e:
                    logger.warning(f"创建 RecentError 失败: {e}, 数据: {item}")
        
        result = DashboardData(
            stats=stats,
            recent_sessions=recent_sessions,
            recent_errors=recent_errors,
        )
        # 直接返回 Pydantic 模型对象，FastAPI 会自动序列化
        return result
    except Exception as e:
        logger.error(f"使用群組AI儀表板API失敗: {e}")
        import traceback
        logger.error(traceback.format_exc())
        # 即使失敗也返回空數據，不使用模擬數據
        
        # 返回空數據結構
        stats = DashboardStats(
            today_sessions=0,
            success_rate=0.0,
            token_usage=0,
            error_count=0,
            avg_response_time=0.0,
            active_users=0,
            sessions_change="0%",
            success_rate_change="0%",
            token_usage_change="0%",
            error_count_change="0%",
            response_time_change="0%",
            active_users_change="0%",
        )
        
        return DashboardData(
            stats=stats,
            recent_sessions=[],
            recent_errors=[],
        )


@router.get("/sessions", response_model=SessionList, tags=["sessions"], dependencies=[Depends(get_current_active_user)])
async def list_sessions(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    q: Optional[str] = Query(None, description="搜索關鍵詞（session_id 或用戶）"),
    time_range: Optional[str] = Query(None, alias="range", description="時間範圍（24h/7d/custom）"),
    start_date: Optional[str] = Query(None, description="開始日期（ISO 格式）"),
    end_date: Optional[str] = Query(None, description="結束日期（ISO 格式）"),
) -> SessionList:
    """獲取會話列表"""
    data = data_sources.get_sessions(page=page, page_size=page_size, q=q, time_range=time_range, start_date=start_date, end_date=end_date)
    from app.schemas.session import Session
    
    items = [Session(**item) for item in data.get("items", [])]
    return SessionList(
        items=items,
        total=data.get("total", len(items)),
        page=data.get("page", page),
        page_size=data.get("page_size", page_size),
    )


@router.get("/sessions/{session_id}", tags=["sessions"], dependencies=[Depends(get_current_active_user)])
async def get_session_detail(session_id: str):
    """獲取單個會話詳情"""
    data = data_sources.get_session_detail(session_id)
    return data


@router.get("/logs", response_model=LogList, tags=["logs"], dependencies=[Depends(get_current_active_user)])
async def list_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    level: Optional[str] = Query(None, pattern="^(error|warning|info)$"),
    q: Optional[str] = Query(None, description="搜索關鍵詞"),
) -> LogList:
    """獲取日誌列表（從群組AI系統和遠程服務器）"""
    import logging
    logger = logging.getLogger(__name__)
    try:
        # 優先使用群組AI日誌API（真實日誌）
        from app.api.group_ai.logs import list_logs as group_ai_list_logs
        return await group_ai_list_logs(page=page, page_size=page_size, level=level, q=q)
    except Exception as e:
        logger.warning(f"使用群組AI日誌API失敗，回退到舊API: {e}")
        # 回退到舊的API（但移除模擬數據）
        data = data_sources.get_logs(page=page, page_size=page_size, level=level, q=q)
        from app.schemas.log import LogEntry
        from datetime import datetime
        
        items = []
        for item in data.get("items", []):
            # 處理時間戳
            if isinstance(item.get("timestamp"), str):
                try:
                    item["timestamp"] = datetime.fromisoformat(item["timestamp"].replace("Z", "+00:00"))
                except:
                    item["timestamp"] = datetime.utcnow()
            items.append(LogEntry(**item))
        
        return LogList(
            items=items,
            total=data.get("total", len(items)),
            page=data.get("page", page),
            page_size=data.get("page_size", page_size),
        )


@router.get("/metrics", response_model=MetricsData, tags=["metrics"], dependencies=[Depends(get_current_active_user)])
async def get_metrics() -> MetricsData:
    """獲取 Metrics 數據（響應時間趨勢、系統狀態，帶緩存）"""
    data = data_sources.get_metrics()
    from app.schemas.metrics import ResponseTimeMetrics, SystemMetrics, ResponseTimeDataPoint, SystemStatusItem
    
    # 确保数据存在，处理空列表情况
    response_time_dict = data.get("response_time", {})
    data_points = response_time_dict.get("data_points", [])
    if not data_points:
        # 如果没有数据点，创建空列表
        data_points = []
    
    response_time_data = [
        ResponseTimeDataPoint(**item) for item in data_points
    ]
    response_time = ResponseTimeMetrics(
        data_points=response_time_data,
        average=response_time_dict.get("average", 0),
        min=response_time_dict.get("min", 0),
        max=response_time_dict.get("max", 0),
        trend=response_time_dict.get("trend", "0%"),
    )
    
    # 确保系统状态数据存在
    system_status_dict = data.get("system_status", {})
    status_items = system_status_dict.get("status_items", [])
    if not status_items:
        status_items = []
    
    system_status_items = [
        SystemStatusItem(**item) for item in status_items
    ]
    system_status = SystemMetrics(
        status_items=system_status_items,
        last_updated=system_status_dict.get("last_updated", ""),
    )
    
    result = MetricsData(
        response_time=response_time,
        system_status=system_status,
    )
    return result


@router.get("/settings/alerts", response_model=AlertSettings, tags=["settings"], dependencies=[Depends(get_current_active_user)])
async def get_alert_settings() -> AlertSettings:
    """獲取告警設置"""
    data = data_sources.get_alert_settings()
    return AlertSettings(**data)


@router.post("/settings/alerts", response_model=dict, tags=["settings"], dependencies=[Depends(get_current_active_user)])
async def save_alert_settings(settings: AlertSettings) -> dict:
    """保存告警設置"""
    result = data_sources.save_alert_settings(settings.model_dump())
    return result


@router.get("/system/monitor", response_model=SystemMonitorData, tags=["system"], dependencies=[Depends(get_current_active_user)])
@cached(prefix="system_monitor", ttl=30)  # 緩存 30 秒
async def get_system_monitor() -> SystemMonitorData:
    """獲取系統監控數據（帶緩存）"""
    data = data_sources.get_system_monitor()
    from app.schemas.system import SystemHealth, SystemMetrics as SystemMetricsSchema
    
    # 確保 data 是字典類型
    if not isinstance(data, dict):
        # 如果 data 不是字典，創建默認值
        data = {}
    
    health_data = data.get("health", {}) if isinstance(data.get("health"), dict) else {}
    metrics_data = data.get("metrics", {}) if isinstance(data.get("metrics"), dict) else {}
    services_data = data.get("services", {}) if isinstance(data.get("services"), dict) else {}
    
    health = SystemHealth(**health_data)
    metrics = SystemMetricsSchema(**metrics_data)
    
    return SystemMonitorData(
        health=health,
        metrics=metrics,
        services=services_data,
    )


@router.get("/system/performance", tags=["system"], dependencies=[Depends(get_current_active_user)])
async def get_performance_monitoring() -> dict:
    """獲取 API 性能統計數據"""
    """用於分析慢請求和 API 性能瓶頸"""
    stats = get_performance_stats()
    return stats

