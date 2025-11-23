"""
系统优化 API
提供性能优化、缓存管理、备份恢复等系统级功能
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, List, Optional

from app.api.deps import get_current_active_user, get_db
from app.models.user import User
from app.core.cache import get_cache_manager
from app.core.auto_backup import get_backup_manager
from app.core.performance_monitor import get_performance_monitor
from app.core.permissions import PermissionCode
from app.middleware.permission import check_permission

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/optimization", tags=["system-optimization"])


@router.get("/cache/stats")
async def get_cache_stats(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取缓存统计信息"""
    check_permission(current_user, PermissionCode.SYSTEM_VIEW.value, db)
    
    cache_manager = get_cache_manager()
    
    stats = {
        "memory_cache_size": len(cache_manager.memory_cache),
        "redis_enabled": cache_manager.redis_client is not None,
        "default_ttl": cache_manager.default_ttl
    }
    
    if cache_manager.redis_client:
        try:
            info = cache_manager.redis_client.info("memory")
            stats["redis_memory_used"] = info.get("used_memory_human", "N/A")
            stats["redis_keys"] = cache_manager.redis_client.dbsize()
        except Exception as e:
            logger.debug(f"获取 Redis 统计失败: {e}")
    
    return stats


@router.post("/cache/clear")
async def clear_cache(
    pattern: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """清除缓存"""
    check_permission(current_user, PermissionCode.SYSTEM_MANAGE.value, db)
    
    cache_manager = get_cache_manager()
    
    if pattern:
        count = await cache_manager.clear_pattern(pattern)
        return {"message": f"已清除 {count} 个匹配的缓存项", "pattern": pattern}
    else:
        # 清除所有内存缓存
        cache_manager.memory_cache.clear()
        if cache_manager.redis_client:
            cache_manager.redis_client.flushdb()
        return {"message": "已清除所有缓存"}


@router.get("/backup/list")
async def list_backups(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """列出所有备份"""
    check_permission(current_user, PermissionCode.SYSTEM_VIEW.value, db)
    
    backup_manager = get_backup_manager()
    backups = []
    
    for backup_file in backup_manager.backup_dir.glob("*"):
        if backup_file.is_file():
            backups.append({
                "filename": backup_file.name,
                "size": backup_file.stat().st_size,
                "created": backup_file.stat().st_mtime,
                "type": "database" if "database" in backup_file.name else
                        "sessions" if "sessions" in backup_file.name else
                        "config" if "config" in backup_file.name else "unknown"
            })
    
    return {"backups": sorted(backups, key=lambda x: x["created"], reverse=True)}


@router.post("/backup/create")
async def create_backup(
    backup_type: Optional[str] = None,  # "full", "database", "sessions", "config"
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """创建备份"""
    check_permission(current_user, PermissionCode.SYSTEM_MANAGE.value, db)
    
    backup_manager = get_backup_manager()
    
    from app.core.config import get_settings
    settings = get_settings()
    
    if backup_type == "full" or backup_type is None:
        results = await backup_manager.full_backup(
            database_url=getattr(settings, "database_url", None),
            sessions_dir="sessions",
            config_files=[".env", "admin-backend/.env"]
        )
        return {"message": "完整备份已创建", "backups": results}
    elif backup_type == "database":
        result = await backup_manager.backup_database(getattr(settings, "database_url", ""))
        return {"message": "数据库备份已创建", "backup": str(result) if result else None}
    elif backup_type == "sessions":
        result = await backup_manager.backup_sessions()
        return {"message": "Session 备份已创建", "backup": str(result) if result else None}
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"不支持的备份类型: {backup_type}"
        )


@router.get("/performance/summary")
async def get_performance_summary(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取性能摘要"""
    check_permission(current_user, PermissionCode.SYSTEM_VIEW.value, db)
    
    monitor = get_performance_monitor()
    return monitor.get_performance_summary()


@router.post("/performance/start-monitoring")
async def start_performance_monitoring(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """启动性能监控"""
    check_permission(current_user, PermissionCode.SYSTEM_MANAGE.value, db)
    
    monitor = get_performance_monitor()
    await monitor.start_monitoring()
    
    return {"message": "性能监控已启动"}


@router.post("/performance/stop-monitoring")
async def stop_performance_monitoring(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """停止性能监控"""
    check_permission(current_user, PermissionCode.SYSTEM_MANAGE.value, db)
    
    monitor = get_performance_monitor()
    monitor.stop_monitoring()
    
    return {"message": "性能监控已停止"}


@router.get("/smart/analyze")
async def analyze_system(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """智能分析系统状态"""
    check_permission(current_user, PermissionCode.SYSTEM_VIEW.value, db)
    
    optimizer = get_smart_optimizer()
    analysis = await optimizer.analyze_system()
    
    return analysis


@router.post("/smart/optimize")
async def auto_optimize(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """执行自动优化"""
    check_permission(current_user, PermissionCode.SYSTEM_MANAGE.value, db)
    
    optimizer = get_smart_optimizer()
    result = await optimizer.auto_optimize()
    
    return result


@router.post("/smart/start-auto-optimization")
async def start_auto_optimization(
    interval_hours: int = 6,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """启动自动优化"""
    check_permission(current_user, PermissionCode.SYSTEM_MANAGE.value, db)
    
    optimizer = get_smart_optimizer()
    await optimizer.start_auto_optimization(interval_hours)
    
    return {"message": f"自动优化已启动，间隔: {interval_hours} 小时"}

