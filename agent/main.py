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
    get_telegram_session_path,
    get_api_base_url,
    get_api_key,
    get_poll_interval,
    get_heartbeat_interval
)
from agent.websocket import WebSocketClient, MessageHandler, MessageType
from agent.modules.redpacket import RedPacketHandler, RedPacketStrategy
from agent.modules.theater import TheaterHandler
from agent.utils.device_fingerprint import get_or_create_device_fingerprint
from agent.utils.proxy_checker import validate_proxy_binding
from agent.core.session_manager import get_device_fingerprint_for_session
from agent.core.scenario_player import ScenarioPlayer
from agent.core.api_client import ApiClient
from agent.core.task_manager import TaskManager

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
    
    # ============================================
    # Phase 5: 初始化 Telethon 客户端（使用设备指纹）
    # ============================================
    telegram_client = None
    
    # 从配置获取 Telegram API 凭据
    api_id = get_telegram_api_id()
    api_hash = get_telegram_api_hash()
    session_string = get_telegram_session_string()
    session_path = get_telegram_session_path()
    
    if api_id and api_hash:
        try:
            from telethon import TelegramClient
            from telethon.sessions import StringSession
            
            # 转换为 Telethon 参数
            device_params = device_fingerprint.to_telethon_params()
            
            logger.info("=" * 60)
            logger.info("Phase 5: 初始化 Telethon 客户端")
            logger.info("=" * 60)
            logger.info(f"使用设备指纹: {device_fingerprint.device_model}")
            logger.info(f"系统版本: {device_params['system_version']}")
            logger.info(f"App 版本: {device_params['app_version']}")
            logger.info("=" * 60)
            logger.info("")
            
            # 确定 Session 类型
            if session_string:
                # 使用字符串 Session
                session = StringSession(session_string)
                logger.info("使用字符串 Session")
            elif session_path:
                # 使用文件 Session
                session = session_path
                logger.info(f"使用文件 Session: {session_path}")
            else:
                # 默认 Session 文件名
                session = "default"
                logger.info("使用默认 Session 文件名: default")
            
            # 初始化 TelegramClient，注入设备指纹
            telegram_client = TelegramClient(
                session=session,
                api_id=int(api_id),
                api_hash=api_hash,
                device_model=device_params["device_model"],
                system_version=device_params["system_version"],
                app_version=device_params["app_version"],
                lang_code=device_params["lang_code"],
                proxy=proxy_url if proxy_url else None  # 如果配置了 Proxy
            )
            
            # 启动客户端
            await telegram_client.start()
            logger.info("✅ Telethon 客户端已启动")
            
        except ImportError:
            logger.warning("⚠️  Telethon 未安装，跳过客户端初始化")
            logger.warning("   安装命令: pip install telethon")
        except Exception as e:
            logger.error(f"❌ Telethon 客户端初始化失败: {e}", exc_info=True)
            logger.warning("   继续运行（部分功能可能不可用）")
    else:
        logger.info("ℹ️  未配置 Telegram API 凭据，跳过 Telethon 客户端初始化")
        logger.info("   如需使用 Telegram 功能，请在 config.json 中配置:")
        logger.info("   {")
        logger.info("     \"telegram\": {")
        logger.info("       \"api_id\": \"YOUR_API_ID\",")
        logger.info("       \"api_hash\": \"YOUR_API_HASH\",")
        logger.info("       \"session_string\": \"...\" 或 \"session_path\": \"sessions/default.session\"")
        logger.info("     }")
        logger.info("   }")
        logger.info("   或设置环境变量:")
        logger.info("   - TELEGRAM_API_ID")
        logger.info("   - TELEGRAM_API_HASH")
        logger.info("   - TELEGRAM_SESSION_STRING 或 TELEGRAM_SESSION_PATH")
    
    # ============================================
    # Phase 6: 云端协同与任务调度
    # ============================================
    
    # 创建剧本执行器
    scenario_player = ScenarioPlayer(client=telegram_client)
    
    # 初始化 API 客户端
    api_base_url = get_api_base_url()
    api_key = get_api_key()
    
    logger.info("=" * 60)
    logger.info("Phase 6: 初始化 API 客户端")
    logger.info("=" * 60)
    logger.info(f"API 基础 URL: {api_base_url}")
    logger.info(f"API 密钥: {'已配置' if api_key else '未配置'}")
    logger.info("=" * 60)
    logger.info("")
    
    try:
        api_client = ApiClient(
            api_base_url=api_base_url,
            api_key=api_key,
            timeout=30,
            max_retries=3
        )
        logger.info("✅ API 客户端初始化成功")
    except Exception as e:
        logger.error(f"❌ API 客户端初始化失败: {e}")
        logger.error("   请检查是否安装了 httpx 或 requests 库")
        logger.error("   安装命令: pip install httpx 或 pip install requests")
        raise
    
    # 初始化任务管理器
    task_manager = TaskManager(
        telegram_client=telegram_client,
        api_client=api_client,
        scenario_player=scenario_player,
        poll_interval=get_poll_interval(),
        heartbeat_interval=get_heartbeat_interval()
    )
    
    # ============================================
    # 保留 WebSocket 客户端（用于接收实时指令）
    # ============================================
    
    # 创建 WebSocket 客户端（用于接收实时指令和配置更新）
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
    
    # 注册消息处理器
    client.register_message_handler(MessageType.COMMAND, handle_command)
    client.register_message_handler(MessageType.CONFIG, handle_config)
    
    # 设置信号处理器
    setup_signal_handlers()
    
    try:
        # 启动 WebSocket 客户端（后台运行，用于接收实时指令）
        websocket_task = None
        try:
            await client.start()
            logger.info("✅ WebSocket 客户端已启动（用于接收实时指令）")
        except Exception as e:
            logger.warning(f"⚠️  WebSocket 客户端启动失败: {e}")
            logger.warning("   继续运行（仅使用 REST API 轮询模式）")
        
        # 启动任务管理器（主循环，接管控制权）
        logger.info("=" * 60)
        logger.info("🚀 启动任务管理器（主循环）")
        logger.info("=" * 60)
        logger.info("Agent 将开始轮询任务...")
        logger.info("按 Ctrl+C 退出")
        logger.info("=" * 60)
        logger.info("")
        
        # 运行任务管理器（这会阻塞，直到停止）
        await task_manager.start_loop()
    
    except KeyboardInterrupt:
        logger.info("[INFO] 收到中断信号")
        task_manager.stop()
    except Exception as e:
        logger.error(f"[ERROR] 运行错误: {e}", exc_info=True)
        task_manager.stop()
    finally:
        # 清理资源
        if client:
            await client.stop()
        if api_client:
            await api_client.close()
        logger.info("[INFO] Agent 已退出")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("[INFO] 程序已中断")
    except Exception as e:
        logger.error(f"[ERROR] 程序错误: {e}", exc_info=True)
        sys.exit(1)
