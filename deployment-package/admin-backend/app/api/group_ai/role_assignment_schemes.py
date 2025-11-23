"""
角色分配方案管理 API
"""
import logging
from typing import List, Optional, Dict
from datetime import datetime
from fastapi import APIRouter, HTTPException, status, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.group_ai import (
    GroupAIRoleAssignmentScheme,
    GroupAIRoleAssignmentHistory,
    GroupAIScript
)
from app.api.deps import get_optional_user, get_current_active_user
from app.middleware.permission import check_permission
from app.core.permissions import PermissionCode
from app.models.user import User
from app.core.errors import UserFriendlyError
from group_ai_service import ServiceManager
from app.api.group_ai.accounts import get_service_manager

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Role Assignment Schemes"])


# ============ 請求/響應模型 ============

class SchemeCreateRequest(BaseModel):
    """創建分配方案請求"""
    name: str = Field(..., description="方案名稱")
    description: Optional[str] = Field(None, description="方案描述")
    script_id: str = Field(..., description="劇本ID")
    assignments: List[Dict] = Field(..., description="分配方案數據: [{role_id, account_id, weight}]")
    mode: str = Field(default="auto", description="分配模式: auto, manual")
    account_ids: List[str] = Field(..., description="參與分配的賬號ID列表")


class SchemeUpdateRequest(BaseModel):
    """更新分配方案請求"""
    name: Optional[str] = Field(None, description="方案名稱")
    description: Optional[str] = Field(None, description="方案描述")
    assignments: Optional[List[Dict]] = Field(None, description="分配方案數據")
    account_ids: Optional[List[str]] = Field(None, description="參與分配的賬號ID列表")


class SchemeResponse(BaseModel):
    """分配方案響應"""
    id: str
    name: str
    description: Optional[str]
    script_id: str
    script_name: Optional[str] = None
    assignments: List[Dict]
    mode: str
    account_ids: List[str]
    created_by: Optional[str]
    created_at: str
    updated_at: str
    
    class Config:
        from_attributes = True


class SchemeListResponse(BaseModel):
    """分配方案列表響應"""
    items: List[SchemeResponse]
    total: int


class ApplySchemeRequest(BaseModel):
    """應用方案請求"""
    account_ids: Optional[List[str]] = Field(None, description="要應用的賬號ID列表（如果為空則應用所有賬號）")


class ApplySchemeResponse(BaseModel):
    """應用方案響應"""
    message: str
    applied_count: int
    history_id: str


class HistoryResponse(BaseModel):
    """歷史記錄響應"""
    id: str
    scheme_id: str
    scheme_name: Optional[str] = None
    script_id: str
    account_id: str
    role_id: str
    applied_by: Optional[str]
    applied_at: str
    extra_data: Dict
    
    class Config:
        from_attributes = True


class HistoryListResponse(BaseModel):
    """歷史記錄列表響應"""
    items: List[HistoryResponse]
    total: int


# ============ API 端點 ============

@router.post("/", response_model=SchemeResponse, status_code=status.HTTP_201_CREATED)
async def create_scheme(
    request: SchemeCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """創建角色分配方案（需要 role_assignment_scheme:create 權限）"""
    check_permission(current_user, PermissionCode.ROLE_ASSIGNMENT_SCHEME_CREATE.value, db)
    try:
        # 驗證劇本是否存在
        script = db.query(GroupAIScript).filter(
            GroupAIScript.script_id == request.script_id
        ).first()
        
        if not script:
            raise UserFriendlyError(
                "SCRIPT_NOT_FOUND",
                detail=f"劇本 {request.script_id} 不存在",
                status_code=404
            )
        
        # 創建方案
        scheme = GroupAIRoleAssignmentScheme(
            name=request.name,
            description=request.description,
            script_id=request.script_id,
            assignments=request.assignments,
            mode=request.mode,
            account_ids=request.account_ids,
            created_by=current_user.email if current_user else "system"
        )
        
        db.add(scheme)
        try:
            # 先 flush 確保數據寫入（但不提交事務）
            db.flush()
            # 然後提交事務
            db.commit()
            # 刷新對象以獲取最新數據（包括自動生成的字段）
            db.refresh(scheme)
            
            logger.info(f"角色分配方案創建成功: {scheme.name} (ID: {scheme.id})")
            
            # 驗證數據是否已保存（使用新的會話確保讀取到最新數據）
            from app.db import SessionLocal as NewSessionLocal
            verify_db = NewSessionLocal()
            try:
                saved_scheme = verify_db.query(GroupAIRoleAssignmentScheme).filter(
                    GroupAIRoleAssignmentScheme.id == scheme.id
                ).first()
                if not saved_scheme:
                    logger.error(f"角色分配方案創建後驗證失敗: {scheme.id} 在數據庫中不存在")
                    raise UserFriendlyError(
                        "INTERNAL_ERROR",
                        detail="角色分配方案保存失敗：數據未正確寫入數據庫",
                        status_code=500
                    )
                logger.info(f"角色分配方案驗證成功: {saved_scheme.id} ({saved_scheme.name}) 已持久化到數據庫")
            finally:
                verify_db.close()
        except UserFriendlyError:
            db.rollback()
            raise
        except Exception as e:
            db.rollback()
            logger.error(f"保存角色分配方案到數據庫失敗: {e}", exc_info=True)
            raise UserFriendlyError(
                "INTERNAL_ERROR",
                detail=f"保存角色分配方案失敗: {str(e)}",
                status_code=500
            )
        
        # 格式化響應
        return SchemeResponse(
            id=scheme.id,
            name=scheme.name,
            description=scheme.description,
            script_id=scheme.script_id,
            script_name=script.name,
            assignments=scheme.assignments,
            mode=scheme.mode,
            account_ids=scheme.account_ids,
            created_by=scheme.created_by,
            created_at=scheme.created_at.isoformat() if scheme.created_at else "",
            updated_at=scheme.updated_at.isoformat() if scheme.updated_at else ""
        )
    
    except UserFriendlyError:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"創建分配方案失敗: {e}", exc_info=True)
        raise UserFriendlyError(
            "INTERNAL_ERROR",
            detail=f"創建分配方案失敗: {str(e)}",
            status_code=500
        )


@router.get("/", response_model=SchemeListResponse)
async def list_schemes(
    script_id: Optional[str] = Query(None, description="按劇本ID過濾"),
    search: Optional[str] = Query(None, description="搜索關鍵詞（方案名稱、描述）"),
    mode: Optional[str] = Query(None, description="分配模式過濾（auto, manual）"),
    sort_by: Optional[str] = Query("created_at", description="排序字段（name, created_at, updated_at）"),
    sort_order: Optional[str] = Query("desc", description="排序順序（asc, desc）"),
    page: int = Query(1, ge=1, description="頁碼"),
    page_size: int = Query(20, ge=1, le=100, description="每頁數量"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """列出所有分配方案（需要 role_assignment_scheme:view 權限）"""
    check_permission(current_user, PermissionCode.ROLE_ASSIGNMENT_SCHEME_VIEW.value, db)
    try:
        query = db.query(GroupAIRoleAssignmentScheme)
        
        # 按劇本ID過濾
        if script_id:
            query = query.filter(GroupAIRoleAssignmentScheme.script_id == script_id)
        
        # 搜索過濾
        if search:
            search_filter = f"%{search}%"
            query = query.filter(
                (GroupAIRoleAssignmentScheme.name.like(search_filter)) |
                (GroupAIRoleAssignmentScheme.description.like(search_filter))
            )
        
        # 分配模式過濾
        if mode:
            query = query.filter(GroupAIRoleAssignmentScheme.mode == mode)
        
        # 排序
        if sort_by == "name":
            order_by = GroupAIRoleAssignmentScheme.name
        elif sort_by == "updated_at":
            order_by = GroupAIRoleAssignmentScheme.updated_at
        else:  # 默認按創建時間
            order_by = GroupAIRoleAssignmentScheme.created_at
        
        if sort_order == "asc":
            query = query.order_by(order_by.asc())
        else:
            query = query.order_by(order_by.desc())
        
        # 總數
        total = query.count()
        
        # 分頁
        offset = (page - 1) * page_size
        schemes = query.offset(offset).limit(page_size).all()
        
        # 獲取劇本名稱
        script_ids = {s.script_id for s in schemes}
        scripts = {s.script_id: s.name for s in db.query(GroupAIScript).filter(
            GroupAIScript.script_id.in_(script_ids)
        ).all()}
        
        # 格式化響應
        items = []
        for scheme in schemes:
            items.append(SchemeResponse(
                id=scheme.id,
                name=scheme.name,
                description=scheme.description,
                script_id=scheme.script_id,
                script_name=scripts.get(scheme.script_id),
                assignments=scheme.assignments,
                mode=scheme.mode,
                account_ids=scheme.account_ids,
                created_by=scheme.created_by,
                created_at=scheme.created_at.isoformat() if scheme.created_at else "",
                updated_at=scheme.updated_at.isoformat() if scheme.updated_at else ""
            ))
        
        return SchemeListResponse(items=items, total=total)
    
    except Exception as e:
        logger.error(f"列出分配方案失敗: {e}", exc_info=True)
        raise UserFriendlyError(
            "INTERNAL_ERROR",
            detail=f"列出分配方案失敗: {str(e)}",
            status_code=500
        )


@router.get("/{scheme_id}", response_model=SchemeResponse)
async def get_scheme(
    scheme_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """獲取分配方案詳情（需要 role_assignment_scheme:view 權限）"""
    check_permission(current_user, PermissionCode.ROLE_ASSIGNMENT_SCHEME_VIEW.value, db)
    try:
        scheme = db.query(GroupAIRoleAssignmentScheme).filter(
            GroupAIRoleAssignmentScheme.id == scheme_id
        ).first()
        
        if not scheme:
            raise UserFriendlyError(
                "SCHEME_NOT_FOUND",
                detail=f"分配方案 {scheme_id} 不存在",
                status_code=404
            )
        
        # 獲取劇本名稱
        script = db.query(GroupAIScript).filter(
            GroupAIScript.script_id == scheme.script_id
        ).first()
        
        return SchemeResponse(
            id=scheme.id,
            name=scheme.name,
            description=scheme.description,
            script_id=scheme.script_id,
            script_name=script.name if script else None,
            assignments=scheme.assignments,
            mode=scheme.mode,
            account_ids=scheme.account_ids,
            created_by=scheme.created_by,
            created_at=scheme.created_at.isoformat() if scheme.created_at else "",
            updated_at=scheme.updated_at.isoformat() if scheme.updated_at else ""
        )
    
    except UserFriendlyError:
        raise
    except Exception as e:
        logger.error(f"獲取分配方案失敗: {e}", exc_info=True)
        raise UserFriendlyError(
            "INTERNAL_ERROR",
            detail=f"獲取分配方案失敗: {str(e)}",
            status_code=500
        )


@router.put("/{scheme_id}", response_model=SchemeResponse)
async def update_scheme(
    scheme_id: str,
    request: SchemeUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """更新分配方案（需要 role_assignment_scheme:update 權限）"""
    check_permission(current_user, PermissionCode.ROLE_ASSIGNMENT_SCHEME_UPDATE.value, db)
    try:
        scheme = db.query(GroupAIRoleAssignmentScheme).filter(
            GroupAIRoleAssignmentScheme.id == scheme_id
        ).first()
        
        if not scheme:
            raise UserFriendlyError(
                "SCHEME_NOT_FOUND",
                detail=f"分配方案 {scheme_id} 不存在",
                status_code=404
            )
        
        # 更新字段
        if request.name is not None:
            scheme.name = request.name
        if request.description is not None:
            scheme.description = request.description
        if request.assignments is not None:
            scheme.assignments = request.assignments
        if request.account_ids is not None:
            scheme.account_ids = request.account_ids
        
        scheme.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(scheme)
        
        # 獲取劇本名稱
        script = db.query(GroupAIScript).filter(
            GroupAIScript.script_id == scheme.script_id
        ).first()
        
        return SchemeResponse(
            id=scheme.id,
            name=scheme.name,
            description=scheme.description,
            script_id=scheme.script_id,
            script_name=script.name if script else None,
            assignments=scheme.assignments,
            mode=scheme.mode,
            account_ids=scheme.account_ids,
            created_by=scheme.created_by,
            created_at=scheme.created_at.isoformat() if scheme.created_at else "",
            updated_at=scheme.updated_at.isoformat() if scheme.updated_at else ""
        )
    
    except UserFriendlyError:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"更新分配方案失敗: {e}", exc_info=True)
        raise UserFriendlyError(
            "INTERNAL_ERROR",
            detail=f"更新分配方案失敗: {str(e)}",
            status_code=500
        )


@router.delete("/{scheme_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_scheme(
    scheme_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """刪除分配方案（需要 role_assignment_scheme:delete 權限）"""
    check_permission(current_user, PermissionCode.ROLE_ASSIGNMENT_SCHEME_DELETE.value, db)
    try:
        scheme = db.query(GroupAIRoleAssignmentScheme).filter(
            GroupAIRoleAssignmentScheme.id == scheme_id
        ).first()
        
        if not scheme:
            raise UserFriendlyError(
                "SCHEME_NOT_FOUND",
                detail=f"分配方案 {scheme_id} 不存在",
                status_code=404
            )
        
        # 刪除相關的歷史記錄
        db.query(GroupAIRoleAssignmentHistory).filter(
            GroupAIRoleAssignmentHistory.scheme_id == scheme_id
        ).delete()
        
        # 刪除方案
        db.delete(scheme)
        db.commit()
        
        return None
    
    except UserFriendlyError:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"刪除分配方案失敗: {e}", exc_info=True)
        raise UserFriendlyError(
            "INTERNAL_ERROR",
            detail=f"刪除分配方案失敗: {str(e)}",
            status_code=500
        )


@router.post("/{scheme_id}/apply", response_model=ApplySchemeResponse)
async def apply_scheme(
    scheme_id: str,
    request: ApplySchemeRequest,
    db: Session = Depends(get_db),
    service_manager: ServiceManager = Depends(get_service_manager),
    current_user: User = Depends(get_current_active_user)
):
    """應用分配方案（需要 role_assignment_scheme:apply 權限）"""
    check_permission(current_user, PermissionCode.ROLE_ASSIGNMENT_SCHEME_APPLY.value, db)
    try:
        # 獲取方案
        scheme = db.query(GroupAIRoleAssignmentScheme).filter(
            GroupAIRoleAssignmentScheme.id == scheme_id
        ).first()
        
        if not scheme:
            raise UserFriendlyError(
                "SCHEME_NOT_FOUND",
                detail=f"分配方案 {scheme_id} 不存在",
                status_code=404
            )
        
        # 確定要應用的賬號列表
        account_ids_to_apply = request.account_ids if request.account_ids else scheme.account_ids
        
        applied_count = 0
        history_records = []
        
        # 構建分配映射 {account_id: role_id}
        assignment_map = {a.get('account_id'): a.get('role_id') for a in scheme.assignments if 'account_id' in a and 'role_id' in a}
        
        # 應用分配
        for account_id in account_ids_to_apply:
            if account_id not in service_manager.account_manager.accounts:
                logger.warning(f"賬號 {account_id} 不存在，跳過")
                continue
            
            role_id = assignment_map.get(account_id)
            if not role_id:
                logger.warning(f"賬號 {account_id} 在方案中沒有分配角色，跳過")
                continue
            
            account = service_manager.account_manager.accounts[account_id]
            
            # 更新賬號配置
            if not hasattr(account.config, 'metadata'):
                account.config.metadata = {}
            
            account.config.metadata['assigned_role_id'] = role_id
            account.config.metadata['script_id'] = scheme.script_id
            
            # 創建歷史記錄
            history = GroupAIRoleAssignmentHistory(
                scheme_id=scheme_id,
                script_id=scheme.script_id,
                account_id=account_id,
                role_id=role_id,
                applied_by=current_user.email if current_user else "system",
                extra_data={
                    'weight': next((a.get('weight') for a in scheme.assignments if a.get('account_id') == account_id), None)
                }
            )
            history_records.append(history)
            
            applied_count += 1
            logger.info(f"已為賬號 {account_id} 分配角色 {role_id}")
        
        # 保存歷史記錄
        if history_records:
            db.add_all(history_records)
            db.commit()
            history_id = history_records[0].id if len(history_records) == 1 else "multiple"
        else:
            history_id = "none"
        
        return ApplySchemeResponse(
            message=f"成功應用分配方案，已更新 {applied_count} 個賬號",
            applied_count=applied_count,
            history_id=history_id
        )
    
    except UserFriendlyError:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"應用分配方案失敗: {e}", exc_info=True)
        raise UserFriendlyError(
            "INTERNAL_ERROR",
            detail=f"應用分配方案失敗: {str(e)}",
            status_code=500
        )


@router.get("/{scheme_id}/history", response_model=HistoryListResponse)
async def get_scheme_history(
    scheme_id: str,
    page: int = Query(1, ge=1, description="頁碼"),
    page_size: int = Query(20, ge=1, le=100, description="每頁數量"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """獲取分配方案歷史（需要 role_assignment_scheme:view 權限）"""
    check_permission(current_user, PermissionCode.ROLE_ASSIGNMENT_SCHEME_VIEW.value, db)
    try:
        # 驗證方案是否存在
        scheme = db.query(GroupAIRoleAssignmentScheme).filter(
            GroupAIRoleAssignmentScheme.id == scheme_id
        ).first()
        
        if not scheme:
            raise UserFriendlyError(
                "SCHEME_NOT_FOUND",
                detail=f"分配方案 {scheme_id} 不存在",
                status_code=404
            )
        
        # 查詢歷史記錄
        query = db.query(GroupAIRoleAssignmentHistory).filter(
            GroupAIRoleAssignmentHistory.scheme_id == scheme_id
        )
        
        total = query.count()
        
        # 分頁
        offset = (page - 1) * page_size
        histories = query.order_by(GroupAIRoleAssignmentHistory.applied_at.desc()).offset(offset).limit(page_size).all()
        
        # 格式化響應
        items = []
        for history in histories:
            items.append(HistoryResponse(
                id=history.id,
                scheme_id=history.scheme_id,
                scheme_name=scheme.name,
                script_id=history.script_id,
                account_id=history.account_id,
                role_id=history.role_id,
                applied_by=history.applied_by,
                applied_at=history.applied_at.isoformat() if history.applied_at else "",
                extra_data=history.extra_data or {}
            ))
        
        return HistoryListResponse(items=items, total=total)
    
    except UserFriendlyError:
        raise
    except Exception as e:
        logger.error(f"獲取應用歷史失敗: {e}", exc_info=True)
        raise UserFriendlyError(
            "INTERNAL_ERROR",
            detail=f"獲取應用歷史失敗: {str(e)}",
            status_code=500
        )

