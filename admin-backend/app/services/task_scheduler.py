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
        """從數據庫加載所有啟用的定時任務"""
        try:
            db = SessionLocal()
            try:
                tasks = db.query(GroupAIAutomationTask).filter(
                    GroupAIAutomationTask.enabled == True,
                    GroupAIAutomationTask.task_type == "scheduled"
                ).all()
                
                for task in tasks:
                    try:
                        self.schedule_task(task)
                    except Exception as e:
                        logger.error(f"加載任務 {task.name} ({task.id}) 失敗: {e}", exc_info=True)
                
                logger.info(f"已加載 {len(tasks)} 個定時任務")
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

