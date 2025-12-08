#!/usr/bin/env python3
"""
自動紅包群組互動啟動腳本
支持多帳號同時運行，自動搶/發紅包，群組聊天互動

特點：
- 每個帳號使用獨立的 API_ID 和 API_HASH（從 Excel 讀取）
- 自動建群並邀請其他 AI 帳號
- 自動搶/發紅包
- 群組聊天互動
"""

import os
import sys
import asyncio
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("AutoRedPacket")

# 嘗試導入依賴
try:
    from telethon import TelegramClient
    from telethon.sessions import StringSession
except ImportError:
    print("錯誤：請安裝 telethon: pip install telethon")
    sys.exit(1)

try:
    import openpyxl
except ImportError:
    print("錯誤：請安裝 openpyxl: pip install openpyxl")
    sys.exit(1)

try:
    import httpx
except ImportError:
    print("錯誤：請安裝 httpx: pip install httpx")
    sys.exit(1)

# 導入自動紅包模組
from worker_auto_redpacket import RedPacketConfig, GroupInteractionManager, MultiAccountManager
from worker_group_manager import (
    GroupManager, TestGroupOrchestrator,
    load_accounts_with_validation, validate_unique_api_credentials
)


# ==================== 配置 ====================

# 紅包 API 配置
REDPACKET_API_URL = os.getenv("REDPACKET_API_URL", "https://api.usdt2026.cc")
REDPACKET_API_KEY = os.getenv("REDPACKET_API_KEY", "test-key-2024")

# Sessions 目錄
SESSIONS_DIR = os.getenv("SESSIONS_DIR", "./sessions")

# 自動建群設置
AUTO_CREATE_GROUP = os.getenv("AUTO_CREATE_GROUP", "true").lower() == "true"
GROUP_NAME = os.getenv("GROUP_NAME", "")  # 自動建群名稱，空則自動生成

# 要加入的群組（如果不自動建群）
TARGET_GROUP = os.getenv("TARGET_GROUP", "")  # 群組邀請鏈接或用戶名

# 自動化設置
AUTO_GRAB_ENABLED = os.getenv("AUTO_GRAB", "true").lower() == "true"
AUTO_SEND_ENABLED = os.getenv("AUTO_SEND", "false").lower() == "true"
AUTO_CHAT_ENABLED = os.getenv("AUTO_CHAT", "true").lower() == "true"

GRAB_DELAY_MIN = float(os.getenv("GRAB_DELAY_MIN", "1"))
GRAB_DELAY_MAX = float(os.getenv("GRAB_DELAY_MAX", "5"))
SEND_INTERVAL = int(os.getenv("SEND_INTERVAL", "300"))
SEND_AMOUNT_MIN = float(os.getenv("SEND_AMOUNT_MIN", "1"))
SEND_AMOUNT_MAX = float(os.getenv("SEND_AMOUNT_MAX", "5"))


# ==================== 帳號載入 ====================

def find_excel_file(sessions_dir: str) -> Optional[str]:
    """查找 Excel 配置文件"""
    sessions_path = Path(sessions_dir)
    
    # 優先查找特定名稱的文件
    priority_names = ["accounts.xlsx", "config.xlsx", "帳號.xlsx", "账号.xlsx"]
    for name in priority_names:
        excel_path = sessions_path / name
        if excel_path.exists():
            return str(excel_path)
    
    # 查找任何 xlsx 文件
    xlsx_files = list(sessions_path.glob("*.xlsx"))
    if xlsx_files:
        return str(xlsx_files[0])
    
    # 查找 xls 文件
    xls_files = list(sessions_path.glob("*.xls"))
    if xls_files:
        return str(xls_files[0])
    
    return None


def scan_session_files(sessions_dir: str) -> List[str]:
    """掃描 session 文件"""
    session_files = []
    sessions_path = Path(sessions_dir)
    
    if not sessions_path.exists():
        logger.warning(f"Sessions 目錄不存在: {sessions_dir}")
        return session_files
    
    for f in sessions_path.glob("*.session"):
        session_files.append(str(f))
    
    logger.info(f"找到 {len(session_files)} 個 session 文件")
    return session_files


def match_session_with_config(
    session_file: str,
    accounts: List[Dict[str, Any]]
) -> Optional[Dict[str, Any]]:
    """
    匹配 session 文件與帳號配置
    
    ⚠️ 每個帳號必須有獨立的 API_ID 和 API_HASH
    """
    session_name = Path(session_file).stem
    
    for account in accounts:
        phone = account.get("phone", "")
        # 精確匹配或部分匹配
        if phone and (phone in session_name or session_name in phone):
            # 驗證有獨立的 API 憑證
            if not account.get("api_id") or not account.get("api_hash"):
                logger.error(f"⚠️ 帳號 {phone} 缺少獨立的 API_ID 或 API_HASH！")
                logger.error("每個帳號必須在 Excel 中配置獨立的 API 憑證")
                return None
            return account
    
    # 沒找到匹配
    logger.warning(f"Session {session_name} 沒有在 Excel 中找到匹配的配置")
    return None


# ==================== 主程序 ====================

async def connect_account(
    session_file: str,
    account_config: Dict[str, Any]
) -> Optional[tuple]:
    """
    連接單個帳號
    
    Returns:
        (client, user_id, account_config) 或 None
    """
    api_id = account_config.get("api_id")
    api_hash = account_config.get("api_hash")
    phone = account_config.get("phone", "未知")
    
    if not api_id or not api_hash:
        logger.error(f"帳號 {phone} 缺少 API 憑證，跳過")
        return None
    
    try:
        client = TelegramClient(session_file, int(api_id), api_hash)
        await client.connect()
        
        if not await client.is_user_authorized():
            logger.error(f"帳號 {phone} 未授權，跳過")
            await client.disconnect()
            return None
        
        me = await client.get_me()
        user_id = me.id
        username = me.username or "N/A"
        
        # 更新配置
        account_config["user_id"] = user_id
        account_config["username"] = username
        account_config["name"] = f"{me.first_name or ''} {me.last_name or ''}".strip()
        
        logger.info(f"✅ 帳號已連接: {username} (ID: {user_id}, Phone: {phone})")
        logger.info(f"   API_ID: {api_id} (獨立憑證)")
        
        return (client, user_id, account_config)
        
    except Exception as e:
        logger.error(f"連接帳號 {phone} 失敗: {e}")
        return None


async def main():
    """主函數"""
    
    print("=" * 60)
    print("  🧧 自動紅包群組互動系統")
    print("  ⚠️ 每個帳號使用獨立的 API_ID/API_HASH")
    print("=" * 60)
    print()
    
    # 創建配置
    config = RedPacketConfig()
    config.api_url = REDPACKET_API_URL
    config.api_key = REDPACKET_API_KEY
    config.auto_grab = AUTO_GRAB_ENABLED
    config.auto_send = AUTO_SEND_ENABLED
    config.auto_chat = AUTO_CHAT_ENABLED
    config.grab_delay_min = GRAB_DELAY_MIN
    config.grab_delay_max = GRAB_DELAY_MAX
    config.send_interval = SEND_INTERVAL
    config.send_amount_min = SEND_AMOUNT_MIN
    config.send_amount_max = SEND_AMOUNT_MAX
    
    print(f"📡 紅包 API: {config.api_url}")
    print(f"🏠 自動建群: {'開啟' if AUTO_CREATE_GROUP else '關閉'}")
    print(f"🤖 自動搶紅包: {'開啟' if config.auto_grab else '關閉'}")
    print(f"📤 自動發紅包: {'開啟' if config.auto_send else '關閉'}")
    print(f"💬 自動聊天: {'開啟' if config.auto_chat else '關閉'}")
    print()
    
    # 查找 Excel 文件
    excel_file = find_excel_file(SESSIONS_DIR)
    if not excel_file:
        logger.error(f"在 {SESSIONS_DIR} 目錄下找不到 Excel 配置文件！")
        logger.error("請創建 accounts.xlsx 並配置每個帳號的獨立 API_ID 和 API_HASH")
        return
    
    logger.info(f"使用 Excel 配置: {excel_file}")
    
    # 載入帳號配置（帶驗證）
    accounts = load_accounts_with_validation(excel_file)
    if not accounts:
        logger.error("沒有有效的帳號配置！")
        return
    
    print()
    print(f"📋 載入了 {len(accounts)} 個帳號配置（已驗證 API 憑證唯一性）")
    print()
    
    # 掃描 session 文件
    session_files = scan_session_files(SESSIONS_DIR)
    if not session_files:
        logger.error("沒有找到任何 session 文件！")
        return
    
    # 連接所有帳號
    connected_accounts = []
    clients = []
    
    for session_file in session_files:
        account_config = match_session_with_config(session_file, accounts)
        if account_config:
            result = await connect_account(session_file, account_config)
            if result:
                client, user_id, config_updated = result
                connected_accounts.append((client, user_id, config_updated))
                clients.append(client)
    
    if not connected_accounts:
        logger.error("沒有成功連接任何帳號！")
        return
    
    print()
    print(f"✅ 成功連接 {len(connected_accounts)}/{len(session_files)} 個帳號")
    print()
    
    # ==================== 自動建群或加入群組 ====================
    
    group_orchestrator = TestGroupOrchestrator()
    
    # 添加帳號到協調器
    for client, user_id, account_config in connected_accounts:
        group_orchestrator.add_account(user_id, client, account_config)
    
    test_group = None
    
    if AUTO_CREATE_GROUP:
        # 自動建群
        print("🏠 正在創建測試群組...")
        
        # 選擇第一個帳號作為創建者
        creator_user_id = connected_accounts[0][1]
        
        test_group = await group_orchestrator.create_test_group(
            creator_user_id=creator_user_id,
            group_name=GROUP_NAME if GROUP_NAME else None
        )
        
        if test_group:
            print()
            print("=" * 50)
            print(f"🎉 測試群組創建成功！")
            print(f"   名稱: {test_group['title']}")
            print(f"   ID: {test_group['id']}")
            print(f"   邀請鏈接: {test_group['invite_link']}")
            print(f"   創建者: {creator_user_id}")
            print("=" * 50)
            print()
            
            # 讓其他帳號通過邀請鏈接加入（以防直接邀請失敗）
            if test_group.get("invite_link"):
                print("正在確保所有帳號都在群組中...")
                results = await group_orchestrator.all_accounts_join_via_link(
                    test_group["invite_link"]
                )
                success_count = sum(1 for success in results.values() if success)
                print(f"加入結果: {success_count}/{len(results)} 個帳號在群組中")
                print()
        else:
            logger.warning("創建群組失敗，將嘗試使用 TARGET_GROUP")
    
    # 如果沒有建群或建群失敗，且有 TARGET_GROUP
    if not test_group and TARGET_GROUP:
        print(f"正在加入指定群組: {TARGET_GROUP}")
        results = await group_orchestrator.all_accounts_join_via_link(TARGET_GROUP)
        success_count = sum(1 for success in results.values() if success)
        print(f"加入群組結果: {success_count}/{len(results)} 成功")
        print()
    
    # ==================== 啟動紅包和聊天自動化 ====================
    
    # 創建紅包互動管理器
    redpacket_manager = MultiAccountManager(config)
    
    for client, user_id, account_config in connected_accounts:
        interaction_manager = redpacket_manager.add_account(client, user_id)
        await interaction_manager.start_listening()
    
    print()
    print("🚀 系統已啟動！")
    print(f"   📊 {len(connected_accounts)} 個帳號在線")
    print(f"   🧧 自動搶紅包: {'✅' if config.auto_grab else '❌'}")
    print(f"   📤 自動發紅包: {'✅' if config.auto_send else '❌'}")
    print(f"   💬 自動聊天: {'✅' if config.auto_chat else '❌'}")
    if test_group:
        print(f"   🏠 測試群組: {test_group['title']}")
    print()
    print("按 Ctrl+C 停止")
    print()
    
    # 啟動自動化任務
    tasks = []
    for user_id, interaction_manager in redpacket_manager.managers.items():
        if config.auto_send:
            tasks.append(asyncio.create_task(interaction_manager.auto_send_loop()))
        if config.auto_chat:
            tasks.append(asyncio.create_task(interaction_manager.auto_chat_loop()))
    
    # 保持運行
    try:
        while True:
            await asyncio.sleep(60)
            # 定期輸出狀態
            total_claimed = sum(len(m.claimed_packets) for m in redpacket_manager.managers.values())
            total_groups = sum(len(m.active_groups) for m in redpacket_manager.managers.values())
            logger.info(f"📊 狀態: {len(redpacket_manager.managers)} 帳號在線, {total_groups} 個活躍群組, {total_claimed} 個紅包已領取")
    except KeyboardInterrupt:
        print("\n正在停止...")
    finally:
        # 取消所有任務
        for task in tasks:
            task.cancel()
        await redpacket_manager.close_all()
        
        # 斷開所有客戶端
        for client in clients:
            try:
                await client.disconnect()
            except:
                pass
        
        print("✅ 已停止")


if __name__ == "__main__":
    asyncio.run(main())
