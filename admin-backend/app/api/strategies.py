"""
紅包策略 API - Phase 2: 擬人化版
"""
import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.group_ai import RedPacketStrategy
from app.schemas.redpacket_strategy import (
    RedPacketStrategyCreate,
    RedPacketStrategyUpdate,
    RedPacketStrategyResponse
)
from app.api.deps import get_current_user
from app.models.user import User
from app.websocket import get_websocket_manager, MessageHandler, MessageType

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/strategies", tags=["RedPacket Strategies"])


@router.get("/", response_model=List[RedPacketStrategyResponse])
async def list_strategies(
    skip: int = 0,
    limit: int = 100,
    enabled: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    獲取紅包策略列表
    """
    try:
        query = db.query(RedPacketStrategy)
        
        if enabled is not None:
            query = query.filter(RedPacketStrategy.enabled == enabled)
        
        strategies = query.offset(skip).limit(limit).all()
        return strategies
    except Exception as e:
        logger.error(f"獲取策略列表失敗: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"獲取策略列表失敗: {str(e)}"
        )


@router.get("/{strategy_id}", response_model=RedPacketStrategyResponse)
async def get_strategy(
    strategy_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    獲取指定策略
    """
    strategy = db.query(RedPacketStrategy).filter(RedPacketStrategy.id == strategy_id).first()
    if not strategy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"策略 {strategy_id} 未找到"
        )
    return strategy


@router.post("/", response_model=RedPacketStrategyResponse, status_code=status.HTTP_201_CREATED)
async def create_strategy(
    strategy: RedPacketStrategyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    創建新策略
    """
    try:
        # 檢查名稱是否已存在
        existing = db.query(RedPacketStrategy).filter(
            RedPacketStrategy.name == strategy.name
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"策略名稱 '{strategy.name}' 已存在"
            )
        
        # 創建策略
        db_strategy = RedPacketStrategy(
            name=strategy.name,
            description=strategy.description,
            keywords=strategy.keywords,
            delay_min=strategy.delay_min,
            delay_max=strategy.delay_max,
            target_groups=strategy.target_groups,
            probability=strategy.probability,
            enabled=strategy.enabled,
            created_by=current_user.id if hasattr(current_user, 'id') else None
        )
        
        db.add(db_strategy)
        db.commit()
        db.refresh(db_strategy)
        
        # 廣播策略更新
        manager = get_websocket_manager()
        message = MessageHandler.create_message(
            MessageType.CONFIG,
            {
                "action": "strategy_created",
                "strategy_id": db_strategy.id,
                "strategy": {
                    "id": db_strategy.id,
                    "name": db_strategy.name,
                    "keywords": db_strategy.keywords,
                    "delay_min": db_strategy.delay_min,
                    "delay_max": db_strategy.delay_max,
                    "target_groups": db_strategy.target_groups,
                    "probability": db_strategy.probability,
                    "enabled": db_strategy.enabled
                }
            }
        )
        await manager.broadcast(message)
        
        logger.info(f"策略已創建: {db_strategy.id} ({db_strategy.name})")
        return db_strategy
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"創建策略失敗: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"創建策略失敗: {str(e)}"
        )


@router.put("/{strategy_id}", response_model=RedPacketStrategyResponse)
async def update_strategy(
    strategy_id: str,
    strategy: RedPacketStrategyUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    更新策略
    """
    try:
        db_strategy = db.query(RedPacketStrategy).filter(
            RedPacketStrategy.id == strategy_id
        ).first()
        if not db_strategy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"策略 {strategy_id} 未找到"
            )
        
        # 檢查名稱是否已被其他策略使用
        if strategy.name and strategy.name != db_strategy.name:
            existing = db.query(RedPacketStrategy).filter(
                RedPacketStrategy.name == strategy.name,
                RedPacketStrategy.id != strategy_id
            ).first()
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"策略名稱 '{strategy.name}' 已被使用"
                )
        
        # 更新字段
        update_data = strategy.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_strategy, field, value)
        
        db.commit()
        db.refresh(db_strategy)
        
        # 廣播策略更新
        manager = get_websocket_manager()
        message = MessageHandler.create_message(
            MessageType.CONFIG,
            {
                "action": "strategy_updated",
                "strategy_id": db_strategy.id,
                "strategy": {
                    "id": db_strategy.id,
                    "name": db_strategy.name,
                    "keywords": db_strategy.keywords,
                    "delay_min": db_strategy.delay_min,
                    "delay_max": db_strategy.delay_max,
                    "target_groups": db_strategy.target_groups,
                    "probability": db_strategy.probability,
                    "enabled": db_strategy.enabled
                }
            }
        )
        await manager.broadcast(message)
        
        logger.info(f"策略已更新: {db_strategy.id} ({db_strategy.name})")
        return db_strategy
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"更新策略失敗: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新策略失敗: {str(e)}"
        )


@router.delete("/{strategy_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_strategy(
    strategy_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    刪除策略
    """
    try:
        db_strategy = db.query(RedPacketStrategy).filter(
            RedPacketStrategy.id == strategy_id
        ).first()
        if not db_strategy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"策略 {strategy_id} 未找到"
            )
        
        strategy_name = db_strategy.name
        db.delete(db_strategy)
        db.commit()
        
        # 廣播策略更新
        manager = get_websocket_manager()
        message = MessageHandler.create_message(
            MessageType.CONFIG,
            {
                "action": "strategy_deleted",
                "strategy_id": strategy_id
            }
        )
        await manager.broadcast(message)
        
        logger.info(f"策略已刪除: {strategy_id} ({strategy_name})")
        return None
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"刪除策略失敗: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"刪除策略失敗: {str(e)}"
        )
