#!/usr/bin/env python3
"""
Agent 主入口文件
"""

import asyncio
import logging
import signal
import sys
from pathlib import Path

from agent.config import (
    get_agent_id, 
    get_server_url, 
    get_metadata,
    get_proxy,
    get_expected_ip,
    get_telegram_api_id,
    get_telegram_api_hash,
    get_telegram_session_string,
    get_telegram_session_path
)
from agent.websocket import WebSocketClient, MessageHandler, MessageType
from agent.modules.redpacket import RedPacketHandler, RedPacketStrategy
from agent.modules.theater import TheaterHandler
from agent.utils.device_fingerprint import get_or_create_device_fingerprint
from agent.utils.proxy_checker import validate_proxy_binding
from agent.core.session_manager import get_device_fingerprint_for_session
from agent.core.scenario_player import ScenarioPlayer, load_scenario_from_file

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
    
    # ============================================
    # Phase 4: 风控与指纹管理
    # ============================================
    
    # 1. 检查 Proxy IP 绑定（如果配置了 Proxy）
    proxy_url = get_proxy()
    expected_ip = get_expected_ip()
    
    if proxy_url:
        logger.info("=" * 60)
        logger.info("Phase 4: Proxy IP 绑定检查")
        logger.info("=" * 60)
        logger.info(f"Proxy URL: {proxy_url}")
        if expected_ip:
            logger.info(f"期望 IP: {expected_ip}")
        
        try:
            await validate_proxy_binding(proxy_url, expected_ip)
            logger.info("✅ Proxy IP 绑定检查通过")
        except RuntimeError as e:
            logger.error(f"❌ {e}")
            logger.error("拒绝启动，请检查 Proxy 配置")
            sys.exit(1)
        logger.info("")
    
    # 2. 获取或创建设备指纹（Phase 4 + Phase 5 集成）
    logger.info("=" * 60)
    logger.info("Phase 4/5: 设备指纹管理与 Telethon 集成")
    logger.info("=" * 60)
    
    # 从配置获取 Session 路径（如果配置了）
    session_path = get_telegram_session_path()
    
    # 获取设备指纹（根据 Session 路径）
    if session_path:
        device_fingerprint = get_device_fingerprint_for_session(session_path)
        logger.info(f"从 Session 文件获取设备指纹: {session_path}")
    else:
        # 兼容模式：使用全局指纹
        phone_number = None  # 可以从 config.json 或环境变量读取
        device_fingerprint = get_or_create_device_fingerprint(phone_number=phone_number)
        logger.info("使用全局设备指纹（兼容模式）")
    
    logger.info(f"设备型号: {device_fingerprint.device_model}")
    logger.info(f"系统版本: {device_fingerprint.system_version}")
    logger.info(f"App 版本: {device_fingerprint.app_version}")
    logger.info(f"语言代码: {device_fingerprint.lang_code}")
    logger.info(f"平台: {device_fingerprint.platform}")
    if device_fingerprint.manufacturer:
        logger.info(f"制造商: {device_fingerprint.manufacturer}")
    logger.info("=" * 60)
    logger.info("")
    
    # ============================================
    # 原有启动逻辑
    # ============================================
    
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
    
    # TODO: 初始化 Telethon 客户端（使用设备指纹）
    # 示例代码（需要安装 telethon）:
    # from telethon import TelegramClient
    # from telethon.sessions import StringSession
    # 
    # # 从 Session 或配置中获取手机号（用于加载对应的设备指纹）
    # phone_number = "+1234567890"  # 从配置或 Session 文件获取
    # 
    # # 获取或创建该手机号对应的设备指纹（每个 Session 唯一）
    # device_fingerprint = get_or_create_device_fingerprint(phone_number=phone_number)
    # 
    # # 转换为 Telethon 参数
    # device_params = device_fingerprint.to_telethon_params()
    # 
    # # 初始化 TelegramClient，注入设备指纹
    # telegram_client = TelegramClient(
    #     session=StringSession(session_string),
    #     api_id=api_id,
    #     api_hash=api_hash,
    #     device_model=device_params["device_model"],
    #     system_version=device_params["system_version"],
    #     app_version=device_params["app_version"],
    #     lang_code=device_params["lang_code"],
    #     proxy=proxy_url  # 如果配置了 Proxy
    # )
    # await telegram_client.start()
    # 
    # 注意：
    # - 每个 Session（手机号）对应唯一的设备指纹
    # - 指纹保存在 data/fingerprints/{phone_number}.json
    # - 一旦生成，绝对不能修改，否则会触发 Telegram 风控
    
    # 创建客户端
    client = WebSocketClient()
    
    # 初始化 RedPacket 处理器（传入 Telethon 客户端）
    global redpacket_handler
    redpacket_handler = RedPacketHandler(
        client=telegram_client,  # Phase 5: 传入 Telethon 客户端
        websocket_client=client
    )
    
    # 初始化 Theater 处理器（传入 Telethon 客户端）
    global theater_handler
    theater_handler = TheaterHandler(
        client=telegram_client,  # Phase 5: 传入 Telethon 客户端
        websocket_client=client
    )
    
    # Phase 5: 创建剧本执行器（用于本地测试）
    scenario_player = ScenarioPlayer(client=telegram_client)
    
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
