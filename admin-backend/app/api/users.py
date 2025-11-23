import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user, get_db_session, require_superuser
from app.models.user import User
from app.schemas.user import UserRead, UserCreate, UserUpdate, UserPasswordReset
from app.crud.user import (
    create_user,
    get_user_by_id,
    get_user_by_email,
    update_user,
    update_user_password,
    delete_user,
)
from app.middleware.permission import check_permission
from app.core.permissions import PermissionCode
from app.utils.audit import log_audit
from fastapi import Request

logger = logging.getLogger(__name__)

# 注意：user_roles.py 中的路由使用相同的 prefix="/users"，所以这里使用不同的 tags
router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserRead)
def read_current_user(current_user=Depends(get_current_active_user)):
    """獲取當前用戶信息"""
    from app.core.config import get_settings
    settings = get_settings()
    
    # 如果禁用認證，返回一個默認的匿名用戶對象
    if settings.disable_auth or current_user is None:
        # 嘗試獲取默認管理員用戶
        from app.crud.user import get_user_by_email
        from app.db import SessionLocal
        from app.models.user import User
        
        db = SessionLocal()
        try:
            admin = get_user_by_email(db, email=settings.admin_default_email)
            if admin:
                return admin
        except Exception as e:
            # 如果數據庫操作失敗（例如表不存在），返回臨時用戶對象
            logger.warning(f"獲取用戶失敗: {e}")
        finally:
            db.close()
        
        # 如果沒有找到，創建一個臨時用戶對象（不保存到數據庫）
        temp_user = User(
            id=0,
            email="anonymous@example.com",
            full_name="匿名用戶",
            hashed_password="",
            is_active=True,
            is_superuser=False,
        )
        return temp_user
    
    return current_user


# 预留超级用户接口
@router.get("/", response_model=List[UserRead], dependencies=[Depends(require_superuser)])
def list_users(db: Session = Depends(get_db_session)):
    return db.query(User).all()


@router.post("/", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def create_user_endpoint(
    user_create: UserCreate,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db_session)
):
    """創建新用戶（需要 user:create 權限）"""
    check_permission(current_user, PermissionCode.USER_CREATE.value, db)
    
    try:
        # 檢查郵箱是否已存在
        existing_user = get_user_by_email(db, email=user_create.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"郵箱 {user_create.email} 已被使用"
            )
        
        user = create_user(
            db,
            email=user_create.email,
            password=user_create.password,
            full_name=user_create.full_name,
            is_superuser=user_create.is_superuser,
        )
        user.is_active = user_create.is_active
        db.add(user)
        db.commit()
        db.refresh(user)
        
        # 記錄審計日誌
        log_audit(
            db,
            user=current_user,
            action="create",
            resource_type="user",
            resource_id=str(user.id),
            description=f"創建用戶: {user.email}",
            after_state={
                "email": user.email,
                "full_name": user.full_name,
                "is_active": user.is_active,
                "is_superuser": user.is_superuser,
            },
            request=request,
        )
        
        return user
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"創建用戶失敗: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"創建用戶失敗: {str(e)}"
        )


@router.put("/{user_id}", response_model=UserRead)
async def update_user_endpoint(
    user_id: int,
    user_update: UserUpdate,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db_session)
):
    """更新用戶信息（需要 user:update 權限）"""
    check_permission(current_user, PermissionCode.USER_UPDATE.value, db)
    
    try:
        user = get_user_by_id(db, user_id=user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"用戶 {user_id} 不存在"
            )
        
        # 如果更新郵箱，檢查是否已被使用
        if user_update.email and user_update.email != user.email:
            existing_user = get_user_by_email(db, email=user_update.email)
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"郵箱 {user_update.email} 已被使用"
                )
        
        # 記錄更新前狀態
        before_state = {
            "email": user.email,
            "full_name": user.full_name,
            "is_active": user.is_active,
            "is_superuser": user.is_superuser,
        }
        
        updated_user = update_user(
            db,
            user=user,
            email=user_update.email,
            full_name=user_update.full_name,
            is_active=user_update.is_active,
            is_superuser=user_update.is_superuser,
        )
        
        # 記錄審計日誌
        log_audit(
            db,
            user=current_user,
            action="update",
            resource_type="user",
            resource_id=str(user_id),
            description=f"更新用戶: {updated_user.email}",
            before_state=before_state,
            after_state={
                "email": updated_user.email,
                "full_name": updated_user.full_name,
                "is_active": updated_user.is_active,
                "is_superuser": updated_user.is_superuser,
            },
            request=request,
        )
        
        return updated_user
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"更新用戶失敗: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新用戶失敗: {str(e)}"
        )


@router.delete("/{user_id}", status_code=status.HTTP_200_OK)
async def delete_user_endpoint(
    user_id: int,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db_session)
):
    """刪除用戶（需要 user:delete 權限）"""
    check_permission(current_user, PermissionCode.USER_DELETE.value, db)
    
    try:
        # 不能刪除自己（如果 current_user 存在）
        if current_user and user_id == current_user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="不能刪除自己的賬號"
            )
        
        user = get_user_by_id(db, user_id=user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"用戶 {user_id} 不存在"
            )
        
        # 記錄刪除前狀態
        before_state = {
            "email": user.email,
            "full_name": user.full_name,
            "is_active": user.is_active,
            "is_superuser": user.is_superuser,
        }
        
        success = delete_user(db, user_id=user_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="刪除用戶失敗"
            )
        
        # 記錄審計日誌
        log_audit(
            db,
            user=current_user,
            action="delete",
            resource_type="user",
            resource_id=str(user_id),
            description=f"刪除用戶: {user.email}",
            before_state=before_state,
            request=request,
        )
        
        return {"message": f"用戶 {user.email} 已刪除"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"刪除用戶失敗: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"刪除用戶失敗: {str(e)}"
        )


@router.post("/{user_id}/reset-password", status_code=status.HTTP_200_OK)
async def reset_user_password_endpoint(
    user_id: int,
    password_reset: UserPasswordReset,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db_session)
):
    """重置用戶密碼（需要 user:update 權限）"""
    check_permission(current_user, PermissionCode.USER_UPDATE.value, db)
    
    try:
        user = get_user_by_id(db, user_id=user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"用戶 {user_id} 不存在"
            )
        
        update_user_password(db, user=user, new_password=password_reset.new_password)
        
        # 記錄審計日誌
        log_audit(
            db,
            user=current_user,
            action="reset_password",
            resource_type="user",
            resource_id=str(user_id),
            description=f"重置用戶密碼: {user.email}",
            request=request,
        )
        
        return {"message": f"用戶 {user.email} 的密碼已重置"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"重置密碼失敗: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"重置密碼失敗: {str(e)}"
        )

