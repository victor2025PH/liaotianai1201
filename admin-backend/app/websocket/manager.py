"""
WebSocket 管理器 - Agent 连接管理
"""

import asyncio
from typing import Dict, Optional, List, Callable
from datetime import datetime, timedelta
import logging
from fastapi import WebSocket, WebSocketDisconnect

from .connection import AgentConnection, ConnectionStatus
from .message_handler import MessageHandler, MessageType

logger = logging.getLogger(__name__)


class WebSocketManager:
    """WebSocket 管理器 - 管理所有 Agent 连接"""
    
    def __init__(self):
        self.connections: Dict[str, AgentConnection] = {}
        self.message_handlers: Dict[MessageType, List[Callable]] = {}
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._cleanup_task: Optional[asyncio.Task] = None
    
    async def start(self):
        """启动管理器（启动后台任务）"""
        if self._heartbeat_task is None:
            self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
        if self._cleanup_task is None:
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        logger.info("WebSocket Manager 已启动")
    
    async def stop(self):
        """停止管理器"""
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
        if self._cleanup_task:
            self._cleanup_task.cancel()
        logger.info("WebSocket Manager 已停止")
    
    async def register_agent(
        self,
        agent_id: str,
        websocket: WebSocket,
        metadata: Optional[Dict] = None
    ) -> AgentConnection:
        """
        注册 Agent 连接
        
        Args:
            agent_id: Agent 唯一标识
            websocket: WebSocket 连接
            metadata: Agent 元数据（IP、版本等）
        
        Returns:
            AgentConnection 对象
        """
        # 如果已存在连接，先断开旧连接
        if agent_id in self.connections:
            logger.warning(f"Agent {agent_id} 已存在连接，断开旧连接")
            old_conn = self.connections[agent_id]
            old_conn.disconnect()
        
        # 创建新连接
        connection = AgentConnection(agent_id, websocket)
        if metadata:
            connection.metadata = metadata
        
        await connection.accept()
        self.connections[agent_id] = connection
        
        logger.info(f"Agent {agent_id} 已注册，当前连接数: {len(self.connections)}")
        
        # 发送注册确认
        await connection.send_json(
            MessageHandler.create_ack_message(agent_id)
        )
        
        return connection
    
    async def unregister_agent(self, agent_id: str):
        """注销 Agent 连接"""
        if agent_id in self.connections:
            connection = self.connections[agent_id]
            connection.disconnect()
            del self.connections[agent_id]
            logger.info(f"Agent {agent_id} 已注销，当前连接数: {len(self.connections)}")
    
    def get_connection(self, agent_id: str) -> Optional[AgentConnection]:
        """获取 Agent 连接"""
        return self.connections.get(agent_id)
    
    def get_all_connections(self) -> List[AgentConnection]:
        """获取所有连接"""
        return list(self.connections.values())
    
    def get_online_agents(self) -> List[str]:
        """获取所有在线 Agent ID"""
        return [
            agent_id for agent_id, conn in self.connections.items()
            if conn.is_alive()
        ]
    
    async def send_to_agent(
        self,
        agent_id: str,
        message: dict
    ) -> bool:
        """
        向指定 Agent 发送消息
        
        Args:
            agent_id: Agent ID
            message: 消息内容
        
        Returns:
            是否发送成功
        """
        connection = self.get_connection(agent_id)
        if not connection:
            logger.warning(f"Agent {agent_id} 未连接")
            return False
        
        if not connection.is_alive():
            logger.warning(f"Agent {agent_id} 连接已断开")
            await self.unregister_agent(agent_id)
            return False
        
        return await connection.send_json(message)
    
    async def broadcast(self, message: dict, exclude: Optional[List[str]] = None):
        """
        广播消息给所有 Agent
        
        Args:
            message: 消息内容
            exclude: 排除的 Agent ID 列表
        """
        exclude = exclude or []
        disconnected = []
        
        for agent_id, connection in self.connections.items():
            if agent_id in exclude:
                continue
            
            if not connection.is_alive():
                disconnected.append(agent_id)
                continue
            
            success = await connection.send_json(message)
            if not success:
                disconnected.append(agent_id)
        
        # 清理断开的连接
        for agent_id in disconnected:
            await self.unregister_agent(agent_id)
    
    async def handle_message(
        self,
        agent_id: str,
        message: dict
    ):
        """
        处理来自 Agent 的消息
        
        Args:
            agent_id: Agent ID
            message: 消息内容
        """
        message_type_str = message.get("type")
        if not message_type_str:
            logger.warning(f"Agent {agent_id} 消息缺少 type 字段")
            return
        
        try:
            message_type = MessageType(message_type_str)
        except ValueError:
            logger.warning(f"Agent {agent_id} 未知消息类型: {message_type_str}")
            return
        
        connection = self.get_connection(agent_id)
        if not connection:
            logger.warning(f"Agent {agent_id} 连接不存在")
            return
        
        # 更新心跳时间
        if message_type == MessageType.HEARTBEAT:
            connection.update_heartbeat()
            # 回复心跳
            await connection.send_json(
                MessageHandler.create_ack_message(agent_id)
            )
            return
        
        # 处理注册消息
        if message_type == MessageType.REGISTER:
            payload = message.get("payload", {})
            metadata = payload.get("metadata", {})
            connection.metadata.update(metadata)
            logger.info(f"Agent {agent_id} 注册信息已更新")
            return
        
        # 处理状态上报
        if message_type == MessageType.STATUS:
            payload = message.get("payload", {})
            # 这里可以保存状态到数据库或缓存
            logger.debug(f"Agent {agent_id} 状态已更新: {payload.get('status')}")
            return
        
        # 处理任务结果
        if message_type == MessageType.RESULT:
            payload = message.get("payload", {})
            # 这里可以处理任务结果
            logger.info(f"Agent {agent_id} 任务结果: {payload.get('task_id')}")
            return
        
        # 调用注册的消息处理器
        if message_type in self.message_handlers:
            for handler in self.message_handlers[message_type]:
                try:
                    await handler(agent_id, message)
                except Exception as e:
                    logger.error(f"消息处理器执行失败: {e}", exc_info=True)
    
    def register_message_handler(
        self,
        message_type: MessageType,
        handler: Callable
    ):
        """注册消息处理器"""
        if message_type not in self.message_handlers:
            self.message_handlers[message_type] = []
        self.message_handlers[message_type].append(handler)
        logger.info(f"已注册 {message_type.value} 消息处理器")
    
    async def _heartbeat_loop(self):
        """心跳循环（定期检查连接状态）"""
        while True:
            try:
                await asyncio.sleep(30)  # 每30秒检查一次
                
                # 检查所有连接的心跳
                dead_connections = []
                for agent_id, connection in self.connections.items():
                    if not connection.is_alive(timeout_seconds=60):
                        logger.warning(f"Agent {agent_id} 心跳超时")
                        dead_connections.append(agent_id)
                
                # 清理死连接
                for agent_id in dead_connections:
                    await self.unregister_agent(agent_id)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"心跳循环错误: {e}", exc_info=True)
    
    async def _cleanup_loop(self):
        """清理循环（定期清理无效连接）"""
        while True:
            try:
                await asyncio.sleep(300)  # 每5分钟清理一次
                
                # 清理所有非活跃连接
                inactive_connections = []
                for agent_id, connection in self.connections.items():
                    if connection.status == ConnectionStatus.DISCONNECTED:
                        inactive_connections.append(agent_id)
                
                for agent_id in inactive_connections:
                    await self.unregister_agent(agent_id)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"清理循环错误: {e}", exc_info=True)
    
    def get_statistics(self) -> dict:
        """获取统计信息"""
        online_count = len(self.get_online_agents())
        total_count = len(self.connections)
        
        return {
            "total_connections": total_count,
            "online_connections": online_count,
            "offline_connections": total_count - online_count,
            "agents": [
                conn.to_dict() for conn in self.connections.values()
            ]
        }


# 全局 WebSocket 管理器实例
_websocket_manager: Optional[WebSocketManager] = None


def get_websocket_manager() -> WebSocketManager:
    """获取 WebSocket 管理器实例（单例模式）"""
    global _websocket_manager
    if _websocket_manager is None:
        _websocket_manager = WebSocketManager()
    return _websocket_manager
