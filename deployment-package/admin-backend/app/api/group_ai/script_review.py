"""
劇本審核與發布流程 API
"""
import logging
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.group_ai import GroupAIScript, GroupAIScriptVersion
from app.core.errors import UserFriendlyError
from app.core.cache import invalidate_cache
from app.api.deps import get_optional_user, get_current_active_user
from app.middleware.permission import check_permission
from app.core.permissions import PermissionCode
from app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Group AI Script Review"])

# 劇本狀態定義
SCRIPT_STATUS = {
    "draft": "草稿",
    "reviewing": "審核中",
    "approved": "已審核通過",
    "rejected": "已拒絕",
    "published": "已發布",
    "disabled": "已停用"
}

# 狀態轉換規則
STATUS_TRANSITIONS = {
    "draft": ["reviewing", "disabled"],
    "reviewing": ["approved", "rejected", "draft"],
    "approved": ["published", "draft"],
    "rejected": ["draft", "reviewing"],
    "published": ["disabled", "draft"],
    "disabled": ["draft", "published"]
}


class SubmitReviewRequest(BaseModel):
    """提交審核請求"""
    change_summary: Optional[str] = Field(None, description="變更說明")


class ReviewDecisionRequest(BaseModel):
    """審核決定請求"""
    decision: str = Field(..., description="審核決定：approve 或 reject")
    review_comment: Optional[str] = Field(None, description="審核意見")


class PublishRequest(BaseModel):
    """發布請求"""
    change_summary: Optional[str] = Field(None, description="發布說明")


@router.post("/{script_id}/submit-review", response_model=dict, status_code=status.HTTP_200_OK)
async def submit_review(
    script_id: str,
    request: SubmitReviewRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """提交劇本審核（需要 script:review 權限）"""
    check_permission(current_user, PermissionCode.SCRIPT_REVIEW.value, db)
    try:
        script = db.query(GroupAIScript).filter(
            GroupAIScript.script_id == script_id
        ).first()
        
        if not script:
            raise UserFriendlyError(
                "NOT_FOUND",
                detail=f"劇本 {script_id} 不存在",
                status_code=404
            )
        
        # 檢查當前狀態
        if script.status != "draft":
            raise UserFriendlyError(
                "VALIDATION_ERROR",
                detail=f"只有草稿狀態的劇本可以提交審核，當前狀態：{SCRIPT_STATUS.get(script.status, script.status)}",
                status_code=400
            )
        
        # 更新狀態
        script.status = "reviewing"
        script.updated_at = datetime.utcnow()
        
        # 記錄變更摘要（如果有）
        if request.change_summary:
            # 創建一個版本記錄（審核提交版本）
            version_record = GroupAIScriptVersion(
                script_id=script_id,
                version=script.version,
                yaml_content=script.yaml_content,
                description=script.description,
                change_summary=f"提交審核：{request.change_summary}",
                created_by=current_user.email if current_user else "system"
            )
            db.add(version_record)
        
        db.commit()
        db.refresh(script)
        
        # 清除緩存
        invalidate_cache("scripts_list")
        
        logger.info(f"劇本 {script_id} 已提交審核")
        
        return {
            "script_id": script_id,
            "status": script.status,
            "status_text": SCRIPT_STATUS.get(script.status),
            "message": "劇本已提交審核"
        }
    
    except UserFriendlyError:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"提交審核失敗: {e}", exc_info=True)
        raise UserFriendlyError(
            "INTERNAL_ERROR",
            detail=f"提交審核失敗: {str(e)}",
            technical_detail=str(e),
            status_code=500
        )


@router.post("/{script_id}/review", response_model=dict, status_code=status.HTTP_200_OK)
async def review_script(
    script_id: str,
    request: ReviewDecisionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """審核劇本（需要 script:review 權限）"""
    check_permission(current_user, PermissionCode.SCRIPT_REVIEW.value, db)
    try:
        if request.decision not in ["approve", "reject"]:
            raise UserFriendlyError(
                "VALIDATION_ERROR",
                detail="審核決定必須是 approve 或 reject",
                status_code=400
            )
        
        script = db.query(GroupAIScript).filter(
            GroupAIScript.script_id == script_id
        ).first()
        
        if not script:
            raise UserFriendlyError(
                "NOT_FOUND",
                detail=f"劇本 {script_id} 不存在",
                status_code=404
            )
        
        # 檢查當前狀態
        if script.status != "reviewing":
            raise UserFriendlyError(
                "VALIDATION_ERROR",
                detail=f"只有審核中狀態的劇本可以審核，當前狀態：{SCRIPT_STATUS.get(script.status, script.status)}",
                status_code=400
            )
        
        # 更新狀態
        if request.decision == "approve":
            script.status = "approved"
            status_text = "已審核通過"
        else:
            script.status = "rejected"
            status_text = "已拒絕"
        
        script.reviewed_by = current_user.email if current_user else "system"
        script.reviewed_at = datetime.utcnow()
        script.updated_at = datetime.utcnow()
        
        # 記錄審核意見
        review_comment = request.review_comment or ""
        change_summary = f"審核{status_text}"
        if review_comment:
            change_summary += f"：{review_comment}"
        
        # 創建版本記錄
        version_record = GroupAIScriptVersion(
            script_id=script_id,
            version=script.version,
            yaml_content=script.yaml_content,
            description=script.description,
            change_summary=change_summary,
            created_by=script.reviewed_by
        )
        db.add(version_record)
        
        db.commit()
        db.refresh(script)
        
        # 清除緩存
        invalidate_cache("scripts_list")
        
        logger.info(f"劇本 {script_id} 審核完成：{status_text}")
        
        return {
            "script_id": script_id,
            "status": script.status,
            "status_text": SCRIPT_STATUS.get(script.status),
            "reviewed_by": script.reviewed_by,
            "reviewed_at": script.reviewed_at.isoformat() if script.reviewed_at else None,
            "message": f"劇本{status_text}"
        }
    
    except UserFriendlyError:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"審核劇本失敗: {e}", exc_info=True)
        raise UserFriendlyError(
            "INTERNAL_ERROR",
            detail=f"審核劇本失敗: {str(e)}",
            technical_detail=str(e),
            status_code=500
        )


@router.post("/{script_id}/publish", response_model=dict, status_code=status.HTTP_200_OK)
async def publish_script(
    script_id: str,
    request: PublishRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """發布劇本（需要 script:publish 權限）"""
    check_permission(current_user, PermissionCode.SCRIPT_PUBLISH.value, db)
    try:
        script = db.query(GroupAIScript).filter(
            GroupAIScript.script_id == script_id
        ).first()
        
        if not script:
            raise UserFriendlyError(
                "NOT_FOUND",
                detail=f"劇本 {script_id} 不存在",
                status_code=404
            )
        
        # 檢查當前狀態
        if script.status not in ["approved", "disabled"]:
            raise UserFriendlyError(
                "VALIDATION_ERROR",
                detail=f"只有已審核通過或已停用狀態的劇本可以發布，當前狀態：{SCRIPT_STATUS.get(script.status, script.status)}",
                status_code=400
            )
        
        # 更新狀態
        script.status = "published"
        script.published_at = datetime.utcnow()
        script.updated_at = datetime.utcnow()
        
        # 記錄發布說明
        change_summary = "發布劇本"
        if request.change_summary:
            change_summary += f"：{request.change_summary}"
        
        # 創建版本記錄
        version_record = GroupAIScriptVersion(
            script_id=script_id,
            version=script.version,
            yaml_content=script.yaml_content,
            description=script.description,
            change_summary=change_summary,
            created_by=current_user.email if current_user else "system"
        )
        db.add(version_record)
        
        db.commit()
        db.refresh(script)
        
        # 清除緩存
        invalidate_cache("scripts_list")
        
        logger.info(f"劇本 {script_id} 已發布")
        
        return {
            "script_id": script_id,
            "status": script.status,
            "status_text": SCRIPT_STATUS.get(script.status),
            "published_at": script.published_at.isoformat() if script.published_at else None,
            "message": "劇本已發布"
        }
    
    except UserFriendlyError:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"發布劇本失敗: {e}", exc_info=True)
        raise UserFriendlyError(
            "INTERNAL_ERROR",
            detail=f"發布劇本失敗: {str(e)}",
            technical_detail=str(e),
            status_code=500
        )


@router.post("/{script_id}/disable", response_model=dict, status_code=status.HTTP_200_OK)
async def disable_script(
    script_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """停用劇本（需要 script:disable 權限）"""
    check_permission(current_user, PermissionCode.SCRIPT_DISABLE.value, db)
    try:
        script = db.query(GroupAIScript).filter(
            GroupAIScript.script_id == script_id
        ).first()
        
        if not script:
            raise UserFriendlyError(
                "NOT_FOUND",
                detail=f"劇本 {script_id} 不存在",
                status_code=404
            )
        
        # 更新狀態
        old_status = script.status
        script.status = "disabled"
        script.updated_at = datetime.utcnow()
        
        # 創建版本記錄
        version_record = GroupAIScriptVersion(
            script_id=script_id,
            version=script.version,
            yaml_content=script.yaml_content,
            description=script.description,
            change_summary=f"停用劇本（從 {SCRIPT_STATUS.get(old_status, old_status)} 狀態）",
            created_by=current_user.email if current_user else "system"
        )
        db.add(version_record)
        
        db.commit()
        db.refresh(script)
        
        # 清除緩存
        invalidate_cache("scripts_list")
        
        logger.info(f"劇本 {script_id} 已停用")
        
        return {
            "script_id": script_id,
            "status": script.status,
            "status_text": SCRIPT_STATUS.get(script.status),
            "message": "劇本已停用"
        }
    
    except UserFriendlyError:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"停用劇本失敗: {e}", exc_info=True)
        raise UserFriendlyError(
            "INTERNAL_ERROR",
            detail=f"停用劇本失敗: {str(e)}",
            technical_detail=str(e),
            status_code=500
        )


@router.post("/{script_id}/revert-to-draft", response_model=dict, status_code=status.HTTP_200_OK)
async def revert_to_draft(
    script_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """撤回為草稿（需要 script:review 權限）"""
    check_permission(current_user, PermissionCode.SCRIPT_REVIEW.value, db)
    try:
        script = db.query(GroupAIScript).filter(
            GroupAIScript.script_id == script_id
        ).first()
        
        if not script:
            raise UserFriendlyError(
                "NOT_FOUND",
                detail=f"劇本 {script_id} 不存在",
                status_code=404
            )
        
        # 更新狀態
        old_status = script.status
        script.status = "draft"
        script.updated_at = datetime.utcnow()
        
        # 創建版本記錄
        version_record = GroupAIScriptVersion(
            script_id=script_id,
            version=script.version,
            yaml_content=script.yaml_content,
            description=script.description,
            change_summary=f"撤回為草稿（從 {SCRIPT_STATUS.get(old_status, old_status)} 狀態）",
            created_by=current_user.email if current_user else "system"
        )
        db.add(version_record)
        
        db.commit()
        db.refresh(script)
        
        # 清除緩存
        invalidate_cache("scripts_list")
        
        logger.info(f"劇本 {script_id} 已撤回為草稿")
        
        return {
            "script_id": script_id,
            "status": script.status,
            "status_text": SCRIPT_STATUS.get(script.status),
            "message": "劇本已撤回為草稿"
        }
    
    except UserFriendlyError:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"撤回為草稿失敗: {e}", exc_info=True)
        raise UserFriendlyError(
            "INTERNAL_ERROR",
            detail=f"撤回為草稿失敗: {str(e)}",
            technical_detail=str(e),
            status_code=500
        )

