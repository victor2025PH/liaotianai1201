"""
用戶角色管理 API
"""
import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.user import User
from app.models.role import Role
from app.crud.user import get_user_by_email, assign_role_to_user
from app.crud.role import get_role_by_name
from app.api.deps import get_current_active_user
from app.middleware.permission import check_permission
from app.core.permissions import PermissionCode
from app.utils.audit import log_audit
from fastapi import Request

logger = logging.getLogger(__name__)

# 注意：这个路由与 users.py 共享相同的 prefix，但使用不同的 tags
# 为了避免冲突，我们使用不同的路径前缀
router = APIRouter(prefix="/user-roles", tags=["user-roles"])


# ============ 請求/響應模型 ============

class UserRoleAssign(BaseModel):
    """用戶角色分配請求"""
    role_name: str


class UserRoleRevoke(BaseModel):
    """用戶角色撤銷請求"""
    role_name: str


class BatchRoleAssign(BaseModel):
    """批量角色分配請求"""
    user_ids: List[int]
    role_name: str


class BatchRoleRevoke(BaseModel):
    """批量角色撤銷請求"""
    user_ids: List[int]
    role_name: str


class BatchOperationResult(BaseModel):
    """批量操作結果"""
    success_count: int
    failed_count: int
    errors: List[str] = []


class UserWithRolesResponse(BaseModel):
    """帶角色的用戶響應"""
    id: int
    email: str
    full_name: Optional[str]
    is_active: bool
    is_superuser: bool
    roles: List[dict] = []
    
    class Config:
        from_attributes = True


# ============ API 端點 ============

@router.get("/users", response_model=List[UserWithRolesResponse])
async def list_users(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """列出所有用戶及其角色（需要 user:view 權限）"""
    check_permission(current_user, PermissionCode.USER_VIEW.value, db)
    
    try:
        users = db.query(User).all()
        return [
            UserWithRolesResponse(
                id=u.id,
                email=u.email,
                full_name=u.full_name,
                is_active=u.is_active,
                is_superuser=u.is_superuser,
                roles=[
                    {
                        "id": r.id,
                        "name": r.name,
                        "description": r.description
                    }
                    for r in u.roles
                ]
            )
            for u in users
        ]
    except Exception as e:
        logger.error(f"列出用戶失敗: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"列出用戶失敗: {str(e)}"
        )


@router.get("/users/{user_id}", response_model=UserWithRolesResponse)
async def get_user(
    user_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """獲取用戶詳情（需要 user:view 權限）"""
    check_permission(current_user, PermissionCode.USER_VIEW.value, db)
    
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"用戶 {user_id} 不存在"
            )
        
        return UserWithRolesResponse(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            is_active=user.is_active,
            is_superuser=user.is_superuser,
            roles=[
                {
                    "id": r.id,
                    "name": r.name,
                    "description": r.description
                }
                for r in user.roles
            ]
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"獲取用戶失敗: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"獲取用戶失敗: {str(e)}"
        )


@router.post("/users/{user_id}/roles", status_code=status.HTTP_200_OK)
async def assign_role_to_user_endpoint(
    user_id: int,
    assign: UserRoleAssign,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """為用戶分配角色（需要 user:role:assign 權限）"""
    check_permission(current_user, PermissionCode.USER_ROLE_ASSIGN.value, db)
    
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"用戶 {user_id} 不存在"
            )
        
        role = get_role_by_name(db, name=assign.role_name)
        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"角色 {assign.role_name} 不存在"
            )
        
        assign_role_to_user(db, user=user, role=role)
        
        return {"message": f"角色 {assign.role_name} 已分配給用戶 {user.email}"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"分配角色失敗: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"分配角色失敗: {str(e)}"
        )


@router.delete("/users/{user_id}/roles/{role_name}", status_code=status.HTTP_200_OK)
async def revoke_role_from_user_endpoint(
    user_id: int,
    role_name: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """從用戶撤銷角色（需要 user:role:assign 權限）"""
    check_permission(current_user, PermissionCode.USER_ROLE_ASSIGN.value, db)
    
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"用戶 {user_id} 不存在"
            )
        
        role = get_role_by_name(db, name=role_name)
        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"角色 {role_name} 不存在"
            )
        
        if role not in user.roles:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"用戶 {user.email} 沒有角色 {role_name}"
            )
        
        user.roles.remove(role)
        db.add(user)
        db.commit()
        db.refresh(user)
        
        return {"message": f"角色 {role_name} 已從用戶 {user.email} 撤銷"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"撤銷角色失敗: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"撤銷角色失敗: {str(e)}"
        )


@router.get("/users/{user_id}/roles", response_model=List[dict])
async def get_user_roles_endpoint(
    user_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """獲取用戶的所有角色（需要 user:view 權限）"""
    check_permission(current_user, PermissionCode.USER_VIEW.value, db)
    
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"用戶 {user_id} 不存在"
            )
        
        return [
            {
                "id": r.id,
                "name": r.name,
                "description": r.description
            }
            for r in user.roles
        ]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"獲取用戶角色失敗: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"獲取用戶角色失敗: {str(e)}"
        )


@router.post("/batch-assign", response_model=BatchOperationResult, status_code=status.HTTP_200_OK)
async def batch_assign_role(
    batch: BatchRoleAssign,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """批量為用戶分配角色（需要 user:role:assign 權限）"""
    check_permission(current_user, PermissionCode.USER_ROLE_ASSIGN.value, db)
    
    if not batch.user_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用戶 ID 列表不能為空"
        )
    
    if not batch.role_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="角色名稱不能為空"
        )
    
    try:
        # 驗證角色是否存在
        role = get_role_by_name(db, name=batch.role_name)
        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"角色 {batch.role_name} 不存在"
            )
        
        success_count = 0
        failed_count = 0
        errors = []
        
        # 批量分配角色
        for user_id in batch.user_ids:
            try:
                user = db.query(User).filter(User.id == user_id).first()
                if not user:
                    failed_count += 1
                    errors.append(f"用戶 {user_id} 不存在")
                    continue
                
                # 檢查用戶是否已經有該角色
                if role in user.roles:
                    failed_count += 1
                    errors.append(f"用戶 {user.email} 已經擁有角色 {batch.role_name}")
                    continue
                
                assign_role_to_user(db, user=user, role=role)
                success_count += 1
            except Exception as e:
                failed_count += 1
                errors.append(f"為用戶 {user_id} 分配角色失敗: {str(e)}")
                logger.error(f"批量分配角色失敗 (用戶 {user_id}): {e}", exc_info=True)
        
        db.commit()
        
        return BatchOperationResult(
            success_count=success_count,
            failed_count=failed_count,
            errors=errors
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"批量分配角色失敗: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"批量分配角色失敗: {str(e)}"
        )


@router.post("/batch-revoke", response_model=BatchOperationResult, status_code=status.HTTP_200_OK)
async def batch_revoke_role(
    batch: BatchRoleRevoke,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """批量從用戶撤銷角色（需要 user:role:assign 權限）"""
    check_permission(current_user, PermissionCode.USER_ROLE_ASSIGN.value, db)
    
    if not batch.user_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用戶 ID 列表不能為空"
        )
    
    if not batch.role_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="角色名稱不能為空"
        )
    
    try:
        # 驗證角色是否存在
        role = get_role_by_name(db, name=batch.role_name)
        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"角色 {batch.role_name} 不存在"
            )
        
        success_count = 0
        failed_count = 0
        errors = []
        
        # 批量撤銷角色
        for user_id in batch.user_ids:
            try:
                user = db.query(User).filter(User.id == user_id).first()
                if not user:
                    failed_count += 1
                    errors.append(f"用戶 {user_id} 不存在")
                    continue
                
                # 檢查用戶是否有該角色
                if role not in user.roles:
                    failed_count += 1
                    errors.append(f"用戶 {user.email} 沒有角色 {batch.role_name}")
                    continue
                
                user.roles.remove(role)
                db.add(user)
                success_count += 1
            except Exception as e:
                failed_count += 1
                errors.append(f"從用戶 {user_id} 撤銷角色失敗: {str(e)}")
                logger.error(f"批量撤銷角色失敗 (用戶 {user_id}): {e}", exc_info=True)
        
        db.commit()
        
        return BatchOperationResult(
            success_count=success_count,
            failed_count=failed_count,
            errors=errors
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"批量撤銷角色失敗: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"批量撤銷角色失敗: {str(e)}"
        )

