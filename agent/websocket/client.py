"""
WebSocket 客户端 - 连接到 Server
"""

import asyncio
import logging
from typing import Optional, Callable, Dict, Any
from datetime import datetime
import aiohttp
from aiohttp import ClientWebSocketResponse

from agent.config import (
    get_agent_id,
    get_server_url,
    get_heartbeat_interval,
    get_reconnect_interval,
    get_reconnect_max_attempts,
    get_metadata,
    update_metadata
)
from agent.websocket.message_handler import MessageHandler, MessageType

logger = logging.getLogger(__name__)


class WebSocketClient:
    """WebSocket 客户端"""
    
    def __init__(self):
        self.agent_id = get_agent_id()
        self.server_url = get_server_url()
        self.heartbeat_interval = get_heartbeat_interval()
        self.reconnect_interval = get_reconnect_interval()
        self.reconnect_max_attempts = get_reconnect_max_attempts()
        
        self.ws: Optional[ClientWebSocketResponse] = None
        self.session: Optional[aiohttp.ClientSession] = None
        self.connected = False
        self.running = False
        
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._receive_task: Optional[asyncio.Task] = None
        self._reconnect_task: Optional[asyncio.Task] = None
        
        self.message_handlers: Dict[MessageType, list] = {}
        self.reconnect_attempts = 0
    
    def register_message_handler(
        self,
        message_type: MessageType,
        handler: Callable[[Dict[str, Any]], None]
    ):
        """注册消息处理器"""
        if message_type not in self.message_handlers:
            self.message_handlers[message_type] = []
        self.message_handlers[message_type].append(handler)
        logger.info(f"已注册 {message_type.value} 消息处理器")
    
    async def connect(self) -> bool:
        """
        连接到 Server
        
        Returns:
            是否连接成功
        """
        try:
            logger.info(f"[INFO] 正在连接服务器: {self.server_url}")
            
            # 创建 aiohttp session
            if self.session is None:
                self.session = aiohttp.ClientSession()
            
            # 连接 WebSocket
            self.ws = await self.session.ws_connect(
                self.server_url,
                heartbeat=self.heartbeat_interval
            )
            
            self.connected = True
            self.reconnect_attempts = 0
            logger.info(f"[SUCCESS] 连接成功! Agent ID: {self.agent_id}")
            
            # 发送注册消息
            await self._send_register()
            
            # 启动接收任务
            self._receive_task = asyncio.create_task(self._receive_loop())
            
            # 启动心跳任务
            self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
            
            return True
            
        except Exception as e:
            logger.error(f"[ERROR] 连接失败: {e}")
            self.connected = False
            return False
    
    async def disconnect(self):
        """断开连接"""
        self.connected = False
        self.running = False
        
        # 取消任务
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
        if self._receive_task:
            self._receive_task.cancel()
        
        # 关闭 WebSocket
        if self.ws:
            try:
                await self.ws.close()
            except:
                pass
            self.ws = None
        
        logger.info("[INFO] 已断开连接")
    
    async def _send_register(self):
        """发送注册消息"""
        metadata = get_metadata()
        message = MessageHandler.create_register_message(self.agent_id, metadata)
        await self.send_message(message)
        logger.info(f"[REGISTER] 已发送注册消息，元数据: {metadata}")
    
    async def send_message(self, message: dict) -> bool:
        """
        发送消息
        
        Args:
            message: 消息字典
        
        Returns:
            是否发送成功
        """
        if not self.connected or not self.ws:
            logger.warning("[WARNING] 未连接，无法发送消息")
            return False
        
        try:
            await self.ws.send_json(message)
            return True
        except Exception as e:
            logger.error(f"[ERROR] 发送消息失败: {e}")
            self.connected = False
            return False
    
    async def _heartbeat_loop(self):
        """心跳循环"""
        while self.connected and self.running:
            try:
                await asyncio.sleep(self.heartbeat_interval)
                
                if not self.connected:
                    break
                
                # 发送心跳
                message = MessageHandler.create_heartbeat_message(self.agent_id)
                success = await self.send_message(message)
                
                if success:
                    logger.debug(f"[HEARTBEAT] 心跳发送 ({datetime.now().strftime('%H:%M:%S')})")
                else:
                    logger.warning("[WARNING] 心跳发送失败")
                    break
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"[ERROR] 心跳循环错误: {e}")
                break
    
    async def _receive_loop(self):
        """接收消息循环"""
        while self.connected and self.running:
            try:
                if not self.ws:
                    break
                
                # 接收消息
                msg = await self.ws.receive()
                
                if msg.type == aiohttp.WSMsgType.TEXT:
                    # 解析消息
                    message = MessageHandler.parse_message(msg.data)
                    if message:
                        await self._handle_message(message)
                
                elif msg.type == aiohttp.WSMsgType.ERROR:
                    logger.error(f"[ERROR] WebSocket 错误: {self.ws.exception()}")
                    break
                
                elif msg.type == aiohttp.WSMsgType.CLOSE:
                    logger.info("[INFO] WebSocket 连接已关闭")
                    break
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"[ERROR] 接收消息错误: {e}")
                break
        
        # 连接断开，触发重连
        self.connected = False
        if self.running:
            await self._start_reconnect()
    
    async def _handle_message(self, message: dict):
        """处理接收到的消息"""
        message_type_str = message.get("type")
        if not message_type_str:
            return
        
        try:
            message_type = MessageType(message_type_str)
        except ValueError:
            logger.warning(f"[WARNING] 未知消息类型: {message_type_str}")
            return
        
        # 调用注册的处理器
        if message_type in self.message_handlers:
            for handler in self.message_handlers[message_type]:
                try:
                    await handler(message) if asyncio.iscoroutinefunction(handler) else handler(message)
                except Exception as e:
                    logger.error(f"[ERROR] 消息处理器执行失败: {e}", exc_info=True)
        
        # 默认处理
        if message_type == MessageType.ACK:
            logger.debug("[ACK] 收到确认消息")
        elif message_type == MessageType.COMMAND:
            logger.info(f"[COMMAND] 收到指令: {message.get('payload', {}).get('action')}")
        elif message_type == MessageType.CONFIG:
            logger.info("[CONFIG] 收到配置更新")
    
    async def _start_reconnect(self):
        """启动重连任务"""
        if self._reconnect_task and not self._reconnect_task.done():
            return  # 已有重连任务在运行
        
        self._reconnect_task = asyncio.create_task(self._reconnect_loop())
    
    async def _reconnect_loop(self):
        """重连循环"""
        logger.info("[INFO] 开始自动重连...")
        
        while self.running:
            # 检查重连次数限制
            if self.reconnect_max_attempts > 0:
                if self.reconnect_attempts >= self.reconnect_max_attempts:
                    logger.error(f"[ERROR] 达到最大重连次数 ({self.reconnect_max_attempts})，停止重连")
                    break
            
            self.reconnect_attempts += 1
            logger.info(f"[INFO] 尝试重连 ({self.reconnect_attempts})...")
            
            # 等待重连间隔
            await asyncio.sleep(self.reconnect_interval)
            
            # 尝试重连
            success = await self.connect()
            if success:
                logger.info("[SUCCESS] 重连成功!")
                break
    
    async def start(self):
        """启动客户端"""
        self.running = True
        
        # 首次连接
        success = await self.connect()
        if not success:
            # 连接失败，启动重连
            await self._start_reconnect()
    
    async def stop(self):
        """停止客户端"""
        logger.info("[INFO] 正在停止 Agent...")
        self.running = False
        await self.disconnect()
        
        # 关闭 session
        if self.session:
            await self.session.close()
            self.session = None
        
        logger.info("[INFO] Agent 已停止")
    
    async def send_status(
        self,
        status: str = "online",
        accounts: list = None,
        metrics: Dict[str, Any] = None
    ):
        """发送状态上报"""
        message = MessageHandler.create_status_message(
            self.agent_id,
            status,
            accounts,
            metrics
        )
        await self.send_message(message)
        logger.debug(f"[STATUS] 状态已上报: {status}")
    
    def is_connected(self) -> bool:
        """检查是否已连接"""
        return self.connected and self.ws is not None
