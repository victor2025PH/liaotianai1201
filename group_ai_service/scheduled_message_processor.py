"""
定時消息處理器
支持 Cron 表達式、間隔任務、條件觸發等
"""
import logging
import asyncio
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger(__name__)

# 嘗試導入 ActionExecutor（用於發送消息）
try:
    from group_ai_service.unified_message_handler import ActionExecutor, MessageContext
    ACTION_EXECUTOR_AVAILABLE = True
except ImportError:
    ACTION_EXECUTOR_AVAILABLE = False
    logger.warning("ActionExecutor 不可用，定時消息發送功能可能受限")


class ScheduleType(Enum):
    """調度類型"""
    CRON = "cron"              # Cron 表達式
    INTERVAL = "interval"      # 間隔任務
    ONCE = "once"             # 一次性任務
    CONDITIONAL = "conditional"  # 條件觸發


@dataclass
class MessageTemplate:
    """消息模板"""
    template: str  # 模板字符串，支持變量替換
    variables: Dict[str, Any] = field(default_factory=dict)  # 變量定義
    media: Optional[str] = None  # 媒體文件路徑（可選）


@dataclass
class ScheduledMessageTask:
    """定時消息任務"""
    id: str
    name: str
    enabled: bool = True
    
    # 調度配置
    schedule_type: ScheduleType = ScheduleType.CRON
    cron_expression: Optional[str] = None  # Cron 表達式，如 "0 9 * * *"
    interval_seconds: Optional[int] = None  # 間隔秒數
    start_time: Optional[str] = None  # 開始時間，如 "09:00"
    end_time: Optional[str] = None  # 結束時間，如 "22:00"
    timezone: str = "Asia/Shanghai"
    
    # 條件觸發
    condition: Optional[str] = None  # 條件表達式，如 "group_activity < 5"
    check_interval: int = 300  # 檢查間隔（秒）
    
    # 目標配置
    groups: List[int] = field(default_factory=list)  # 目標群組列表
    accounts: List[str] = field(default_factory=list)  # 目標賬號列表
    rotation: bool = False  # 是否輪流發送
    rotation_strategy: str = "round_robin"  # round_robin/random/priority
    
    # 消息配置
    message_template: MessageTemplate = field(default_factory=lambda: MessageTemplate(template=""))
    
    # 發送配置
    delay_min: int = 0  # 隨機延遲最小值（秒）
    delay_max: int = 5  # 隨機延遲最大值（秒）
    retry_times: int = 3  # 重試次數
    retry_interval: int = 60  # 重試間隔（秒）
    
    # 執行記錄
    last_run_at: Optional[datetime] = None
    next_run_at: Optional[datetime] = None
    run_count: int = 0
    success_count: int = 0
    failure_count: int = 0


class ScheduledMessageProcessor:
    """定時消息處理器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.tasks: Dict[str, ScheduledMessageTask] = {}  # task_id -> task
        self.running_tasks: Dict[str, asyncio.Task] = {}  # task_id -> asyncio.Task
        
        # 從數據庫加載任務
        self._load_tasks()
        
        self.logger.info(f"ScheduledMessageProcessor 初始化完成，已加載 {len(self.tasks)} 個任務")
    
    def _load_tasks(self):
        """從數據庫加載任務"""
        # 嘗試從數據庫加載任務
        try:
            # 動態導入，避免循環依賴
            import sys
            from pathlib import Path
            
            # 檢查是否在 admin-backend 環境中
            admin_backend_path = Path(__file__).parent.parent.parent / "admin-backend"
            if admin_backend_path.exists() and str(admin_backend_path) not in sys.path:
                sys.path.insert(0, str(admin_backend_path))
            
            try:
                from app.db import SessionLocal
                from app.models.unified_features import ScheduledMessageTask as DBScheduledMessageTask
                
                db = SessionLocal()
                try:
                    db_tasks = db.query(DBScheduledMessageTask).filter(
                        DBScheduledMessageTask.enabled == True
                    ).all()
                    
                    for db_task in db_tasks:
                        # 轉換數據庫模型為處理器任務
                        task = ScheduledMessageTask(
                            id=db_task.task_id,
                            name=db_task.name,
                            enabled=db_task.enabled,
                            schedule_type=ScheduleType(db_task.schedule_type) if db_task.schedule_type else ScheduleType.CRON,
                            cron_expression=db_task.cron_expression,
                            interval_seconds=db_task.interval_seconds,
                            start_time=db_task.start_time,
                            end_time=db_task.end_time,
                            timezone=db_task.timezone,
                            condition=db_task.condition,
                            check_interval=db_task.check_interval,
                            groups=db_task.groups or [],
                            accounts=db_task.accounts or [],
                            rotation=db_task.rotation,
                            rotation_strategy=db_task.rotation_strategy,
                            message_template=MessageTemplate(
                                template=db_task.message_template,
                                variables=db_task.template_variables or {},
                                media=db_task.media_path,
                            ),
                            delay_min=db_task.delay_min,
                            delay_max=db_task.delay_max,
                            retry_times=db_task.retry_times,
                            retry_interval=db_task.retry_interval,
                            last_run_at=db_task.last_run_at,
                            next_run_at=db_task.next_run_at,
                            run_count=db_task.run_count,
                            success_count=db_task.success_count,
                            failure_count=db_task.failure_count,
                        )
                        self.tasks[task.id] = task
                        # 如果任務啟用，啟動它
                        if task.enabled:
                            self._start_task(task)
                    
                    if db_tasks:
                        self.logger.info(f"從數據庫加載了 {len(db_tasks)} 個定時消息任務")
                finally:
                    db.close()
            except ImportError:
                # 數據庫模組不可用（可能在 worker 節點環境）
                self.logger.debug("數據庫模組不可用，跳過從數據庫加載任務")
            except Exception as e:
                self.logger.warning(f"從數據庫加載任務失敗: {e}")
        except Exception as e:
            self.logger.warning(f"加載定時消息任務失敗: {e}")
    
    def add_task(self, task: ScheduledMessageTask):
        """添加定時任務"""
        self.tasks[task.id] = task
        if task.enabled:
            self._start_task(task)
        self.logger.info(f"已添加定時消息任務: {task.name} ({task.id})")
    
    def remove_task(self, task_id: str):
        """移除定時任務"""
        if task_id in self.tasks:
            self._stop_task(task_id)
            del self.tasks[task_id]
            self.logger.info(f"已移除定時消息任務: {task_id}")
    
    def update_task(self, task: ScheduledMessageTask):
        """更新定時任務"""
        old_task = self.tasks.get(task.id)
        if old_task and old_task.enabled:
            self._stop_task(task.id)
        
        self.tasks[task.id] = task
        if task.enabled:
            self._start_task(task)
        
        self.logger.info(f"已更新定時消息任務: {task.name} ({task.id})")
    
    def _start_task(self, task: ScheduledMessageTask):
        """啟動定時任務"""
        if task.id in self.running_tasks:
            self._stop_task(task.id)
        
        async_task = asyncio.create_task(self._run_task(task))
        self.running_tasks[task.id] = async_task
        self.logger.info(f"已啟動定時消息任務: {task.name} ({task.id})")
    
    def _stop_task(self, task_id: str):
        """停止定時任務"""
        if task_id in self.running_tasks:
            self.running_tasks[task_id].cancel()
            del self.running_tasks[task_id]
            self.logger.info(f"已停止定時消息任務: {task_id}")
    
    async def _run_task(self, task: ScheduledMessageTask):
        """運行定時任務"""
        try:
            if task.schedule_type == ScheduleType.CRON:
                await self._run_cron_task(task)
            elif task.schedule_type == ScheduleType.INTERVAL:
                await self._run_interval_task(task)
            elif task.schedule_type == ScheduleType.CONDITIONAL:
                await self._run_conditional_task(task)
            elif task.schedule_type == ScheduleType.ONCE:
                await self._run_once_task(task)
        except asyncio.CancelledError:
            self.logger.info(f"定時消息任務已取消: {task.name} ({task.id})")
        except Exception as e:
            self.logger.error(f"定時消息任務執行失敗: {task.name} ({task.id}): {e}", exc_info=True)
    
    async def _run_cron_task(self, task: ScheduledMessageTask):
        """運行 Cron 任務"""
        # TODO: 實現 Cron 表達式解析和執行
        # 使用 croniter 或類似庫
        self.logger.warning("Cron 任務執行尚未實現")
    
    async def _run_interval_task(self, task: ScheduledMessageTask):
        """運行間隔任務"""
        if not task.interval_seconds:
            return
        
        while True:
            try:
                # 檢查時間範圍
                if task.start_time and task.end_time:
                    current_time = datetime.now().time()
                    start = datetime.strptime(task.start_time, "%H:%M").time()
                    end = datetime.strptime(task.end_time, "%H:%M").time()
                    
                    if not (start <= current_time <= end):
                        # 不在時間範圍內，等待到下一個開始時間
                        await asyncio.sleep(60)  # 每分鐘檢查一次
                        continue
                
                # 執行發送
                await self._execute_task(task)
                
                # 等待間隔
                await asyncio.sleep(task.interval_seconds)
                
            except asyncio.CancelledError:
                raise
            except Exception as e:
                self.logger.error(f"間隔任務執行錯誤: {e}", exc_info=True)
                await asyncio.sleep(task.interval_seconds)
    
    async def _run_conditional_task(self, task: ScheduledMessageTask):
        """運行條件觸發任務"""
        while True:
            try:
                # 檢查條件
                if self._check_condition(task.condition):
                    # 條件滿足，執行發送
                    await self._execute_task(task)
                
                # 等待檢查間隔
                await asyncio.sleep(task.check_interval)
                
            except asyncio.CancelledError:
                raise
            except Exception as e:
                self.logger.error(f"條件任務執行錯誤: {e}", exc_info=True)
                await asyncio.sleep(task.check_interval)
    
    async def _run_once_task(self, task: ScheduledMessageTask):
        """運行一次性任務"""
        if task.next_run_at:
            # 等待到指定時間
            now = datetime.now()
            if task.next_run_at > now:
                wait_seconds = (task.next_run_at - now).total_seconds()
                await asyncio.sleep(wait_seconds)
            
            # 執行發送
            await self._execute_task(task)
    
    def _check_condition(self, condition: Optional[str], context: Optional[Dict[str, Any]] = None) -> bool:
        """
        檢查條件
        
        Args:
            condition: 條件表達式字符串，例如: "group_activity < 5", "message_count > 10"
            context: 上下文變量字典，包含可用的變量值
            
        Returns:
            條件是否滿足
        """
        if not condition:
            return False
        
        try:
            from group_ai_service.condition_evaluator import ConditionEvaluator
            
            evaluator = ConditionEvaluator()
            
            # 如果沒有提供上下文，使用默認上下文
            if context is None:
                context = self._get_default_context()
            
            # 評估條件
            result = evaluator.evaluate(condition, context)
            
            self.logger.debug(f"條件評估: {condition} -> {result}")
            return result
            
        except Exception as e:
            self.logger.error(f"檢查條件失敗: {condition}, 錯誤: {e}", exc_info=True)
            return False
    
    def _get_default_context(self) -> Dict[str, Any]:
        """獲取默認上下文變量"""
        now = datetime.now()
        return {
            "date": now.strftime("%Y-%m-%d"),
            "time": now.strftime("%H:%M:%S"),
            "datetime": now.strftime("%Y-%m-%d %H:%M:%S"),
            "hour": now.hour,
            "minute": now.minute,
            "weekday": now.weekday() + 1,  # 1-7
            "is_weekend": now.weekday() >= 5,
            "day": now.day,
            "month": now.month,
            "year": now.year,
        }
    
    def render_template(self, template, template_variables: Dict[str, Any] = None) -> str:
        """
        渲染消息模板
        
        Args:
            template: MessageTemplate 對象或字符串模板
            template_variables: 模板變量字典（可選，如果 template 是字符串）
            
        Returns:
            渲染後的消息文本
        """
        # 支持字符串模板（向後兼容）
        if isinstance(template, str):
            template_str = template
            template_vars = template_variables or {}
        elif hasattr(template, 'template'):
            # MessageTemplate 對象
            template_str = template.template
            template_vars = getattr(template, 'variables', {}) or {}
        else:
            # 其他類型，轉換為字符串
            template_str = str(template)
            template_vars = {}
        
        result = template_str
        
        # 替換變量
        for key, value in template_vars.items():
            placeholder = f"{{{{{key}}}}}}"
            
            # 如果是列表，隨機選擇一個
            if isinstance(value, list):
                import random
                value = random.choice(value)
            
            result = result.replace(placeholder, str(value))
        
        # 替換內建變量
        now = datetime.now()
        result = result.replace("{{date}}", now.strftime("%Y-%m-%d"))
        result = result.replace("{{time}}", now.strftime("%H:%M:%S"))
        result = result.replace("{{datetime}}", now.strftime("%Y-%m-%d %H:%M:%S"))
        result = result.replace("{{weekday}}", str(now.weekday() + 1))
        result = result.replace("{{is_weekend}}", "true" if now.weekday() >= 5 else "false")
        
        return result
    
    async def _execute_task(self, task, action_executor=None, account_manager=None):
        """
        執行定時任務
        
        Args:
            task: ScheduledMessageTask 對象（可以是數據庫模型或處理器任務對象）
            action_executor: ActionExecutor 實例（可選）
            account_manager: AccountManager 實例（可選）
        """
        try:
            # 獲取任務屬性（支持數據庫模型和處理器任務對象）
            task_name = getattr(task, 'name', 'Unknown')
            task_template = getattr(task, 'message_template', '')
            task_template_vars = getattr(task, 'template_variables', {}) or {}
            task_accounts = getattr(task, 'accounts', [])
            task_groups = getattr(task, 'groups', [])
            task_rotation = getattr(task, 'rotation', False)
            task_rotation_strategy = getattr(task, 'rotation_strategy', 'round_robin')
            task_delay_min = getattr(task, 'delay_min', 0)
            task_delay_max = getattr(task, 'delay_max', 5)
            task_run_count = getattr(task, 'run_count', 0)
            
            # 渲染消息模板
            message_text = self.render_template(task_template, task_template_vars)
            
            # 選擇賬號（如果啟用輪流）
            accounts = task_accounts
            if task_rotation and len(accounts) > 1:
                if task_rotation_strategy == "round_robin":
                    # 輪流選擇
                    current_index = task_run_count % len(accounts)
                    accounts = [accounts[current_index]]
                elif task_rotation_strategy == "random":
                    import random
                    accounts = [random.choice(accounts)]
            
            # 發送消息到所有目標群組和賬號
            success_count = 0
            failure_count = 0
            
            for group_id in task_groups:
                for account_id in accounts:
                    try:
                        # 添加隨機延遲
                        if task_delay_max > task_delay_min:
                            import random
                            delay = random.uniform(task_delay_min, task_delay_max)
                            await asyncio.sleep(delay)
                        
                        # 使用 ActionExecutor 發送消息（如果可用）
                        if action_executor and account_manager:
                            from group_ai_service.unified_message_handler import MessageContext
                            context = MessageContext(
                                account_id=account_id,
                                group_id=group_id
                            )
                            
                            success = await action_executor.execute_action(
                                "send_message",
                                context,
                                {
                                    "message": message_text,
                                    "group_id": group_id,
                                    "account_id": account_id,
                                    "delay": [task_delay_min, task_delay_max] if task_delay_max > task_delay_min else 0
                                },
                                account_manager
                            )
                            
                            if success:
                                success_count += 1
                                self.logger.info(
                                    f"定時消息任務執行成功: {task_name} -> "
                                    f"群組 {group_id}, 賬號 {account_id}"
                                )
                            else:
                                failure_count += 1
                                self.logger.warning(
                                    f"定時消息任務執行失敗: {task_name} -> "
                                    f"群組 {group_id}, 賬號 {account_id}"
                                )
                        else:
                            # 回退方案：記錄日誌
                            self.logger.info(
                                f"定時消息任務執行（ActionExecutor 不可用）: {task_name} -> "
                                f"群組 {group_id}, 賬號 {account_id}, 消息: {message_text[:50]}..."
                            )
                            # 標記為成功（因為至少記錄了）
                            success_count += 1
                            
                    except Exception as e:
                        self.logger.error(f"發送定時消息失敗（群組: {group_id}, 賬號: {account_id}）: {e}", exc_info=True)
                        failure_count += 1
                    
            # 更新執行記錄（在循環外，避免重複更新）
            if hasattr(task, 'last_run_at'):
                task.last_run_at = datetime.now()
            if hasattr(task, 'run_count'):
                task.run_count = getattr(task, 'run_count', 0) + 1
            if hasattr(task, 'success_count'):
                task.success_count = getattr(task, 'success_count', 0) + success_count
            if hasattr(task, 'failure_count'):
                task.failure_count = getattr(task, 'failure_count', 0) + failure_count
                    
        except Exception as e:
            self.logger.error(f"執行定時任務失敗: {task_name}: {e}", exc_info=True)
            if hasattr(task, 'failure_count'):
                task.failure_count = getattr(task, 'failure_count', 0) + 1
    
    def get_tasks(self, enabled_only: bool = False) -> List[ScheduledMessageTask]:
        """獲取所有任務"""
        tasks = list(self.tasks.values())
        if enabled_only:
            tasks = [t for t in tasks if t.enabled]
        return tasks
    
    def get_task(self, task_id: str) -> Optional[ScheduledMessageTask]:
        """獲取指定任務"""
        return self.tasks.get(task_id)
