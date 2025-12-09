"""
自動化任務管理 API
"""
import logging
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.group_ai import GroupAIAutomationTask, GroupAIAutomationTaskLog
from app.api.deps import get_current_active_user
from app.middleware.permission import check_permission
from app.core.permissions import PermissionCode
from app.models.user import User
from app.core.cache import cached, invalidate_cache

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Automation Tasks"])


# ============ 請求/響應模型 ============

class AutomationTaskCreate(BaseModel):
    """創建自動化任務請求"""
    name: str
    description: Optional[str] = None
    task_type: str  # scheduled, triggered, manual
    task_action: str  # account_start, account_stop, script_publish, alert_check, etc.
    schedule_config: Optional[dict] = None  # cron表達式或間隔配置
    trigger_config: Optional[dict] = None  # 觸發條件配置
    action_config: dict = {}  # 任務執行參數
    enabled: bool = True
    dependent_tasks: Optional[List[str]] = []  # 依賴的任務ID列表
    notify_on_success: bool = False  # 成功時通知
    notify_on_failure: bool = True  # 失敗時通知
    notify_recipients: Optional[List[str]] = []  # 通知接收人列表


class AutomationTaskUpdate(BaseModel):
    """更新自動化任務請求"""
    name: Optional[str] = None
    description: Optional[str] = None
    schedule_config: Optional[dict] = None
    trigger_config: Optional[dict] = None
    action_config: Optional[dict] = None
    enabled: Optional[bool] = None
    dependent_tasks: Optional[List[str]] = None  # 依賴的任務ID列表
    notify_on_success: Optional[bool] = None  # 成功時通知
    notify_on_failure: Optional[bool] = None  # 失敗時通知
    notify_recipients: Optional[List[str]] = None  # 通知接收人列表


class AutomationTaskResponse(BaseModel):
    """自動化任務響應"""
    id: str
    name: str
    description: Optional[str]
    task_type: str
    task_action: str
    schedule_config: Optional[dict]
    trigger_config: Optional[dict]
    action_config: dict
    enabled: bool
    last_run_at: Optional[str]
    next_run_at: Optional[str]
    run_count: int
    success_count: int
    failure_count: int
    last_result: Optional[str]
    created_at: str
    updated_at: str
    created_by: Optional[str]
    dependent_tasks: Optional[List[str]] = []
    notify_on_success: bool = False
    notify_on_failure: bool = True
    notify_recipients: Optional[List[str]] = []
    
    class Config:
        from_attributes = True


class TaskLogResponse(BaseModel):
    """任務執行日誌響應"""
    id: str
    task_id: str
    status: str
    started_at: str
    completed_at: Optional[str]
    duration_seconds: Optional[float]
    result: Optional[str]
    error_message: Optional[str]
    execution_data: Optional[dict]
    
    class Config:
        from_attributes = True


# ============ API 端點 ============

@router.post("", response_model=AutomationTaskResponse, status_code=status.HTTP_201_CREATED)
async def create_automation_task(
    task: AutomationTaskCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """創建自動化任務（需要 automation_task:create 權限）"""
    check_permission(current_user, PermissionCode.AUTOMATION_TASK_CREATE.value, db)
    try:
        db_task = GroupAIAutomationTask(
            name=task.name,
            description=task.description,
            task_type=task.task_type,
            task_action=task.task_action,
            schedule_config=task.schedule_config,
            trigger_config=task.trigger_config,
            action_config=task.action_config,
            enabled=task.enabled,
            dependent_tasks=task.dependent_tasks or [],
            notify_on_success=task.notify_on_success,
            notify_on_failure=task.notify_on_failure,
            notify_recipients=task.notify_recipients or [],
            created_by=current_user.email
        )
        db.add(db_task)
        # 先 flush 確保數據寫入
        db.flush()
        # 然後提交事務
        db.commit()
        # 刷新對象以獲取最新數據
        db.refresh(db_task)
        
        # 驗證數據是否已保存（使用新的會話確保讀取到最新數據）
        from app.db import SessionLocal as NewSessionLocal
        verify_db = NewSessionLocal()
        try:
            saved_task = verify_db.query(GroupAIAutomationTask).filter(
                GroupAIAutomationTask.id == db_task.id
            ).first()
            if not saved_task:
                logger.error(f"任務創建後驗證失敗: {db_task.id} 在數據庫中不存在")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="任務保存失敗：數據未正確寫入數據庫"
                )
            logger.info(f"任務驗證成功: {saved_task.id} ({saved_task.name}) 已持久化到數據庫")
        finally:
            verify_db.close()
        
        # 如果是定時任務且已啟用，添加到調度器
        if db_task.task_type == "scheduled" and db_task.enabled:
            from app.services.task_scheduler import get_task_scheduler
            scheduler = get_task_scheduler()
            if scheduler.is_running:
                try:
                    scheduler.schedule_task(db_task)
                    logger.info(f"任務 {db_task.name} ({db_task.id}) 已添加到調度器")
                except Exception as e:
                    logger.error(f"添加任務到調度器失敗: {e}", exc_info=True)
        
        return AutomationTaskResponse(
            id=db_task.id,
            name=db_task.name,
            description=db_task.description,
            task_type=db_task.task_type,
            task_action=db_task.task_action,
            schedule_config=db_task.schedule_config,
            trigger_config=db_task.trigger_config,
            action_config=db_task.action_config,
            enabled=db_task.enabled,
            last_run_at=db_task.last_run_at.isoformat() if db_task.last_run_at else None,
            next_run_at=db_task.next_run_at.isoformat() if db_task.next_run_at else None,
            run_count=db_task.run_count,
            success_count=db_task.success_count,
            failure_count=db_task.failure_count,
            last_result=db_task.last_result,
            created_at=db_task.created_at.isoformat(),
            updated_at=db_task.updated_at.isoformat(),
            created_by=db_task.created_by,
            dependent_tasks=db_task.dependent_tasks or [],
            notify_on_success=db_task.notify_on_success,
            notify_on_failure=db_task.notify_on_failure,
            notify_recipients=db_task.notify_recipients or []
        )
    except Exception as e:
        db.rollback()
        logger.error(f"創建自動化任務失敗: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"創建自動化任務失敗: {str(e)}"
        )


@router.get("", response_model=List[AutomationTaskResponse])
@cached(prefix="automation_tasks_list", ttl=60)  # 緩存 60 秒
async def list_automation_tasks(
    page: int = Query(1, ge=1, description="頁碼"),
    page_size: int = Query(20, ge=1, le=100, description="每頁數量"),
    task_type: Optional[str] = Query(None, description="任務類型過濾"),
    enabled: Optional[bool] = Query(None, description="是否啟用過濾"),
    _t: Optional[int] = Query(None, description="強制刷新時間戳（繞過緩存）"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """列出自動化任務（需要 automation_task:view 權限，帶緩存）"""
    # 如果提供了強制刷新時間戳，清除緩存
    if _t is not None:
        invalidate_cache("automation_tasks_list:*")
    check_permission(current_user, PermissionCode.AUTOMATION_TASK_VIEW.value, db)
    try:
        query = db.query(GroupAIAutomationTask)
        
        if task_type:
            query = query.filter(GroupAIAutomationTask.task_type == task_type)
        if enabled is not None:
            query = query.filter(GroupAIAutomationTask.enabled == enabled)
        
        total = query.count()
        tasks = query.order_by(GroupAIAutomationTask.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
        
        return [
            AutomationTaskResponse(
                id=task.id,
                name=task.name,
                description=task.description,
                task_type=task.task_type,
                task_action=task.task_action,
                schedule_config=task.schedule_config,
                trigger_config=task.trigger_config,
                action_config=task.action_config,
                enabled=task.enabled,
                last_run_at=task.last_run_at.isoformat() if task.last_run_at else None,
                next_run_at=task.next_run_at.isoformat() if task.next_run_at else None,
                run_count=task.run_count,
                success_count=task.success_count,
                failure_count=task.failure_count,
                last_result=task.last_result,
                created_at=task.created_at.isoformat(),
                updated_at=task.updated_at.isoformat(),
                created_by=task.created_by,
                dependent_tasks=task.dependent_tasks or [],
                notify_on_success=task.notify_on_success,
                notify_on_failure=task.notify_on_failure,
                notify_recipients=task.notify_recipients or []
            )
            for task in tasks
        ]
    except Exception as e:
        logger.error(f"列出自動化任務失敗: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"列出自動化任務失敗: {str(e)}"
        )


@router.get("/{task_id}", response_model=AutomationTaskResponse)
async def get_automation_task(
    task_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """獲取自動化任務詳情（需要 automation_task:view 權限）"""
    check_permission(current_user, PermissionCode.AUTOMATION_TASK_VIEW.value, db)
    try:
        task = db.query(GroupAIAutomationTask).filter(GroupAIAutomationTask.id == task_id).first()
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"自動化任務 {task_id} 不存在"
            )
        
        return AutomationTaskResponse(
            id=task.id,
            name=task.name,
            description=task.description,
            task_type=task.task_type,
            task_action=task.task_action,
            schedule_config=task.schedule_config,
            trigger_config=task.trigger_config,
            action_config=task.action_config,
            enabled=task.enabled,
            last_run_at=task.last_run_at.isoformat() if task.last_run_at else None,
            next_run_at=task.next_run_at.isoformat() if task.next_run_at else None,
            run_count=task.run_count,
            success_count=task.success_count,
            failure_count=task.failure_count,
            last_result=task.last_result,
            created_at=task.created_at.isoformat(),
            updated_at=task.updated_at.isoformat(),
            created_by=task.created_by
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"獲取自動化任務失敗: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"獲取自動化任務失敗: {str(e)}"
        )


@router.put("/{task_id}", response_model=AutomationTaskResponse)
async def update_automation_task(
    task_id: str,
    task_update: AutomationTaskUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """更新自動化任務（需要 automation_task:update 權限）"""
    check_permission(current_user, PermissionCode.AUTOMATION_TASK_UPDATE.value, db)
    try:
        task = db.query(GroupAIAutomationTask).filter(GroupAIAutomationTask.id == task_id).first()
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"自動化任務 {task_id} 不存在"
            )
        
        if task_update.name is not None:
            task.name = task_update.name
        if task_update.description is not None:
            task.description = task_update.description
        if task_update.schedule_config is not None:
            task.schedule_config = task_update.schedule_config
        if task_update.trigger_config is not None:
            task.trigger_config = task_update.trigger_config
        if task_update.action_config is not None:
            task.action_config = task_update.action_config
        if task_update.enabled is not None:
            task.enabled = task_update.enabled
        if task_update.dependent_tasks is not None:
            task.dependent_tasks = task_update.dependent_tasks
        if task_update.notify_on_success is not None:
            task.notify_on_success = task_update.notify_on_success
        if task_update.notify_on_failure is not None:
            task.notify_on_failure = task_update.notify_on_failure
        if task_update.notify_recipients is not None:
            task.notify_recipients = task_update.notify_recipients
        
        task.updated_at = datetime.now()
        db.commit()
        db.refresh(task)
        
        # 如果是定時任務，重新加載到調度器
        if task.task_type == "scheduled":
            from app.services.task_scheduler import get_task_scheduler
            scheduler = get_task_scheduler()
            scheduler.reload_task(task_id)
        
        return AutomationTaskResponse(
            id=task.id,
            name=task.name,
            description=task.description,
            task_type=task.task_type,
            task_action=task.task_action,
            schedule_config=task.schedule_config,
            trigger_config=task.trigger_config,
            action_config=task.action_config,
            enabled=task.enabled,
            last_run_at=task.last_run_at.isoformat() if task.last_run_at else None,
            next_run_at=task.next_run_at.isoformat() if task.next_run_at else None,
            run_count=task.run_count,
            success_count=task.success_count,
            failure_count=task.failure_count,
            last_result=task.last_result,
            created_at=task.created_at.isoformat(),
            updated_at=task.updated_at.isoformat(),
            created_by=task.created_by,
            dependent_tasks=task.dependent_tasks or [],
            notify_on_success=task.notify_on_success,
            notify_on_failure=task.notify_on_failure,
            notify_recipients=task.notify_recipients or []
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"更新自動化任務失敗: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新自動化任務失敗: {str(e)}"
        )


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_automation_task(
    task_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """刪除自動化任務（需要 automation_task:delete 權限）"""
    check_permission(current_user, PermissionCode.AUTOMATION_TASK_DELETE.value, db)
    try:
        task = db.query(GroupAIAutomationTask).filter(GroupAIAutomationTask.id == task_id).first()
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"自動化任務 {task_id} 不存在"
            )
        
        # 從調度器中移除任務
        if task.task_type == "scheduled":
            from app.services.task_scheduler import get_task_scheduler
            scheduler = get_task_scheduler()
            scheduler.unschedule_task(task_id)
        
        db.delete(task)
        db.commit()
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"刪除自動化任務失敗: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"刪除自動化任務失敗: {str(e)}"
        )


@router.post("/{task_id}/run", status_code=status.HTTP_200_OK)
async def run_automation_task(
    task_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """手動執行自動化任務（需要 automation_task:run 權限）"""
    check_permission(current_user, PermissionCode.AUTOMATION_TASK_RUN.value, db)
    try:
        task = db.query(GroupAIAutomationTask).filter(GroupAIAutomationTask.id == task_id).first()
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"自動化任務 {task_id} 不存在"
            )
        
        # 執行任務
        from app.services.task_executor import get_task_executor
        executor = get_task_executor()
        
        # 異步執行任務（不阻塞API響應）
        import asyncio
        asyncio.create_task(executor.execute_task(task))
        
        return {
            "message": "任務已提交執行",
            "task_id": task_id,
            "status": "running"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"執行自動化任務失敗: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"執行自動化任務失敗: {str(e)}"
        )


@router.get("/{task_id}/logs", response_model=List[TaskLogResponse])
async def get_task_logs(
    task_id: str,
    limit: int = Query(50, ge=1, le=500, description="返回數量"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """獲取任務執行日誌（需要 automation_task:log:view 權限）"""
    check_permission(current_user, PermissionCode.AUTOMATION_TASK_LOG_VIEW.value, db)
    try:
        logs = db.query(GroupAIAutomationTaskLog).filter(
            GroupAIAutomationTaskLog.task_id == task_id
        ).order_by(GroupAIAutomationTaskLog.started_at.desc()).limit(limit).all()
        
        return [
            TaskLogResponse(
                id=log.id,
                task_id=log.task_id,
                status=log.status,
                started_at=log.started_at.isoformat(),
                completed_at=log.completed_at.isoformat() if log.completed_at else None,
                duration_seconds=log.duration_seconds,
                result=log.result,
                error_message=log.error_message,
                execution_data=log.execution_data
            )
            for log in logs
        ]
    except Exception as e:
        logger.error(f"獲取任務日誌失敗: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"獲取任務日誌失敗: {str(e)}"
        )

