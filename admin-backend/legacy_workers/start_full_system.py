#!/usr/bin/env python3
"""
🚀 完整業務自動化系統 - 集成啟動腳本

整合所有功能：
- 🤖 LLM 智能對話
- 📊 多群組管理
- 🖥️ 實時監控
- 📈 數據分析
- 🧧 紅包遊戲（含炸彈紅包）
- 📝 日誌持久化
- 🔄 錯誤重試機制
"""

import os
import sys
import asyncio
import signal
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional

# 設置項目路徑
sys.path.insert(0, str(Path(__file__).parent))

# 導入日誌模組（最先初始化）
from worker_logging import setup_logging, get_structured_logger, LogConfig

# 初始化日誌
log_config = LogConfig(
    log_dir="./logs",
    log_level=os.getenv("LOG_LEVEL", "INFO"),
    json_log_enabled=True
)
log_manager = setup_logging(log_config)
logger = get_structured_logger("main")

# 導入其他模組
try:
    from telethon import TelegramClient, events
    from telethon.tl.types import Message, User, Chat, Channel
except ImportError:
    logger.critical("請安裝 telethon: pip install telethon")
    sys.exit(1)

try:
    import openpyxl
except ImportError:
    logger.critical("請安裝 openpyxl: pip install openpyxl")
    sys.exit(1)

# 導入業務模組
from worker_redpacket_client import (
    RedPacketAPIClient, RedPacketAPIConfig,
    RedPacketGameEngine, GameStrategy,
    RedPacketInfo, ClaimResult
)
from worker_llm_dialogue import (
    SmartDialogueManager, LLMConfig, LLMProvider
)
from worker_multi_group_manager import (
    MultiGroupManager, GroupConfig, GroupInfo,
    AIAssignmentStrategy
)
from worker_realtime_monitor import (
    RealtimeMonitor, EventType, AlertLevel, MonitorEvent
)
from worker_analytics import AnalyticsService
from worker_group_manager import load_accounts_with_validation


# ==================== 配置 ====================

# 基本配置
SESSIONS_DIR = os.getenv("SESSIONS_DIR", "./sessions")
SCRIPTS_DIR = os.getenv("SCRIPTS_DIR", "./scripts")

# 紅包 API 配置
REDPACKET_API_URL = os.getenv("REDPACKET_API_URL", "https://api.usdt2026.cc")
REDPACKET_API_KEY = os.getenv("REDPACKET_API_KEY", "test-key-2024")

# LLM 配置
LLM_ENABLED = os.getenv("LLM_ENABLED", "true").lower() == "true"
LLM_API_KEY = os.getenv("OPENAI_API_KEY", os.getenv("LLM_API_KEY", ""))

# 遊戲策略
GAME_STRATEGY = os.getenv("GAME_STRATEGY", "balanced")

# 自動化設置
AUTO_CREATE_GROUP = os.getenv("AUTO_CREATE_GROUP", "true").lower() == "true"
AUTO_GRAB = os.getenv("AUTO_GRAB", "true").lower() == "true"
AUTO_SEND = os.getenv("AUTO_SEND", "false").lower() == "true"
AUTO_CHAT = os.getenv("AUTO_CHAT", "true").lower() == "true"

# AI 帳號列表
AI_ACCOUNTS = [
    639277358115,  # AI-1
    639543603735,  # AI-2
    639952948692,  # AI-3
    639454959591,  # AI-4
    639542360349,  # AI-5
    639950375245,  # AI-6
]


# ==================== 集成系統 ====================

class FullAutomationSystem:
    """完整自動化系統"""
    
    def __init__(self):
        # 初始化各模組
        self.redpacket_config = RedPacketAPIConfig(
            api_url=REDPACKET_API_URL,
            api_key=REDPACKET_API_KEY
        )
        self.redpacket_client = RedPacketAPIClient(self.redpacket_config)
        
        # 遊戲引擎
        strategy = getattr(GameStrategy, GAME_STRATEGY.upper(), GameStrategy.BALANCED)
        self.game_engine = RedPacketGameEngine(self.redpacket_client, strategy)
        
        # LLM 對話
        if LLM_ENABLED and LLM_API_KEY:
            self.dialogue_manager = SmartDialogueManager(LLMConfig.from_env())
        else:
            self.dialogue_manager = None
            logger.warning("LLM 未啟用（缺少 API Key）")
        
        # 多群組管理
        self.group_manager = MultiGroupManager(
            default_config=GroupConfig(
                name_template="🧧 福利交流群 {index}",
                min_ai_count=4,
                max_ai_count=6
            ),
            ai_strategy=AIAssignmentStrategy.LEAST_LOADED
        )
        
        # 實時監控
        self.monitor = RealtimeMonitor()
        
        # 數據分析
        self.analytics = AnalyticsService()
        
        # Telegram 客戶端
        self.clients: Dict[int, TelegramClient] = {}
        
        # 運行狀態
        self.running = False
        self._tasks: List[asyncio.Task] = []
    
    async def start(self):
        """啟動系統"""
        logger.info("=" * 60)
        logger.info("🚀 完整業務自動化系統啟動中...")
        logger.info("=" * 60)
        
        # 檢查 API 連通性
        if await self.redpacket_client.health_check():
            logger.info("✅ 紅包 API 連接正常")
        else:
            logger.error("❌ 紅包 API 連接失敗")
        
        # 啟動監控
        await self.monitor.start()
        logger.info("✅ 實時監控已啟動")
        
        self.running = True
        logger.info("✅ 系統啟動完成")
    
    async def stop(self):
        """停止系統"""
        logger.info("正在停止系統...")
        self.running = False
        
        # 取消所有任務
        for task in self._tasks:
            task.cancel()
        
        # 停止各模組
        await self.monitor.stop()
        await self.redpacket_client.close()
        
        if self.dialogue_manager:
            await self.dialogue_manager.close()
        
        # 斷開客戶端
        for client in self.clients.values():
            try:
                await client.disconnect()
            except:
                pass
        
        logger.info("✅ 系統已停止")
    
    async def connect_account(
        self,
        session_file: str,
        account_config: Dict
    ) -> bool:
        """連接帳號"""
        api_id = account_config.get("api_id")
        api_hash = account_config.get("api_hash")
        phone = account_config.get("phone", "未知")
        
        if not api_id or not api_hash:
            logger.error(f"帳號 {phone} 缺少 API 憑證")
            return False
        
        try:
            client = TelegramClient(session_file, int(api_id), api_hash)
            await client.connect()
            
            if not await client.is_user_authorized():
                logger.error(f"帳號 {phone} 未授權")
                await client.disconnect()
                return False
            
            me = await client.get_me()
            user_id = me.id
            
            # 保存客戶端
            self.clients[user_id] = client
            
            # 註冊到群組管理器
            self.group_manager.register_client(user_id, client)
            
            # 初始化餘額緩存
            try:
                balance = await self.redpacket_client.get_balance(user_id)
                self.game_engine.balance_cache[user_id] = balance.get_balance("usdt")
                logger.info(f"✅ 帳號 {me.username or phone} (ID: {user_id}) 餘額: {balance.get_balance('usdt')} USDT")
            except Exception as e:
                logger.warning(f"獲取餘額失敗: {e}")
            
            # 設置消息處理
            @client.on(events.NewMessage)
            async def handler(event, uid=user_id):
                await self._handle_message(uid, event)
            
            return True
            
        except Exception as e:
            logger.error(f"連接帳號 {phone} 失敗: {e}")
            return False
    
    async def _handle_message(self, user_id: int, event: events.NewMessage.Event):
        """處理消息"""
        message = event.message
        chat = await event.get_chat()
        
        # 只處理群消息
        if not isinstance(chat, (Chat, Channel)):
            return
        
        group_id = chat.id
        text = message.text or ""
        sender_id = message.sender_id
        
        # 忽略自己的消息
        if sender_id == user_id:
            return
        
        # 記錄到分析系統
        self.analytics.record_message(sender_id, group_id, text)
        
        # 記錄到監控
        await self.monitor.record_event(MonitorEvent(
            event_type=EventType.GROUP_MESSAGE,
            group_id=group_id,
            user_id=sender_id,
            data={"text_length": len(text)}
        ))
        
        # 處理紅包
        if self._is_redpacket_message(text):
            await self._handle_redpacket(user_id, group_id, text)
            return
        
        # LLM 智能回復
        if self.dialogue_manager and AUTO_CHAT:
            await self._handle_dialogue(user_id, group_id, text, sender_id)
    
    def _is_redpacket_message(self, text: str) -> bool:
        """判斷是否是紅包消息"""
        keywords = ["紅包", "红包", "🧧", "💰", "packet", "hongbao", "startapp=p_"]
        return any(kw.lower() in text.lower() for kw in keywords)
    
    def _extract_packet_uuid(self, text: str) -> Optional[str]:
        """提取紅包 UUID"""
        import re
        patterns = [
            r'startapp=p_([a-f0-9-]{36})',
            r'packet[s]?/([a-f0-9-]{36})',
            r'([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        return None
    
    async def _handle_redpacket(self, user_id: int, group_id: int, text: str):
        """處理紅包消息"""
        if not AUTO_GRAB:
            return
        
        packet_uuid = self._extract_packet_uuid(text)
        if not packet_uuid:
            return
        
        logger.info(f"[{user_id}] 檢測到紅包: {packet_uuid}")
        
        # 使用遊戲引擎判斷是否搶
        # 先獲取紅包信息（如果可能）
        packet_info = None
        try:
            packet_info = await self.redpacket_client.get_packet_info(user_id, packet_uuid)
        except:
            # 直接嘗試領取
            pass
        
        if packet_info and not self.game_engine.should_claim_packet(user_id, packet_info):
            logger.info(f"[{user_id}] 策略決定不搶此紅包")
            return
        
        # 領取紅包
        result = await self.game_engine.claim_packet(user_id, packet_uuid)
        
        if result.success:
            # 記錄到分析
            self.analytics.record_redpacket_claimed(
                user_id, group_id, result.claimed_amount
            )
            
            # 記錄到監控
            await self.monitor.record_event(MonitorEvent(
                event_type=EventType.REDPACKET_CLAIMED,
                group_id=group_id,
                user_id=user_id,
                data={
                    "amount": result.claimed_amount,
                    "is_bomb_hit": result.is_bomb_hit,
                    "penalty": result.penalty_amount
                }
            ))
            
            # 踩雷告警
            if result.is_bomb_hit:
                await self.monitor.create_alert(
                    AlertLevel.WARNING,
                    "踩雷警告",
                    f"用戶 {user_id} 踩雷，賠付 {result.penalty_amount} USDT",
                    group_id=group_id
                )
    
    async def _handle_dialogue(
        self,
        user_id: int,
        group_id: int,
        text: str,
        sender_id: int
    ):
        """處理對話"""
        try:
            # 獲取發送者名稱
            client = self.clients.get(user_id)
            if not client:
                return
            
            try:
                sender = await client.get_entity(sender_id)
                sender_name = getattr(sender, 'first_name', '') or str(sender_id)
            except:
                sender_name = str(sender_id)
            
            # 生成回復
            response = await self.dialogue_manager.generate_group_response(
                group_id=group_id,
                user_message=text,
                user_id=sender_id,
                user_name=sender_name
            )
            
            if response:
                role_name, reply_text = response
                
                # 發送回復
                await client.send_message(group_id, reply_text)
                
                logger.info(f"[{role_name}] 回復: {reply_text[:50]}...")
                
        except Exception as e:
            logger.error(f"對話處理失敗: {e}")
    
    async def send_ai_redpacket(
        self,
        sender_id: int,
        group_id: int = None,
        **kwargs
    ) -> Optional[RedPacketInfo]:
        """發送 AI 紅包"""
        if not AUTO_SEND:
            return None
        
        # 檢查是否應該發
        should_send, params = self.game_engine.should_send_packet(sender_id)
        if not should_send:
            return None
        
        # 合併參數
        params.update(kwargs)
        
        # 發送
        packet = await self.game_engine.send_packet(sender_id, **params)
        
        if packet:
            # 記錄到分析
            self.analytics.record_redpacket_sent(
                sender_id,
                group_id or 0,
                params.get("total_amount", 0),
                params.get("total_count", 0)
            )
            
            # 記錄到監控
            await self.monitor.record_event(MonitorEvent(
                event_type=EventType.REDPACKET_SENT,
                group_id=group_id,
                user_id=sender_id,
                data={
                    "amount": params.get("total_amount"),
                    "count": params.get("total_count"),
                    "is_bomb": params.get("bomb_number") is not None
                }
            ))
            
            # 發送到群組（如果指定）
            if group_id and sender_id in self.clients:
                client = self.clients[sender_id]
                message = f"🧧 {packet.message}\n領取: https://t.me/luckyred_bot/app?startapp=p_{packet.packet_uuid}"
                await client.send_message(group_id, message)
        
        return packet
    
    def get_system_status(self) -> Dict:
        """獲取系統狀態"""
        return {
            "running": self.running,
            "clients_count": len(self.clients),
            "groups": self.group_manager.get_all_groups_status(),
            "redpacket_stats": self.redpacket_client.get_stats(),
            "game_stats": self.game_engine.get_game_stats(),
            "analytics": {
                "funnel": self.analytics.get_funnel_report(),
                "segments": self.analytics.get_user_segments()
            },
            "monitor": self.monitor.get_dashboard_data()
        }


# ==================== 主程序 ====================

async def main():
    """主函數"""
    
    print("=" * 70)
    print("  🚀 完整業務自動化系統")
    print("  功能: LLM對話 | 多群組 | 紅包遊戲 | 實時監控 | 數據分析")
    print("=" * 70)
    print()
    
    # 創建系統
    system = FullAutomationSystem()
    
    # 處理信號
    loop = asyncio.get_event_loop()
    
    def signal_handler():
        asyncio.create_task(system.stop())
    
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, signal_handler)
        except NotImplementedError:
            pass  # Windows 不支持
    
    try:
        # 啟動系統
        await system.start()
        
        # 查找 Excel 配置
        sessions_path = Path(SESSIONS_DIR)
        excel_files = list(sessions_path.glob("*.xlsx"))
        
        if excel_files:
            # 載入帳號配置
            accounts = load_accounts_with_validation(str(excel_files[0]))
            
            if accounts:
                logger.info(f"載入了 {len(accounts)} 個帳號配置")
                
                # 掃描 session 文件
                session_files = list(sessions_path.glob("*.session"))
                
                # 連接帳號
                for session_file in session_files:
                    session_name = session_file.stem
                    
                    # 匹配配置
                    for account in accounts:
                        phone = account.get("phone", "")
                        if phone and (phone in session_name or session_name in phone):
                            await system.connect_account(str(session_file), account)
                            break
                
                logger.info(f"✅ 連接了 {len(system.clients)} 個帳號")
        
        # 自動創建群組
        if AUTO_CREATE_GROUP and system.clients:
            logger.info("正在創建測試群組...")
            
            creator_id = list(system.clients.keys())[0]
            group = await system.group_manager.create_group(
                name="🧧 AI 紅包互動群",
                script_id="红包游戏陪玩剧本"
            )
            
            if group:
                logger.info(f"✅ 群組創建成功: {group.name}")
                logger.info(f"   邀請鏈接: {group.invite_link}")
        
        # 輸出狀態
        print()
        print("🚀 系統已啟動！")
        print(f"   📊 {len(system.clients)} 個帳號在線")
        print(f"   🤖 LLM 對話: {'✅' if system.dialogue_manager else '❌'}")
        print(f"   🧧 自動搶紅包: {'✅' if AUTO_GRAB else '❌'}")
        print(f"   📤 自動發紅包: {'✅' if AUTO_SEND else '❌'}")
        print(f"   💬 智能聊天: {'✅' if AUTO_CHAT else '❌'}")
        print(f"   📈 遊戲策略: {GAME_STRATEGY}")
        print()
        print("按 Ctrl+C 停止")
        print()
        
        # 保持運行
        while system.running:
            await asyncio.sleep(60)
            
            # 定期輸出狀態
            stats = system.game_engine.get_game_stats()
            logger.info(
                f"📊 狀態: 帳號={len(system.clients)}, "
                f"紅包領取={stats['packets_claimed']}, "
                f"淨收益={stats['net_profit']:.2f} USDT"
            )
    
    except KeyboardInterrupt:
        pass
    finally:
        await system.stop()


if __name__ == "__main__":
    asyncio.run(main())
