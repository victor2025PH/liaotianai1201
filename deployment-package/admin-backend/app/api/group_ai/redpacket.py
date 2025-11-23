"""
紅包服務 HTTP API
"""
import logging
import sys
from pathlib import Path
from typing import List, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

# 添加項目根目錄到路徑
project_root = Path(__file__).parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from group_ai_service import ServiceManager
from group_ai_service.redpacket_handler import RedpacketHandler, RedpacketStrategy, RandomStrategy, TimeBasedStrategy, AmountBasedStrategy, FrequencyStrategy, CompositeStrategy
from app.db import get_db

# 導入緩存功能
from app.core.cache import cached, invalidate_cache

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Group AI Redpacket"])


class RedpacketStatsResponse(BaseModel):
    """紅包統計響應"""
    account_id: Optional[str] = None
    total_participations: int
    successful: int
    failed: int
    success_rate: float
    total_amount: float
    average_amount: float
    time_range: Optional[str] = None


class RedpacketHistoryItem(BaseModel):
    """紅包參與歷史項"""
    redpacket_id: str
    account_id: str
    success: bool
    amount: Optional[float] = None
    error: Optional[str] = None
    timestamp: str


class RedpacketHistoryResponse(BaseModel):
    """紅包參與歷史響應"""
    account_id: Optional[str] = None
    history: List[RedpacketHistoryItem]
    total_count: int
    time_range: Optional[str] = None


class StrategyUpdateRequest(BaseModel):
    """策略更新請求"""
    account_id: Optional[str] = None  # None 表示更新默認策略
    strategy_type: str  # random, time_based, amount_based, frequency, composite
    strategy_params: dict  # 策略參數


class StrategyUpdateResponse(BaseModel):
    """策略更新響應"""
    success: bool
    message: str
    strategy_type: Optional[str] = None


def get_service_manager() -> ServiceManager:
    """獲取服務管理器實例"""
    return ServiceManager.get_instance()


def get_redpacket_handler(manager: ServiceManager) -> RedpacketHandler:
    """獲取紅包處理器"""
    dialogue_manager = manager.dialogue_manager
    if not dialogue_manager or not dialogue_manager.redpacket_handler:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="紅包處理器未初始化"
        )
    return dialogue_manager.redpacket_handler


@router.get("/stats", response_model=RedpacketStatsResponse)
@cached(prefix="redpacket_stats", ttl=60)  # 緩存 60 秒
async def get_redpacket_stats(
    account_id: Optional[str] = Query(None, description="賬號ID（可選，過濾）"),
    time_range_hours: Optional[int] = Query(None, ge=1, le=168, description="時間範圍（小時，可選）"),
    manager: ServiceManager = Depends(get_service_manager),
    db: Session = Depends(get_db)
):
    """
    獲取紅包統計
    
    返回指定賬號或所有賬號的紅包參與統計
    """
    try:
        handler = get_redpacket_handler(manager)
        
        # 計算時間範圍
        time_range = None
        if time_range_hours:
            time_range = timedelta(hours=time_range_hours)
        
        # 獲取統計
        stats = handler.get_participation_stats(
            account_id=account_id,
            time_range=time_range
        )
        
        return RedpacketStatsResponse(
            account_id=account_id,
            total_participations=stats["total_participations"],
            successful=stats["successful"],
            failed=stats["failed"],
            success_rate=stats["success_rate"],
            total_amount=stats["total_amount"],
            average_amount=stats["average_amount"],
            time_range=f"{time_range_hours}小時" if time_range_hours else None
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"獲取紅包統計失敗: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"獲取紅包統計失敗: {str(e)}"
        )


@router.get("/history", response_model=RedpacketHistoryResponse)
@cached(prefix="redpacket_history", ttl=30)  # 緩存 30 秒
async def get_redpacket_history(
    account_id: Optional[str] = Query(None, description="賬號ID（可選，過濾）"),
    limit: int = Query(100, ge=1, le=1000, description="返回數量"),
    time_range_hours: Optional[int] = Query(None, ge=1, le=168, description="時間範圍（小時，可選）"),
    manager: ServiceManager = Depends(get_service_manager),
    db: Session = Depends(get_db)
):
    """
    獲取紅包參與歷史
    
    返回指定賬號或所有賬號的紅包參與歷史記錄
    """
    try:
        handler = get_redpacket_handler(manager)
        
        # 獲取參與日誌
        results = handler.participation_log
        
        # 過濾賬號
        if account_id:
            results = [r for r in results if r.account_id == account_id]
        
        # 過濾時間範圍
        if time_range_hours:
            cutoff = datetime.now() - timedelta(hours=time_range_hours)
            results = [r for r in results if r.timestamp >= cutoff]
        
        # 排序（最新的在前）
        results.sort(key=lambda x: x.timestamp, reverse=True)
        
        # 限制數量
        results = results[:limit]
        
        history_items = []
        for result in results:
            history_items.append(RedpacketHistoryItem(
                redpacket_id=result.redpacket_id,
                account_id=result.account_id,
                success=result.success,
                amount=result.amount,
                error=result.error,
                timestamp=result.timestamp.isoformat() if isinstance(result.timestamp, datetime) else str(result.timestamp)
            ))
        
        return RedpacketHistoryResponse(
            account_id=account_id,
            history=history_items,
            total_count=len(handler.participation_log),
            time_range=f"{time_range_hours}小時" if time_range_hours else None
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"獲取紅包歷史失敗: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"獲取紅包歷史失敗: {str(e)}"
        )


@router.post("/strategy", response_model=StrategyUpdateResponse)
async def update_redpacket_strategy(
    request: StrategyUpdateRequest,
    manager: ServiceManager = Depends(get_service_manager),
    db: Session = Depends(get_db)
):
    """
    更新紅包參與策略
    
    更新指定賬號或默認的紅包參與策略
    """
    try:
        handler = get_redpacket_handler(manager)
        
        # 根據策略類型創建策略對象
        strategy: Optional[RedpacketStrategy] = None
        strategy_type = request.strategy_type.lower()
        params = request.strategy_params or {}
        
        if strategy_type == "random":
            strategy = RandomStrategy(
                base_probability=params.get("base_probability", 0.5)
            )
        
        elif strategy_type == "time_based":
            strategy = TimeBasedStrategy(
                peak_hours=params.get("peak_hours", [18, 19, 20, 21]),
                peak_probability=params.get("peak_probability", 0.8),
                off_peak_probability=params.get("off_peak_probability", 0.3)
            )
        
        elif strategy_type == "amount_based":
            strategy = AmountBasedStrategy(
                min_amount=params.get("min_amount", 0.01),
                max_amount=params.get("max_amount", 100.0),
                high_amount_probability=params.get("high_amount_probability", 0.9),
                low_amount_probability=params.get("low_amount_probability", 0.3)
            )
        
        elif strategy_type == "frequency":
            strategy = FrequencyStrategy(
                max_per_hour=params.get("max_per_hour", 5),
                cooldown_seconds=params.get("cooldown_seconds", 300)
            )
        
        elif strategy_type == "composite":
            # 組合策略需要子策略列表
            sub_strategies = params.get("sub_strategies", [])
            if not sub_strategies:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="組合策略需要提供 sub_strategies 參數"
                )
            
            strategy_list = []
            for sub_strategy_config in sub_strategies:
                sub_type = sub_strategy_config.get("type")
                sub_params = sub_strategy_config.get("params", {})
                weight = sub_strategy_config.get("weight", 1.0)
                
                if sub_type == "random":
                    sub_strategy = RandomStrategy(base_probability=sub_params.get("base_probability", 0.5))
                elif sub_type == "time_based":
                    sub_strategy = TimeBasedStrategy(
                        peak_hours=sub_params.get("peak_hours", [18, 19, 20, 21]),
                        peak_probability=sub_params.get("peak_probability", 0.8),
                        off_peak_probability=sub_params.get("off_peak_probability", 0.3)
                    )
                elif sub_type == "amount_based":
                    sub_strategy = AmountBasedStrategy(
                        min_amount=sub_params.get("min_amount", 0.01),
                        max_amount=sub_params.get("max_amount", 100.0),
                        high_amount_probability=sub_params.get("high_amount_probability", 0.9),
                        low_amount_probability=sub_params.get("low_amount_probability", 0.3)
                    )
                else:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"不支持的子策略類型: {sub_type}"
                    )
                
                strategy_list.append((sub_strategy, weight))
            
            strategy = CompositeStrategy(strategy_list)
        
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"不支持的策略類型: {request.strategy_type}"
            )
        
        # 設置策略
        if request.account_id:
            # 為指定賬號設置策略（需要註冊）
            handler.register_strategy(request.account_id, strategy)
            message = f"已為賬號 {request.account_id} 設置 {strategy_type} 策略"
        else:
            # 設置默認策略
            handler.set_default_strategy(strategy)
            message = f"已設置默認 {strategy_type} 策略"
        
        logger.info(message)
        
        # 清除相關緩存
        invalidate_cache("redpacket_stats")
        invalidate_cache("redpacket_history")
        
        return StrategyUpdateResponse(
            success=True,
            message=message,
            strategy_type=strategy_type
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新紅包策略失敗: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新紅包策略失敗: {str(e)}"
        )


@router.get("/hourly-count/{account_id}", response_model=dict)
@cached(prefix="redpacket_hourly_count", ttl=10)  # 緩存 10 秒（因為是實時數據，緩存時間較短）
async def get_hourly_participation_count(
    account_id: str,
    manager: ServiceManager = Depends(get_service_manager),
    db: Session = Depends(get_db)
):
    """
    獲取指定賬號當前小時的紅包參與次數
    
    用於查看賬號是否已達到每小時參與上限
    """
    try:
        handler = get_redpacket_handler(manager)
        
        count = handler.get_hourly_participation_count(account_id)
        
        # 獲取賬號配置中的每小時上限
        from group_ai_service.config import get_group_ai_config
        config = get_group_ai_config()
        max_per_hour = config.redpacket_max_per_hour
        
        return {
            "account_id": account_id,
            "current_hour_count": count,
            "max_per_hour": max_per_hour,
            "remaining_quota": max(0, max_per_hour - count),
            "is_at_limit": count >= max_per_hour
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"獲取每小時參與次數失敗: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"獲取每小時參與次數失敗: {str(e)}"
        )

