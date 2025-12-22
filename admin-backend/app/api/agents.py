"""
Agent 管理 API - WebSocket 端点和 REST API
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from fastapi.responses import JSONResponse
from typing import List, Optional
import logging
import json

from app.websocket import get_websocket_manager, MessageHandler, MessageType
from app.api.deps import get_current_user
from app.schemas.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agents", tags=["agents"])


@router.websocket("/ws/{agent_id}")
async def websocket_endpoint(websocket: WebSocket, agent_id: str):
    """
    Agent WebSocket 连接端点
    
    Agent 连接到此端点后：
    1. 发送注册消息（包含 metadata）
    2. 定期发送心跳消息
    3. 接收 Server 指令
    4. 上报状态和任务结果
    """
    manager = get_websocket_manager()
    connection = None
    
    try:
        # 注册 Agent 连接
        connection = await manager.register_agent(agent_id, websocket)
        
        # 消息循环
        while True:
            try:
                # 接收消息
                data = await websocket.receive_text()
                
                # 解析消息
                message = MessageHandler.parse_message(data)
                if not message:
                    continue
                
                # 处理消息
                await manager.handle_message(agent_id, message)
                
            except WebSocketDisconnect:
                logger.info(f"Agent {agent_id} WebSocket 断开")
                break
            except Exception as e:
                logger.error(f"处理 Agent {agent_id} 消息时出错: {e}", exc_info=True)
                # 发送错误响应
                try:
                    await connection.send_json({
                        "type": "error",
                        "message": str(e),
                        "timestamp": MessageHandler.create_message(MessageType.ACK, {})["timestamp"]
                    })
                except:
                    pass
    
    except Exception as e:
        logger.error(f"Agent {agent_id} WebSocket 连接错误: {e}", exc_info=True)
    finally:
        # 清理连接
        if connection:
            await manager.unregister_agent(agent_id)


@router.get("/", response_model=List[dict])
async def list_agents(
    current_user: User = Depends(get_current_user)
):
    """
    获取所有 Agent 列表
    """
    manager = get_websocket_manager()
    connections = manager.get_all_connections()
    
    return [conn.to_dict() for conn in connections]


@router.get("/{agent_id}", response_model=dict)
async def get_agent(
    agent_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    获取指定 Agent 信息
    """
    manager = get_websocket_manager()
    connection = manager.get_connection(agent_id)
    
    if not connection:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} 未找到")
    
    return connection.to_dict()


@router.post("/{agent_id}/command")
async def send_command(
    agent_id: str,
    command: dict,
    current_user: User = Depends(get_current_user)
):
    """
    向指定 Agent 发送指令
    
    Request Body:
    {
        "action": "redpacket" | "chat" | "monitor",
        "payload": {...}
    }
    """
    manager = get_websocket_manager()
    
    action = command.get("action")
    payload = command.get("payload", {})
    
    if not action:
        raise HTTPException(status_code=400, detail="缺少 action 字段")
    
    # 创建指令消息
    message = MessageHandler.create_command_message(
        action=action,
        payload=payload,
        target_agent_id=agent_id
    )
    
    # 发送消息
    success = await manager.send_to_agent(agent_id, message)
    
    if not success:
        raise HTTPException(
            status_code=404,
            detail=f"Agent {agent_id} 未连接或连接已断开"
        )
    
    return {
        "success": True,
        "message": "指令已发送",
        "agent_id": agent_id,
        "action": action
    }


@router.post("/broadcast")
async def broadcast_command(
    command: dict,
    current_user: User = Depends(get_current_user)
):
    """
    向所有 Agent 广播指令
    
    Request Body:
    {
        "action": "redpacket" | "chat" | "monitor",
        "payload": {...},
        "exclude": ["agent_id1", "agent_id2"]  # 可选，排除的 Agent
    }
    """
    manager = get_websocket_manager()
    
    action = command.get("action")
    payload = command.get("payload", {})
    exclude = command.get("exclude", [])
    
    if not action:
        raise HTTPException(status_code=400, detail="缺少 action 字段")
    
    # 创建指令消息
    message = MessageHandler.create_command_message(
        action=action,
        payload=payload
    )
    
    # 广播消息
    await manager.broadcast(message, exclude=exclude)
    
    return {
        "success": True,
        "message": "指令已广播",
        "action": action,
        "exclude": exclude
    }


@router.get("/statistics", response_model=dict)
async def get_statistics(
    current_user: User = Depends(get_current_user)
):
    """
    获取 WebSocket 连接统计信息
    """
    manager = get_websocket_manager()
    return manager.get_statistics()
