"""
權限管理 API
"""
import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.permission import Permission
from app.models.role import Role
from app.crud.permission import (
    get_permission_by_code,
    get_permission_by_id,
    list_permissions,
    create_permission,
    update_permission,
    delete_permission,
    assign_permission_to_role,
    revoke_permission_from_role,
    get_role_permissions,
    get_user_permissions,
    user_has_permission,
)
from app.crud.role import get_role_by_name
from app.api.deps import get_current_active_user
from app.middleware.permission import check_permission
from app.core.permissions import PermissionCode
from app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/permissions", tags=["permissions"])


# ============ 請求/響應模型 ============

class PermissionCreate(BaseModel):
    """創建權限請求"""
    code: str
    description: Optional[str] = None


class PermissionUpdate(BaseModel):
    """更新權限請求"""
    code: Optional[str] = None
    description: Optional[str] = None


class PermissionResponse(BaseModel):
    """權限響應"""
    id: int
    code: str
    description: Optional[str]
    
    class Config:
        from_attributes = True


class RolePermissionAssign(BaseModel):
    """角色權限分配請求"""
    permission_code: str


class UserPermissionCheck(BaseModel):
    """用戶權限檢查請求"""
    permission_code: str


class UserPermissionCheckResponse(BaseModel):
    """用戶權限檢查響應"""
    has_permission: bool
    permission_code: str
    user_email: str


# ============ API 端點 ============

@router.post("", response_model=PermissionResponse, status_code=status.HTTP_201_CREATED)
async def create_permission_endpoint(
    permission: PermissionCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """創建權限（需要權限管理權限）"""
    check_permission(current_user, PermissionCode.PERMISSION_CREATE.value, db)
    
    try:
        db_permission = create_permission(
            db,
            code=permission.code,
            description=permission.description
        )
        return PermissionResponse(
            id=db_permission.id,
            code=db_permission.code,
            description=db_permission.description
        )
    except Exception as e:
        db.rollback()
        logger.error(f"創建權限失敗: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"創建權限失敗: {str(e)}"
        )


@router.get("", response_model=List[PermissionResponse])
async def list_permissions_endpoint(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """列出所有權限（需要權限查看權限）"""
    check_permission(current_user, PermissionCode.PERMISSION_VIEW.value, db)
    
    try:
        permissions = list_permissions(db, skip=skip, limit=limit)
        return [
            PermissionResponse(
                id=p.id,
                code=p.code,
                description=p.description
            )
            for p in permissions
        ]
    except Exception as e:
        logger.error(f"列出權限失敗: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"列出權限失敗: {str(e)}"
        )


@router.get("/{permission_id}", response_model=PermissionResponse)
async def get_permission_endpoint(
    permission_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """獲取權限詳情（需要權限查看權限）"""
    check_permission(current_user, PermissionCode.PERMISSION_VIEW.value, db)
    
    try:
        permission = get_permission_by_id(db, permission_id=permission_id)
        if not permission:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"權限 {permission_id} 不存在"
            )
        
        return PermissionResponse(
            id=permission.id,
            code=permission.code,
            description=permission.description
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"獲取權限失敗: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"獲取權限失敗: {str(e)}"
        )


@router.put("/{permission_id}", response_model=PermissionResponse)
async def update_permission_endpoint(
    permission_id: int,
    permission_update: PermissionUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """更新權限（需要權限更新權限）"""
    check_permission(current_user, PermissionCode.PERMISSION_UPDATE.value, db)
    
    try:
        permission = get_permission_by_id(db, permission_id=permission_id)
        if not permission:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"權限 {permission_id} 不存在"
            )
        
        updated_permission = update_permission(
            db,
            permission=permission,
            code=permission_update.code,
            description=permission_update.description
        )
        
        return PermissionResponse(
            id=updated_permission.id,
            code=updated_permission.code,
            description=updated_permission.description
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"更新權限失敗: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新權限失敗: {str(e)}"
        )


@router.delete("/{permission_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_permission_endpoint(
    permission_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """刪除權限（需要權限刪除權限）"""
    check_permission(current_user, PermissionCode.PERMISSION_DELETE.value, db)
    
    try:
        permission = get_permission_by_id(db, permission_id=permission_id)
        if not permission:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"權限 {permission_id} 不存在"
            )
        
        delete_permission(db, permission=permission)
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"刪除權限失敗: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"刪除權限失敗: {str(e)}"
        )


@router.post("/roles/{role_name}/permissions", status_code=status.HTTP_200_OK)
async def assign_permission_to_role_endpoint(
    role_name: str,
    assign: RolePermissionAssign,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """為角色分配權限（需要權限分配權限）"""
    check_permission(current_user, PermissionCode.PERMISSION_ASSIGN.value, db)
    
    try:
        role = get_role_by_name(db, name=role_name)
        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"角色 {role_name} 不存在"
            )
        
        permission = get_permission_by_code(db, code=assign.permission_code)
        if not permission:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"權限 {assign.permission_code} 不存在"
            )
        
        assign_permission_to_role(db, role=role, permission=permission)
        
        return {"message": f"權限 {assign.permission_code} 已分配給角色 {role_name}"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"分配權限失敗: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"分配權限失敗: {str(e)}"
        )


@router.delete("/roles/{role_name}/permissions/{permission_code}", status_code=status.HTTP_200_OK)
async def revoke_permission_from_role_endpoint(
    role_name: str,
    permission_code: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """從角色撤銷權限（需要權限分配權限）"""
    check_permission(current_user, PermissionCode.PERMISSION_ASSIGN.value, db)
    
    try:
        role = get_role_by_name(db, name=role_name)
        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"角色 {role_name} 不存在"
            )
        
        permission = get_permission_by_code(db, code=permission_code)
        if not permission:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"權限 {permission_code} 不存在"
            )
        
        revoke_permission_from_role(db, role=role, permission=permission)
        
        return {"message": f"權限 {permission_code} 已從角色 {role_name} 撤銷"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"撤銷權限失敗: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"撤銷權限失敗: {str(e)}"
        )


@router.get("/roles/{role_name}/permissions", response_model=List[PermissionResponse])
async def get_role_permissions_endpoint(
    role_name: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """獲取角色的所有權限（需要權限查看權限）"""
    check_permission(current_user, PermissionCode.PERMISSION_VIEW.value, db)
    
    try:
        role = get_role_by_name(db, name=role_name)
        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"角色 {role_name} 不存在"
            )
        
        permissions = get_role_permissions(db, role=role)
        return [
            PermissionResponse(
                id=p.id,
                code=p.code,
                description=p.description
            )
            for p in permissions
        ]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"獲取角色權限失敗: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"獲取角色權限失敗: {str(e)}"
        )


@router.get("/me/permissions", response_model=List[PermissionResponse])
async def get_my_permissions_endpoint(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """獲取當前用戶的所有權限"""
    try:
        # 重新查询用户并预加载 roles 和 permissions，避免 N+1 查询
        from sqlalchemy.orm import selectinload
        from app.models.role import Role
        from app.models.permission import Permission
        
        user = db.query(User).options(
            selectinload(User.roles).selectinload(Role.permissions)
        ).filter(User.id == current_user.id).first()
        
        if not user:
            raise HTTPException(status_code=404, detail="用戶不存在")
        
        permissions = get_user_permissions(db, user=user)
        return [
            PermissionResponse(
                id=p.id,
                code=p.code,
                description=p.description
            )
            for p in permissions
        ]
    except Exception as e:
        logger.error(f"獲取用戶權限失敗: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"獲取用戶權限失敗: {str(e)}"
        )


@router.post("/me/check", response_model=UserPermissionCheckResponse)
async def check_my_permission_endpoint(
    check: UserPermissionCheck,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """檢查當前用戶是否有指定權限"""
    try:
        has_perm = user_has_permission(
            db,
            user=current_user,
            permission_code=check.permission_code
        )
        
        return UserPermissionCheckResponse(
            has_permission=has_perm,
            permission_code=check.permission_code,
            user_email=current_user.email if current_user else "anonymous"
        )
    except Exception as e:
        logger.error(f"檢查權限失敗: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"檢查權限失敗: {str(e)}"
        )


@router.post("/init", status_code=status.HTTP_200_OK)
async def init_permissions_endpoint(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """初始化系統權限（僅超級管理員可執行）"""
    from app.core.config import get_settings
    settings = get_settings()
    
    # 如果禁用認證，允許初始化（開發模式）
    if not settings.disable_auth:
        if not current_user or not current_user.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="僅超級管理員可執行此操作"
            )
    
    try:
        # 創建所有權限
        from app.core.permissions import PermissionCode
        created_count = 0
        
        for permission_code in PermissionCode:
            existing = get_permission_by_code(db, code=permission_code.value)
            if not existing:
                create_permission(
                    db,
                    code=permission_code.value,
                    description=f"權限: {permission_code.value}"
                )
                created_count += 1
        
        # 創建預定義角色並分配權限
        from app.core.permissions import PREDEFINED_ROLES
        from app.crud.user import create_role, assign_role_to_user
        
        role_created_count = 0
        for role_name, role_config in PREDEFINED_ROLES.items():
            role = create_role(db, name=role_name, description=role_config["description"])
            role_created_count += 1
            
            # 為角色分配權限
            for perm_code in role_config["permissions"]:
                permission = get_permission_by_code(db, code=perm_code)
                if permission:
                    assign_permission_to_role(db, role=role, permission=permission)
        
        return {
            "message": "權限初始化完成",
            "permissions_created": created_count,
            "roles_created": role_created_count
        }
    except Exception as e:
        db.rollback()
        logger.error(f"初始化權限失敗: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"初始化權限失敗: {str(e)}"
        )

