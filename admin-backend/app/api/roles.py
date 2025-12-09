"""
角色管理 API
"""
import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session, selectinload

from app.db import get_db
from app.models.role import Role
from app.models.permission import Permission
from app.crud.role import get_role_by_name
from app.crud.permission import (
    get_permission_by_code,
    get_role_permissions,
    assign_permission_to_role,
    revoke_permission_from_role,
)
from app.api.deps import get_current_active_user
from app.middleware.permission import check_permission
from app.core.permissions import PermissionCode
from app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/roles", tags=["roles"])


# ============ 請求/響應模型 ============

class RoleCreate(BaseModel):
    """創建角色請求"""
    name: str
    description: Optional[str] = None


class RoleUpdate(BaseModel):
    """更新角色請求"""
    name: Optional[str] = None
    description: Optional[str] = None


class RoleResponse(BaseModel):
    """角色響應"""
    id: int
    name: str
    description: Optional[str]
    
    class Config:
        from_attributes = True


class RoleWithPermissionsResponse(RoleResponse):
    """帶權限的角色響應"""
    permissions: List[dict] = []


class RolePermissionAssign(BaseModel):
    """角色權限分配請求"""
    permission_code: str


class RolePermissionRevoke(BaseModel):
    """角色權限撤銷請求"""
    permission_code: str


# ============ API 端點 ============

@router.post("", response_model=RoleResponse, status_code=status.HTTP_201_CREATED)
async def create_role(
    role: RoleCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """創建角色（需要 role:create 權限）"""
    check_permission(current_user, PermissionCode.ROLE_CREATE.value, db)
    
    try:
        from app.crud.user import create_role
        
        # 檢查角色是否已存在
        existing = get_role_by_name(db, name=role.name)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"角色 {role.name} 已存在"
            )
        
        db_role = create_role(db, name=role.name, description=role.description)
        
        return RoleResponse(
            id=db_role.id,
            name=db_role.name,
            description=db_role.description
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"創建角色失敗: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"創建角色失敗: {str(e)}"
        )


@router.get("", response_model=List[RoleResponse])
async def list_roles(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """列出所有角色（需要 role:view 權限）"""
    check_permission(current_user, PermissionCode.ROLE_VIEW.value, db)
    
    try:
        roles = db.query(Role).all()
        return [
            RoleResponse(
                id=r.id,
                name=r.name,
                description=r.description
            )
            for r in roles
        ]
    except Exception as e:
        logger.error(f"列出角色失敗: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"列出角色失敗: {str(e)}"
        )


@router.get("/{role_id}", response_model=RoleWithPermissionsResponse)
async def get_role(
    role_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """獲取角色詳情（需要 role:view 權限）"""
    check_permission(current_user, PermissionCode.ROLE_VIEW.value, db)
    
    try:
        # 使用 selectinload 预加载 permissions，避免 N+1 查询
        role = db.query(Role).options(selectinload(Role.permissions)).filter(Role.id == role_id).first()
        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"角色 {role_id} 不存在"
            )
        
        # 直接使用预加载的 permissions，避免额外查询
        return RoleWithPermissionsResponse(
            id=role.id,
            name=role.name,
            description=role.description,
            permissions=[
                {
                    "id": p.id,
                    "code": p.code,
                    "description": p.description
                }
                for p in role.permissions
            ]
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"獲取角色失敗: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"獲取角色失敗: {str(e)}"
        )


@router.put("/{role_id}", response_model=RoleResponse)
async def update_role(
    role_id: int,
    role_update: RoleUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """更新角色（需要 role:update 權限）"""
    check_permission(current_user, PermissionCode.ROLE_UPDATE.value, db)
    
    try:
        role = db.query(Role).filter(Role.id == role_id).first()
        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"角色 {role_id} 不存在"
            )
        
        if role_update.name is not None:
            # 檢查新名稱是否已被其他角色使用
            existing = get_role_by_name(db, name=role_update.name)
            if existing and existing.id != role_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"角色名稱 {role_update.name} 已被使用"
                )
            role.name = role_update.name
        
        if role_update.description is not None:
            role.description = role_update.description
        
        db.add(role)
        db.commit()
        db.refresh(role)
        
        return RoleResponse(
            id=role.id,
            name=role.name,
            description=role.description
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"更新角色失敗: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新角色失敗: {str(e)}"
        )


@router.delete("/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_role(
    role_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """刪除角色（需要 role:delete 權限）"""
    check_permission(current_user, PermissionCode.ROLE_DELETE.value, db)
    
    try:
        role = db.query(Role).filter(Role.id == role_id).first()
        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"角色 {role_id} 不存在"
            )
        
        # 檢查是否為預定義角色（不能刪除系統預設角色）
        if role.name == "admin":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="不能刪除系統預設的 'admin' 角色，此角色由系統自動創建和管理"
            )
        
        # 檢查是否有用戶正在使用此角色 - 使用 selectinload 预加载，避免 N+1 查询
        users_with_role = db.query(User).options(selectinload(User.roles)).join(User.roles).filter(Role.id == role_id).all()
        if users_with_role:
            user_emails = [u.email for u in users_with_role]
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"不能刪除此角色，因為有 {len(users_with_role)} 個用戶正在使用：{', '.join(user_emails[:3])}{'...' if len(user_emails) > 3 else ''}。請先移除這些用戶的角色分配。"
            )
        
        db.delete(role)
        db.commit()
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"刪除角色失敗: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"刪除角色失敗: {str(e)}"
        )


@router.post("/{role_id}/permissions", status_code=status.HTTP_200_OK)
async def assign_permission_to_role_endpoint(
    role_id: int,
    assign: RolePermissionAssign,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """為角色分配權限（需要 permission:assign 權限）"""
    check_permission(current_user, PermissionCode.PERMISSION_ASSIGN.value, db)
    
    try:
        role = db.query(Role).filter(Role.id == role_id).first()
        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"角色 {role_id} 不存在"
            )
        
        permission = get_permission_by_code(db, code=assign.permission_code)
        if not permission:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"權限 {assign.permission_code} 不存在"
            )
        
        assign_permission_to_role(db, role=role, permission=permission)
        
        return {"message": f"權限 {assign.permission_code} 已分配給角色 {role.name}"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"分配權限失敗: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"分配權限失敗: {str(e)}"
        )


@router.delete("/{role_id}/permissions/{permission_code}", status_code=status.HTTP_200_OK)
async def revoke_permission_from_role_endpoint(
    role_id: int,
    permission_code: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """從角色撤銷權限（需要 permission:assign 權限）"""
    check_permission(current_user, PermissionCode.PERMISSION_ASSIGN.value, db)
    
    try:
        role = db.query(Role).filter(Role.id == role_id).first()
        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"角色 {role_id} 不存在"
            )
        
        permission = get_permission_by_code(db, code=permission_code)
        if not permission:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"權限 {permission_code} 不存在"
            )
        
        revoke_permission_from_role(db, role=role, permission=permission)
        
        return {"message": f"權限 {permission_code} 已從角色 {role.name} 撤銷"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"撤銷權限失敗: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"撤銷權限失敗: {str(e)}"
        )


@router.get("/{role_id}/permissions", response_model=List[dict])
async def get_role_permissions_endpoint(
    role_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """獲取角色的所有權限（需要 role:view 權限）"""
    check_permission(current_user, PermissionCode.ROLE_VIEW.value, db)
    
    try:
        # 使用 selectinload 预加载 permissions，避免 N+1 查询
        role = db.query(Role).options(selectinload(Role.permissions)).filter(Role.id == role_id).first()
        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"角色 {role_id} 不存在"
            )
        
        # 直接使用预加载的 permissions，避免额外查询
        return [
            {
                "id": p.id,
                "code": p.code,
                "description": p.description
            }
            for p in role.permissions
        ]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"獲取角色權限失敗: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"獲取角色權限失敗: {str(e)}"
        )

