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
@cached(prefix="dashboard", ttl=30)  # 緩存 30 秒（儀表板數據更新頻繁）
async def get_dashboard() -> DashboardData:
    """獲取 Dashboard 統計數據（從群組AI系統，帶緩存）"""
    import logging
    logger = logging.getLogger(__name__)
    try:
        # 優先使用群組AI儀表板API（真實數據）
        from app.api.group_ai.dashboard import get_dashboard_stats
        data = get_dashboard_stats()
        from app.schemas.dashboard import DashboardStats, RecentSession, RecentError
        
        # 確保數據結構正確
        stats_data = data.get("stats", {})
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
        
        recent_sessions = [RecentSession(**item) for item in recent_sessions_data]
        recent_errors = [RecentError(**item) for item in recent_errors_data]
        
        return DashboardData(
            stats=stats,
            recent_sessions=recent_sessions,
            recent_errors=recent_errors,
        )
    except Exception as e:
        logger.error(f"使用群組AI儀表板API失敗: {e}")
        import traceback
        logger.error(traceback.format_exc())
        # 即使失敗也返回空數據，不使用模擬數據
        from app.schemas.dashboard import DashboardStats, RecentSession, RecentError
        
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
@cached(prefix="metrics", ttl=30)  # 緩存 30 秒
async def get_metrics() -> MetricsData:
    """獲取 Metrics 數據（響應時間趨勢、系統狀態，帶緩存）"""
    data = data_sources.get_metrics()
    from app.schemas.metrics import ResponseTimeMetrics, SystemMetrics, ResponseTimeDataPoint, SystemStatusItem
    
    response_time_data = [
        ResponseTimeDataPoint(**item) for item in data.get("response_time", {}).get("data_points", [])
    ]
    response_time = ResponseTimeMetrics(
        data_points=response_time_data,
        average=data.get("response_time", {}).get("average", 0),
        min=data.get("response_time", {}).get("min", 0),
        max=data.get("response_time", {}).get("max", 0),
        trend=data.get("response_time", {}).get("trend", "0%"),
    )
    
    system_status_items = [
        SystemStatusItem(**item) for item in data.get("system_status", {}).get("status_items", [])
    ]
    system_status = SystemMetrics(
        status_items=system_status_items,
        last_updated=data.get("system_status", {}).get("last_updated", ""),
    )
    
    return MetricsData(
        response_time=response_time,
        system_status=system_status,
    )


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
    
    health = SystemHealth(**data.get("health", {}))
    metrics = SystemMetricsSchema(**data.get("metrics", {}))
    
    return SystemMonitorData(
        health=health,
        metrics=metrics,
        services=data.get("services", {}),
    )


@router.get("/system/performance", tags=["system"], dependencies=[Depends(get_current_active_user)])
async def get_performance_monitoring() -> dict:
    """獲取 API 性能統計數據"""
    """用於分析慢請求和 API 性能瓶頸"""
    stats = get_performance_stats()
    return stats

