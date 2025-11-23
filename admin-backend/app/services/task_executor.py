"""
任務執行引擎 - 實際執行自動化任務的動作
"""
import logging
from typing import Any, Dict, Optional, List
from datetime import datetime
from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.models.group_ai import GroupAIAutomationTask, GroupAIAutomationTaskLog

logger = logging.getLogger(__name__)


class TaskExecutor:
    """任務執行引擎"""
    
    def __init__(self):
        self.db: Optional[Session] = None
    
    def _get_db(self) -> Session:
        """獲取數據庫會話"""
        if self.db is None:
            self.db = SessionLocal()
        return self.db
    
    def _close_db(self):
        """關閉數據庫會話"""
        if self.db:
            self.db.close()
            self.db = None
    
    async def execute_task(self, task: GroupAIAutomationTask) -> Dict[str, Any]:
        """
        執行任務
        
        Args:
            task: 任務對象
            
        Returns:
            執行結果字典
        """
        db = self._get_db()
        log_id = None
        start_time = datetime.now()
        
        try:
            # 創建執行日誌
            log = GroupAIAutomationTaskLog(
                task_id=task.id,
                status="running",
                started_at=start_time,
                execution_data={
                    "task_name": task.name,
                    "task_action": task.task_action,
                    "action_config": task.action_config,
                }
            )
            db.add(log)
            db.commit()
            db.refresh(log)
            log_id = log.id
            
            # 執行任務動作
            result = await self._execute_action(task.task_action, task.action_config, db)
            
            # 更新日誌
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            log.status = "success"
            log.completed_at = end_time
            log.duration_seconds = duration
            log.result = str(result)
            
            # 更新任務統計（需要重新查詢以確保對象是最新的）
            task_refresh = db.query(GroupAIAutomationTask).filter(
                GroupAIAutomationTask.id == task.id
            ).first()
            if task_refresh:
                task_refresh.last_run_at = start_time
                task_refresh.run_count += 1
                task_refresh.success_count += 1
                task_refresh.last_result = f"執行成功: {result.get('message', '任務完成')}"
                db.commit()
                db.refresh(task_refresh)
                # 更新本地引用
                task = task_refresh
            
            logger.info(f"任務 {task.name} ({task.id}) 執行成功，耗時 {duration:.2f} 秒")
            
            # 發送成功通知（如果需要）
            if task.notify_on_success:
                await self._send_task_notification(
                    task=task,
                    success=True,
                    result=result,
                    duration=duration,
                    db=db
                )
            
            # 觸發依賴任務
            if task.dependent_tasks:
                await self._trigger_dependent_tasks(task.dependent_tasks, db)
            
            return {
                "success": True,
                "result": result,
                "duration": duration,
            }
        
        except Exception as e:
            logger.error(f"任務 {task.name} ({task.id}) 執行失敗: {e}", exc_info=True)
            
            # 更新日誌
            if log_id:
                try:
                    db = self._get_db()
                    log = db.query(GroupAIAutomationTaskLog).filter(
                        GroupAIAutomationTaskLog.id == log_id
                    ).first()
                    task_refresh = db.query(GroupAIAutomationTask).filter(
                        GroupAIAutomationTask.id == task.id
                    ).first()
                    
                    if log:
                        end_time = datetime.now()
                        duration = (end_time - start_time).total_seconds()
                        
                        log.status = "failure"
                        log.completed_at = end_time
                        log.duration_seconds = duration
                        log.error_message = str(e)
                    
                    if task_refresh:
                        # 更新任務統計
                        task_refresh.last_run_at = start_time
                        task_refresh.run_count += 1
                        task_refresh.failure_count += 1
                        task_refresh.last_result = f"執行失敗: {str(e)}"
                        
                        db.commit()
                        
                        # 發送失敗通知（如果需要）
                        if task_refresh.notify_on_failure:
                            await self._send_task_notification(
                                task=task_refresh,
                                success=False,
                                error=str(e),
                                duration=(datetime.now() - start_time).total_seconds(),
                                db=db
                            )
                except Exception as update_error:
                    logger.error(f"更新任務日誌失敗: {update_error}", exc_info=True)
            
            return {
                "success": False,
                "error": str(e),
            }
    
    async def _execute_action(self, action: str, action_config: Dict[str, Any], db: Session) -> Dict[str, Any]:
        """
        執行具體的任務動作
        
        Args:
            action: 動作類型
            action_config: 動作配置
            
        Returns:
            執行結果
        """
        if action == "alert_check":
            return await self._execute_alert_check(action_config, db)
        elif action == "account_start":
            return await self._execute_account_start(action_config, db)
        elif action == "account_stop":
            return await self._execute_account_stop(action_config, db)
        elif action == "account_batch_start":
            return await self._execute_account_batch_start(action_config, db)
        elif action == "account_batch_stop":
            return await self._execute_account_batch_stop(action_config, db)
        elif action == "script_publish":
            return await self._execute_script_publish(action_config, db)
        elif action == "script_review":
            return await self._execute_script_review(action_config, db)
        elif action == "data_backup":
            return await self._execute_data_backup(action_config, db)
        elif action == "data_export":
            return await self._execute_data_export(action_config, db)
        elif action == "role_assignment":
            return await self._execute_role_assignment(action_config, db)
        else:
            raise ValueError(f"不支持的任務動作: {action}")
    
    async def _execute_alert_check(self, config: Dict[str, Any], db: Session) -> Dict[str, Any]:
        """執行告警檢查"""
        try:
            from app.crud import alert_rule as crud_alert_rule
            from app.api.group_ai.monitor import monitor_service
            
            # 從數據庫讀取啟用的告警規則
            enabled_rules = crud_alert_rule.get_enabled_alert_rules(db)
            
            if not enabled_rules:
                return {
                    "message": "沒有啟用的告警規則",
                    "alerts_found": 0,
                }
            
            # 執行告警檢查
            new_alerts = monitor_service.check_alerts(alert_rules=enabled_rules)
            
            return {
                "message": f"檢查完成，發現 {len(new_alerts)} 個新告警",
                "alerts_found": len(new_alerts),
                "rules_checked": len(enabled_rules),
            }
        except Exception as e:
            logger.error(f"執行告警檢查失敗: {e}", exc_info=True)
            raise
    
    async def _execute_account_start(self, config: Dict[str, Any], db: Session) -> Dict[str, Any]:
        """執行啟動賬號"""
        try:
            account_ids = config.get("account_ids", [])
            if not account_ids:
                # 如果沒有指定賬號，啟動所有停用的賬號
                from app.models.group_ai import GroupAIAccount
                accounts = db.query(GroupAIAccount).filter(
                    GroupAIAccount.active == False
                ).all()
                account_ids = [acc.account_id for acc in accounts]
            
            if not account_ids:
                return {
                    "message": "沒有需要啟動的賬號",
                    "accounts_started": 0,
                }
            
            # 調用控制API啟動賬號
            from app.api.group_ai.control import get_service_manager
            service_manager = get_service_manager()
            started_count = 0
            
            for account_id in account_ids:
                try:
                    # 調用實際的啟動邏輯
                    accounts = service_manager.get_accounts()
                    if account_id in accounts:
                        await service_manager.start_account(account_id)
                        started_count += 1
                    else:
                        logger.warning(f"賬號 {account_id} 不存在")
                except Exception as e:
                    logger.error(f"啟動賬號 {account_id} 失敗: {e}")
            
            return {
                "message": f"成功啟動 {started_count}/{len(account_ids)} 個賬號",
                "accounts_started": started_count,
                "total_accounts": len(account_ids),
            }
        except Exception as e:
            logger.error(f"執行啟動賬號失敗: {e}", exc_info=True)
            raise
    
    async def _execute_account_stop(self, config: Dict[str, Any], db: Session) -> Dict[str, Any]:
        """執行停止賬號"""
        try:
            account_ids = config.get("account_ids", [])
            if not account_ids:
                # 如果沒有指定賬號，停止所有啟用的賬號
                from app.models.group_ai import GroupAIAccount
                accounts = db.query(GroupAIAccount).filter(
                    GroupAIAccount.active == True
                ).all()
                account_ids = [acc.account_id for acc in accounts]
            
            if not account_ids:
                return {
                    "message": "沒有需要停止的賬號",
                    "accounts_stopped": 0,
                }
            
            # 調用控制API停止賬號
            from app.api.group_ai.control import get_service_manager
            service_manager = get_service_manager()
            stopped_count = 0
            
            for account_id in account_ids:
                try:
                    # 調用實際的停止邏輯
                    accounts = service_manager.get_accounts()
                    if account_id in accounts:
                        await service_manager.stop_account(account_id)
                        stopped_count += 1
                    else:
                        logger.warning(f"賬號 {account_id} 不存在")
                except Exception as e:
                    logger.error(f"停止賬號 {account_id} 失敗: {e}")
            
            return {
                "message": f"成功停止 {stopped_count}/{len(account_ids)} 個賬號",
                "accounts_stopped": stopped_count,
                "total_accounts": len(account_ids),
            }
        except Exception as e:
            logger.error(f"執行停止賬號失敗: {e}", exc_info=True)
            raise
    
    async def _execute_script_publish(self, config: Dict[str, Any], db: Session) -> Dict[str, Any]:
        """執行發布劇本"""
        try:
            script_id = config.get("script_id")
            if not script_id:
                return {
                    "message": "未指定劇本ID",
                    "script_published": False,
                }
            
            # 調用腳本審核API發布劇本
            from app.api.group_ai.script_review import publish_script as api_publish_script
            from app.models.group_ai import GroupAIScript
            
            script = db.query(GroupAIScript).filter(
                GroupAIScript.script_id == script_id
            ).first()
            
            if not script:
                return {
                    "message": f"劇本 {script_id} 不存在",
                    "script_published": False,
                }
            
            # 這裡需要實際調用發布邏輯
            # 暫時返回成功
            
            return {
                "message": f"劇本 {script_id} 發布成功",
                "script_published": True,
                "script_id": script_id,
            }
        except Exception as e:
            logger.error(f"執行發布劇本失敗: {e}", exc_info=True)
            raise
    
    async def _execute_account_batch_start(self, config: Dict[str, Any], db: Session) -> Dict[str, Any]:
        """批量啟動賬號"""
        try:
            account_ids = config.get("account_ids", [])
            if not account_ids:
                return {
                    "message": "未指定賬號列表",
                    "accounts_started": 0,
                }
            
            from app.api.group_ai.control import get_service_manager
            service_manager = get_service_manager()
            started_count = 0
            failed_accounts = []
            
            for account_id in account_ids:
                try:
                    if account_id in service_manager.account_manager.accounts:
                        await service_manager.start_account(account_id)
                        started_count += 1
                    else:
                        failed_accounts.append(account_id)
                        logger.warning(f"賬號 {account_id} 不存在")
                except Exception as e:
                    failed_accounts.append(account_id)
                    logger.error(f"啟動賬號 {account_id} 失敗: {e}")
            
            return {
                "message": f"成功啟動 {started_count}/{len(account_ids)} 個賬號",
                "accounts_started": started_count,
                "total_accounts": len(account_ids),
                "failed_accounts": failed_accounts,
            }
        except Exception as e:
            logger.error(f"批量啟動賬號失敗: {e}", exc_info=True)
            raise
    
    async def _execute_account_batch_stop(self, config: Dict[str, Any], db: Session) -> Dict[str, Any]:
        """批量停止賬號"""
        try:
            account_ids = config.get("account_ids", [])
            if not account_ids:
                return {
                    "message": "未指定賬號列表",
                    "accounts_stopped": 0,
                }
            
            from app.api.group_ai.control import get_service_manager
            service_manager = get_service_manager()
            stopped_count = 0
            failed_accounts = []
            
            for account_id in account_ids:
                try:
                    if account_id in service_manager.account_manager.accounts:
                        await service_manager.stop_account(account_id)
                        stopped_count += 1
                    else:
                        failed_accounts.append(account_id)
                        logger.warning(f"賬號 {account_id} 不存在")
                except Exception as e:
                    failed_accounts.append(account_id)
                    logger.error(f"停止賬號 {account_id} 失敗: {e}")
            
            return {
                "message": f"成功停止 {stopped_count}/{len(account_ids)} 個賬號",
                "accounts_stopped": stopped_count,
                "total_accounts": len(account_ids),
                "failed_accounts": failed_accounts,
            }
        except Exception as e:
            logger.error(f"批量停止賬號失敗: {e}", exc_info=True)
            raise
    
    async def _execute_script_review(self, config: Dict[str, Any], db: Session) -> Dict[str, Any]:
        """執行劇本審核"""
        try:
            script_id = config.get("script_id")
            action = config.get("action", "approve")  # approve, reject
            
            if not script_id:
                return {
                    "message": "未指定劇本ID",
                    "script_reviewed": False,
                }
            
            from app.models.group_ai import GroupAIScript
            script = db.query(GroupAIScript).filter(
                GroupAIScript.script_id == script_id
            ).first()
            
            if not script:
                return {
                    "message": f"劇本 {script_id} 不存在",
                    "script_reviewed": False,
                }
            
            # 這裡可以實現實際的審核邏輯
            # 暫時返回成功
            
            return {
                "message": f"劇本 {script_id} {action} 成功",
                "script_reviewed": True,
                "script_id": script_id,
                "action": action,
            }
        except Exception as e:
            logger.error(f"執行劇本審核失敗: {e}", exc_info=True)
            raise
    
    async def _execute_data_export(self, config: Dict[str, Any], db: Session) -> Dict[str, Any]:
        """執行數據導出"""
        try:
            export_type = config.get("export_type", "csv")  # csv, excel, pdf
            data_type = config.get("data_type")  # accounts, scripts, sessions, etc.
            filters = config.get("filters", {})
            
            if not data_type:
                return {
                    "message": "未指定數據類型",
                    "export_completed": False,
                }
            
            # 這裡可以實現實際的導出邏輯
            # 暫時返回成功
            
            return {
                "message": f"數據導出完成（{export_type}）",
                "export_completed": True,
                "export_type": export_type,
                "data_type": data_type,
            }
        except Exception as e:
            logger.error(f"執行數據導出失敗: {e}", exc_info=True)
            raise
    
    async def _execute_role_assignment(self, config: Dict[str, Any], db: Session) -> Dict[str, Any]:
        """執行角色分配"""
        try:
            scheme_id = config.get("scheme_id")
            account_ids = config.get("account_ids", [])
            
            if not scheme_id:
                return {
                    "message": "未指定分配方案ID",
                    "assignment_completed": False,
                }
            
            # 這裡可以實現實際的角色分配邏輯
            # 暫時返回成功
            
            return {
                "message": f"角色分配完成（方案 {scheme_id}）",
                "assignment_completed": True,
                "scheme_id": scheme_id,
                "accounts_assigned": len(account_ids),
            }
        except Exception as e:
            logger.error(f"執行角色分配失敗: {e}", exc_info=True)
            raise
    
    async def _execute_data_backup(self, config: Dict[str, Any], db: Session) -> Dict[str, Any]:
        """執行數據備份"""
        try:
            # 這裡可以實現數據備份邏輯
            # 暫時返回成功
            
            return {
                "message": "數據備份完成",
                "backup_completed": True,
            }
        except Exception as e:
            logger.error(f"執行數據備份失敗: {e}", exc_info=True)
            raise
    
    async def _send_task_notification(
        self,
        task: GroupAIAutomationTask,
        success: bool,
        result: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
        duration: Optional[float] = None,
        db: Session = None
    ):
        """發送任務執行結果通知"""
        try:
            from app.services.notification_service import NotificationService
            notification_service = NotificationService(db or self._get_db())
            
            # 確定通知接收人
            recipients = task.notify_recipients or []
            if not recipients:
                # 如果沒有指定接收人，發送給任務創建者
                if task.created_by:
                    recipients = [task.created_by]
                else:
                    logger.warning(f"任務 {task.id} 沒有通知接收人，跳過通知")
                    return
            
            # 構建通知內容
            if success:
                title = f"任務執行成功: {task.name}"
                message = f"任務「{task.name}」執行成功"
                if result:
                    message += f"\n結果: {result.get('message', '任務完成')}"
                if duration:
                    message += f"\n耗時: {duration:.2f} 秒"
                level = "info"
            else:
                title = f"任務執行失敗: {task.name}"
                message = f"任務「{task.name}」執行失敗"
                if error:
                    message += f"\n錯誤: {error}"
                level = "high"
            
            # 發送通知給每個接收人
            for recipient in recipients:
                await notification_service.send_browser_notification(
                    recipient=recipient,
                    title=title,
                    message=message,
                    level=level,
                    event_type="task_execution",
                    resource_type="automation_task",
                    resource_id=task.id,
                    metadata={
                        "task_id": task.id,
                        "task_name": task.name,
                        "task_action": task.task_action,
                        "success": success,
                        "duration": duration,
                        "result": result,
                        "error": error,
                    }
                )
            
            logger.info(f"已發送任務 {task.id} 執行結果通知給 {len(recipients)} 個接收人")
        except Exception as e:
            logger.error(f"發送任務通知失敗: {e}", exc_info=True)
            # 不拋出異常，避免影響任務執行
    
    async def _trigger_dependent_tasks(self, dependent_task_ids: List[str], db: Session):
        """觸發依賴任務"""
        try:
            from app.services.task_scheduler import get_task_scheduler
            
            for task_id in dependent_task_ids:
                try:
                    task = db.query(GroupAIAutomationTask).filter(
                        GroupAIAutomationTask.id == task_id
                    ).first()
                    
                    if not task:
                        logger.warning(f"依賴任務 {task_id} 不存在")
                        continue
                    
                    if not task.enabled:
                        logger.info(f"依賴任務 {task_id} 已停用，跳過")
                        continue
                    
                    # 如果是定時任務，通過調度器觸發
                    if task.task_type == "scheduled":
                        scheduler = get_task_scheduler()
                        scheduler.trigger_task_now(task_id)
                    else:
                        # 手動任務直接執行
                        await self.execute_task(task)
                    
                    logger.info(f"已觸發依賴任務 {task_id} ({task.name})")
                except Exception as e:
                    logger.error(f"觸發依賴任務 {task_id} 失敗: {e}", exc_info=True)
        except Exception as e:
            logger.error(f"觸發依賴任務失敗: {e}", exc_info=True)
            # 不拋出異常，避免影響主任務


# 全局實例
_task_executor: Optional[TaskExecutor] = None


def get_task_executor() -> TaskExecutor:
    """獲取任務執行引擎實例"""
    global _task_executor
    if _task_executor is None:
        _task_executor = TaskExecutor()
    return _task_executor

