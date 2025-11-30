"""
回復質量管理器 - 優化回復多樣化和防重複
"""
import logging
import time
from typing import List, Optional, Dict, Any, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import deque

logger = logging.getLogger(__name__)


@dataclass
class ReplyHistory:
    """回復歷史記錄"""
    reply_text: str
    used_at: datetime
    account_id: str
    group_id: int
    template_id: Optional[str] = None  # 使用的模板ID（如果有）


class ReplyQualityManager:
    """回復質量管理器 - 確保回復多樣化和避免重複"""
    
    def __init__(
        self,
        max_history_per_account: int = 50,  # 每個賬號保留的最大歷史記錄數
        duplicate_check_window: int = 300,  # 重複檢查時間窗口（秒）
        similarity_threshold: float = 0.8  # 相似度閾值（0-1）
    ):
        """
        初始化回復質量管理器
        
        Args:
            max_history_per_account: 每個賬號保留的最大歷史記錄數
            duplicate_check_window: 重複檢查時間窗口（秒），在此時間窗口內不會使用相似的回復
            similarity_threshold: 相似度閾值，超過此值視為重複
        """
        self.max_history_per_account = max_history_per_account
        self.duplicate_check_window = duplicate_check_window
        self.similarity_threshold = similarity_threshold
        
        # 回復歷史：account_id -> group_id -> deque[ReplyHistory]
        self.reply_history: Dict[str, Dict[int, deque]] = {}
        
        # 模板使用記錄：account_id -> group_id -> deque[template_id]
        self.template_usage: Dict[str, Dict[int, deque]] = {}
        
        logger.info(
            f"ReplyQualityManager 初始化完成 "
            f"(max_history={max_history_per_account}, "
            f"window={duplicate_check_window}s, "
            f"threshold={similarity_threshold})"
        )
    
    def record_reply(
        self,
        account_id: str,
        group_id: int,
        reply_text: str,
        template_id: Optional[str] = None
    ):
        """
        記錄回復使用歷史
        
        Args:
            account_id: 賬號ID
            group_id: 群組ID
            reply_text: 回復文本
            template_id: 使用的模板ID（可選）
        """
        # 初始化數據結構
        if account_id not in self.reply_history:
            self.reply_history[account_id] = {}
        if group_id not in self.reply_history[account_id]:
            self.reply_history[account_id][group_id] = deque(maxlen=self.max_history_per_account)
        
        if account_id not in self.template_usage:
            self.template_usage[account_id] = {}
        if group_id not in self.template_usage[account_id]:
            self.template_usage[account_id][group_id] = deque(maxlen=self.max_history_per_account)
        
        # 記錄回復
        history_entry = ReplyHistory(
            reply_text=reply_text,
            used_at=datetime.now(),
            account_id=account_id,
            group_id=group_id,
            template_id=template_id
        )
        
        self.reply_history[account_id][group_id].append(history_entry)
        
        # 記錄模板使用
        if template_id:
            self.template_usage[account_id][group_id].append(template_id)
        
        logger.debug(
            f"記錄回復歷史（賬號: {account_id}, 群組: {group_id}, "
            f"模板: {template_id or 'N/A'}）"
        )
    
    def is_duplicate(
        self,
        account_id: str,
        group_id: int,
        reply_text: str,
        check_template: bool = True
    ) -> bool:
        """
        檢查回復是否為重複（在時間窗口內）
        
        Args:
            account_id: 賬號ID
            group_id: 群組ID
            reply_text: 待檢查的回復文本
            check_template: 是否檢查模板重複
        
        Returns:
            如果為重複則返回 True
        """
        now = datetime.now()
        window_start = now - timedelta(seconds=self.duplicate_check_window)
        
        # 檢查是否有歷史記錄
        if account_id not in self.reply_history:
            return False
        if group_id not in self.reply_history[account_id]:
            return False
        
        history = self.reply_history[account_id][group_id]
        
        # 檢查時間窗口內的回復
        for entry in reversed(history):  # 從最近開始檢查
            if entry.used_at < window_start:
                break  # 超出時間窗口，後續的都更早
            
            # 檢查文本相似度
            similarity = self._calculate_similarity(reply_text, entry.reply_text)
            if similarity >= self.similarity_threshold:
                logger.debug(
                    f"檢測到重複回復（相似度: {similarity:.2f}, "
                    f"賬號: {account_id}, 群組: {group_id}）"
                )
                return True
        
        return False
    
    def select_best_response(
        self,
        account_id: str,
        group_id: int,
        responses: List[Any],
        get_template_id: callable = None
    ) -> Optional[Any]:
        """
        從多個回復中選擇最佳回復（避免重複，優先使用未使用的）
        
        Args:
            account_id: 賬號ID
            group_id: 群組ID
            responses: 回復列表（Response 對象或字符串）
            get_template_id: 獲取模板ID的函數（可選）
        
        Returns:
            選中的回復，如果都重複則返回 None
        """
        if not responses:
            return None
        
        # 獲取模板使用歷史
        template_history = None
        if account_id in self.template_usage and group_id in self.template_usage[account_id]:
            template_history = self.template_usage[account_id][group_id]
        
        # 分類回復：未使用、已使用但過期、重複
        unused_responses = []
        expired_responses = []
        
        for response in responses:
            # 獲取回復文本
            reply_text = response.template if hasattr(response, 'template') else str(response)
            
            # 獲取模板ID
            template_id = None
            if get_template_id:
                template_id = get_template_id(response)
            elif hasattr(response, 'id'):
                template_id = response.id
            
            # 檢查是否重複
            if self.is_duplicate(account_id, group_id, reply_text):
                continue  # 跳過重複的回復
            
            # 檢查模板是否最近使用過
            if template_id and template_history and template_id in template_history:
                # 檢查模板使用時間
                used_recently = False
                for entry in reversed(self.reply_history.get(account_id, {}).get(group_id, deque())):
                    if entry.template_id == template_id:
                        time_since_use = (datetime.now() - entry.used_at).total_seconds()
                        if time_since_use < self.duplicate_check_window:
                            used_recently = True
                        break
                
                if used_recently:
                    expired_responses.append(response)
                else:
                    unused_responses.append(response)
            else:
                unused_responses.append(response)
        
        # 優先選擇未使用的回復
        if unused_responses:
            import random
            selected = random.choice(unused_responses)
            logger.debug(
                f"選擇未使用的回復（賬號: {account_id}, 群組: {group_id}, "
                f"未使用: {len(unused_responses)}, 已過期: {len(expired_responses)}）"
            )
            return selected
        
        # 如果沒有未使用的，選擇已過期的（但不在時間窗口內）
        if expired_responses:
            import random
            selected = random.choice(expired_responses)
            logger.debug(
                f"選擇已過期的回復（賬號: {account_id}, 群組: {group_id}）"
            )
            return selected
        
        # 所有回復都重複，返回 None
        logger.warning(
            f"所有回復都重複（賬號: {account_id}, 群組: {group_id}, "
            f"總數: {len(responses)}）"
        )
        return None
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """
        計算兩個文本的相似度（簡單實現，使用編輯距離）
        
        Args:
            text1: 文本1
            text2: 文本2
        
        Returns:
            相似度（0-1），1表示完全相同
        """
        if not text1 or not text2:
            return 0.0
        
        # 簡單的相似度計算：使用集合交集
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        # Jaccard 相似度
        intersection = len(words1 & words2)
        union = len(words1 | words2)
        
        if union == 0:
            return 0.0
        
        similarity = intersection / union
        
        # 如果文本完全相同，返回1.0
        if text1.strip().lower() == text2.strip().lower():
            similarity = 1.0
        
        return similarity
    
    def get_reply_stats(
        self,
        account_id: str,
        group_id: int
    ) -> Dict[str, Any]:
        """
        獲取回復統計信息
        
        Args:
            account_id: 賬號ID
            group_id: 群組ID
        
        Returns:
            統計信息字典
        """
        stats = {
            "total_replies": 0,
            "unique_templates": 0,
            "recent_replies": 0,
            "duplicate_rate": 0.0
        }
        
        if account_id not in self.reply_history:
            return stats
        
        if group_id not in self.reply_history[account_id]:
            return stats
        
        history = self.reply_history[account_id][group_id]
        stats["total_replies"] = len(history)
        
        # 統計唯一模板
        templates = set()
        for entry in history:
            if entry.template_id:
                templates.add(entry.template_id)
        stats["unique_templates"] = len(templates)
        
        # 統計最近回復（最近5分鐘）
        now = datetime.now()
        recent_window = now - timedelta(minutes=5)
        recent_count = sum(1 for entry in history if entry.used_at >= recent_window)
        stats["recent_replies"] = recent_count
        
        # 計算重複率（簡化：檢查最近10條是否有重複）
        if len(history) >= 2:
            recent_entries = list(history)[-10:]
            duplicates = 0
            for i, entry1 in enumerate(recent_entries):
                for entry2 in recent_entries[i+1:]:
                    similarity = self._calculate_similarity(entry1.reply_text, entry2.reply_text)
                    if similarity >= self.similarity_threshold:
                        duplicates += 1
                        break
            
            if len(recent_entries) > 0:
                stats["duplicate_rate"] = duplicates / len(recent_entries)
        
        return stats
    
    def clear_history(self, account_id: Optional[str] = None, group_id: Optional[int] = None):
        """
        清理歷史記錄
        
        Args:
            account_id: 賬號ID（如果為None，清理所有）
            group_id: 群組ID（如果為None，清理賬號的所有群組）
        """
        if account_id is None:
            self.reply_history.clear()
            self.template_usage.clear()
            logger.info("已清理所有回復歷史")
        elif group_id is None:
            if account_id in self.reply_history:
                del self.reply_history[account_id]
            if account_id in self.template_usage:
                del self.template_usage[account_id]
            logger.info(f"已清理賬號 {account_id} 的所有回復歷史")
        else:
            if account_id in self.reply_history and group_id in self.reply_history[account_id]:
                del self.reply_history[account_id][group_id]
            if account_id in self.template_usage and group_id in self.template_usage[account_id]:
                del self.template_usage[account_id][group_id]
            logger.info(f"已清理賬號 {account_id} 群組 {group_id} 的回復歷史")
