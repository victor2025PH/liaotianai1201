"""
智能剧场调度器 - Phase 3: 多账号协同表演
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

from app.websocket import get_websocket_manager, MessageHandler, MessageType

logger = logging.getLogger(__name__)


class TheaterScheduler:
    """剧场调度器"""
    
    def __init__(self):
        self.running_executions: Dict[str, asyncio.Task] = {}
        self.manager = get_websocket_manager()
    
    async def execute_scenario(
        self,
        scenario_id: str,
        scenario_name: str,
        group_id: str,
        timeline: List[Dict[str, Any]],
        agent_mapping: Dict[str, str]
    ) -> str:
        """
        执行剧场场景
        
        Args:
            scenario_id: 场景ID
            scenario_name: 场景名称
            group_id: 目标群组ID
            timeline: 时间轴动作列表
            agent_mapping: Agent 映射 {"UserA": "agent_id_1", "UserB": "agent_id_2"}
        
        Returns:
            执行记录ID
        """
        execution_id = f"exec_{scenario_id}_{int(datetime.now().timestamp())}"
        
        # 验证 Agent 映射
        required_roles = {action.get("role") for action in timeline if action.get("role")}
        mapped_agents = set(agent_mapping.keys())
        
        if not required_roles.issubset(mapped_agents):
            missing_roles = required_roles - mapped_agents
            raise ValueError(f"缺少角色映射: {missing_roles}")
        
        # 验证 Agent 是否在线
        for role, agent_id in agent_mapping.items():
            connection = self.manager.get_connection(agent_id)
            if not connection or not connection.is_alive():
                raise ValueError(f"Agent {agent_id} (角色: {role}) 未在线")
        
        # 创建执行任务
        task = asyncio.create_task(
            self._execute_timeline(
                execution_id,
                scenario_id,
                scenario_name,
                group_id,
                timeline,
                agent_mapping
            )
        )
        
        self.running_executions[execution_id] = task
        
        logger.info(
            f"[THEATER] 开始执行场景: {scenario_name} (ID: {scenario_id}, 执行ID: {execution_id})"
        )
        
        return execution_id
    
    async def _execute_timeline(
        self,
        execution_id: str,
        scenario_id: str,
        scenario_name: str,
        group_id: str,
        timeline: List[Dict[str, Any]],
        agent_mapping: Dict[str, str]
    ):
        """执行时间轴"""
        start_time = datetime.now()
        executed_actions = []
        
        try:
            # 按时间偏移排序
            sorted_timeline = sorted(timeline, key=lambda x: x.get("time_offset", 0))
            
            if not sorted_timeline:
                logger.warning(f"[THEATER] 时间轴为空，跳过执行")
                return
            
            last_offset = 0
            
            for action in sorted_timeline:
                time_offset = action.get("time_offset", 0)
                role = action.get("role")
                content = action.get("content", "")
                action_type = action.get("action", "send_message")
                payload = action.get("payload", {})
                
                # 计算等待时间
                wait_seconds = time_offset - last_offset
                if wait_seconds > 0:
                    logger.info(
                        f"[THEATER] 等待 {wait_seconds} 秒 (时间偏移: {time_offset}s)"
                    )
                    await asyncio.sleep(wait_seconds)
                
                # 获取对应的 Agent ID
                agent_id = agent_mapping.get(role)
                if not agent_id:
                    logger.warning(f"[THEATER] 角色 {role} 没有对应的 Agent，跳过")
                    continue
                
                # 发送执行指令
                message = MessageHandler.create_message(
                    MessageType.COMMAND,
                    {
                        "action": "theater_execute",
                        "execution_id": execution_id,
                        "scenario_id": scenario_id,
                        "group_id": group_id,
                        "role": role,
                        "action_type": action_type,
                        "content": content,
                        "payload": payload
                    }
                )
                
                success = await self.manager.send_to_agent(agent_id, message)
                
                if success:
                    executed_actions.append({
                        "time_offset": time_offset,
                        "role": role,
                        "agent_id": agent_id,
                        "action_type": action_type,
                        "content": content,
                        "executed_at": datetime.now().isoformat(),
                        "success": True
                    })
                    logger.info(
                        f"[THEATER] 已发送指令: {role} -> {agent_id} "
                        f"(动作: {action_type}, 内容: {content[:50]})"
                    )
                else:
                    executed_actions.append({
                        "time_offset": time_offset,
                        "role": role,
                        "agent_id": agent_id,
                        "action_type": action_type,
                        "content": content,
                        "executed_at": datetime.now().isoformat(),
                        "success": False,
                        "error": "Agent 未连接"
                    })
                    logger.error(
                        f"[THEATER] 发送指令失败: {role} -> {agent_id} (Agent 未连接)"
                    )
                
                last_offset = time_offset
            
            # 执行完成
            end_time = datetime.now()
            duration = int((end_time - start_time).total_seconds())
            
            logger.info(
                f"[THEATER] 场景执行完成: {scenario_name} "
                f"(执行ID: {execution_id}, 耗时: {duration}s, 动作数: {len(executed_actions)})"
            )
            
        except asyncio.CancelledError:
            logger.info(f"[THEATER] 场景执行被取消: {execution_id}")
            raise
        except Exception as e:
            logger.error(f"[THEATER] 场景执行失败: {execution_id}, 错误: {e}", exc_info=True)
            raise
        finally:
            # 清理执行记录
            if execution_id in self.running_executions:
                del self.running_executions[execution_id]
    
    def cancel_execution(self, execution_id: str) -> bool:
        """取消执行"""
        if execution_id in self.running_executions:
            task = self.running_executions[execution_id]
            task.cancel()
            del self.running_executions[execution_id]
            logger.info(f"[THEATER] 已取消执行: {execution_id}")
            return True
        return False
    
    def get_running_executions(self) -> List[str]:
        """获取正在执行的执行ID列表"""
        return list(self.running_executions.keys())


# 全局调度器实例
_scheduler: Optional[TheaterScheduler] = None


def get_theater_scheduler() -> TheaterScheduler:
    """获取剧场调度器实例（单例）"""
    global _scheduler
    if _scheduler is None:
        _scheduler = TheaterScheduler()
    return _scheduler
