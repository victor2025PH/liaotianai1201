"""
WebSocket 消息处理
"""

from enum import Enum
from typing import Dict, Any, Optional
from datetime import datetime
import json
import logging

logger = logging.getLogger(__name__)


class MessageType(str, Enum):
    """消息类型（与 Server 端保持一致）"""
    # Agent -> Server
    REGISTER = "register"
    STATUS = "status"
    HEARTBEAT = "heartbeat"
    RESULT = "result"
    
    # Server -> Agent
    COMMAND = "command"
    CONFIG = "config"
    ACK = "ack"


class MessageHandler:
    """消息处理器"""
    
    @staticmethod
    def create_message(
        message_type: MessageType,
        payload: Dict[str, Any],
        agent_id: Optional[str] = None
    ) -> dict:
        """创建标准消息格式"""
        message = {
            "type": message_type.value,
            "payload": payload,
            "timestamp": datetime.now().isoformat()
        }
        if agent_id:
            message["agent_id"] = agent_id
        return message
    
    @staticmethod
    def parse_message(data: str) -> Optional[Dict[str, Any]]:
        """解析消息"""
        try:
            message = json.loads(data)
            
            # 验证必需字段
            if "type" not in message:
                logger.warning("消息缺少 type 字段")
                return None
            
            # 验证消息类型
            try:
                MessageType(message["type"])
            except ValueError:
                logger.warning(f"未知的消息类型: {message['type']}")
                return None
            
            return message
        except json.JSONDecodeError as e:
            logger.error(f"消息 JSON 解析失败: {e}")
            return None
    
    @staticmethod
    def create_register_message(agent_id: str, metadata: Dict[str, Any]) -> dict:
        """创建注册消息"""
        return MessageHandler.create_message(
            MessageType.REGISTER,
            {
                "agent_id": agent_id,
                "metadata": metadata
            },
            agent_id=agent_id
        )
    
    @staticmethod
    def create_heartbeat_message(agent_id: str) -> dict:
        """创建心跳消息"""
        return MessageHandler.create_message(
            MessageType.HEARTBEAT,
            {},
            agent_id=agent_id
        )
    
    @staticmethod
    def create_status_message(
        agent_id: str,
        status: str,
        accounts: list = None,
        metrics: Dict[str, Any] = None
    ) -> dict:
        """创建状态上报消息"""
        payload = {
            "status": status,
            "accounts": accounts or [],
            "metrics": metrics or {}
        }
        return MessageHandler.create_message(
            MessageType.STATUS,
            payload,
            agent_id=agent_id
        )
    
    @staticmethod
    def create_result_message(
        agent_id: str,
        task_id: str,
        success: bool,
        result: Dict[str, Any] = None
    ) -> dict:
        """创建任务结果消息"""
        payload = {
            "task_id": task_id,
            "success": success,
            "result": result or {}
        }
        return MessageHandler.create_message(
            MessageType.RESULT,
            payload,
            agent_id=agent_id
        )
