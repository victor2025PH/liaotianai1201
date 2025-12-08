"""
📊 多群組管理模組
支持：
- 群組池管理
- 資源調度（AI 帳號分配）
- 跨群組協調
- 群組生命周期管理
"""

import asyncio
import random
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any, Set, Callable
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict

from telethon import TelegramClient

logger = logging.getLogger(__name__)


# ==================== 群組狀態 ====================

class GroupStatus(Enum):
    """群組狀態"""
    PENDING = "pending"          # 待創建
    CREATING = "creating"        # 創建中
    WARMING_UP = "warming_up"    # 熱身中
    ACTIVE = "active"            # 活躍
    FULL = "full"                # 已滿
    COOLING = "cooling"          # 冷卻中
    ARCHIVED = "archived"        # 已歸檔
    ERROR = "error"              # 錯誤


class AIAssignmentStrategy(Enum):
    """AI 分配策略"""
    ROUND_ROBIN = "round_robin"      # 輪詢分配
    LEAST_LOADED = "least_loaded"    # 最少負載
    RANDOM = "random"                # 隨機分配
    SKILL_BASED = "skill_based"      # 技能匹配


# ==================== 數據結構 ====================

@dataclass
class GroupConfig:
    """群組配置"""
    name_template: str = "🧧 福利交流群 {index}"
    max_users: int = 100
    min_ai_count: int = 4
    max_ai_count: int = 8
    warmup_duration_minutes: int = 10
    script_id: str = ""
    auto_archive_after_hours: int = 72


@dataclass
class GroupInfo:
    """群組信息"""
    group_id: int
    name: str
    invite_link: Optional[str] = None
    status: GroupStatus = GroupStatus.PENDING
    
    # 創建信息
    created_at: datetime = field(default_factory=datetime.now)
    creator_id: Optional[int] = None
    
    # 成員統計
    ai_members: Set[int] = field(default_factory=set)
    real_users: Set[int] = field(default_factory=set)
    
    # 活動統計
    total_messages: int = 0
    last_activity: Optional[datetime] = None
    
    # 配置
    config: GroupConfig = field(default_factory=GroupConfig)
    script_id: Optional[str] = None
    
    @property
    def ai_count(self) -> int:
        return len(self.ai_members)
    
    @property
    def user_count(self) -> int:
        return len(self.real_users)
    
    @property
    def is_full(self) -> bool:
        return self.user_count >= self.config.max_users
    
    def to_dict(self) -> dict:
        return {
            "group_id": self.group_id,
            "name": self.name,
            "invite_link": self.invite_link,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "ai_count": self.ai_count,
            "user_count": self.user_count,
            "total_messages": self.total_messages,
            "last_activity": self.last_activity.isoformat() if self.last_activity else None,
        }


@dataclass
class AIAccountInfo:
    """AI 帳號信息"""
    user_id: int
    username: Optional[str] = None
    phone: Optional[str] = None
    
    # 分配狀態
    assigned_groups: Set[int] = field(default_factory=set)
    max_groups: int = 5
    
    # 狀態
    is_online: bool = True
    last_heartbeat: datetime = field(default_factory=datetime.now)
    
    # 統計
    messages_sent: int = 0
    errors_count: int = 0
    
    @property
    def load(self) -> float:
        """當前負載（0-1）"""
        return len(self.assigned_groups) / self.max_groups
    
    @property
    def can_assign_more(self) -> bool:
        return len(self.assigned_groups) < self.max_groups


# ==================== 群組池 ====================

class GroupPool:
    """群組池 - 管理所有群組"""
    
    def __init__(self, default_config: GroupConfig = None):
        self.default_config = default_config or GroupConfig()
        self.groups: Dict[int, GroupInfo] = {}
        self._group_index = 0
    
    def add_group(self, group_info: GroupInfo) -> GroupInfo:
        """添加群組"""
        self.groups[group_info.group_id] = group_info
        return group_info
    
    def get_group(self, group_id: int) -> Optional[GroupInfo]:
        """獲取群組"""
        return self.groups.get(group_id)
    
    def remove_group(self, group_id: int):
        """移除群組"""
        if group_id in self.groups:
            del self.groups[group_id]
    
    def get_groups_by_status(self, status: GroupStatus) -> List[GroupInfo]:
        """按狀態獲取群組"""
        return [g for g in self.groups.values() if g.status == status]
    
    def get_active_groups(self) -> List[GroupInfo]:
        """獲取活躍群組"""
        return [g for g in self.groups.values() if g.status in [
            GroupStatus.WARMING_UP, GroupStatus.ACTIVE
        ]]
    
    def get_available_groups(self) -> List[GroupInfo]:
        """獲取可接收新用戶的群組"""
        return [g for g in self.groups.values() if 
                g.status == GroupStatus.ACTIVE and not g.is_full]
    
    def get_next_group_name(self) -> str:
        """生成下一個群組名稱"""
        self._group_index += 1
        return self.default_config.name_template.format(index=self._group_index)
    
    def get_statistics(self) -> dict:
        """獲取統計信息"""
        status_counts = defaultdict(int)
        for group in self.groups.values():
            status_counts[group.status.value] += 1
        
        return {
            "total_groups": len(self.groups),
            "by_status": dict(status_counts),
            "total_ai": sum(g.ai_count for g in self.groups.values()),
            "total_users": sum(g.user_count for g in self.groups.values()),
            "total_messages": sum(g.total_messages for g in self.groups.values()),
        }


# ==================== AI 資源調度器 ====================

class AIResourceScheduler:
    """AI 資源調度器"""
    
    def __init__(
        self,
        strategy: AIAssignmentStrategy = AIAssignmentStrategy.LEAST_LOADED
    ):
        self.strategy = strategy
        self.ai_accounts: Dict[int, AIAccountInfo] = {}
        self._round_robin_index = 0
    
    def register_ai(self, ai_info: AIAccountInfo):
        """註冊 AI 帳號"""
        self.ai_accounts[ai_info.user_id] = ai_info
        logger.info(f"註冊 AI 帳號: {ai_info.user_id}")
    
    def unregister_ai(self, user_id: int):
        """註銷 AI 帳號"""
        if user_id in self.ai_accounts:
            del self.ai_accounts[user_id]
    
    def get_available_ais(self) -> List[AIAccountInfo]:
        """獲取可用的 AI"""
        return [ai for ai in self.ai_accounts.values() 
                if ai.is_online and ai.can_assign_more]
    
    def allocate_ais_for_group(
        self,
        group_id: int,
        count: int
    ) -> List[int]:
        """
        為群組分配 AI
        
        Returns:
            分配的 AI user_id 列表
        """
        available = self.get_available_ais()
        
        if len(available) < count:
            logger.warning(f"可用 AI 不足：需要 {count}，可用 {len(available)}")
            count = len(available)
        
        if count == 0:
            return []
        
        # 根據策略選擇
        if self.strategy == AIAssignmentStrategy.ROUND_ROBIN:
            selected = self._select_round_robin(available, count)
        elif self.strategy == AIAssignmentStrategy.LEAST_LOADED:
            selected = self._select_least_loaded(available, count)
        elif self.strategy == AIAssignmentStrategy.RANDOM:
            selected = self._select_random(available, count)
        else:
            selected = self._select_least_loaded(available, count)
        
        # 更新分配狀態
        for ai in selected:
            ai.assigned_groups.add(group_id)
        
        return [ai.user_id for ai in selected]
    
    def release_ais_from_group(self, group_id: int):
        """釋放群組的 AI"""
        for ai in self.ai_accounts.values():
            ai.assigned_groups.discard(group_id)
    
    def _select_round_robin(
        self,
        available: List[AIAccountInfo],
        count: int
    ) -> List[AIAccountInfo]:
        """輪詢選擇"""
        selected = []
        for _ in range(count):
            self._round_robin_index = (self._round_robin_index + 1) % len(available)
            selected.append(available[self._round_robin_index])
        return selected
    
    def _select_least_loaded(
        self,
        available: List[AIAccountInfo],
        count: int
    ) -> List[AIAccountInfo]:
        """選擇負載最低的"""
        sorted_ais = sorted(available, key=lambda x: x.load)
        return sorted_ais[:count]
    
    def _select_random(
        self,
        available: List[AIAccountInfo],
        count: int
    ) -> List[AIAccountInfo]:
        """隨機選擇"""
        return random.sample(available, min(count, len(available)))
    
    def get_ais_for_group(self, group_id: int) -> List[AIAccountInfo]:
        """獲取群組的 AI"""
        return [ai for ai in self.ai_accounts.values() 
                if group_id in ai.assigned_groups]
    
    def get_statistics(self) -> dict:
        """獲取統計"""
        online_count = sum(1 for ai in self.ai_accounts.values() if ai.is_online)
        total_assigned = sum(len(ai.assigned_groups) for ai in self.ai_accounts.values())
        
        return {
            "total_ais": len(self.ai_accounts),
            "online_ais": online_count,
            "total_assignments": total_assigned,
            "average_load": total_assigned / len(self.ai_accounts) if self.ai_accounts else 0
        }


# ==================== 多群組管理器 ====================

class MultiGroupManager:
    """多群組管理器 - 協調所有群組和 AI"""
    
    def __init__(
        self,
        default_config: GroupConfig = None,
        ai_strategy: AIAssignmentStrategy = AIAssignmentStrategy.LEAST_LOADED
    ):
        self.group_pool = GroupPool(default_config)
        self.ai_scheduler = AIResourceScheduler(ai_strategy)
        
        # Telegram 客戶端
        self.clients: Dict[int, TelegramClient] = {}
        
        # 事件回調
        self.on_group_created: Optional[Callable] = None
        self.on_group_status_changed: Optional[Callable] = None
        self.on_user_joined: Optional[Callable] = None
    
    def register_client(self, user_id: int, client: TelegramClient):
        """註冊 Telegram 客戶端"""
        self.clients[user_id] = client
        
        # 同時註冊為 AI
        ai_info = AIAccountInfo(user_id=user_id)
        self.ai_scheduler.register_ai(ai_info)
    
    async def create_group(
        self,
        name: str = None,
        config: GroupConfig = None,
        script_id: str = None
    ) -> Optional[GroupInfo]:
        """創建新群組"""
        config = config or self.group_pool.default_config
        name = name or self.group_pool.get_next_group_name()
        
        # 選擇創建者
        available_ais = self.ai_scheduler.get_available_ais()
        if not available_ais:
            logger.error("沒有可用的 AI 來創建群組")
            return None
        
        creator_ai = available_ais[0]
        client = self.clients.get(creator_ai.user_id)
        
        if not client:
            logger.error(f"找不到 AI {creator_ai.user_id} 的客戶端")
            return None
        
        # 分配 AI
        ai_count = random.randint(config.min_ai_count, config.max_ai_count)
        assigned_ai_ids = self.ai_scheduler.allocate_ais_for_group(0, ai_count)  # 臨時 ID
        
        try:
            # 創建群組
            from telethon.tl.functions.channels import CreateChannelRequest
            from telethon.tl.functions.messages import ExportChatInviteRequest
            
            result = await client(CreateChannelRequest(
                title=name,
                about="歡迎加入！這裡有紅包福利和精彩互動 🎉",
                megagroup=True
            ))
            
            chat = result.chats[0]
            group_id = chat.id
            
            # 獲取邀請鏈接
            invite_result = await client(ExportChatInviteRequest(peer=chat))
            invite_link = invite_result.link
            
            # 創建群組信息
            group_info = GroupInfo(
                group_id=group_id,
                name=name,
                invite_link=invite_link,
                status=GroupStatus.CREATING,
                creator_id=creator_ai.user_id,
                config=config,
                script_id=script_id
            )
            
            # 更新 AI 分配
            self.ai_scheduler.release_ais_from_group(0)
            for ai_id in assigned_ai_ids:
                self.ai_scheduler.ai_accounts[ai_id].assigned_groups.add(group_id)
                group_info.ai_members.add(ai_id)
            
            # 邀請 AI 成員
            await self._invite_ais_to_group(group_info)
            
            # 添加到群組池
            self.group_pool.add_group(group_info)
            
            # 更新狀態
            group_info.status = GroupStatus.WARMING_UP
            
            # 觸發回調
            if self.on_group_created:
                await self.on_group_created(group_info)
            
            logger.info(f"創建群組成功: {name} (ID: {group_id})")
            return group_info
            
        except Exception as e:
            logger.error(f"創建群組失敗: {e}")
            # 釋放分配的 AI
            self.ai_scheduler.release_ais_from_group(0)
            return None
    
    async def _invite_ais_to_group(self, group_info: GroupInfo):
        """邀請 AI 到群組"""
        from telethon.tl.functions.channels import InviteToChannelRequest
        
        creator_client = self.clients.get(group_info.creator_id)
        if not creator_client:
            return
        
        for ai_id in group_info.ai_members:
            if ai_id == group_info.creator_id:
                continue
            
            try:
                user = await creator_client.get_entity(ai_id)
                await creator_client(InviteToChannelRequest(
                    channel=group_info.group_id,
                    users=[user]
                ))
                await asyncio.sleep(random.uniform(2, 5))
            except Exception as e:
                logger.warning(f"邀請 AI {ai_id} 失敗: {e}")
    
    async def activate_group(self, group_id: int):
        """激活群組（熱身完成後）"""
        group = self.group_pool.get_group(group_id)
        if group and group.status == GroupStatus.WARMING_UP:
            group.status = GroupStatus.ACTIVE
            
            if self.on_group_status_changed:
                await self.on_group_status_changed(group, GroupStatus.ACTIVE)
    
    async def archive_group(self, group_id: int):
        """歸檔群組"""
        group = self.group_pool.get_group(group_id)
        if group:
            group.status = GroupStatus.ARCHIVED
            self.ai_scheduler.release_ais_from_group(group_id)
            
            if self.on_group_status_changed:
                await self.on_group_status_changed(group, GroupStatus.ARCHIVED)
    
    def get_best_group_for_user(self) -> Optional[GroupInfo]:
        """獲取最適合新用戶的群組"""
        available = self.group_pool.get_available_groups()
        if not available:
            return None
        
        # 選擇用戶最少的群組
        return min(available, key=lambda g: g.user_count)
    
    def record_user_join(self, group_id: int, user_id: int):
        """記錄用戶加入"""
        group = self.group_pool.get_group(group_id)
        if group:
            group.real_users.add(user_id)
            group.last_activity = datetime.now()
            
            # 檢查是否已滿
            if group.is_full:
                group.status = GroupStatus.FULL
    
    def record_message(self, group_id: int, user_id: int):
        """記錄消息"""
        group = self.group_pool.get_group(group_id)
        if group:
            group.total_messages += 1
            group.last_activity = datetime.now()
    
    def get_all_groups_status(self) -> List[dict]:
        """獲取所有群組狀態"""
        return [g.to_dict() for g in self.group_pool.groups.values()]
    
    def get_system_statistics(self) -> dict:
        """獲取系統統計"""
        return {
            "groups": self.group_pool.get_statistics(),
            "ai_accounts": self.ai_scheduler.get_statistics()
        }
    
    async def auto_scale(self, target_available_groups: int = 3):
        """自動擴縮容"""
        available_count = len(self.group_pool.get_available_groups())
        
        if available_count < target_available_groups:
            # 需要創建更多群組
            to_create = target_available_groups - available_count
            logger.info(f"自動擴容：創建 {to_create} 個新群組")
            
            for _ in range(to_create):
                await self.create_group()
                await asyncio.sleep(5)  # 間隔避免限流


# 導出
__all__ = [
    "GroupStatus",
    "AIAssignmentStrategy",
    "GroupConfig",
    "GroupInfo",
    "AIAccountInfo",
    "GroupPool",
    "AIResourceScheduler",
    "MultiGroupManager"
]
