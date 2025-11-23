"""
權限 CRUD 操作
"""
from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.permission import Permission
from app.models.role import Role


def get_permission_by_code(db: Session, *, code: str) -> Optional[Permission]:
    """根據權限代碼獲取權限"""
    return db.query(Permission).filter(Permission.code == code).first()


def get_permission_by_id(db: Session, *, permission_id: int) -> Optional[Permission]:
    """根據ID獲取權限"""
    return db.query(Permission).filter(Permission.id == permission_id).first()


def list_permissions(db: Session, *, skip: int = 0, limit: int = 100) -> List[Permission]:
    """列出所有權限"""
    return db.query(Permission).offset(skip).limit(limit).all()


def create_permission(
    db: Session,
    *,
    code: str,
    description: Optional[str] = None
) -> Permission:
    """創建權限"""
    permission = get_permission_by_code(db, code=code)
    if permission:
        return permission
    
    permission = Permission(code=code, description=description)
    db.add(permission)
    db.commit()
    db.refresh(permission)
    return permission


def update_permission(
    db: Session,
    *,
    permission: Permission,
    code: Optional[str] = None,
    description: Optional[str] = None
) -> Permission:
    """更新權限"""
    if code is not None:
        permission.code = code
    if description is not None:
        permission.description = description
    db.add(permission)
    db.commit()
    db.refresh(permission)
    return permission


def delete_permission(db: Session, *, permission: Permission) -> None:
    """刪除權限"""
    db.delete(permission)
    db.commit()


def assign_permission_to_role(db: Session, *, role: Role, permission: Permission) -> None:
    """為角色分配權限"""
    if permission not in role.permissions:
        role.permissions.append(permission)
        db.add(role)
        db.commit()
        db.refresh(role)


def revoke_permission_from_role(db: Session, *, role: Role, permission: Permission) -> None:
    """從角色撤銷權限"""
    if permission in role.permissions:
        role.permissions.remove(permission)
        db.add(role)
        db.commit()
        db.refresh(role)


def get_role_permissions(db: Session, *, role: Role) -> List[Permission]:
    """獲取角色的所有權限"""
    return role.permissions


def get_user_permissions(db: Session, *, user) -> List[Permission]:
    """獲取用戶的所有權限（通過角色）"""
    from app.models.user import User
    from app.core.config import get_settings
    
    # 如果禁用認證，返回所有權限（開發模式）
    settings = get_settings()
    if settings.disable_auth:
        # 返回所有權限，表示擁有所有權限
        return list_permissions(db, skip=0, limit=10000)
    
    if not isinstance(user, User):
        return []
    
    permissions = set()
    for role in user.roles:
        for permission in role.permissions:
            permissions.add(permission)
    
    return list(permissions)


def user_has_permission(db: Session, *, user, permission_code: str) -> bool:
    """檢查用戶是否有指定權限"""
    from app.models.user import User
    from app.core.config import get_settings
    
    # 如果禁用認證，允許所有操作（開發模式）
    settings = get_settings()
    if settings.disable_auth:
        return True
    
    if not isinstance(user, User):
        return False
    
    # 超級管理員擁有所有權限
    if user.is_superuser:
        return True
    
    # 檢查用戶的角色是否擁有該權限
    user_permissions = get_user_permissions(db, user=user)
    for permission in user_permissions:
        if permission.code == permission_code:
            return True
    
    return False


def user_has_any_permission(db: Session, *, user, permission_codes: List[str]) -> bool:
    """檢查用戶是否有任意一個指定權限"""
    for code in permission_codes:
        if user_has_permission(db, user=user, permission_code=code):
            return True
    return False


def user_has_all_permissions(db: Session, *, user, permission_codes: List[str]) -> bool:
    """檢查用戶是否有所有指定權限"""
    for code in permission_codes:
        if not user_has_permission(db, user=user, permission_code=code):
            return False
    return True

