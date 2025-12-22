"""
任务管理器 - Phase 6: 云端协同与任务调度
作为 Agent 的主大脑，轮询任务并执行
"""

import asyncio
import logging
from typing import Optional, Dict, Any
from datetime import datetime

from agent.core.api_client import ApiClient
from agent.core.scenario_player import ScenarioPlayer

logger = logging.getLogger(__name__)


class TaskManager:
    """任务管理器 - 轮询任务并执行"""
    
    def __init__(
        self,
        telegram_client,
        api_client: ApiClient,
        scenario_player: ScenarioPlayer,
        poll_interval: float = 5.0,
        heartbeat_interval: float = 30.0
    ):
        """
        初始化任务管理器
        
        Args:
            telegram_client: Telethon 客户端（用于执行任务）
            api_client: API 客户端（用于与后端交互）
            scenario_player: 剧本执行器（用于执行剧本）
            poll_interval: 轮询间隔（秒），无任务时的等待时间
            heartbeat_interval: 心跳间隔（秒），定期发送心跳保持在线
        """
        self.telegram_client = telegram_client
        self.api_client = api_client
        self.scenario_player = scenario_player
        self.poll_interval = poll_interval
        self.heartbeat_interval = heartbeat_interval
        
        self.is_running = False
        self.current_task_id: Optional[str] = None
        self.last_heartbeat: Optional[datetime] = None
    
    async def start_loop(self):
        """
        启动任务轮询循环（主循环）
        
        流程:
        1. 初始化：注册设备
        2. 死循环：
           - 获取待执行任务
           - 有任务：执行并汇报结果
           - 无任务：休眠并发送心跳
        3. 异常处理：网络断开时等待后重试
        """
        self.is_running = True
        
        logger.info("=" * 60)
        logger.info("Phase 6: 任务管理器启动")
        logger.info("=" * 60)
        
        # Step 1: 初始化 - 注册设备
        try:
            logger.info("正在向后端注册设备...")
            await self.api_client.register_device()
            logger.info("✅ 设备注册成功")
        except Exception as e:
            logger.error(f"❌ 设备注册失败: {e}")
            logger.warning("继续运行，但可能无法接收任务...")
        
        logger.info("=" * 60)
        logger.info("")
        
        # Step 2: 主循环
        consecutive_errors = 0
        max_consecutive_errors = 5
        
        while self.is_running:
            try:
                # 检查心跳（定期发送）
                now = datetime.now()
                if (self.last_heartbeat is None or 
                    (now - self.last_heartbeat).total_seconds() >= self.heartbeat_interval):
                    try:
                        await self.api_client.send_heartbeat()
                        self.last_heartbeat = now
                        logger.debug("💓 心跳已发送")
                    except Exception as e:
                        logger.warning(f"心跳发送失败: {e}")
                
                # 获取待执行任务
                task = await self.api_client.fetch_pending_task()
                
                if task:
                    # 有任务：执行任务
                    task_id = task.get("task_id")
                    task_type = task.get("task_type", "unknown")
                    
                    logger.info("=" * 60)
                    logger.info(f"📋 收到新任务: {task_id} (类型: {task_type})")
                    logger.info("=" * 60)
                    
                    self.current_task_id = task_id
                    
                    try:
                        # 更新任务状态为 running
                        await self.api_client.update_task_status(
                            task_id=task_id,
                            status="running"
                        )
                        
                        # 执行任务
                        success = await self._execute_task(task)
                        
                        if success:
                            # 执行成功
                            await self.api_client.update_task_status(
                                task_id=task_id,
                                status="completed",
                                result={"executed_at": datetime.now().isoformat()}
                            )
                            logger.info(f"✅ 任务执行成功: {task_id}")
                        else:
                            # 执行失败
                            await self.api_client.update_task_status(
                                task_id=task_id,
                                status="failed",
                                error="任务执行返回失败"
                            )
                            logger.warning(f"⚠️  任务执行失败: {task_id}")
                    
                    except Exception as e:
                        # 执行异常
                        error_msg = str(e)
                        logger.error(f"❌ 任务执行异常: {task_id}, 错误: {error_msg}", exc_info=True)
                        
                        try:
                            await self.api_client.update_task_status(
                                task_id=task_id,
                                status="failed",
                                error=error_msg
                            )
                        except Exception as update_error:
                            logger.error(f"更新任务状态失败: {update_error}")
                    
                    finally:
                        self.current_task_id = None
                        logger.info("=" * 60)
                        logger.info("")
                
                else:
                    # 无任务：休眠
                    await asyncio.sleep(self.poll_interval)
                
                # 重置连续错误计数
                consecutive_errors = 0
            
            except Exception as e:
                consecutive_errors += 1
                logger.error(
                    f"任务轮询循环错误 (连续错误 {consecutive_errors}/{max_consecutive_errors}): {e}",
                    exc_info=True
                )
                
                if consecutive_errors >= max_consecutive_errors:
                    logger.error("连续错误过多，等待 30 秒后重试...")
                    await asyncio.sleep(30)
                    consecutive_errors = 0
                else:
                    # 指数退避
                    wait_time = min(self.poll_interval * (2 ** consecutive_errors), 30)
                    logger.warning(f"等待 {wait_time:.1f} 秒后重试...")
                    await asyncio.sleep(wait_time)
    
    async def _execute_task(self, task: Dict[str, Any]) -> bool:
        """
        执行任务
        
        Args:
            task: 任务数据字典
        
        Returns:
            是否执行成功
        """
        task_type = task.get("task_type", "unknown")
        task_id = task.get("task_id")
        
        logger.info(f"开始执行任务: {task_id} (类型: {task_type})")
        
        try:
            if task_type == "scenario_execute":
                # 执行剧本任务
                return await self._execute_scenario_task(task)
            else:
                logger.warning(f"未知的任务类型: {task_type}")
                return False
        
        except Exception as e:
            logger.error(f"执行任务失败: {e}", exc_info=True)
            raise
    
    async def _execute_scenario_task(self, task: Dict[str, Any]) -> bool:
        """
        执行剧本任务
        
        Args:
            task: 任务数据字典，包含 scenario_data 和 variables
        
        Returns:
            是否执行成功
        """
        scenario_data = task.get("scenario_data", {})
        variables = task.get("variables", {})
        task_id = task.get("task_id")
        
        if not scenario_data:
            logger.error("任务中缺少 scenario_data")
            return False
        
        logger.info(f"执行剧本: {scenario_data.get('name', '未命名')}")
        logger.info(f"变量: {list(variables.keys())}")
        
        try:
            # 设置变量
            self.scenario_player.set_variables(variables)
            
            # 执行剧本
            await self.scenario_player.play(
                scenario=scenario_data,
                variables=variables,
                execution_id=task_id
            )
            
            return True
        
        except Exception as e:
            logger.error(f"执行剧本失败: {e}", exc_info=True)
            raise
    
    def stop(self):
        """停止任务管理器"""
        logger.info("正在停止任务管理器...")
        self.is_running = False
