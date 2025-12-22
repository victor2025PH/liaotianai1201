"""
智能剧场模块 - Phase 3: 多账号协同表演
实现拟人化消息发送逻辑（标记已读、输入状态、延迟、发送、上报）
"""

import asyncio
import logging
import random
from typing import Optional, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class TheaterHandler:
    """剧场处理器 - 处理剧场场景执行指令"""
    
    def __init__(self, client, websocket_client):
        """
        初始化剧场处理器
        
        Args:
            client: Telethon 客户端（用于操作 Telegram）
            websocket_client: WebSocket 客户端（用于上报结果）
        """
        self.client = client
        self.websocket_client = websocket_client
        self.active = True
    
    async def handle_theater_action(self, payload: Dict[str, Any]):
        """
        处理剧场动作指令（拟人化执行）
        
        指令格式:
        {
            "action": "theater_execute",
            "execution_id": "exec_xxx",
            "scenario_id": "scenario_xxx",
            "group_id": "123456789",
            "role": "UserA",
            "action_type": "send_message",
            "content": "你好",
            "payload": {
                "reply_to": 456  # 可选，回复的消息ID
            }
        }
        """
        try:
            execution_id = payload.get("execution_id")
            scenario_id = payload.get("scenario_id")
            group_id = payload.get("group_id")
            role = payload.get("role")
            action_type = payload.get("action_type", "send_message")
            content = payload.get("content", "")
            extra_payload = payload.get("payload", {})
            
            logger.info(
                f"[THEATER] 收到剧场动作指令: "
                f"执行ID={execution_id}, 场景ID={scenario_id}, 角色={role}, "
                f"动作={action_type}, 内容={content[:50]}"
            )
            
            if not self.client:
                logger.warning("[THEATER] Telethon 客户端未初始化，无法执行动作")
                await self._report_action_complete(
                    execution_id=execution_id,
                    success=False,
                    error="Telethon 客户端未初始化"
                )
                return
            
            # 根据动作类型执行
            if action_type == "send_message":
                await self._execute_send_message(
                    execution_id=execution_id,
                    group_id=group_id,
                    content=content,
                    reply_to=extra_payload.get("reply_to"),
                    role=role
                )
            else:
                logger.warning(f"[THEATER] 未知的动作类型: {action_type}")
                await self._report_action_complete(
                    execution_id=execution_id,
                    success=False,
                    error=f"未知的动作类型: {action_type}"
                )
        
        except Exception as e:
            logger.error(f"[THEATER] 处理剧场动作失败: {e}", exc_info=True)
            execution_id = payload.get("execution_id", "unknown")
            await self._report_action_complete(
                execution_id=execution_id,
                success=False,
                error=str(e)
            )
    
    async def _execute_send_message(
        self,
        execution_id: str,
        group_id: str,
        content: str,
        reply_to: Optional[int] = None,
        role: Optional[str] = None
    ):
        """
        执行发送消息动作（拟人化流程）
        
        Step 1: 标记已读
        Step 2: 计算输入耗时
        Step 3: 发送"正在输入"状态
        Step 4: 等待（模拟输入时间）
        Step 5: 发送消息
        Step 6: 上报完成
        """
        try:
            # 将 group_id 转换为整数（Telegram 群组 ID 通常是负数）
            try:
                chat_id = int(group_id)
            except (ValueError, TypeError):
                logger.error(f"[THEATER] 无效的群组ID: {group_id}")
                await self._report_action_complete(
                    execution_id=execution_id,
                    success=False,
                    error=f"无效的群组ID: {group_id}"
                )
                return
            
            # Step 1: 标记已读（如果客户端支持）
            try:
                # Telethon: client.send_read_acknowledge(chat_id)
                if hasattr(self.client, 'send_read_acknowledge'):
                    await self.client.send_read_acknowledge(chat_id)
                    logger.debug(f"[THEATER] 已标记群组 {chat_id} 为已读")
            except Exception as e:
                logger.warning(f"[THEATER] 标记已读失败（可忽略）: {e}")
            
            # Step 2: 计算输入耗时（拟人化）
            # 公式: duration = len(content) * 0.15 + random.uniform(1.0, 3.0)
            base_duration = len(content) * 0.15
            random_duration = random.uniform(1.0, 3.0)
            duration = base_duration + random_duration
            
            logger.info(
                f"[THEATER] 模拟输入中... "
                f"内容长度={len(content)}, 预计耗时={duration:.2f}秒"
            )
            
            # Step 3: 发送"正在输入"状态
            try:
                # Telethon: await client.action(chat_id, 'typing')
                if hasattr(self.client, 'action'):
                    await self.client.action(chat_id, 'typing')
                    logger.debug(f"[THEATER] 已发送'正在输入'状态到群组 {chat_id}")
            except Exception as e:
                logger.warning(f"[THEATER] 发送输入状态失败（可忽略）: {e}")
            
            # Step 4: 等待（模拟输入时间）
            await asyncio.sleep(duration)
            
            # Step 5: 发送消息
            try:
                # Telethon: await client.send_message(chat_id, content, reply_to=reply_to)
                send_options = {}
                if reply_to:
                    send_options['reply_to'] = reply_to
                
                if hasattr(self.client, 'send_message'):
                    sent_message = await self.client.send_message(chat_id, content, **send_options)
                    message_id = sent_message.id if hasattr(sent_message, 'id') else None
                    
                    logger.info(
                        f"[THEATER] 消息已发送: 群组={chat_id}, "
                        f"消息ID={message_id}, 内容={content[:50]}"
                    )
                else:
                    # 如果没有 Telethon 客户端，模拟发送
                    logger.warning("[THEATER] Telethon 客户端未实现 send_message，模拟发送")
                    message_id = None
                
                # Step 6: 上报完成
                await self._report_action_complete(
                    execution_id=execution_id,
                    success=True,
                    result={
                        "action_type": "send_message",
                        "chat_id": str(chat_id),
                        "message_id": message_id,
                        "content": content,
                        "reply_to": reply_to,
                        "duration_seconds": round(duration, 2),
                        "role": role
                    }
                )
            
            except Exception as e:
                logger.error(f"[THEATER] 发送消息失败: {e}", exc_info=True)
                await self._report_action_complete(
                    execution_id=execution_id,
                    success=False,
                    error=f"发送消息失败: {str(e)}"
                )
        
        except Exception as e:
            logger.error(f"[THEATER] 执行发送消息动作失败: {e}", exc_info=True)
            await self._report_action_complete(
                execution_id=execution_id,
                success=False,
                error=str(e)
            )
    
    async def _report_action_complete(
        self,
        execution_id: str,
        success: bool,
        result: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None
    ):
        """
        上报动作完成结果
        
        Args:
            execution_id: 执行ID
            success: 是否成功
            result: 成功时的结果数据
            error: 失败时的错误信息
        """
        try:
            from agent.websocket import MessageHandler, MessageType
            
            payload = {
                "task_id": execution_id,
                "success": success,
                "result": result or {},
                "error": error
            }
            
            message = MessageHandler.create_result_message(
                agent_id=self.websocket_client.agent_id,
                task_id=execution_id,
                success=success,
                result=payload
            )
            
            await self.websocket_client.send_message(message)
            
            logger.info(
                f"[THEATER] 已上报动作完成: 执行ID={execution_id}, "
                f"成功={success}, 错误={error or '无'}"
            )
        
        except Exception as e:
            logger.error(f"[THEATER] 上报动作完成失败: {e}", exc_info=True)
