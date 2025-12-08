"""
Worker 自動紅包和群組互動模組
支持：
- 監聽群消息
- 自動搶紅包
- 自動發紅包
- 群組聊天互動
"""

import asyncio
import random
import httpx
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
from telethon import TelegramClient, events
from telethon.tl.types import Message, User, Chat, Channel

logger = logging.getLogger(__name__)


class RedPacketConfig:
    """紅包配置"""
    def __init__(self):
        self.api_url = "https://api.usdt2026.cc"
        self.api_key = "test-key-2024"
        self.enabled = True
        
        # 自動搶紅包設置
        self.auto_grab = True
        self.grab_delay_min = 1  # 最小延遲秒數
        self.grab_delay_max = 5  # 最大延遲秒數
        
        # 自動發紅包設置
        self.auto_send = False
        self.send_interval = 300  # 發紅包間隔（秒）
        self.send_amount_min = 1.0
        self.send_amount_max = 5.0
        self.send_count_min = 3
        self.send_count_max = 5
        
        # 聊天設置
        self.auto_chat = True
        self.chat_interval_min = 30
        self.chat_interval_max = 120


class GroupInteractionManager:
    """群組互動管理器"""
    
    def __init__(
        self,
        telegram_client: TelegramClient,
        telegram_user_id: int,
        config: RedPacketConfig
    ):
        self.client = telegram_client
        self.user_id = telegram_user_id
        self.config = config
        self.http_client = httpx.AsyncClient(timeout=30.0)
        
        # 狀態追蹤
        self.claimed_packets: set = set()  # 已領取的紅包 UUID
        self.last_send_time: Optional[datetime] = None
        self.last_chat_time: Optional[datetime] = None
        self.active_groups: Dict[int, dict] = {}  # 活躍群組
        
        # 聊天消息模板
        self.chat_messages = [
            "大家好！今天運氣怎麼樣？",
            "紅包來啦！手速要快～",
            "感謝老闆發紅包！🧧",
            "哈哈，搶到了！",
            "下一個紅包我來發！",
            "今天手氣不錯呀",
            "大家繼續加油！",
            "紅包雨來襲！",
            "祝大家發財！💰",
            "運氣爆棚中～",
        ]
        
        # 紅包關鍵詞
        self.redpacket_keywords = [
            "紅包", "红包", "🧧", "💰", "發紅包", "发红包",
            "搶紅包", "抢红包", "紅包來了", "红包来了",
            "lucky", "packet", "hongbao"
        ]
    
    def _get_headers(self) -> Dict[str, str]:
        """獲取 API 請求頭"""
        return {
            "Authorization": f"Bearer {self.config.api_key}",
            "X-Telegram-User-Id": str(self.user_id),
            "Content-Type": "application/json"
        }
    
    async def get_balance(self) -> float:
        """查詢餘額"""
        try:
            response = await self.http_client.get(
                f"{self.config.api_url}/api/v2/ai/wallet/balance",
                headers=self._get_headers()
            )
            data = response.json()
            if data.get("success"):
                return data["data"]["balances"].get("usdt", 0)
        except Exception as e:
            logger.error(f"查詢餘額失敗: {e}")
        return 0
    
    async def send_redpacket(
        self,
        amount: float = None,
        count: int = None,
        message: str = "🤖 AI 紅包"
    ) -> Optional[str]:
        """發送紅包"""
        if not self.config.auto_send:
            return None
        
        # 檢查間隔
        if self.last_send_time:
            elapsed = (datetime.now() - self.last_send_time).total_seconds()
            if elapsed < self.config.send_interval:
                return None
        
        # 隨機金額和份數
        if amount is None:
            amount = random.uniform(
                self.config.send_amount_min,
                self.config.send_amount_max
            )
        if count is None:
            count = random.randint(
                self.config.send_count_min,
                self.config.send_count_max
            )
        
        try:
            response = await self.http_client.post(
                f"{self.config.api_url}/api/v2/ai/packets/send",
                headers=self._get_headers(),
                json={
                    "currency": "usdt",
                    "packet_type": "random",
                    "total_amount": round(amount, 2),
                    "total_count": count,
                    "message": message
                }
            )
            data = response.json()
            if data.get("success"):
                packet_id = data["data"]["packet_id"]
                self.last_send_time = datetime.now()
                logger.info(f"[用戶 {self.user_id}] 發送紅包成功: {packet_id}, {amount} USDT, {count}份")
                return packet_id
            else:
                logger.warning(f"發送紅包失敗: {data.get('error')}")
        except Exception as e:
            logger.error(f"發送紅包異常: {e}")
        
        return None
    
    async def claim_redpacket(self, packet_uuid: str) -> Optional[float]:
        """領取紅包"""
        if packet_uuid in self.claimed_packets:
            logger.debug(f"紅包 {packet_uuid} 已領取過")
            return None
        
        # 隨機延遲，模擬真人
        delay = random.uniform(
            self.config.grab_delay_min,
            self.config.grab_delay_max
        )
        logger.info(f"[用戶 {self.user_id}] 等待 {delay:.1f}秒 後搶紅包...")
        await asyncio.sleep(delay)
        
        try:
            response = await self.http_client.post(
                f"{self.config.api_url}/api/v2/ai/packets/claim",
                headers=self._get_headers(),
                json={"packet_uuid": packet_uuid}
            )
            data = response.json()
            if data.get("success"):
                claimed_amount = data["data"].get("claimed_amount", 0)
                self.claimed_packets.add(packet_uuid)
                logger.info(f"[用戶 {self.user_id}] 搶紅包成功！獲得 {claimed_amount} USDT")
                return claimed_amount
            else:
                error = data.get("error", {}).get("detail", "未知錯誤")
                if "已領取" in error or "already" in error.lower():
                    self.claimed_packets.add(packet_uuid)
                logger.warning(f"搶紅包失敗: {error}")
        except Exception as e:
            logger.error(f"搶紅包異常: {e}")
        
        return None
    
    async def send_chat_message(self, chat_id: int, message: str = None) -> bool:
        """發送聊天消息"""
        if not self.config.auto_chat:
            return False
        
        # 檢查間隔
        if self.last_chat_time:
            elapsed = (datetime.now() - self.last_chat_time).total_seconds()
            min_interval = self.config.chat_interval_min
            if elapsed < min_interval:
                return False
        
        if message is None:
            message = random.choice(self.chat_messages)
        
        try:
            await self.client.send_message(chat_id, message)
            self.last_chat_time = datetime.now()
            logger.info(f"[用戶 {self.user_id}] 發送消息到群 {chat_id}: {message}")
            return True
        except Exception as e:
            logger.error(f"發送消息失敗: {e}")
            return False
    
    def extract_packet_uuid(self, text: str) -> Optional[str]:
        """從消息中提取紅包 UUID"""
        import re
        
        # 匹配常見的紅包鏈接格式
        patterns = [
            r'packet[s]?/([a-f0-9-]{36})',  # /packets/uuid
            r'startapp=p_([a-f0-9-]{36})',  # startapp=p_uuid
            r'([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})',  # 標準 UUID
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None
    
    def is_redpacket_message(self, text: str) -> bool:
        """判斷是否是紅包相關消息"""
        text_lower = text.lower()
        return any(kw.lower() in text_lower for kw in self.redpacket_keywords)
    
    async def handle_message(self, event: events.NewMessage.Event):
        """處理新消息"""
        message: Message = event.message
        chat = await event.get_chat()
        
        # 只處理群消息
        if not isinstance(chat, (Chat, Channel)):
            return
        
        chat_id = chat.id
        text = message.text or ""
        sender_id = message.sender_id
        
        # 忽略自己發的消息
        if sender_id == self.user_id:
            return
        
        logger.debug(f"[群 {chat_id}] 收到消息: {text[:50]}...")
        
        # 檢查是否是紅包消息
        if self.is_redpacket_message(text):
            packet_uuid = self.extract_packet_uuid(text)
            if packet_uuid and self.config.auto_grab:
                logger.info(f"[用戶 {self.user_id}] 檢測到紅包: {packet_uuid}")
                claimed = await self.claim_redpacket(packet_uuid)
                
                # 搶到紅包後隨機發一條感謝消息
                if claimed and random.random() < 0.3:
                    await asyncio.sleep(random.uniform(2, 5))
                    thanks_messages = [
                        "謝謝老闆！🙏",
                        "感謝紅包！",
                        "手氣不錯！",
                        "謝謝！",
                        "💰 收到！",
                    ]
                    await self.send_chat_message(chat_id, random.choice(thanks_messages))
        
        # 記錄活躍群組
        if chat_id not in self.active_groups:
            self.active_groups[chat_id] = {
                "name": getattr(chat, "title", str(chat_id)),
                "last_activity": datetime.now()
            }
        else:
            self.active_groups[chat_id]["last_activity"] = datetime.now()
    
    async def start_listening(self):
        """開始監聽消息"""
        logger.info(f"[用戶 {self.user_id}] 開始監聽群消息...")
        
        @self.client.on(events.NewMessage)
        async def handler(event):
            await self.handle_message(event)
        
        logger.info(f"[用戶 {self.user_id}] 消息監聯已啟動")
    
    async def auto_send_loop(self):
        """自動發紅包循環"""
        if not self.config.auto_send:
            return
        
        logger.info(f"[用戶 {self.user_id}] 自動發紅包循環啟動，間隔 {self.config.send_interval}秒")
        
        while True:
            try:
                await asyncio.sleep(self.config.send_interval)
                
                # 檢查餘額
                balance = await self.get_balance()
                if balance < self.config.send_amount_min:
                    logger.warning(f"[用戶 {self.user_id}] 餘額不足 ({balance} USDT)，跳過發紅包")
                    continue
                
                # 發送紅包
                await self.send_redpacket()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"自動發紅包異常: {e}")
                await asyncio.sleep(60)
    
    async def auto_chat_loop(self):
        """自動聊天循環"""
        if not self.config.auto_chat:
            return
        
        logger.info(f"[用戶 {self.user_id}] 自動聊天循環啟動")
        
        while True:
            try:
                # 隨機間隔
                interval = random.randint(
                    self.config.chat_interval_min,
                    self.config.chat_interval_max
                )
                await asyncio.sleep(interval)
                
                # 在活躍群組中隨機發消息
                if self.active_groups:
                    chat_id = random.choice(list(self.active_groups.keys()))
                    await self.send_chat_message(chat_id)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"自動聊天異常: {e}")
                await asyncio.sleep(60)
    
    async def join_group(self, invite_link: str) -> bool:
        """加入群組"""
        try:
            from telethon.tl.functions.messages import ImportChatInviteRequest
            from telethon.tl.functions.channels import JoinChannelRequest
            
            if "joinchat/" in invite_link or "+" in invite_link:
                # 私有群邀請鏈接
                hash_part = invite_link.split("/")[-1].replace("+", "")
                await self.client(ImportChatInviteRequest(hash_part))
            else:
                # 公開群/頻道
                await self.client(JoinChannelRequest(invite_link))
            
            logger.info(f"[用戶 {self.user_id}] 成功加入群組: {invite_link}")
            return True
        except Exception as e:
            logger.error(f"加入群組失敗: {e}")
            return False
    
    async def close(self):
        """關閉資源"""
        await self.http_client.aclose()


class MultiAccountManager:
    """多帳號管理器"""
    
    def __init__(self, config: RedPacketConfig):
        self.config = config
        self.managers: Dict[int, GroupInteractionManager] = {}
    
    def add_account(
        self,
        client: TelegramClient,
        user_id: int
    ) -> GroupInteractionManager:
        """添加帳號"""
        manager = GroupInteractionManager(client, user_id, self.config)
        self.managers[user_id] = manager
        return manager
    
    async def start_all(self):
        """啟動所有帳號的監聽"""
        tasks = []
        for user_id, manager in self.managers.items():
            tasks.append(manager.start_listening())
            if self.config.auto_send:
                tasks.append(asyncio.create_task(manager.auto_send_loop()))
            if self.config.auto_chat:
                tasks.append(asyncio.create_task(manager.auto_chat_loop()))
        
        logger.info(f"啟動了 {len(self.managers)} 個帳號的自動化")
        await asyncio.gather(*tasks)
    
    async def join_group_all(self, invite_link: str):
        """所有帳號加入同一群組"""
        results = []
        for user_id, manager in self.managers.items():
            success = await manager.join_group(invite_link)
            results.append((user_id, success))
            # 間隔加入，避免被限制
            await asyncio.sleep(random.uniform(5, 15))
        return results
    
    async def close_all(self):
        """關閉所有管理器"""
        for manager in self.managers.values():
            await manager.close()


# 示例使用
async def main_example():
    """示例：如何使用自動紅包和群組互動"""
    
    # 配置
    config = RedPacketConfig()
    config.auto_grab = True
    config.auto_send = True
    config.auto_chat = True
    config.send_interval = 300  # 5分鐘發一次紅包
    
    # 創建 Telegram 客戶端
    api_id = 12345678
    api_hash = "your_api_hash"
    
    client = TelegramClient("session_name", api_id, api_hash)
    await client.start()
    
    me = await client.get_me()
    user_id = me.id
    
    # 創建互動管理器
    manager = GroupInteractionManager(client, user_id, config)
    
    # 加入群組（可選）
    # await manager.join_group("https://t.me/+xxxxx")
    
    # 開始監聽和自動化
    await manager.start_listening()
    
    # 啟動自動發紅包和聊天
    tasks = []
    if config.auto_send:
        tasks.append(asyncio.create_task(manager.auto_send_loop()))
    if config.auto_chat:
        tasks.append(asyncio.create_task(manager.auto_chat_loop()))
    
    # 運行直到被中斷
    try:
        await client.run_until_disconnected()
    finally:
        await manager.close()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s"
    )
    asyncio.run(main_example())
