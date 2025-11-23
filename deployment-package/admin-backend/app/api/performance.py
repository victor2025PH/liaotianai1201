"""
性能監控 API
提供緩存統計、數據庫查詢統計等性能指標
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any

from app.db import get_db
from app.api.deps import get_current_active_user
from app.models.user import User
from app.core.cache import get_cache_manager
from app.middleware.performance import get_performance_stats

router = APIRouter(prefix="/performance", tags=["Performance"])


@router.get("/cache/stats")
async def get_cache_stats(
    current_user: User = Depends(get_current_active_user),
) -> Dict[str, Any]:
    """獲取緩存統計信息（需要管理員權限）"""
    # 檢查是否為管理員（可選，根據需求調整）
    # if not current_user.is_superuser:
    #     raise HTTPException(
    #         status_code=status.HTTP_403_FORBIDDEN,
    #         detail="需要管理員權限"
    #     )
    
    cache_manager = get_cache_manager()
    stats = cache_manager.get_stats()
    
    return {
        "cache": stats,
        "message": "緩存統計信息獲取成功"
    }


@router.post("/cache/clear")
async def clear_cache(
    pattern: str = "*",
    current_user: User = Depends(get_current_active_user),
) -> Dict[str, Any]:
    """清除緩存（需要管理員權限）"""
    # 檢查是否為管理員（可選，根據需求調整）
    # if not current_user.is_superuser:
    #     raise HTTPException(
    #         status_code=status.HTTP_403_FORBIDDEN,
    #         detail="需要管理員權限"
    #     )
    
    cache_manager = get_cache_manager()
    count = cache_manager.clear_pattern(pattern)
    
    return {
        "message": f"已清除 {count} 個緩存項",
        "cleared_count": count,
        "pattern": pattern
    }


@router.get("/stats")
async def get_performance_stats_endpoint(
    current_user: User = Depends(get_current_active_user),
) -> Dict[str, Any]:
    """獲取性能統計信息"""
    stats = get_performance_stats()
    
    return {
        "performance": stats,
        "message": "性能統計信息獲取成功"
    }

