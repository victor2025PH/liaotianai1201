"""
私聊自動化處理器 - 處理好友請求、私聊培養、定時邀請進群
"""
import asyncio
import random
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from enum import Enum
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


class UserStage(str, Enum):
    """用戶階段"""
    NEW_FRIEND = "new_friend"
    GREETING = "greeting"
    WARMING_UP = "warming_up"
    BUILDING_TRUST = "building_trust"
    READY_TO_INVITE = "ready_to_invite"
    INVITED = "invited"
    JOINED_GROUP = "joined_group"
    CONVERTED = "converted"


class ChatTopic(str, Enum):
    """聊天話題"""
    GREETING = "greeting"
    DAILY_LIFE = "daily_life"
    INTERESTS = "interests"
    ENTERTAINMENT = "entertainment"
    GAMES = "games"
    RED_PACKET = "red_packet"


@dataclass
class PrivateUser:
    """私聊用戶數據"""
    user_id: int
    username: str = ""
    first_name: str = ""
    ai_account_id: str = ""
    stage: UserStage = UserStage.NEW_FRIEND
    added_at: datetime = field(default_factory=datetime.now)
    last_message_at: Optional[datetime] = None
    last_ai_message_at: Optional[datetime] = None
    message_count: int = 0
    ai_message_count: int = 0
    current_topic: ChatTopic = ChatTopic.GREETING
    interests: List[str] = field(default_factory=list)
    sentiment: str = "neutral"
    invite_scheduled_at: Optional[datetime] = None
    invited_at: Optional[datetime] = None
    target_group_id: Optional[int] = None
    daily_messages_sent: int = 0
    last_daily_reset: datetime = field(default_factory=datetime.now)


class PrivateChatHandler:
    """私聊自動化處理器"""
    
    def __init__(self, client_manager, ai_engine=None):
        self.client_manager = client_manager
        self.ai_engine = ai_engine
        self.running = False
        
        # 用戶數據
        self.users: Dict[int, PrivateUser] = {}
        
        # 配置
        self.config = {
            "enabled": True,
            "auto_accept_friend": True,
            "greeting_delay_seconds": 60,
            "chat_interval_min": 1800,
            "chat_interval_max": 7200,
            "daily_message_limit": 10,
            "reply_delay_min": 3,
            "reply_delay_max": 30,
            "invite_after_days": 3.0,
            "min_messages_before_invite": 10,
            "target_group_ids": [],
        }
        
        # 話題消息庫
        self.topic_messages = {
            ChatTopic.GREETING: [
                "你好呀～很高興認識你 😊",
                "Hi～加個好友，以後多交流呀",
                "哈嘍～我是{ai_name}，很高興認識你！",
                "終於加上了！感覺很有緣呢 ✨",
            ],
            ChatTopic.DAILY_LIFE: [
                "今天過得怎麼樣？",
                "吃飯了嗎？😋",
                "最近忙不忙呀？",
                "這天氣真的太{weather}了",
                "週末有什麼安排嗎？",
                "今天心情怎麼樣？",
            ],
            ChatTopic.INTERESTS: [
                "平時喜歡做什麼呀？",
                "你有什麼愛好嗎？",
                "看你感覺很有趣的樣子 😄",
                "最近有什麼好玩的事嗎？",
            ],
            ChatTopic.ENTERTAINMENT: [
                "最近有什麼好看的劇推薦嗎？",
                "你玩遊戲嗎？",
                "週末一般怎麼放鬆？",
                "有沒有試過線上小遊戲？挺解壓的",
            ],
            ChatTopic.GAMES: [
                "我發現了一個超好玩的遊戲，有興趣嗎？",
                "最近群裡大家都在玩小遊戲，挺有意思的",
                "你玩過搶紅包遊戲嗎？",
                "我們群裡經常搞遊戲活動，獎品還不錯呢",
            ],
            ChatTopic.RED_PACKET: [
                "對了，我有個群，裡面經常有紅包活動",
                "群裡今晚有紅包雨，要不要來試試手氣？🧧",
                "最近群裡紅包挺多的，我都搶了不少 😁",
                "我拉你進群吧，裡面經常有福利活動",
            ],
        }
        
        # 邀請話術
        self.invite_scripts = [
            {
                "pre_invite": "對了，我有個群，裡面大家經常聊天玩遊戲，氣氛很好",
                "invite": "要不要我拉你進去？認識多點朋友",
                "follow_up": "群裡今晚有紅包活動哦 🧧"
            },
            {
                "pre_invite": "最近群裡在玩一個搶紅包的遊戲，挺刺激的",
                "invite": "我拉你進來一起玩吧？",
                "follow_up": "手氣好的話能搶不少呢"
            },
            {
                "pre_invite": "我們有個小群，經常搞福利活動",
                "invite": "想不想進來看看？",
                "follow_up": "裡面都是聊得來的朋友"
            },
        ]
        
        # 階段話題映射
        self.stage_topics = {
            UserStage.GREETING: [ChatTopic.GREETING],
            UserStage.WARMING_UP: [ChatTopic.GREETING, ChatTopic.DAILY_LIFE],
            UserStage.BUILDING_TRUST: [ChatTopic.DAILY_LIFE, ChatTopic.INTERESTS, ChatTopic.ENTERTAINMENT],
            UserStage.READY_TO_INVITE: [ChatTopic.GAMES, ChatTopic.RED_PACKET],
        }
        
        # 階段時長配置（小時）
        self.stage_duration = {
            UserStage.NEW_FRIEND: 0,
            UserStage.GREETING: 24,
            UserStage.WARMING_UP: 24,
            UserStage.BUILDING_TRUST: 24,
            UserStage.READY_TO_INVITE: 0,
        }
    
    async def start(self):
        """啟動私聊處理器"""
        self.running = True
        logger.info("私聊自動化處理器已啟動")
        
        # 啟動後台任務
        asyncio.create_task(self._main_loop())
        asyncio.create_task(self._invite_check_loop())
    
    async def stop(self):
        """停止私聊處理器"""
        self.running = False
        logger.info("私聊自動化處理器已停止")
    
    def update_config(self, config: Dict[str, Any]):
        """更新配置"""
        self.config.update(config)
        logger.info(f"私聊配置已更新: {config}")
    
    async def on_friend_request(self, user_id: int, username: str = "", first_name: str = "", ai_account_id: str = ""):
        """處理好友請求"""
        if not self.config.get("auto_accept_friend", True):
            logger.info(f"自動接受好友已禁用，忽略請求: {user_id}")
            return False
        
        logger.info(f"收到好友請求: user_id={user_id}, username={username}")
        
        # 創建用戶記錄
        user = PrivateUser(
            user_id=user_id,
            username=username,
            first_name=first_name,
            ai_account_id=ai_account_id,
            stage=UserStage.NEW_FRIEND,
            added_at=datetime.now(),
            invite_scheduled_at=datetime.now() + timedelta(days=self.config.get("invite_after_days", 3))
        )
        self.users[user_id] = user
        
        # 延遲發送問候
        delay = self.config.get("greeting_delay_seconds", 60)
        asyncio.create_task(self._send_greeting_after_delay(user_id, delay))
        
        return True
    
    async def _send_greeting_after_delay(self, user_id: int, delay: int):
        """延遲發送問候"""
        await asyncio.sleep(delay)
        
        if user_id not in self.users:
            return
        
        user = self.users[user_id]
        await self._send_topic_message(user, ChatTopic.GREETING)
        user.stage = UserStage.GREETING
        logger.info(f"已向用戶 {user_id} 發送問候，進入 GREETING 階段")
    
    async def on_private_message(self, user_id: int, message: str, ai_account_id: str = ""):
        """處理收到的私聊消息"""
        # 確保用戶存在
        if user_id not in self.users:
            # 新用戶，可能是主動發消息的
            self.users[user_id] = PrivateUser(
                user_id=user_id,
                ai_account_id=ai_account_id,
                stage=UserStage.NEW_FRIEND,
                added_at=datetime.now(),
                invite_scheduled_at=datetime.now() + timedelta(days=self.config.get("invite_after_days", 3))
            )
        
        user = self.users[user_id]
        user.last_message_at = datetime.now()
        user.message_count += 1
        
        # 分析消息情感
        self._analyze_sentiment(user, message)
        
        # 提取興趣
        self._extract_interests(user, message)
        
        # 檢查是否需要更新階段
        self._check_stage_progression(user)
        
        # 生成並發送回覆
        await self._reply_to_message(user, message)
        
        logger.info(f"處理用戶 {user_id} 消息，當前階段: {user.stage.value}, 消息數: {user.message_count}")
    
    def _analyze_sentiment(self, user: PrivateUser, message: str):
        """分析消息情感"""
        positive_words = ["好", "棒", "讚", "喜歡", "開心", "謝謝", "哈哈", "😊", "😄", "👍", "❤️"]
        negative_words = ["不", "沒", "煩", "累", "忙", "討厭", "算了", "😢", "😞"]
        
        message_lower = message.lower()
        positive_count = sum(1 for w in positive_words if w in message_lower)
        negative_count = sum(1 for w in negative_words if w in message_lower)
        
        if positive_count > negative_count:
            user.sentiment = "positive"
        elif negative_count > positive_count:
            user.sentiment = "negative"
        else:
            user.sentiment = "neutral"
    
    def _extract_interests(self, user: PrivateUser, message: str):
        """提取用戶興趣"""
        interest_keywords = {
            "遊戲": ["遊戲", "游戏", "玩", "game"],
            "美食": ["吃", "美食", "餐廳", "火鍋", "奶茶"],
            "旅行": ["旅行", "旅遊", "出去玩", "景點"],
            "運動": ["運動", "健身", "跑步", "球"],
            "追劇": ["劇", "電視", "電影", "看劇"],
            "音樂": ["音樂", "歌", "唱"],
            "投資": ["投資", "理財", "股票", "賺錢"],
        }
        
        message_lower = message.lower()
        for interest, keywords in interest_keywords.items():
            if any(kw in message_lower for kw in keywords):
                if interest not in user.interests:
                    user.interests.append(interest)
    
    def _check_stage_progression(self, user: PrivateUser):
        """檢查並更新用戶階段"""
        now = datetime.now()
        hours_since_added = (now - user.added_at).total_seconds() / 3600
        
        # 階段進度檢查
        if user.stage == UserStage.NEW_FRIEND:
            if user.ai_message_count > 0:
                user.stage = UserStage.GREETING
                
        elif user.stage == UserStage.GREETING:
            if hours_since_added >= 24 or (user.message_count >= 3 and user.sentiment == "positive"):
                user.stage = UserStage.WARMING_UP
                
        elif user.stage == UserStage.WARMING_UP:
            if hours_since_added >= 48 or (user.message_count >= 8 and user.sentiment == "positive"):
                user.stage = UserStage.BUILDING_TRUST
                
        elif user.stage == UserStage.BUILDING_TRUST:
            days_since_added = hours_since_added / 24
            min_messages = self.config.get("min_messages_before_invite", 10)
            invite_days = self.config.get("invite_after_days", 3)
            
            if days_since_added >= invite_days and user.message_count >= min_messages:
                user.stage = UserStage.READY_TO_INVITE
                logger.info(f"用戶 {user.user_id} 已準備好邀請進群")
    
    async def _reply_to_message(self, user: PrivateUser, incoming_message: str):
        """回覆消息"""
        # 延遲回覆
        delay = random.randint(
            self.config.get("reply_delay_min", 3),
            self.config.get("reply_delay_max", 30)
        )
        await asyncio.sleep(delay)
        
        # 根據階段選擇話題
        topics = self.stage_topics.get(user.stage, [ChatTopic.GREETING])
        topic = random.choice(topics)
        
        # 生成回覆
        if self.ai_engine:
            # 使用 AI 引擎生成回覆
            context = f"用戶說: {incoming_message}\n當前話題: {topic.value}\n用戶興趣: {', '.join(user.interests)}"
            reply = await self.ai_engine.generate_reply(context)
        else:
            # 使用預設回覆
            reply = self._get_contextual_reply(user, incoming_message, topic)
        
        # 發送回覆
        await self._send_message(user, reply)
        user.current_topic = topic
    
    def _get_contextual_reply(self, user: PrivateUser, message: str, topic: ChatTopic) -> str:
        """獲取上下文相關的回覆"""
        message_lower = message.lower()
        
        # 問候回覆
        if any(w in message_lower for w in ["你好", "hi", "hello", "嗨"]):
            return random.choice(["你好呀～ 😊", "嗨～今天過得怎麼樣？", "Hello～很高興認識你！"])
        
        # 問題回覆
        if "?" in message or "？" in message or any(w in message_lower for w in ["什麼", "嗎", "呢"]):
            return random.choice(["嗯嗯，是這樣的～", "對呀對呀", "哈哈，是呢"])
        
        # 正面回覆
        if user.sentiment == "positive":
            return random.choice(["哈哈是呀～ 😄", "開心！", "太好了！", "我也覺得！"])
        
        # 話題相關回覆
        topic_replies = {
            ChatTopic.GREETING: ["很高興認識你～", "以後多聊聊呀"],
            ChatTopic.DAILY_LIFE: ["是呢，生活就是這樣", "我懂的～", "加油加油！"],
            ChatTopic.INTERESTS: ["聽起來很有趣！", "我也喜歡！", "下次一起呀"],
            ChatTopic.ENTERTAINMENT: ["這個我也喜歡！", "好玩嗎？", "推薦推薦！"],
            ChatTopic.GAMES: ["遊戲超好玩的！", "要不要一起？", "我最近也在玩"],
            ChatTopic.RED_PACKET: ["紅包真的很刺激！", "手氣怎麼樣？", "群裡經常有活動"],
        }
        
        return random.choice(topic_replies.get(topic, ["嗯嗯～", "是呢", "哈哈"]))
    
    async def _send_topic_message(self, user: PrivateUser, topic: ChatTopic):
        """發送話題消息"""
        messages = self.topic_messages.get(topic, [])
        if not messages:
            return
        
        message = random.choice(messages)
        
        # 替換變量
        message = message.replace("{ai_name}", "我")
        message = message.replace("{weather}", random.choice(["熱", "冷", "舒服"]))
        
        await self._send_message(user, message)
    
    async def _send_message(self, user: PrivateUser, message: str):
        """發送消息給用戶"""
        try:
            # 檢查每日限制
            if user.last_daily_reset.date() != datetime.now().date():
                user.daily_messages_sent = 0
                user.last_daily_reset = datetime.now()
            
            if user.daily_messages_sent >= self.config.get("daily_message_limit", 10):
                logger.info(f"用戶 {user.user_id} 已達每日消息上限")
                return
            
            # 發送消息
            client = self.client_manager.get_client(user.ai_account_id)
            if client:
                await client.send_message(user.user_id, message)
                user.ai_message_count += 1
                user.daily_messages_sent += 1
                user.last_ai_message_at = datetime.now()
                logger.info(f"已向用戶 {user.user_id} 發送消息: {message[:50]}...")
            else:
                logger.warning(f"找不到 AI 賬號 {user.ai_account_id} 的客戶端")
                
        except Exception as e:
            logger.error(f"發送消息給用戶 {user.user_id} 失敗: {e}")
    
    async def invite_user_to_group(self, user_id: int, group_id: int):
        """邀請用戶進群"""
        if user_id not in self.users:
            logger.warning(f"用戶 {user_id} 不存在")
            return False
        
        user = self.users[user_id]
        
        try:
            # 發送邀請前的鋪墊
            script = random.choice(self.invite_scripts)
            
            await self._send_message(user, script["pre_invite"])
            await asyncio.sleep(random.randint(5, 15))
            
            await self._send_message(user, script["invite"])
            await asyncio.sleep(random.randint(3, 8))
            
            # 發送群組邀請鏈接
            client = self.client_manager.get_client(user.ai_account_id)
            if client:
                try:
                    # 獲取群組邀請鏈接
                    chat = await client.get_entity(group_id)
                    invite_link = await client(ExportChatInviteRequest(peer=chat))
                    
                    await client.send_message(user.user_id, f"這是群組鏈接: {invite_link.link}")
                    
                    user.stage = UserStage.INVITED
                    user.invited_at = datetime.now()
                    user.target_group_id = group_id
                    
                    logger.info(f"已邀請用戶 {user_id} 加入群組 {group_id}")
                    
                    # 發送跟進消息
                    await asyncio.sleep(random.randint(10, 30))
                    await self._send_message(user, script["follow_up"])
                    
                    return True
                except Exception as e:
                    logger.error(f"獲取群組邀請鏈接失敗: {e}")
                    # 備用方案：直接邀請
                    await self._send_message(user, f"我把你拉進群裡，你等一下哦～")
                    return True
        
        except Exception as e:
            logger.error(f"邀請用戶 {user_id} 失敗: {e}")
            return False
    
    async def _main_loop(self):
        """主循環 - 主動發送消息"""
        while self.running:
            try:
                if not self.config.get("enabled", True):
                    await asyncio.sleep(60)
                    continue
                
                now = datetime.now()
                
                for user_id, user in list(self.users.items()):
                    # 跳過已邀請/已進群的用戶
                    if user.stage in [UserStage.INVITED, UserStage.JOINED_GROUP, UserStage.CONVERTED]:
                        continue
                    
                    # 檢查是否需要主動發消息
                    last_msg_time = user.last_ai_message_at or user.added_at
                    time_since_last = (now - last_msg_time).total_seconds()
                    
                    min_interval = self.config.get("chat_interval_min", 1800)
                    max_interval = self.config.get("chat_interval_max", 7200)
                    
                    # 隨機決定是否發送
                    if time_since_last >= min_interval:
                        if random.random() < 0.3 or time_since_last >= max_interval:
                            topics = self.stage_topics.get(user.stage, [ChatTopic.DAILY_LIFE])
                            topic = random.choice(topics)
                            await self._send_topic_message(user, topic)
                            
                            # 檢查階段進度
                            self._check_stage_progression(user)
                
                await asyncio.sleep(60)  # 每分鐘檢查一次
                
            except Exception as e:
                logger.error(f"私聊主循環錯誤: {e}")
                await asyncio.sleep(60)
    
    async def _invite_check_loop(self):
        """邀請檢查循環"""
        while self.running:
            try:
                if not self.config.get("enabled", True):
                    await asyncio.sleep(300)
                    continue
                
                target_groups = self.config.get("target_group_ids", [])
                if not target_groups:
                    await asyncio.sleep(300)
                    continue
                
                now = datetime.now()
                
                for user_id, user in list(self.users.items()):
                    # 只處理準備邀請的用戶
                    if user.stage != UserStage.READY_TO_INVITE:
                        continue
                    
                    # 檢查是否到達邀請時間
                    if user.invite_scheduled_at and now >= user.invite_scheduled_at:
                        group_id = random.choice(target_groups)
                        await self.invite_user_to_group(user_id, group_id)
                        await asyncio.sleep(random.randint(60, 180))  # 避免頻繁邀請
                
                await asyncio.sleep(300)  # 每5分鐘檢查一次
                
            except Exception as e:
                logger.error(f"邀請檢查循環錯誤: {e}")
                await asyncio.sleep(300)
    
    def get_status(self) -> Dict[str, Any]:
        """獲取狀態"""
        stage_counts = {}
        for stage in UserStage:
            stage_counts[stage.value] = sum(1 for u in self.users.values() if u.stage == stage)
        
        return {
            "running": self.running,
            "enabled": self.config.get("enabled", True),
            "total_users": len(self.users),
            "by_stage": stage_counts,
            "config": self.config,
        }
