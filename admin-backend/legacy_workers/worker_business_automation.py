"""
業務驅動自動化模組
支持：
- 業務驅動的自動建群
- 聊天進度追蹤
- 根據聊天進度自動邀請真實用戶
- 劇本系統集成
"""

import asyncio
import random
import logging
import re
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any, Callable, Set
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from telethon import TelegramClient, events
from telethon.tl.types import Message, User, Chat, Channel
from telethon.tl.functions.messages import (
    CreateChatRequest, AddChatUserRequest, ExportChatInviteRequest
)
from telethon.tl.functions.channels import (
    CreateChannelRequest, InviteToChannelRequest
)

logger = logging.getLogger(__name__)


# ==================== 聊天階段定義 ====================

class ChatStage(Enum):
    """聊天階段"""
    INITIAL = "initial"              # 初始階段（剛建群）
    WARMING_UP = "warming_up"        # 熱身階段（AI 互相聊天）
    READY_FOR_USERS = "ready"        # 準備好邀請用戶
    USERS_JOINED = "users_joined"    # 用戶已加入
    ENGAGING = "engaging"            # 互動中（引導用戶參與）
    GAME_INTRODUCED = "game_intro"   # 已介紹紅包遊戲
    GAME_PLAYING = "game_playing"    # 遊戲進行中
    CONVERSION = "conversion"        # 轉化階段
    COMPLETED = "completed"          # 完成


class UserEngagementLevel(Enum):
    """用戶參與度等級"""
    COLD = "cold"          # 冷淡（只看不說話）
    LUKEWARM = "lukewarm"  # 溫和（偶爾說話）
    WARM = "warm"          # 熱情（積極參與）
    HOT = "hot"            # 高度參與（頻繁互動、玩遊戲）


# ==================== 數據結構 ====================

@dataclass
class UserProfile:
    """用戶檔案"""
    user_id: int
    username: Optional[str] = None
    first_name: Optional[str] = None
    phone: Optional[str] = None
    
    # 互動數據
    message_count: int = 0
    last_message_time: Optional[datetime] = None
    joined_time: Optional[datetime] = None
    
    # 遊戲數據
    redpacket_sent: int = 0
    redpacket_claimed: int = 0
    total_amount_won: float = 0
    
    # 狀態
    engagement_level: UserEngagementLevel = UserEngagementLevel.COLD
    is_ai: bool = False
    is_invited: bool = False
    
    def update_engagement(self):
        """根據互動數據更新參與度等級"""
        if self.redpacket_claimed > 0 or self.redpacket_sent > 0:
            self.engagement_level = UserEngagementLevel.HOT
        elif self.message_count >= 10:
            self.engagement_level = UserEngagementLevel.WARM
        elif self.message_count >= 3:
            self.engagement_level = UserEngagementLevel.LUKEWARM
        else:
            self.engagement_level = UserEngagementLevel.COLD


@dataclass
class GroupSession:
    """群組會話"""
    group_id: int
    group_name: str
    invite_link: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    creator_id: Optional[int] = None
    
    # 階段追蹤
    current_stage: ChatStage = ChatStage.INITIAL
    stage_history: List[tuple] = field(default_factory=list)  # [(stage, timestamp), ...]
    
    # 成員管理
    ai_members: Set[int] = field(default_factory=set)
    real_users: Dict[int, UserProfile] = field(default_factory=dict)
    pending_invites: Set[int] = field(default_factory=set)
    
    # 消息統計
    total_messages: int = 0
    ai_messages: int = 0
    user_messages: int = 0
    
    # 劇本執行
    script_id: Optional[str] = None
    current_scene: Optional[str] = None
    
    def transition_to_stage(self, new_stage: ChatStage):
        """轉換到新階段"""
        self.stage_history.append((self.current_stage, datetime.now()))
        self.current_stage = new_stage
        logger.info(f"群組 {self.group_id} 進入階段: {new_stage.value}")
    
    def add_ai_member(self, user_id: int):
        """添加 AI 成員"""
        self.ai_members.add(user_id)
    
    def add_real_user(self, user: User):
        """添加真實用戶"""
        profile = UserProfile(
            user_id=user.id,
            username=user.username,
            first_name=user.first_name,
            joined_time=datetime.now(),
            is_ai=False
        )
        self.real_users[user.id] = profile
    
    def get_engagement_summary(self) -> Dict[str, int]:
        """獲取參與度摘要"""
        summary = {level.value: 0 for level in UserEngagementLevel}
        for user in self.real_users.values():
            summary[user.engagement_level.value] += 1
        return summary


# ==================== 聊天進度追蹤器 ====================

class ChatProgressTracker:
    """聊天進度追蹤器 - 追蹤用戶互動並決定何時邀請新用戶"""
    
    def __init__(self):
        self.sessions: Dict[int, GroupSession] = {}
        
        # 階段轉換規則
        self.stage_rules = {
            ChatStage.INITIAL: self._check_initial_complete,
            ChatStage.WARMING_UP: self._check_warmup_complete,
            ChatStage.READY_FOR_USERS: self._check_users_ready,
            ChatStage.USERS_JOINED: self._check_engaging,
            ChatStage.ENGAGING: self._check_game_intro,
            ChatStage.GAME_INTRODUCED: self._check_game_playing,
            ChatStage.GAME_PLAYING: self._check_conversion,
        }
        
        # 階段要求
        self.stage_requirements = {
            ChatStage.INITIAL: {"min_ai_messages": 5, "min_duration_minutes": 2},
            ChatStage.WARMING_UP: {"min_ai_messages": 20, "min_duration_minutes": 5},
            ChatStage.READY_FOR_USERS: {"min_real_users": 1},
            ChatStage.USERS_JOINED: {"min_user_messages": 3},
            ChatStage.ENGAGING: {"min_user_engagement": 0.3},  # 30% 用戶有互動
            ChatStage.GAME_INTRODUCED: {"game_mentioned": True},
            ChatStage.GAME_PLAYING: {"min_game_participants": 1},
        }
    
    def create_session(
        self,
        group_id: int,
        group_name: str,
        creator_id: int,
        invite_link: str = None,
        script_id: str = None
    ) -> GroupSession:
        """創建新的群組會話"""
        session = GroupSession(
            group_id=group_id,
            group_name=group_name,
            invite_link=invite_link,
            creator_id=creator_id,
            script_id=script_id
        )
        self.sessions[group_id] = session
        logger.info(f"創建群組會話: {group_name} (ID: {group_id})")
        return session
    
    def get_session(self, group_id: int) -> Optional[GroupSession]:
        """獲取群組會話"""
        return self.sessions.get(group_id)
    
    def record_message(
        self,
        group_id: int,
        sender_id: int,
        message_text: str,
        is_ai: bool = False
    ):
        """記錄消息"""
        session = self.sessions.get(group_id)
        if not session:
            return
        
        session.total_messages += 1
        
        if is_ai or sender_id in session.ai_members:
            session.ai_messages += 1
        else:
            session.user_messages += 1
            
            # 更新用戶檔案
            if sender_id in session.real_users:
                user = session.real_users[sender_id]
                user.message_count += 1
                user.last_message_time = datetime.now()
                user.update_engagement()
        
        # 檢查是否需要轉換階段
        self._check_stage_transition(session)
    
    def record_redpacket_activity(
        self,
        group_id: int,
        user_id: int,
        activity_type: str,  # "send" or "claim"
        amount: float = 0
    ):
        """記錄紅包活動"""
        session = self.sessions.get(group_id)
        if not session:
            return
        
        if user_id in session.real_users:
            user = session.real_users[user_id]
            if activity_type == "send":
                user.redpacket_sent += 1
            elif activity_type == "claim":
                user.redpacket_claimed += 1
                user.total_amount_won += amount
            user.update_engagement()
        
        self._check_stage_transition(session)
    
    def _check_stage_transition(self, session: GroupSession):
        """檢查是否需要轉換階段"""
        current_stage = session.current_stage
        check_func = self.stage_rules.get(current_stage)
        
        if check_func and check_func(session):
            # 確定下一階段
            next_stage = self._get_next_stage(current_stage)
            if next_stage:
                session.transition_to_stage(next_stage)
    
    def _get_next_stage(self, current: ChatStage) -> Optional[ChatStage]:
        """獲取下一階段"""
        stage_order = [
            ChatStage.INITIAL,
            ChatStage.WARMING_UP,
            ChatStage.READY_FOR_USERS,
            ChatStage.USERS_JOINED,
            ChatStage.ENGAGING,
            ChatStage.GAME_INTRODUCED,
            ChatStage.GAME_PLAYING,
            ChatStage.CONVERSION,
            ChatStage.COMPLETED
        ]
        
        try:
            idx = stage_order.index(current)
            if idx < len(stage_order) - 1:
                return stage_order[idx + 1]
        except ValueError:
            pass
        return None
    
    def _check_initial_complete(self, session: GroupSession) -> bool:
        """檢查初始階段是否完成"""
        reqs = self.stage_requirements[ChatStage.INITIAL]
        duration = (datetime.now() - session.created_at).total_seconds() / 60
        return (
            session.ai_messages >= reqs["min_ai_messages"] and
            duration >= reqs["min_duration_minutes"]
        )
    
    def _check_warmup_complete(self, session: GroupSession) -> bool:
        """檢查熱身階段是否完成"""
        reqs = self.stage_requirements[ChatStage.WARMING_UP]
        duration = (datetime.now() - session.created_at).total_seconds() / 60
        return (
            session.ai_messages >= reqs["min_ai_messages"] and
            duration >= reqs["min_duration_minutes"]
        )
    
    def _check_users_ready(self, session: GroupSession) -> bool:
        """檢查是否有用戶加入"""
        reqs = self.stage_requirements[ChatStage.READY_FOR_USERS]
        return len(session.real_users) >= reqs["min_real_users"]
    
    def _check_engaging(self, session: GroupSession) -> bool:
        """檢查用戶是否開始互動"""
        reqs = self.stage_requirements[ChatStage.USERS_JOINED]
        return session.user_messages >= reqs["min_user_messages"]
    
    def _check_game_intro(self, session: GroupSession) -> bool:
        """檢查是否已介紹遊戲"""
        # 這需要從劇本狀態判斷
        engaged_users = sum(
            1 for u in session.real_users.values()
            if u.engagement_level in [UserEngagementLevel.WARM, UserEngagementLevel.HOT]
        )
        total_users = len(session.real_users)
        if total_users == 0:
            return False
        
        engagement_rate = engaged_users / total_users
        reqs = self.stage_requirements[ChatStage.ENGAGING]
        return engagement_rate >= reqs["min_user_engagement"]
    
    def _check_game_playing(self, session: GroupSession) -> bool:
        """檢查是否有用戶參與遊戲"""
        reqs = self.stage_requirements[ChatStage.GAME_INTRODUCED]
        return any(
            u.redpacket_claimed > 0 or u.redpacket_sent > 0
            for u in session.real_users.values()
        )
    
    def _check_conversion(self, session: GroupSession) -> bool:
        """檢查轉化情況"""
        hot_users = sum(
            1 for u in session.real_users.values()
            if u.engagement_level == UserEngagementLevel.HOT
        )
        return hot_users >= 1
    
    def should_invite_more_users(self, group_id: int) -> bool:
        """判斷是否應該邀請更多用戶"""
        session = self.sessions.get(group_id)
        if not session:
            return False
        
        # 只在準備好階段或之後才邀請
        ready_stages = [
            ChatStage.READY_FOR_USERS,
            ChatStage.USERS_JOINED,
            ChatStage.ENGAGING
        ]
        
        return session.current_stage in ready_stages
    
    def get_invitation_priority(self, group_id: int) -> str:
        """獲取邀請優先級建議"""
        session = self.sessions.get(group_id)
        if not session:
            return "low"
        
        if session.current_stage == ChatStage.READY_FOR_USERS:
            return "high"  # 急需用戶
        elif session.current_stage == ChatStage.USERS_JOINED:
            return "medium"  # 可以邀請更多
        elif session.current_stage == ChatStage.ENGAGING:
            engaged = session.get_engagement_summary()
            if engaged.get("hot", 0) > 0:
                return "medium"  # 有活躍用戶，可以擴展
            return "low"
        
        return "low"


# ==================== 用戶邀請管理器 ====================

class UserInvitationManager:
    """用戶邀請管理器 - 管理真實用戶的邀請"""
    
    def __init__(self, progress_tracker: ChatProgressTracker):
        self.progress_tracker = progress_tracker
        self.user_pool: List[UserProfile] = []  # 待邀請用戶池
        self.invitation_history: Dict[int, List[dict]] = {}  # user_id -> invitations
        
        # 邀請策略配置
        self.config = {
            "min_warmup_messages": 20,  # 邀請前最少 AI 消息數
            "max_invites_per_batch": 3,  # 每批最多邀請人數
            "invite_interval_seconds": 60,  # 邀請間隔
            "cooldown_after_invite": 300,  # 邀請後冷卻時間
        }
    
    def add_to_pool(self, users: List[dict]):
        """添加用戶到邀請池"""
        for user_data in users:
            profile = UserProfile(
                user_id=user_data.get("user_id"),
                username=user_data.get("username"),
                first_name=user_data.get("first_name"),
                phone=user_data.get("phone"),
                is_invited=False
            )
            self.user_pool.append(profile)
        
        logger.info(f"添加 {len(users)} 個用戶到邀請池")
    
    def get_users_to_invite(
        self,
        group_id: int,
        count: int = None
    ) -> List[UserProfile]:
        """獲取待邀請的用戶"""
        if not self.progress_tracker.should_invite_more_users(group_id):
            return []
        
        if count is None:
            count = self.config["max_invites_per_batch"]
        
        # 過濾已邀請的用戶
        available = [u for u in self.user_pool if not u.is_invited]
        
        # 選擇用戶
        selected = available[:count]
        
        return selected
    
    async def invite_users_to_group(
        self,
        client: TelegramClient,
        group_id: int,
        users: List[UserProfile]
    ) -> Dict[int, bool]:
        """邀請用戶到群組"""
        results = {}
        session = self.progress_tracker.get_session(group_id)
        
        for user_profile in users:
            try:
                # 嘗試通過 user_id 邀請
                user = await client.get_entity(user_profile.user_id)
                
                await client(AddChatUserRequest(
                    chat_id=group_id,
                    user_id=user,
                    fwd_limit=50
                ))
                
                user_profile.is_invited = True
                results[user_profile.user_id] = True
                
                # 記錄到會話
                if session:
                    session.add_real_user(user)
                
                logger.info(f"成功邀請用戶 {user_profile.user_id} 到群組 {group_id}")
                
                # 間隔
                await asyncio.sleep(random.uniform(5, 15))
                
            except Exception as e:
                results[user_profile.user_id] = False
                logger.error(f"邀請用戶 {user_profile.user_id} 失敗: {e}")
        
        return results
    
    async def auto_invite_loop(
        self,
        client: TelegramClient,
        group_id: int
    ):
        """自動邀請循環"""
        while True:
            try:
                # 檢查是否應該邀請
                priority = self.progress_tracker.get_invitation_priority(group_id)
                
                if priority == "high":
                    interval = 60
                    count = 3
                elif priority == "medium":
                    interval = 180
                    count = 2
                else:
                    interval = 300
                    count = 1
                
                # 獲取待邀請用戶
                users = self.get_users_to_invite(group_id, count)
                
                if users:
                    await self.invite_users_to_group(client, group_id, users)
                
                await asyncio.sleep(interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"自動邀請異常: {e}")
                await asyncio.sleep(60)


# ==================== 業務驅動群組管理器 ====================

class BusinessGroupManager:
    """業務驅動的群組管理器"""
    
    def __init__(
        self,
        progress_tracker: ChatProgressTracker,
        invitation_manager: UserInvitationManager
    ):
        self.progress_tracker = progress_tracker
        self.invitation_manager = invitation_manager
        self.active_groups: Dict[int, dict] = {}
        
        # 業務配置
        self.config = {
            "group_name_template": "🧧 福利交流群 {index}",
            "max_groups_per_account": 5,
            "warmup_duration_minutes": 10,
            "target_users_per_group": 50,
        }
    
    async def create_business_group(
        self,
        client: TelegramClient,
        creator_user_id: int,
        group_name: str = None,
        script_id: str = None,
        ai_member_ids: List[int] = None
    ) -> Optional[GroupSession]:
        """創建業務群組"""
        
        # 生成群組名稱
        if not group_name:
            index = len(self.active_groups) + 1
            group_name = self.config["group_name_template"].format(index=index)
        
        try:
            # 獲取 AI 成員
            users_to_add = []
            if ai_member_ids:
                for uid in ai_member_ids[:10]:
                    try:
                        user = await client.get_entity(uid)
                        if isinstance(user, User):
                            users_to_add.append(user)
                    except Exception as e:
                        logger.warning(f"無法獲取用戶 {uid}: {e}")
            
            # 創建超級群組
            result = await client(CreateChannelRequest(
                title=group_name,
                about="歡迎加入！這裡有紅包福利和精彩互動 🎉",
                megagroup=True
            ))
            
            chat = result.chats[0]
            group_id = chat.id
            
            logger.info(f"創建業務群組成功: {group_name} (ID: {group_id})")
            
            # 獲取邀請鏈接
            invite_result = await client(ExportChatInviteRequest(peer=chat))
            invite_link = invite_result.link
            
            # 邀請 AI 成員
            if users_to_add:
                try:
                    await client(InviteToChannelRequest(
                        channel=chat,
                        users=users_to_add
                    ))
                except Exception as e:
                    logger.warning(f"邀請 AI 成員失敗: {e}")
            
            # 創建會話追蹤
            session = self.progress_tracker.create_session(
                group_id=group_id,
                group_name=group_name,
                creator_id=creator_user_id,
                invite_link=invite_link,
                script_id=script_id
            )
            
            # 記錄 AI 成員
            session.add_ai_member(creator_user_id)
            for uid in (ai_member_ids or []):
                session.add_ai_member(uid)
            
            # 保存到活躍群組
            self.active_groups[group_id] = {
                "session": session,
                "chat": chat,
                "invite_link": invite_link
            }
            
            return session
            
        except Exception as e:
            logger.error(f"創建業務群組失敗: {e}")
            return None
    
    async def start_warmup_chat(
        self,
        clients: Dict[int, TelegramClient],
        group_id: int,
        script_responses: List[dict] = None
    ):
        """開始熱身聊天（AI 之間互動）"""
        session = self.progress_tracker.get_session(group_id)
        if not session:
            return
        
        # 默認熱身消息
        warmup_messages = script_responses or [
            {"speaker": "小柒", "text": "大家好！今天天氣真不錯～ ☀️"},
            {"speaker": "米米", "text": "是呀是呀！心情都變好了呢 😊"},
            {"speaker": "浩哥", "text": "大家都在忙什麼？"},
            {"speaker": "小柒", "text": "我在追劇！最近有個新劇超好看的 📺"},
            {"speaker": "米米", "text": "是什麼劇？我也想看！"},
            {"speaker": "小雨", "text": "今天讀了一首很美的詩，想分享給大家 🌸"},
            {"speaker": "阿強", "text": "剛忙完工作，來看看大家在聊什麼"},
            {"speaker": "小柒", "text": "話說等會要不要玩紅包遊戲？ 🧧"},
            {"speaker": "米米", "text": "好呀好呀！我手氣一直很好的 ✨"},
            {"speaker": "浩哥", "text": "可以，等人多了再開始"},
        ]
        
        ai_members = list(session.ai_members)
        if not ai_members:
            return
        
        for msg_data in warmup_messages:
            # 隨機選擇一個 AI 發送
            sender_id = random.choice(ai_members)
            client = clients.get(sender_id)
            
            if client:
                try:
                    await client.send_message(
                        group_id,
                        msg_data["text"]
                    )
                    
                    # 記錄消息
                    self.progress_tracker.record_message(
                        group_id, sender_id, msg_data["text"], is_ai=True
                    )
                    
                    # 隨機間隔
                    await asyncio.sleep(random.uniform(15, 45))
                    
                except Exception as e:
                    logger.error(f"發送熱身消息失敗: {e}")
            
            # 檢查是否熱身完成
            if session.current_stage != ChatStage.INITIAL:
                break
        
        logger.info(f"群組 {group_id} 熱身完成")
    
    def get_group_status(self, group_id: int) -> Optional[dict]:
        """獲取群組狀態"""
        session = self.progress_tracker.get_session(group_id)
        if not session:
            return None
        
        return {
            "group_id": group_id,
            "group_name": session.group_name,
            "stage": session.current_stage.value,
            "invite_link": session.invite_link,
            "ai_count": len(session.ai_members),
            "user_count": len(session.real_users),
            "total_messages": session.total_messages,
            "engagement": session.get_engagement_summary(),
            "created_at": session.created_at.isoformat()
        }
    
    def get_all_groups_status(self) -> List[dict]:
        """獲取所有群組狀態"""
        return [
            self.get_group_status(gid)
            for gid in self.active_groups.keys()
        ]


# ==================== 集成劇本系統 ====================

class ScriptIntegratedAutomation:
    """劇本集成自動化 - 將劇本系統與自動化模組結合"""
    
    def __init__(
        self,
        business_manager: BusinessGroupManager,
        progress_tracker: ChatProgressTracker
    ):
        self.business_manager = business_manager
        self.progress_tracker = progress_tracker
        self.script_states: Dict[int, dict] = {}  # group_id -> script state
    
    def load_script_for_group(self, group_id: int, script_data: dict):
        """為群組載入劇本"""
        self.script_states[group_id] = {
            "script_id": script_data.get("script_id"),
            "current_scene": "scene1_welcome",
            "scenes_completed": [],
            "variables": {}
        }
        
        session = self.progress_tracker.get_session(group_id)
        if session:
            session.script_id = script_data.get("script_id")
    
    def get_response_for_stage(
        self,
        group_id: int,
        trigger_type: str,
        context: dict = None
    ) -> Optional[dict]:
        """根據當前階段和觸發條件獲取回復"""
        session = self.progress_tracker.get_session(group_id)
        if not session:
            return None
        
        script_state = self.script_states.get(group_id)
        if not script_state:
            return None
        
        # 根據階段選擇場景
        stage_scene_map = {
            ChatStage.INITIAL: "scene1_welcome",
            ChatStage.WARMING_UP: "scene2_casual_chat",
            ChatStage.USERS_JOINED: "scene2_casual_chat",
            ChatStage.ENGAGING: "scene3_introduce_game",
            ChatStage.GAME_INTRODUCED: "scene4_game_playing",
            ChatStage.GAME_PLAYING: "scene5_game_result",
        }
        
        recommended_scene = stage_scene_map.get(session.current_stage)
        
        return {
            "scene": recommended_scene,
            "trigger_type": trigger_type,
            "stage": session.current_stage.value
        }
    
    def advance_script(self, group_id: int, scene_completed: str):
        """推進劇本進度"""
        script_state = self.script_states.get(group_id)
        if script_state:
            script_state["scenes_completed"].append(scene_completed)
            
            # 更新當前場景
            scene_order = [
                "scene1_welcome",
                "scene2_casual_chat",
                "scene3_introduce_game",
                "scene4_game_playing",
                "scene5_game_result",
                "scene6_continue_chat"
            ]
            
            try:
                idx = scene_order.index(scene_completed)
                if idx < len(scene_order) - 1:
                    script_state["current_scene"] = scene_order[idx + 1]
            except ValueError:
                pass


# ==================== 完整業務自動化系統 ====================

class FullBusinessAutomation:
    """完整業務自動化系統 - 整合所有功能"""
    
    def __init__(self):
        self.progress_tracker = ChatProgressTracker()
        self.invitation_manager = UserInvitationManager(self.progress_tracker)
        self.business_manager = BusinessGroupManager(
            self.progress_tracker,
            self.invitation_manager
        )
        self.script_automation = ScriptIntegratedAutomation(
            self.business_manager,
            self.progress_tracker
        )
        
        self.clients: Dict[int, TelegramClient] = {}
        self.running = False
    
    def add_client(self, user_id: int, client: TelegramClient):
        """添加 Telegram 客戶端"""
        self.clients[user_id] = client
    
    def add_users_to_invite_pool(self, users: List[dict]):
        """添加用戶到邀請池"""
        self.invitation_manager.add_to_pool(users)
    
    async def create_and_start_group(
        self,
        creator_user_id: int,
        group_name: str = None,
        script_id: str = None
    ) -> Optional[GroupSession]:
        """創建並啟動業務群組"""
        
        client = self.clients.get(creator_user_id)
        if not client:
            logger.error(f"找不到用戶 {creator_user_id} 的客戶端")
            return None
        
        # 獲取其他 AI 的 user_id
        other_ai_ids = [uid for uid in self.clients.keys() if uid != creator_user_id]
        
        # 創建群組
        session = await self.business_manager.create_business_group(
            client=client,
            creator_user_id=creator_user_id,
            group_name=group_name,
            script_id=script_id,
            ai_member_ids=other_ai_ids
        )
        
        if not session:
            return None
        
        # 載入劇本
        if script_id:
            self.script_automation.load_script_for_group(
                session.group_id,
                {"script_id": script_id}
            )
        
        # 開始熱身聊天
        asyncio.create_task(
            self.business_manager.start_warmup_chat(
                self.clients,
                session.group_id
            )
        )
        
        return session
    
    async def start_auto_invitation(self, group_id: int):
        """啟動自動邀請"""
        # 選擇一個客戶端執行邀請
        if self.clients:
            client = list(self.clients.values())[0]
            asyncio.create_task(
                self.invitation_manager.auto_invite_loop(client, group_id)
            )
    
    def get_system_status(self) -> dict:
        """獲取系統狀態"""
        return {
            "clients_count": len(self.clients),
            "active_groups": self.business_manager.get_all_groups_status(),
            "invite_pool_size": len(self.invitation_manager.user_pool),
            "running": self.running
        }


# 導出
__all__ = [
    "ChatStage",
    "UserEngagementLevel",
    "UserProfile",
    "GroupSession",
    "ChatProgressTracker",
    "UserInvitationManager",
    "BusinessGroupManager",
    "ScriptIntegratedAutomation",
    "FullBusinessAutomation"
]
