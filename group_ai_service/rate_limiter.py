"""
消息處理頻率限制器
防止過度處理消息，保護系統穩定性
"""
import logging
from typing import Dict, Optional, Any
from datetime import datetime, timedelta
from collections import defaultdict, deque

logger = logging.getLogger(__name__)


class MessageRateLimiter:
    """消息處理頻率限制器"""
    
    def __init__(
        self,
        max_per_minute: int = 60,  # 每分鐘最多處理的消息數
        max_per_hour: int = 1000,  # 每小時最多處理的消息數
        max_per_account_per_minute: int = 30,  # 每個賬號每分鐘最多處理的消息數
        max_per_group_per_minute: int = 20,  # 每個群組每分鐘最多處理的消息數
        window_size: int = 60  # 時間窗口大小（秒）
    ):
        """
        初始化頻率限制器
        
        Args:
            max_per_minute: 全局每分鐘最大處理數
            max_per_hour: 全局每小時最大處理數
            max_per_account_per_minute: 每個賬號每分鐘最大處理數
            max_per_group_per_minute: 每個群組每分鐘最大處理數
            window_size: 滑動窗口大小（秒）
        """
        self.max_per_minute = max_per_minute
        self.max_per_hour = max_per_hour
        self.max_per_account_per_minute = max_per_account_per_minute
        self.max_per_group_per_minute = max_per_group_per_minute
        self.window_size = window_size
        
        # 全局計數器（使用滑動窗口）
        self.global_timestamps: deque = deque()
        self.hourly_timestamps: deque = deque()
        
        # 按賬號計數
        self.account_timestamps: Dict[str, deque] = defaultdict(lambda: deque())
        
        # 按群組計數
        self.group_timestamps: Dict[int, deque] = defaultdict(lambda: deque())
        
        self.logger = logging.getLogger(__name__)
    
    def check_rate_limit(
        self,
        account_id: str,
        group_id: Optional[int] = None
    ) -> tuple[bool, Optional[str]]:
        """
        檢查是否超過頻率限制
        
        Args:
            account_id: 賬號 ID
            group_id: 群組 ID（可選）
            
        Returns:
            (是否允許, 錯誤消息)
        """
        now = datetime.now()
        minute_ago = now - timedelta(seconds=60)
        hour_ago = now - timedelta(seconds=3600)
        
        # 清理過期記錄
        self._cleanup_old_records(minute_ago, hour_ago)
        
        # 1. 檢查全局每分鐘限制
        if len(self.global_timestamps) >= self.max_per_minute:
            self.logger.warning(
                f"全局頻率限制：每分鐘已處理 {len(self.global_timestamps)} 條消息 "
                f"（限制: {self.max_per_minute}）"
            )
            return False, f"系統處理繁忙，請稍後再試（每分鐘限制: {self.max_per_minute}）"
        
        # 2. 檢查全局每小時限制
        if len(self.hourly_timestamps) >= self.max_per_hour:
            self.logger.warning(
                f"全局頻率限制：每小時已處理 {len(self.hourly_timestamps)} 條消息 "
                f"（限制: {self.max_per_hour}）"
            )
            return False, f"系統處理繁忙，請稍後再試（每小時限制: {self.max_per_hour}）"
        
        # 3. 檢查賬號每分鐘限制
        account_timestamps = self.account_timestamps[account_id]
        if len(account_timestamps) >= self.max_per_account_per_minute:
            self.logger.debug(
                f"賬號 {account_id} 頻率限制：每分鐘已處理 {len(account_timestamps)} 條消息 "
                f"（限制: {self.max_per_account_per_minute}）"
            )
            return False, f"賬號處理頻率過高（每分鐘限制: {self.max_per_account_per_minute}）"
        
        # 4. 檢查群組每分鐘限制（如果提供了群組 ID）
        if group_id is not None:
            group_timestamps = self.group_timestamps[group_id]
            if len(group_timestamps) >= self.max_per_group_per_minute:
                self.logger.debug(
                    f"群組 {group_id} 頻率限制：每分鐘已處理 {len(group_timestamps)} 條消息 "
                    f"（限制: {self.max_per_group_per_minute}）"
                )
                return False, f"群組處理頻率過高（每分鐘限制: {self.max_per_group_per_minute}）"
        
        # 所有檢查通過
        return True, None
    
    def record_message(
        self,
        account_id: str,
        group_id: Optional[int] = None
    ):
        """
        記錄已處理的消息
        
        Args:
            account_id: 賬號 ID
            group_id: 群組 ID（可選）
        """
        now = datetime.now()
        
        # 記錄全局計數
        self.global_timestamps.append(now)
        self.hourly_timestamps.append(now)
        
        # 記錄賬號計數
        self.account_timestamps[account_id].append(now)
        
        # 記錄群組計數（如果提供了群組 ID）
        if group_id is not None:
            self.group_timestamps[group_id].append(now)
    
    def _cleanup_old_records(self, minute_ago: datetime, hour_ago: datetime):
        """清理過期的時間戳記錄"""
        # 清理全局每分鐘記錄
        while self.global_timestamps and self.global_timestamps[0] < minute_ago:
            self.global_timestamps.popleft()
        
        # 清理全局每小時記錄
        while self.hourly_timestamps and self.hourly_timestamps[0] < hour_ago:
            self.hourly_timestamps.popleft()
        
        # 清理賬號記錄
        for account_id in list(self.account_timestamps.keys()):
            timestamps = self.account_timestamps[account_id]
            while timestamps and timestamps[0] < minute_ago:
                timestamps.popleft()
            
            # 如果記錄為空，刪除鍵
            if not timestamps:
                del self.account_timestamps[account_id]
        
        # 清理群組記錄
        for group_id in list(self.group_timestamps.keys()):
            timestamps = self.group_timestamps[group_id]
            while timestamps and timestamps[0] < minute_ago:
                timestamps.popleft()
            
            # 如果記錄為空，刪除鍵
            if not timestamps:
                del self.group_timestamps[group_id]
    
    def get_statistics(self) -> Dict[str, Any]:
        """獲取頻率限制統計信息"""
        now = datetime.now()
        minute_ago = now - timedelta(seconds=60)
        hour_ago = now - timedelta(seconds=3600)
        
        self._cleanup_old_records(minute_ago, hour_ago)
        
        return {
            "global_per_minute": {
                "current": len(self.global_timestamps),
                "limit": self.max_per_minute,
                "usage_percent": (len(self.global_timestamps) / self.max_per_minute * 100) if self.max_per_minute > 0 else 0
            },
            "global_per_hour": {
                "current": len(self.hourly_timestamps),
                "limit": self.max_per_hour,
                "usage_percent": (len(self.hourly_timestamps) / self.max_per_hour * 100) if self.max_per_hour > 0 else 0
            },
            "accounts_tracked": len(self.account_timestamps),
            "groups_tracked": len(self.group_timestamps)
        }
