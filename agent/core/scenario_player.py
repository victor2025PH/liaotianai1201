"""
剧本执行器 - Phase 5: 剧本执行引擎
解析和执行剧场模式定义的 JSON 脚本
"""

import asyncio
import logging
import random
import re
from typing import Dict, Any, List, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class ScenarioPlayer:
    """剧本执行器 - 执行剧场场景"""
    
    def __init__(self, client):
        """
        初始化剧本执行器
        
        Args:
            client: Telethon 客户端（用于操作 Telegram）
        """
        self.client = client
        self.variables: Dict[str, Any] = {}
        self.is_playing = False
        self.current_execution_id: Optional[str] = None
    
    def set_variables(self, variables: Dict[str, Any]):
        """
        设置上下文变量
        
        Args:
            variables: 变量字典，例如 {"target_user": "张三", "group_id": "123456789"}
        """
        self.variables.update(variables)
        logger.info(f"[SCENARIO] 设置变量: {list(variables.keys())}")
    
    def resolve_variables(self, text: str) -> str:
        """
        解析变量占位符
        
        Args:
            text: 包含变量占位符的文本，例如 "你好 {target_user}"
        
        Returns:
            解析后的文本，例如 "你好 张三"
        """
        if not text:
            return text
        
        def replace_var(match):
            var_name = match.group(1)
            return str(self.variables.get(var_name, match.group(0)))
        
        # 支持 {variable_name} 格式
        resolved = re.sub(r'\{(\w+)\}', replace_var, text)
        return resolved
    
    async def play(
        self,
        scenario: Dict[str, Any],
        variables: Optional[Dict[str, Any]] = None,
        execution_id: Optional[str] = None
    ):
        """
        执行剧本
        
        Args:
            scenario: 剧本数据字典，包含 timeline 字段
            variables: 上下文变量（可选）
            execution_id: 执行ID（用于上报结果）
        
        剧本格式:
        {
            "name": "测试剧本",
            "timeline": [
                {
                    "time_offset": 2,
                    "role": "UserA",
                    "content": "你好 {target_user}",
                    "action": "send_message"
                },
                {
                    "time_offset": 5,
                    "action": "wait",
                    "duration": 3
                }
            ]
        }
        """
        if self.is_playing:
            logger.warning("[SCENARIO] 已有剧本正在执行，忽略新请求")
            return
        
        self.is_playing = True
        self.current_execution_id = execution_id or f"exec_{int(asyncio.get_event_loop().time())}"
        
        try:
            # 设置变量
            if variables:
                self.set_variables(variables)
            
            # 获取时间轴
            timeline = scenario.get("timeline", [])
            if not timeline:
                logger.warning("[SCENARIO] 时间轴为空，跳过执行")
                return
            
            scenario_name = scenario.get("name", "未命名剧本")
            logger.info(
                f"[SCENARIO] 开始执行剧本: {scenario_name} "
                f"(执行ID: {self.current_execution_id}, 动作数: {len(timeline)})"
            )
            
            # 按时间偏移排序
            sorted_timeline = sorted(timeline, key=lambda x: x.get("time_offset", 0))
            
            # 执行时间轴
            last_offset = 0
            for action in sorted_timeline:
                time_offset = action.get("time_offset", 0)
                
                # 计算等待时间（相对于上一个动作）
                wait_time = time_offset - last_offset
                if wait_time > 0:
                    # 添加随机波动（±10%）模拟真人
                    jitter = wait_time * 0.1
                    actual_wait = wait_time + random.uniform(-jitter, jitter)
                    actual_wait = max(0.1, actual_wait)  # 至少等待 0.1 秒
                    
                    logger.info(f"[SCENARIO] 等待 {actual_wait:.2f} 秒 (计划: {wait_time}秒)")
                    await asyncio.sleep(actual_wait)
                
                # 执行动作
                await self.execute_action(action)
                
                last_offset = time_offset
            
            logger.info(f"[SCENARIO] 剧本执行完成: {scenario_name}")
        
        except Exception as e:
            logger.error(f"[SCENARIO] 执行剧本失败: {e}", exc_info=True)
            raise
        finally:
            self.is_playing = False
            self.current_execution_id = None
    
    async def execute_action(self, action: Dict[str, Any]):
        """
        执行单个动作
        
        Args:
            action: 动作字典，包含 type, content, role 等字段
        """
        action_type = action.get("action", action.get("type", "send_message"))
        
        logger.info(f"[SCENARIO] 执行动作: {action_type}")
        
        try:
            if action_type == "send_message":
                await self._execute_send_message(action)
            elif action_type == "wait":
                await self._execute_wait(action)
            elif action_type == "join_channel":
                await self._execute_join_channel(action)
            else:
                logger.warning(f"[SCENARIO] 未知的动作类型: {action_type}")
        
        except Exception as e:
            logger.error(f"[SCENARIO] 执行动作失败 ({action_type}): {e}", exc_info=True)
            raise
    
    async def _execute_send_message(self, action: Dict[str, Any]):
        """
        执行发送消息动作
        
        动作格式:
        {
            "action": "send_message",
            "role": "UserA",
            "content": "你好 {target_user}",
            "chat_id": "123456789",  # 可选，如果不提供则使用变量中的 group_id
            "reply_to": 456  # 可选，回复的消息ID
        }
        """
        if not self.client:
            logger.warning("[SCENARIO] Telethon 客户端未初始化，模拟发送消息")
            content = action.get("content", "")
            resolved_content = self.resolve_variables(content)
            logger.info(f"[SCENARIO] [模拟] 发送消息: {resolved_content[:50]}")
            return
        
        # 解析内容（替换变量）
        content = action.get("content", "")
        resolved_content = self.resolve_variables(content)
        
        # 获取聊天ID
        chat_id = action.get("chat_id")
        if not chat_id:
            # 尝试从变量中获取
            chat_id = self.variables.get("group_id") or self.variables.get("chat_id")
        
        if not chat_id:
            raise ValueError("未指定 chat_id，且变量中也没有 group_id")
        
        # 转换为整数（Telegram 群组 ID 通常是负数）
        try:
            chat_id = int(chat_id)
        except (ValueError, TypeError):
            raise ValueError(f"无效的聊天ID: {chat_id}")
        
        # 获取回复消息ID（可选）
        reply_to = action.get("reply_to")
        if reply_to:
            try:
                reply_to = int(reply_to)
            except (ValueError, TypeError):
                logger.warning(f"[SCENARIO] 无效的回复消息ID: {reply_to}，忽略")
                reply_to = None
        
        # 拟人化流程
        # Step 1: 标记已读
        try:
            if hasattr(self.client, 'send_read_acknowledge'):
                await self.client.send_read_acknowledge(chat_id)
                logger.debug(f"[SCENARIO] 已标记群组 {chat_id} 为已读")
        except Exception as e:
            logger.warning(f"[SCENARIO] 标记已读失败（可忽略）: {e}")
        
        # Step 2: 计算输入耗时（拟人化）
        base_duration = len(resolved_content) * 0.15
        random_duration = random.uniform(1.0, 3.0)
        duration = base_duration + random_duration
        
        logger.info(
            f"[SCENARIO] 模拟输入中... "
            f"内容长度={len(resolved_content)}, 预计耗时={duration:.2f}秒"
        )
        
        # Step 3: 发送"正在输入"状态
        try:
            if hasattr(self.client, 'action'):
                await self.client.action(chat_id, 'typing')
                logger.debug(f"[SCENARIO] 已发送'正在输入'状态")
        except Exception as e:
            logger.warning(f"[SCENARIO] 发送输入状态失败（可忽略）: {e}")
        
        # Step 4: 等待（模拟输入时间）
        await asyncio.sleep(duration)
        
        # Step 5: 发送消息
        send_options = {}
        if reply_to:
            send_options['reply_to'] = reply_to
        
        if hasattr(self.client, 'send_message'):
            sent_message = await self.client.send_message(chat_id, resolved_content, **send_options)
            message_id = sent_message.id if hasattr(sent_message, 'id') else None
            
            logger.info(
                f"[SCENARIO] 消息已发送: 群组={chat_id}, "
                f"消息ID={message_id}, 内容={resolved_content[:50]}"
            )
        else:
            logger.warning("[SCENARIO] Telethon 客户端未实现 send_message，模拟发送")
    
    async def _execute_wait(self, action: Dict[str, Any]):
        """
        执行等待动作
        
        动作格式:
        {
            "action": "wait",
            "duration": 5  # 等待秒数
        }
        """
        duration = action.get("duration", 1)
        
        # 添加随机波动（±10%）
        jitter = duration * 0.1
        actual_duration = duration + random.uniform(-jitter, jitter)
        actual_duration = max(0.1, actual_duration)  # 至少等待 0.1 秒
        
        logger.info(f"[SCENARIO] 等待 {actual_duration:.2f} 秒 (计划: {duration}秒)")
        await asyncio.sleep(actual_duration)
    
    async def _execute_join_channel(self, action: Dict[str, Any]):
        """
        执行加入频道/群组动作
        
        动作格式:
        {
            "action": "join_channel",
            "chat_id": "123456789"  # 或使用变量 {target_chat_id}
        }
        """
        if not self.client:
            logger.warning("[SCENARIO] Telethon 客户端未初始化，无法加入频道")
            return
        
        chat_id = action.get("chat_id")
        if not chat_id:
            chat_id = self.variables.get("target_chat_id") or self.variables.get("chat_id")
        
        if not chat_id:
            raise ValueError("未指定 chat_id，且变量中也没有 target_chat_id")
        
        # 解析变量
        chat_id = self.resolve_variables(str(chat_id))
        
        try:
            chat_id = int(chat_id)
        except (ValueError, TypeError):
            # 可能是用户名，直接使用
            pass
        
        try:
            # Telethon: JoinChannelRequest
            from telethon.tl.functions.channels import JoinChannelRequest
            from telethon.tl.functions.messages import ImportChatInviteRequest
            
            # 尝试作为频道加入
            try:
                await self.client(JoinChannelRequest(chat_id))
                logger.info(f"[SCENARIO] 已加入频道/群组: {chat_id}")
            except Exception as e1:
                # 如果失败，可能是邀请链接，尝试其他方法
                logger.warning(f"[SCENARIO] 加入频道失败，尝试其他方法: {e1}")
                # 这里可以添加更多处理逻辑
                raise
        
        except Exception as e:
            logger.error(f"[SCENARIO] 加入频道失败: {e}", exc_info=True)
            raise


def load_scenario_from_file(file_path: str) -> Dict[str, Any]:
    """
    从 JSON 文件加载剧本
    
    Args:
        file_path: JSON 文件路径
    
    Returns:
        剧本数据字典
    """
    import json
    
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"剧本文件不存在: {file_path}")
    
    with open(path, "r", encoding="utf-8") as f:
        scenario = json.load(f)
    
    logger.info(f"[SCENARIO] 已加载剧本文件: {file_path}")
    return scenario
