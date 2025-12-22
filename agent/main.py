#!/usr/bin/env python3
"""
Agent 主入口文件
"""

import asyncio
import logging
import signal
import sys
from pathlib import Path

from agent.config import get_agent_id, get_server_url, get_metadata
from agent.websocket import WebSocketClient, MessageHandler, MessageType
from agent.modules.redpacket import RedPacketHandler, RedPacketStrategy
from agent.modules.theater import TheaterHandler

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

logger = logging.getLogger(__name__)

# 全局客户端实例
client: WebSocketClient = None
redpacket_handler: RedPacketHandler = None
theater_handler: TheaterHandler = None


def setup_signal_handlers():
    """设置信号处理器（优雅退出）"""
    def signal_handler(sig, frame):
        logger.info("[INFO] 收到退出信号，正在关闭...")
        if client:
            asyncio.create_task(client.stop())
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)


async def handle_command(message: dict):
    """处理 Server 指令"""
    payload = message.get("payload", {})
    action = payload.get("action")
    
    logger.info(f"[COMMAND] 收到指令: {action}")
    logger.info(f"[COMMAND] 指令内容: {payload}")
    
    # TODO: 根据 action 执行相应任务
    # 例如：redpacket, chat, monitor 等
    
    # 示例：回复确认
    if action == "test":
        logger.info("[COMMAND] 执行测试指令")
        # 可以在这里执行实际任务
        # result = await execute_task(payload)
        # await client.send_message(MessageHandler.create_result_message(...))


async def handle_config(message: dict):
    """处理配置更新（策略更新）"""
    global redpacket_handler
    
    payload = message.get("payload", {})
    action = payload.get("action")
    
    logger.info(f"[CONFIG] 收到配置更新: {action}")
    
    if not redpacket_handler:
        logger.warning("[CONFIG] RedPacket 处理器未初始化，忽略配置更新")
        return
    
    try:
        if action == "strategy_created" or action == "strategy_updated":
            strategy_data = payload.get("strategy", {})
            strategy = redpacket_handler.load_strategy_from_config(strategy_data)
            
            if action == "strategy_created":
                redpacket_handler.add_strategy(strategy)
            else:
                redpacket_handler.update_strategy(strategy)
            
            logger.info(f"[CONFIG] 策略已{'添加' if action == 'strategy_created' else '更新'}: {strategy.name}")
        
        elif action == "strategy_deleted":
            strategy_id = payload.get("strategy_id")
            if strategy_id:
                redpacket_handler.remove_strategy(strategy_id)
                logger.info(f"[CONFIG] 策略已删除: {strategy_id}")
    
    except Exception as e:
        logger.error(f"[CONFIG] 处理配置更新失败: {e}", exc_info=True)


async def main():
    """主函数"""
    global client
    
    # 打印启动信息
    agent_id = get_agent_id()
    server_url = get_server_url()
    metadata = get_metadata()
    
    logger.info("=" * 60)
    logger.info("Telegram Agent - 智能执行端")
    logger.info("=" * 60)
    logger.info(f"Agent ID: {agent_id}")
    logger.info(f"Server URL: {server_url}")
    logger.info(f"元数据: {metadata}")
    logger.info("=" * 60)
    logger.info("")
    
    # 创建客户端
    client = WebSocketClient()
    
    # 初始化 RedPacket 处理器（TODO: 需要传入 Telethon 客户端）
    # 目前先创建，后续集成 Telethon 时再传入真实的 client
    global redpacket_handler
    redpacket_handler = RedPacketHandler(
        client=None,  # TODO: 传入 Telethon 客户端
        websocket_client=client
    )
    
    # 注册消息处理器
    client.register_message_handler(MessageType.COMMAND, handle_command)
    client.register_message_handler(MessageType.CONFIG, handle_config)
    
    # 设置信号处理器
    setup_signal_handlers()
    
    try:
        # 启动客户端
        await client.start()
        
        # 定期发送状态（可选）
        async def status_loop():
            while client.is_connected():
                await asyncio.sleep(60)  # 每60秒发送一次状态
                if client.is_connected():
                    await client.send_status(
                        status="online",
                        accounts=[],
                        metrics={
                            "tasks_completed": 0,
                            "tasks_failed": 0
                        }
                    )
        
        status_task = asyncio.create_task(status_loop())
        
        # 保持运行
        logger.info("[INFO] Agent 运行中，按 Ctrl+C 退出")
        try:
            await asyncio.Event().wait()  # 永久等待
        except asyncio.CancelledError:
            pass
        finally:
            status_task.cancel()
            await client.stop()
    
    except KeyboardInterrupt:
        logger.info("[INFO] 收到中断信号")
    except Exception as e:
        logger.error(f"[ERROR] 运行错误: {e}", exc_info=True)
    finally:
        if client:
            await client.stop()
        logger.info("[INFO] Agent 已退出")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("[INFO] 程序已中断")
    except Exception as e:
        logger.error(f"[ERROR] 程序错误: {e}", exc_info=True)
        sys.exit(1)
