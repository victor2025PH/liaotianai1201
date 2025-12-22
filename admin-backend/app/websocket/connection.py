"""
Agent 连接管理
"""

from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum
from fastapi import WebSocket
import json
import logging

logger = logging.getLogger(__name__)


class ConnectionStatus(str, Enum):
    """连接状态"""
    CONNECTING = "connecting"
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"


class AgentConnection:
    """Agent 连接对象"""
    
    def __init__(self, agent_id: str, websocket: WebSocket):
        self.agent_id = agent_id
        self.websocket = websocket
        self.status = ConnectionStatus.CONNECTING
        self.connected_at = datetime.now()
        self.last_heartbeat = datetime.now()
        self.metadata: Dict[str, Any] = {}
        
    async def accept(self):
        """接受 WebSocket 连接"""
        await self.websocket.accept()
        self.status = ConnectionStatus.CONNECTED
        logger.info(f"Agent {self.agent_id} 连接已接受")
    
    async def send_json(self, data: dict):
        """发送 JSON 消息"""
        try:
            await self.websocket.send_json(data)
            return True
        except Exception as e:
            logger.error(f"向 Agent {self.agent_id} 发送消息失败: {e}")
            self.status = ConnectionStatus.ERROR
            return False
    
    async def send_text(self, text: str):
        """发送文本消息"""
        try:
            await self.websocket.send_text(text)
            return True
        except Exception as e:
            logger.error(f"向 Agent {self.agent_id} 发送文本失败: {e}")
            self.status = ConnectionStatus.ERROR
            return False
    
    async def receive_text(self) -> Optional[str]:
        """接收文本消息"""
        try:
            return await self.websocket.receive_text()
        except Exception as e:
            logger.error(f"从 Agent {self.agent_id} 接收消息失败: {e}")
            self.status = ConnectionStatus.ERROR
            return None
    
    async def receive_json(self) -> Optional[dict]:
        """接收 JSON 消息"""
        try:
            text = await self.receive_text()
            if text:
                return json.loads(text)
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Agent {self.agent_id} 消息 JSON 解析失败: {e}")
            return None
    
    def update_heartbeat(self):
        """更新心跳时间"""
        self.last_heartbeat = datetime.now()
    
    def is_alive(self, timeout_seconds: int = 60) -> bool:
        """检查连接是否存活"""
        if self.status != ConnectionStatus.CONNECTED:
            return False
        
        elapsed = (datetime.now() - self.last_heartbeat).total_seconds()
        return elapsed < timeout_seconds
    
    def disconnect(self):
        """断开连接"""
        self.status = ConnectionStatus.DISCONNECTED
        logger.info(f"Agent {self.agent_id} 连接已断开")
    
    def to_dict(self) -> dict:
        """转换为字典（用于 API 返回）"""
        return {
            "agent_id": self.agent_id,
            "status": self.status.value,
            "connected_at": self.connected_at.isoformat(),
            "last_heartbeat": self.last_heartbeat.isoformat(),
            "is_alive": self.is_alive(),
            "metadata": self.metadata
        }
