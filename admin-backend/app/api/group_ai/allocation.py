"""
智能分配API接口
提供账号分配、重新分配等功能
"""
import logging
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_active_user
from app.models.user import User
from app.core.intelligent_allocator import IntelligentAllocator, AllocationResult, RebalanceResult
from app.core.load_balancer import AllocationStrategy
from app.middleware.permission import check_permission
from app.core.permissions import PermissionCode

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/allocation", tags=["allocation"])


class AllocationRequest(BaseModel):
    """分配请求"""
    account_id: str
    session_file: str
    script_id: Optional[str] = None
    strategy: str = "load_balance"  # load_balance, location, affinity, isolation
    account_location: Optional[str] = None


class AllocationResponse(BaseModel):
    """分配响应"""
    success: bool
    server_id: Optional[str] = None
    remote_path: Optional[str] = None
    load_score: Optional[float] = None
    message: str
    error: Optional[str] = None


class RebalanceRequest(BaseModel):
    """重新分配请求"""
    threshold: float = 30.0  # 负载差异阈值
    max_migrations: int = 10  # 最大迁移数量


class RebalanceResponse(BaseModel):
    """重新分配响应"""
    success: bool
    migrated_accounts: List[str]
    failed_accounts: List[str]
    message: str


class ServerRankingResponse(BaseModel):
    """服务器排名响应"""
    rankings: List[dict]  # [{"server_id": "...", "score": 45.2}, ...]


def get_allocator() -> IntelligentAllocator:
    """获取智能分配引擎实例"""
    return IntelligentAllocator()


@router.post("/allocate", response_model=AllocationResponse)
async def allocate_account(
    request: AllocationRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    allocator: IntelligentAllocator = Depends(get_allocator)
):
    """
    分配账号到最优服务器
    
    需要权限: ACCOUNT_UPDATE
    """
    check_permission(current_user, PermissionCode.ACCOUNT_UPDATE.value, db)
    
    try:
        # 转换策略字符串为枚举
        strategy_map = {
            "load_balance": AllocationStrategy.LOAD_BALANCE,
            "location": AllocationStrategy.LOCATION,
            "affinity": AllocationStrategy.AFFINITY,
            "isolation": AllocationStrategy.ISOLATION
        }
        
        strategy = strategy_map.get(request.strategy, AllocationStrategy.LOAD_BALANCE)
        
        # 执行分配
        result: AllocationResult = await allocator.allocate_account(
            account_id=request.account_id,
            session_file=request.session_file,
            script_id=request.script_id,
            strategy=strategy,
            account_location=request.account_location,
            db=db
        )
        
        if result.success:
            return AllocationResponse(
                success=True,
                server_id=result.server_id,
                remote_path=result.remote_path,
                load_score=result.load_score,
                message=result.message
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.message
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"分配账号失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"分配账号失败: {str(e)}"
        )


@router.post("/rebalance", response_model=RebalanceResponse)
async def rebalance_accounts(
    request: RebalanceRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    allocator: IntelligentAllocator = Depends(get_allocator)
):
    """
    重新平衡账号分布
    
    需要权限: ACCOUNT_UPDATE
    """
    check_permission(current_user, PermissionCode.ACCOUNT_UPDATE.value, db)
    
    try:
        result: RebalanceResult = await allocator.rebalance_accounts(
            db=db,
            threshold=request.threshold,
            max_migrations=request.max_migrations
        )
        
        return RebalanceResponse(
            success=result.success,
            migrated_accounts=result.migrated_accounts,
            failed_accounts=result.failed_accounts,
            message=result.message
        )
        
    except Exception as e:
        logger.error(f"重新平衡账号失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"重新平衡账号失败: {str(e)}"
        )


@router.get("/rankings", response_model=ServerRankingResponse)
async def get_server_rankings(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    allocator: IntelligentAllocator = Depends(get_allocator)
):
    """
    获取服务器排名（按负载分数排序）
    
    需要权限: SERVER_VIEW
    """
    check_permission(current_user, PermissionCode.SERVER_VIEW.value, db)
    
    try:
        rankings = await allocator.get_server_rankings()
        
        return ServerRankingResponse(
            rankings=[
                {"server_id": server_id, "score": score}
                for server_id, score in rankings
            ]
        )
        
    except Exception as e:
        logger.error(f"获取服务器排名失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取服务器排名失败: {str(e)}"
        )

