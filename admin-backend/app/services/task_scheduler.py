"""
任務調度器 - 管理定時任務的調度和執行
"""
import asyncio
import logging
from typing import Optional, Dict, Set
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.date import DateTrigger

from app.db import SessionLocal
from app.models.group_ai import GroupAIAutomationTask
from app.models.unified_features import ScheduledMessageTask
from app.services.task_executor import get_task_executor

logger = logging.getLogger(__name__)


class TaskScheduler:
    """任務調度器"""
    
    def __init__(self):
        self.scheduler: Optional[AsyncIOScheduler] = None
        self.scheduled_job_ids: Set[str] = set()
        self.is_running = False
    
    def start(self):
        """啟動調度器"""
        if self.is_running:
            logger.warning("任務調度器已經在運行中")
            return
        
        self.scheduler = AsyncIOScheduler()
        self.scheduler.start()
        self.is_running = True
        logger.info("任務調度器已啟動")
        
        # 加載所有啟用的定時任務
        self.load_scheduled_tasks()
    
    def stop(self):
        """停止調度器"""
        if not self.is_running:
            logger.warning("任務調度器未運行")
            return
        
        if self.scheduler:
            self.scheduler.shutdown()
            self.scheduler = None
        
        self.scheduled_job_ids.clear()
        self.is_running = False
        logger.info("任務調度器已停止")
    
    def load_scheduled_tasks(self):
        """從數據庫加載所有啟用的定時任務（包括新的定時消息任務）"""
        try:
            db = SessionLocal()
            try:
                # 加載原有的自動化任務
                automation_tasks = db.query(GroupAIAutomationTask).filter(
                    GroupAIAutomationTask.enabled == True,
                    GroupAIAutomationTask.task_type == "scheduled"
                ).all()
                
                for task in automation_tasks:
                    try:
                        self.schedule_task(task)
                    except Exception as e:
                        logger.error(f"加載自動化任務 {task.name} ({task.id}) 失敗: {e}", exc_info=True)
                
                # 加載新的定時消息任務
                try:
                    scheduled_message_tasks = db.query(ScheduledMessageTask).filter(
                        ScheduledMessageTask.enabled == True
                    ).all()
                    
                    for task in scheduled_message_tasks:
                        try:
                            self.schedule_scheduled_message_task(task)
                        except Exception as e:
                            logger.error(f"加載定時消息任務 {task.name} ({task.task_id}) 失敗: {e}", exc_info=True)
                    
                    logger.info(f"已加載 {len(automation_tasks)} 個自動化任務和 {len(scheduled_message_tasks)} 個定時消息任務")
                except Exception as e:
                    logger.warning(f"加載定時消息任務失敗（可能表尚未創建）: {e}")
                    logger.info(f"已加載 {len(automation_tasks)} 個自動化任務")
            finally:
                db.close()
        except Exception as e:
            logger.error(f"加載定時任務失敗: {e}", exc_info=True)
    
    def schedule_task(self, task: GroupAIAutomationTask):
        """調度一個任務"""
        if not self.scheduler:
            logger.error("調度器未啟動")
            return
        
        # 移除舊的任務（如果存在）
        self.unschedule_task(task.id)
        
        # 解析調度配置
        trigger = self._parse_schedule_config(task.schedule_config, task.id)
        if not trigger:
            logger.warning(f"任務 {task.name} ({task.id}) 的調度配置無效，跳過")
            return
        
        # 添加任務到調度器
        job_id = f"task_{task.id}"
        
        self.scheduler.add_job(
            func=self._execute_task_wrapper,
            trigger=trigger,
            args=[task.id],
            id=job_id,
            name=task.name,
            replace_existing=True,
        )
        
        self.scheduled_job_ids.add(job_id)
        logger.info(f"任務 {task.name} ({task.id}) 已添加到調度器")
    
    def unschedule_task(self, task_id: str):
        """取消調度一個任務"""
        if not self.scheduler:
            return
        
        job_id = f"task_{task_id}"
        if job_id in self.scheduled_job_ids:
            try:
                self.scheduler.remove_job(job_id)
                self.scheduled_job_ids.discard(job_id)
                logger.info(f"任務 {task_id} 已從調度器移除")
            except Exception as e:
                logger.warning(f"移除任務 {task_id} 失敗: {e}")
    
    def schedule_scheduled_message_task(self, task: ScheduledMessageTask):
        """調度一個定時消息任務"""
        if not self.scheduler:
            logger.error("調度器未啟動")
            return
        
        # 移除舊的任務（如果存在）
        job_id = f"scheduled_message_{task.task_id}"
        self.unschedule_task_by_job_id(job_id)
        
        # 解析調度配置
        trigger = None
        if task.schedule_type == "cron" and task.cron_expression:
            try:
                # 解析 Cron 表達式
                parts = task.cron_expression.split()
                if len(parts) == 5:
                    trigger = CronTrigger(
                        minute=parts[0],
                        hour=parts[1],
                        day=parts[2],
                        month=parts[3],
                        day_of_week=parts[4],
                        timezone=task.timezone
                    )
            except Exception as e:
                logger.error(f"解析 Cron 表達式失敗: {task.cron_expression}: {e}")
        elif task.schedule_type == "interval" and task.interval_seconds:
            trigger = IntervalTrigger(seconds=task.interval_seconds)
        elif task.schedule_type == "once" and task.next_run_at:
            trigger = DateTrigger(run_date=task.next_run_at)
        
        if not trigger:
            logger.warning(f"定時消息任務 {task.name} ({task.task_id}) 的調度配置無效，跳過")
            return
        
        # 添加任務到調度器
        self.scheduler.add_job(
            func=self._execute_scheduled_message_task_wrapper,
            trigger=trigger,
            args=[task.task_id],
            id=job_id,
            name=f"scheduled_message_{task.name}",
            replace_existing=True,
        )
        
        self.scheduled_job_ids.add(job_id)
        logger.info(f"定時消息任務 {task.name} ({task.task_id}) 已添加到調度器")
    
    def unschedule_task_by_job_id(self, job_id: str):
        """通過 job_id 取消調度任務"""
        if not self.scheduler:
            return
        
        try:
            if self.scheduler.get_job(job_id):
                self.scheduler.remove_job(job_id)
                self.scheduled_job_ids.discard(job_id)
                logger.info(f"任務 {job_id} 已從調度器移除")
        except Exception as e:
            logger.warning(f"移除任務 {job_id} 失敗: {e}")
    
    def _execute_scheduled_message_task_wrapper(self, task_id: str):
        """定時消息任務執行包裝器"""
        import asyncio
        try:
            # 創建新的事件循環（如果當前線程沒有）
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            # 執行異步任務
            if loop.is_running():
                # 如果循環正在運行，創建任務
                asyncio.create_task(self._execute_scheduled_message_task(task_id))
            else:
                # 如果循環未運行，運行直到完成
                loop.run_until_complete(self._execute_scheduled_message_task(task_id))
        except Exception as e:
            logger.error(f"執行定時消息任務 {task_id} 失敗: {e}", exc_info=True)
    
    async def _execute_scheduled_message_task(self, task_id: str):
        """執行定時消息任務（異步）"""
        try:
            db = SessionLocal()
            try:
                task = db.query(ScheduledMessageTask).filter(
                    ScheduledMessageTask.task_id == task_id
                ).first()
                
                if not task or not task.enabled:
                    logger.warning(f"定時消息任務 {task_id} 不存在或已停用")
                    return
                
                # 使用 ScheduledMessageProcessor 執行任務
                from group_ai_service.scheduled_message_processor import ScheduledMessageProcessor
                processor = ScheduledMessageProcessor()
                
                # 獲取 ActionExecutor 和 AccountManager（如果可用）
                action_executor = None
                account_manager = None
                try:
                    # 嘗試從 ServiceManager 獲取
                    import sys
                    from pathlib import Path
                    project_root = Path(__file__).parent.parent.parent.parent
                    if str(project_root) not in sys.path:
                        sys.path.insert(0, str(project_root))
                    
                    from group_ai_service.service_manager import ServiceManager
                    service_manager = ServiceManager.get_instance()
                    if service_manager:
                        if hasattr(service_manager, 'unified_message_handler') and service_manager.unified_message_handler:
                            action_executor = service_manager.unified_message_handler.action_executor
                        if hasattr(service_manager, 'account_manager'):
                            account_manager = service_manager.account_manager
                except Exception as e:
                    logger.debug(f"無法獲取 ActionExecutor/AccountManager: {e}")
                
                # 執行任務
                await processor._execute_task(task, action_executor, account_manager)
                
                # 更新執行記錄（從處理器任務對象同步回來）
                task.last_run_at = datetime.now()
                task.run_count = getattr(task, 'run_count', 0) + 1
                task.success_count = getattr(task, 'success_count', 0) + (getattr(task, 'success_count', 0) if hasattr(task, 'success_count') else 0)
                task.failure_count = getattr(task, 'failure_count', 0) + (getattr(task, 'failure_count', 0) if hasattr(task, 'failure_count') else 0)
                
                db.commit()
                logger.info(f"定時消息任務 {task.name} ({task_id}) 執行完成")
            finally:
                db.close()
        except Exception as e:
            logger.error(f"執行定時消息任務 {task_id} 失敗: {e}", exc_info=True)
    
    def _parse_schedule_config(self, config: Optional[Dict], task_id: str):
        """解析調度配置，返回 trigger 對象"""
        if not config:
            return None
        
        # 支持 cron 表達式
        if "cron" in config:
            cron_expr = config["cron"]
            try:
                # 解析 cron 表達式: "minute hour day month day_of_week"
                # 例如: "0 9 * * *" 表示每天9點
                parts = cron_expr.split()
                if len(parts) == 5:
                    return CronTrigger(
                        minute=parts[0],
                        hour=parts[1],
                        day=parts[2],
                        month=parts[3],
                        day_of_week=parts[4],
                    )
                elif len(parts) == 6:
                    # 支持秒級 cron: "second minute hour day month day_of_week"
                    return CronTrigger(
                        second=parts[0],
                        minute=parts[1],
                        hour=parts[2],
                        day=parts[3],
                        month=parts[4],
                        day_of_week=parts[5],
                    )
                else:
                    logger.error(f"任務 {task_id} 的 cron 表達式格式錯誤: {cron_expr}")
                    return None
            except Exception as e:
                logger.error(f"解析任務 {task_id} 的 cron 表達式失敗: {e}")
                return None
        
        # 支持間隔調度（秒）
        elif "interval_seconds" in config:
            interval = config["interval_seconds"]
            try:
                return IntervalTrigger(seconds=int(interval))
            except Exception as e:
                logger.error(f"解析任務 {task_id} 的間隔配置失敗: {e}")
                return None
        
        # 支持間隔調度（分鐘）
        elif "interval_minutes" in config:
            interval = config["interval_minutes"]
            try:
                return IntervalTrigger(minutes=int(interval))
            except Exception as e:
                logger.error(f"解析任務 {task_id} 的間隔配置失敗: {e}")
                return None
        
        # 支持間隔調度（小時）
        elif "interval_hours" in config:
            interval = config["interval_hours"]
            try:
                return IntervalTrigger(hours=int(interval))
            except Exception as e:
                logger.error(f"解析任務 {task_id} 的間隔配置失敗: {e}")
                return None
        
        else:
            logger.warning(f"任務 {task_id} 的調度配置格式不支持")
            return None
    
    async def _execute_task_wrapper(self, task_id: str):
        """任務執行包裝函數"""
        try:
            db = SessionLocal()
            try:
                task = db.query(GroupAIAutomationTask).filter(
                    GroupAIAutomationTask.id == task_id
                ).first()
                
                if not task:
                    logger.error(f"任務 {task_id} 不存在")
                    return
                
                if not task.enabled:
                    logger.debug(f"任務 {task_id} 已停用，跳過執行")
                    return
                
                # 執行任務
                executor = get_task_executor()
                result = await executor.execute_task(task)
                
                if result.get("success"):
                    logger.info(f"定時任務 {task.name} ({task_id}) 執行成功")
                else:
                    logger.error(f"定時任務 {task.name} ({task_id}) 執行失敗: {result.get('error')}")
                
                # 計算下次執行時間
                if self.scheduler:
                    job = self.scheduler.get_job(f"task_{task_id}")
                    if job and job.next_run_time:
                        task.next_run_at = job.next_run_time
                        db.commit()
            
            finally:
                db.close()
        except Exception as e:
            logger.error(f"執行任務 {task_id} 失敗: {e}", exc_info=True)
    
    def reload_task(self, task_id: str):
        """重新加載任務（用於任務更新後）"""
        try:
            db = SessionLocal()
            try:
                task = db.query(GroupAIAutomationTask).filter(
                    GroupAIAutomationTask.id == task_id
                ).first()
                
                if not task:
                    self.unschedule_task(task_id)
                    return
                
                if task.enabled and task.task_type == "scheduled":
                    self.schedule_task(task)
                else:
                    self.unschedule_task(task_id)
            finally:
                db.close()
        except Exception as e:
            logger.error(f"重新加載任務 {task_id} 失敗: {e}", exc_info=True)


# 全局實例
_task_scheduler: Optional[TaskScheduler] = None


def get_task_scheduler() -> TaskScheduler:
    """獲取任務調度器實例"""
    global _task_scheduler
    if _task_scheduler is None:
        _task_scheduler = TaskScheduler()
    return _task_scheduler

