"""
多賬號協同管理器 - 協調多個賬號在同一群組中的對話
"""
import asyncio
import logging
import time
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict
from enum import Enum

from pyrogram.types import Message

logger = logging.getLogger(__name__)


class ReplyPriority(Enum):
    """回復優先級"""
    HIGH = 3      # 高優先級（例如：角色互動序列中的第一個）
    NORMAL = 2    # 正常優先級
    LOW = 1       # 低優先級（例如：備用角色）
    NONE = 0      # 不回復


@dataclass
class AccountRoleInfo:
    """賬號角色信息"""
    account_id: str
    role_id: Optional[str] = None
    role_name: Optional[str] = None
    priority: ReplyPriority = ReplyPriority.NORMAL
    last_reply_time: Optional[datetime] = None
    reply_count_recent: int = 0  # 最近回復次數（用於負載均衡）
    is_active: bool = True


@dataclass
class ReplyLock:
    """回復鎖 - 防止多個賬號同時回復同一消息"""
    message_id: int
    group_id: int
    locked_account_id: Optional[str] = None
    locked_at: Optional[datetime] = None
    lock_ttl: int = 30  # 鎖的TTL（秒）


@dataclass
class GroupCoordination:
    """群組協調信息"""
    group_id: int
    accounts: Dict[str, AccountRoleInfo] = field(default_factory=dict)
    role_sequence: List[str] = field(default_factory=list)  # 角色互動序列
    last_message_id: Optional[int] = None
    last_reply_time: Optional[datetime] = None
    active_reply_locks: Dict[int, ReplyLock] = field(default_factory=dict)  # message_id -> ReplyLock


class CoordinationManager:
    """多賬號協同管理器"""
    
    def __init__(self, lock_ttl: int = 30, cleanup_interval: int = 60):
        """
        初始化協同管理器
        
        Args:
            lock_ttl: 回復鎖的TTL（秒）
            cleanup_interval: 清理過期鎖的間隔（秒）
        """
        self.logger = logging.getLogger(__name__)
        self.lock_ttl = lock_ttl
        self.cleanup_interval = cleanup_interval
        
        # group_id -> GroupCoordination
        self.group_coordinations: Dict[int, GroupCoordination] = {}
        
        # account_id -> role_id 映射（從角色分配方案獲取）
        self.account_roles: Dict[str, str] = {}
        
        # 角色優先級映射（可配置）
        self.role_priorities: Dict[str, ReplyPriority] = {}
        
        # 清理任務
        self._cleanup_task: Optional[asyncio.Task] = None
        self._running = False
        
        self.logger.info("CoordinationManager 初始化完成")
    
    async def start(self):
        """啟動協同管理器（啟動清理任務）"""
        if self._running:
            return
        
        self._running = True
        self._cleanup_task = asyncio.create_task(self._cleanup_expired_locks())
        self.logger.info("CoordinationManager 已啟動")
    
    async def stop(self):
        """停止協同管理器"""
        self._running = False
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        self.logger.info("CoordinationManager 已停止")
    
    def register_account_role(
        self,
        account_id: str,
        role_id: Optional[str] = None,
        role_name: Optional[str] = None,
        priority: Optional[ReplyPriority] = None
    ):
        """
        註冊賬號角色
        
        Args:
            account_id: 賬號ID
            role_id: 角色ID
            role_name: 角色名稱
            priority: 優先級（可選）
        """
        if role_id:
            self.account_roles[account_id] = role_id
        
        # 設置優先級
        if priority:
            self.role_priorities[role_id or account_id] = priority
        elif role_id and role_id in self.role_priorities:
            priority = self.role_priorities[role_id]
        else:
            priority = ReplyPriority.NORMAL
        
        self.logger.info(f"註冊賬號角色: {account_id} -> {role_id} ({role_name}), 優先級: {priority.name}")
    
    def unregister_account(self, account_id: str):
        """取消註冊賬號"""
        self.account_roles.pop(account_id, None)
        # 從所有群組協調中移除
        for group_coord in self.group_coordinations.values():
            group_coord.accounts.pop(account_id, None)
        self.logger.info(f"取消註冊賬號: {account_id}")
    
    def register_account_to_group(
        self,
        account_id: str,
        group_id: int
    ):
        """註冊賬號到群組"""
        group_coord = self._get_or_create_group_coordination(group_id)
        
        role_id = self.account_roles.get(account_id)
        role_name = None  # 可以從其他地方獲取
        
        priority = self.role_priorities.get(role_id or account_id, ReplyPriority.NORMAL)
        
        account_info = AccountRoleInfo(
            account_id=account_id,
            role_id=role_id,
            role_name=role_name,
            priority=priority,
            is_active=True
        )
        
        group_coord.accounts[account_id] = account_info
        self.logger.info(f"註冊賬號到群組: {account_id} -> 群組 {group_id}, 角色: {role_id}")
    
    def unregister_account_from_group(
        self,
        account_id: str,
        group_id: int
    ):
        """從群組取消註冊賬號"""
        if group_id in self.group_coordinations:
            self.group_coordinations[group_id].accounts.pop(account_id, None)
            self.logger.info(f"從群組取消註冊: {account_id} -> 群組 {group_id}")
    
    def set_role_sequence(
        self,
        group_id: int,
        role_sequence: List[str]
    ):
        """設置角色互動序列"""
        group_coord = self._get_or_create_group_coordination(group_id)
        group_coord.role_sequence = role_sequence
        
        # 根據序列設置優先級
        for i, role_id in enumerate(role_sequence):
            priority = ReplyPriority.HIGH if i == 0 else ReplyPriority.NORMAL
            self.role_priorities[role_id] = priority
            
            # 更新群組中相關賬號的優先級
            for account_info in group_coord.accounts.values():
                if account_info.role_id == role_id:
                    account_info.priority = priority
        
        self.logger.info(f"設置群組 {group_id} 角色序列: {role_sequence}")
    
    async def should_reply(
        self,
        account_id: str,
        group_id: int,
        message: Message
    ) -> Tuple[bool, Optional[str]]:
        """
        判斷賬號是否應該回復消息
        
        Returns:
            (should_reply: bool, reason: str or None)
        """
        group_coord = self._get_or_create_group_coordination(group_id)
        
        # 獲取賬號信息
        account_info = group_coord.accounts.get(account_id)
        if not account_info:
            return False, "賬號未註冊到該群組"
        
        if not account_info.is_active:
            return False, "賬號未激活"
        
        # 檢查回復鎖
        lock = group_coord.active_reply_locks.get(message.id)
        if lock:
            # 如果已經被其他賬號鎖定，檢查是否是當前賬號鎖定的
            if lock.locked_account_id == account_id:
                # 當前賬號已鎖定，允許回復
                return True, None
            else:
                # 被其他賬號鎖定，不回復
                return False, f"消息已被賬號 {lock.locked_account_id} 鎖定"
        
        # 獲取該群組中所有可能回復的賬號
        candidate_accounts = self._get_reply_candidates(group_coord, message)
        
        if not candidate_accounts:
            return False, "沒有可回復的賬號"
        
        # 根據優先級選擇賬號
        selected_account = self._select_account_to_reply(candidate_accounts, group_coord)
        
        if selected_account.account_id != account_id:
            return False, f"應該由賬號 {selected_account.account_id} 回復（優先級更高）"
        
        # 當前賬號應該回復，創建回復鎖
        await self._create_reply_lock(group_coord, message.id, account_id)
        
        return True, None
    
    async def on_reply_sent(
        self,
        account_id: str,
        group_id: int,
        message_id: int
    ):
        """當回復發送後調用，更新狀態"""
        group_coord = self._get_or_create_group_coordination(group_id)
        account_info = group_coord.accounts.get(account_id)
        
        if account_info:
            account_info.last_reply_time = datetime.now()
            account_info.reply_count_recent += 1
        
        group_coord.last_reply_time = datetime.now()
        group_coord.last_message_id = message_id
        
        # 保留鎖一段時間，然後清理
        # 鎖會通過清理任務自動過期
        
        self.logger.debug(f"賬號 {account_id} 在群組 {group_id} 發送了回復")
    
    def _get_or_create_group_coordination(self, group_id: int) -> GroupCoordination:
        """獲取或創建群組協調信息"""
        if group_id not in self.group_coordinations:
            self.group_coordinations[group_id] = GroupCoordination(group_id=group_id)
        return self.group_coordinations[group_id]
    
    def _get_reply_candidates(
        self,
        group_coord: GroupCoordination,
        message: Message
    ) -> List[AccountRoleInfo]:
        """獲取可能回復的賬號候選列表"""
        candidates = []
        
        for account_info in group_coord.accounts.values():
            if account_info.is_active:
                candidates.append(account_info)
        
        return candidates
    
    def _select_account_to_reply(
        self,
        candidates: List[AccountRoleInfo],
        group_coord: GroupCoordination
    ) -> AccountRoleInfo:
        """
        從候選賬號中選擇一個來回復
        
        選擇邏輯：
        1. 根據角色序列優先級
        2. 根據角色優先級
        3. 根據最近回復次數（負載均衡）
        4. 根據最後回復時間
        """
        if not candidates:
            raise ValueError("沒有候選賬號")
        
        if len(candidates) == 1:
            return candidates[0]
        
        # 如果有角色序列，優先選擇序列中的第一個角色
        if group_coord.role_sequence:
            for role_id in group_coord.role_sequence:
                for account_info in candidates:
                    if account_info.role_id == role_id:
                        return account_info
        
        # 按優先級排序
        candidates.sort(key=lambda a: (
            a.priority.value,  # 優先級（高優先級在前）
            a.reply_count_recent,  # 最近回復次數（少優先）
            -a.last_reply_time.timestamp() if a.last_reply_time else 0  # 最後回復時間（早優先）
        ), reverse=True)
        
        return candidates[0]
    
    async def _create_reply_lock(
        self,
        group_coord: GroupCoordination,
        message_id: int,
        account_id: str
    ):
        """創建回復鎖"""
        lock = ReplyLock(
            message_id=message_id,
            group_id=group_coord.group_id,
            locked_account_id=account_id,
            locked_at=datetime.now(),
            lock_ttl=self.lock_ttl
        )
        
        group_coord.active_reply_locks[message_id] = lock
        self.logger.debug(f"創建回復鎖: 消息 {message_id} 被賬號 {account_id} 鎖定")
    
    async def _cleanup_expired_locks(self):
        """清理過期的回復鎖"""
        while self._running:
            try:
                await asyncio.sleep(self.cleanup_interval)
                
                now = datetime.now()
                expired_locks = []
                
                for group_coord in self.group_coordinations.values():
                    for message_id, lock in list(group_coord.active_reply_locks.items()):
                        if lock.locked_at:
                            age = (now - lock.locked_at).total_seconds()
                            if age > lock.lock_ttl:
                                expired_locks.append((group_coord.group_id, message_id))
                    
                    # 清理過期鎖
                    for group_id, message_id in expired_locks:
                        group_coord.active_reply_locks.pop(message_id, None)
                
                if expired_locks:
                    self.logger.debug(f"清理了 {len(expired_locks)} 個過期回復鎖")
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"清理過期鎖時發生錯誤: {e}", exc_info=True)
    
    def get_group_accounts(self, group_id: int) -> List[AccountRoleInfo]:
        """獲取群組中的所有賬號信息"""
        group_coord = self.group_coordinations.get(group_id)
        if not group_coord:
            return []
        return list(group_coord.accounts.values())
    
    def get_account_role(self, account_id: str) -> Optional[str]:
        """獲取賬號的角色ID"""
        return self.account_roles.get(account_id)
