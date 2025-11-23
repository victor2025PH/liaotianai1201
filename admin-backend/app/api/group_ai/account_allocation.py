"""
賬號分配管理API
用於智能分配和手動調整賬號到服務器
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_current_active_user
from app.models.group_ai import GroupAIAccount
from app.models.user import User
from app.middleware.permission import check_permission
from app.core.permissions import PermissionCode
import logging

logger = logging.getLogger(__name__)

router = APIRouter(tags=["account-allocation"])


class AccountAllocationRequest(BaseModel):
    """賬號分配請求"""
    account_id: str
    server_id: str


class BatchAllocationRequest(BaseModel):
    """批量分配請求"""
    allocations: List[AccountAllocationRequest]


class AutoAllocationRequest(BaseModel):
    """自動分配請求"""
    strategy: str = "balanced"  # balanced, round_robin, least_loaded
    max_accounts_per_server: Optional[int] = None


class AllocationResponse(BaseModel):
    """分配響應"""
    success: bool
    message: str
    allocations: Optional[Dict[str, str]] = None  # account_id -> server_id


@router.post("/auto", response_model=AllocationResponse)
async def auto_allocate_accounts(
    request: AutoAllocationRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """自動分配所有賬號到服務器"""
    check_permission(current_user, PermissionCode.ACCOUNT_UPDATE.value, db)
    
    try:
        # 加載服務器配置
        from pathlib import Path
        import json
        project_root = Path(__file__).parent.parent.parent.parent.parent
        config_path = project_root / "data" / "master_config.json"
        
        if not config_path.exists():
            raise HTTPException(status_code=404, detail="服務器配置文件不存在")
        
        with open(config_path, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
            servers = config_data.get('servers', {})
        
        # 獲取所有未分配的賬號
        unallocated_accounts = db.query(GroupAIAccount).filter(
            GroupAIAccount.server_id.is_(None)
        ).all()
        
        # 獲取所有已分配的賬號（用於計算負載）
        all_accounts = db.query(GroupAIAccount).all()
        server_loads = {}
        for server_id in servers.keys():
            count = db.query(GroupAIAccount).filter(
                GroupAIAccount.server_id == server_id
            ).count()
            max_accounts = servers[server_id].get('max_accounts', 5)
            server_loads[server_id] = {
                'current': count,
                'max': max_accounts,
                'available': max_accounts - count
            }
        
        allocations = {}
        
        if request.strategy == "balanced":
            # 平衡分配：盡量讓每個服務器的負載均衡
            for account in unallocated_accounts:
                # 找到可用空間最多的服務器
                best_server = None
                max_available = -1
                
                for server_id, load in server_loads.items():
                    if load['available'] > 0 and load['available'] > max_available:
                        max_available = load['available']
                        best_server = server_id
                
                if best_server:
                    account.server_id = best_server
                    allocations[account.account_id] = best_server
                    server_loads[best_server]['current'] += 1
                    server_loads[best_server]['available'] -= 1
                else:
                    logger.warning(f"無法分配賬號 {account.account_id}，所有服務器已滿")
        
        elif request.strategy == "round_robin":
            # 輪詢分配：依次分配給每個服務器
            server_ids = list(servers.keys())
            server_index = 0
            
            for account in unallocated_accounts:
                assigned = False
                attempts = 0
                
                while not assigned and attempts < len(server_ids):
                    server_id = server_ids[server_index]
                    if server_loads[server_id]['available'] > 0:
                        account.server_id = server_id
                        allocations[account.account_id] = server_id
                        server_loads[server_id]['current'] += 1
                        server_loads[server_id]['available'] -= 1
                        assigned = True
                    
                    server_index = (server_index + 1) % len(server_ids)
                    attempts += 1
        
        elif request.strategy == "least_loaded":
            # 最少負載優先：總是分配給當前負載最少的服務器
            for account in unallocated_accounts:
                best_server = None
                min_load_ratio = float('inf')
                
                for server_id, load in server_loads.items():
                    if load['available'] > 0:
                        load_ratio = load['current'] / load['max'] if load['max'] > 0 else 1.0
                        if load_ratio < min_load_ratio:
                            min_load_ratio = load_ratio
                            best_server = server_id
                
                if best_server:
                    account.server_id = best_server
                    allocations[account.account_id] = best_server
                    server_loads[best_server]['current'] += 1
                    server_loads[best_server]['available'] -= 1
        
        db.commit()
        
        return AllocationResponse(
            success=True,
            message=f"成功分配 {len(allocations)} 個賬號",
            allocations=allocations
        )
    
    except Exception as e:
        logger.error(f"自動分配失敗: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=f"自動分配失敗: {str(e)}")


@router.post("/batch", response_model=AllocationResponse)
async def batch_allocate_accounts(
    request: BatchAllocationRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """批量手動分配賬號"""
    check_permission(current_user, PermissionCode.ACCOUNT_UPDATE.value, db)
    
    try:
        # 驗證服務器是否存在
        from pathlib import Path
        import json
        project_root = Path(__file__).parent.parent.parent.parent.parent
        config_path = project_root / "data" / "master_config.json"
        
        if not config_path.exists():
            raise HTTPException(status_code=404, detail="服務器配置文件不存在")
        
        with open(config_path, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
            servers = config_data.get('servers', {})
        
        allocations = {}
        errors = []
        
        for allocation in request.allocations:
            # 驗證服務器存在
            if allocation.server_id not in servers:
                errors.append(f"服務器 {allocation.server_id} 不存在")
                continue
            
            # 檢查服務器是否已滿
            current_count = db.query(GroupAIAccount).filter(
                GroupAIAccount.server_id == allocation.server_id
            ).count()
            max_accounts = servers[allocation.server_id].get('max_accounts', 5)
            
            if current_count >= max_accounts:
                errors.append(f"服務器 {allocation.server_id} 已滿 ({current_count}/{max_accounts})")
                continue
            
            # 更新賬號
            account = db.query(GroupAIAccount).filter(
                GroupAIAccount.account_id == allocation.account_id
            ).first()
            
            if not account:
                errors.append(f"賬號 {allocation.account_id} 不存在")
                continue
            
            account.server_id = allocation.server_id
            allocations[account.account_id] = allocation.server_id
        
        if errors:
            db.rollback()
            raise HTTPException(status_code=400, detail=f"分配失敗: {', '.join(errors)}")
        
        db.commit()
        
        return AllocationResponse(
            success=True,
            message=f"成功分配 {len(allocations)} 個賬號",
            allocations=allocations
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"批量分配失敗: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=f"批量分配失敗: {str(e)}")


@router.get("/summary")
async def get_allocation_summary(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """獲取分配摘要"""
    check_permission(current_user, PermissionCode.ACCOUNT_VIEW.value, db)
    
    try:
        # 加載服務器配置
        from pathlib import Path
        import json
        project_root = Path(__file__).parent.parent.parent.parent.parent
        config_path = project_root / "data" / "master_config.json"
        
        if not config_path.exists():
            raise HTTPException(status_code=404, detail="服務器配置文件不存在")
        
        with open(config_path, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
            servers = config_data.get('servers', {})
        
        summary = {}
        total_accounts = db.query(GroupAIAccount).count()
        unallocated_count = db.query(GroupAIAccount).filter(
            GroupAIAccount.server_id.is_(None)
        ).count()
        
        for server_id, server_config in servers.items():
            count = db.query(GroupAIAccount).filter(
                GroupAIAccount.server_id == server_id
            ).count()
            max_accounts = server_config.get('max_accounts', 5)
            
            summary[server_id] = {
                'current': count,
                'max': max_accounts,
                'available': max_accounts - count,
                'usage_percent': (count / max_accounts * 100) if max_accounts > 0 else 0
            }
        
        return {
            'total_accounts': total_accounts,
            'unallocated': unallocated_count,
            'allocated': total_accounts - unallocated_count,
            'servers': summary
        }
    
    except Exception as e:
        logger.error(f"獲取分配摘要失敗: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"獲取分配摘要失敗: {str(e)}")

