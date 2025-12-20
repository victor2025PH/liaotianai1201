"""
關鍵詞觸發處理器
支持高級關鍵詞匹配和觸發動作
"""
import logging
import re
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

from pyrogram.types import Message

logger = logging.getLogger(__name__)


class MatchType(Enum):
    """匹配類型"""
    SIMPLE = "simple"      # 簡單關鍵詞匹配
    REGEX = "regex"        # 正則表達式匹配
    FUZZY = "fuzzy"        # 模糊匹配
    ALL = "all"           # 必須包含所有關鍵詞（AND）
    ANY = "any"           # 包含任意關鍵詞（OR）
    CONTEXT = "context"   # 上下文匹配


@dataclass
class TriggerCondition:
    """觸發條件"""
    sender_ids: List[int] = field(default_factory=list)  # 發送者 ID 列表（白名單）
    sender_blacklist: List[int] = field(default_factory=list)  # 發送者黑名單
    time_range: Optional[Dict[str, str]] = None  # {"start": "09:00", "end": "18:00"}
    weekdays: List[int] = field(default_factory=list)  # [1,2,3,4,5] 週一到週五
    group_ids: List[int] = field(default_factory=list)  # 特定群組
    message_length_min: Optional[int] = None
    message_length_max: Optional[int] = None
    conditions: List[Dict[str, Any]] = field(default_factory=list)  # 組合條件
    condition_logic: str = "AND"  # AND/OR


@dataclass
class TriggerAction:
    """觸發動作"""
    type: str  # send_message, grab_redpacket, join_group, forward_message等
    params: Dict[str, Any] = field(default_factory=dict)
    delay_min: int = 0  # 秒
    delay_max: int = 0  # 秒


@dataclass
class KeywordTriggerRule:
    """關鍵詞觸發規則"""
    id: str
    name: str
    enabled: bool = True
    keywords: List[str] = field(default_factory=list)
    pattern: Optional[str] = None  # 正則表達式模式
    match_type: MatchType = MatchType.ANY
    case_sensitive: bool = False
    conditions: Optional[TriggerCondition] = None
    actions: List[TriggerAction] = field(default_factory=list)
    priority: int = 0  # 優先級（數字越大優先級越高）
    context_window: int = 0  # 上下文窗口（前後 N 條消息）


class KeywordTriggerProcessor:
    """關鍵詞觸發處理器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.rules: Dict[str, KeywordTriggerRule] = {}  # rule_id -> rule
        self.message_history: Dict[int, List[Message]] = {}  # group_id -> messages
        
        # 從數據庫或配置文件加載規則
        self._load_rules()
        
        self.logger.info(f"KeywordTriggerProcessor 初始化完成，已加載 {len(self.rules)} 個規則")
    
    def _load_rules(self):
        """從數據庫或配置文件加載規則"""
        # 嘗試從數據庫加載規則
        try:
            # 動態導入，避免循環依賴
            import sys
            from pathlib import Path
            
            # 檢查是否在 admin-backend 環境中
            admin_backend_path = Path(__file__).parent.parent.parent / "admin-backend"
            if admin_backend_path.exists() and str(admin_backend_path) not in sys.path:
                sys.path.insert(0, str(admin_backend_path))
            
            try:
                from app.db import SessionLocal
                from app.models.unified_features import KeywordTriggerRule as DBKeywordTriggerRule
                
                db = SessionLocal()
                try:
                    db_rules = db.query(DBKeywordTriggerRule).filter(
                        DBKeywordTriggerRule.enabled == True
                    ).all()
                    
                    for db_rule in db_rules:
                        # 轉換數據庫模型為處理器規則
                        rule = KeywordTriggerRule(
                            id=db_rule.rule_id,
                            name=db_rule.name,
                            enabled=db_rule.enabled,
                            keywords=db_rule.keywords or [],
                            pattern=db_rule.pattern,
                            match_type=MatchType(db_rule.match_type) if db_rule.match_type else MatchType.ANY,
                            case_sensitive=db_rule.case_sensitive,
                            conditions=TriggerCondition(
                                sender_ids=db_rule.sender_ids or [],
                                sender_blacklist=db_rule.sender_blacklist or [],
                                time_range={"start": db_rule.time_range_start, "end": db_rule.time_range_end} if db_rule.time_range_start and db_rule.time_range_end else None,
                                weekdays=db_rule.weekdays or [],
                                group_ids=db_rule.group_ids or [],
                                message_length_min=db_rule.message_length_min,
                                message_length_max=db_rule.message_length_max,
                                condition_logic=db_rule.condition_logic or "AND",
                            ) if (db_rule.sender_ids or db_rule.group_ids or db_rule.time_range_start) else None,
                            actions=[
                                TriggerAction(
                                    type=action.get("type", "send_message"),
                                    params=action.get("params", {}),
                                    delay_min=action.get("delay_min", 0),
                                    delay_max=action.get("delay_max", 0),
                                ) for action in (db_rule.actions or [])
                            ],
                            priority=db_rule.priority,
                            context_window=db_rule.context_window,
                        )
                        self.rules[rule.id] = rule
                    
                    if db_rules:
                        self.logger.info(f"從數據庫加載了 {len(db_rules)} 個關鍵詞觸發規則")
                finally:
                    db.close()
            except ImportError:
                # 數據庫模組不可用（可能在 worker 節點環境）
                self.logger.debug("數據庫模組不可用，跳過從數據庫加載規則")
            except Exception as e:
                self.logger.warning(f"從數據庫加載規則失敗: {e}")
        except Exception as e:
            self.logger.warning(f"加載關鍵詞觸發規則失敗: {e}")
    
    def add_rule(self, rule: KeywordTriggerRule):
        """添加規則"""
        self.rules[rule.id] = rule
        self.logger.info(f"已添加關鍵詞觸發規則: {rule.name} ({rule.id})")
    
    def remove_rule(self, rule_id: str):
        """移除規則"""
        if rule_id in self.rules:
            del self.rules[rule_id]
            self.logger.info(f"已移除關鍵詞觸發規則: {rule_id}")
    
    def update_rule(self, rule: KeywordTriggerRule):
        """更新規則"""
        self.rules[rule.id] = rule
        self.logger.info(f"已更新關鍵詞觸發規則: {rule.name} ({rule.id})")
    
    def match_keywords(
        self,
        message: Message,
        rule: KeywordTriggerRule,
        group_id: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """
        匹配關鍵詞
        
        Returns:
            匹配結果字典，包含匹配的關鍵詞等信息，如果未匹配則返回 None
        """
        text = message.text or ""
        
        if rule.match_type == MatchType.SIMPLE:
            # 簡單匹配
            text_to_match = text if rule.case_sensitive else text.lower()
            for keyword in rule.keywords:
                keyword_to_match = keyword if rule.case_sensitive else keyword.lower()
                if keyword_to_match in text_to_match:
                    return {
                        "matched_keyword": keyword,
                        "match_type": "simple",
                        "matched_text": text
                    }
        
        elif rule.match_type == MatchType.REGEX:
            # 正則表達式匹配
            if rule.pattern:
                flags = 0 if rule.case_sensitive else re.IGNORECASE
                match = re.search(rule.pattern, text, flags)
                if match:
                    return {
                        "matched_keyword": rule.pattern,
                        "match_type": "regex",
                        "matched_text": match.group(0),
                        "groups": match.groups()
                    }
        
        elif rule.match_type == MatchType.ALL:
            # 必須包含所有關鍵詞
            text_to_match = text if rule.case_sensitive else text.lower()
            matched_keywords = []
            for keyword in rule.keywords:
                keyword_to_match = keyword if rule.case_sensitive else keyword.lower()
                if keyword_to_match in text_to_match:
                    matched_keywords.append(keyword)
            
            if len(matched_keywords) == len(rule.keywords):
                return {
                    "matched_keywords": matched_keywords,
                    "match_type": "all",
                    "matched_text": text
                }
        
        elif rule.match_type == MatchType.ANY:
            # 包含任意關鍵詞
            text_to_match = text if rule.case_sensitive else text.lower()
            for keyword in rule.keywords:
                keyword_to_match = keyword if rule.case_sensitive else keyword.lower()
                if keyword_to_match in text_to_match:
                    return {
                        "matched_keyword": keyword,
                        "match_type": "any",
                        "matched_text": text
                    }
        
        elif rule.match_type == MatchType.CONTEXT:
            # 上下文匹配 - 檢查上下文窗口內的消息
            context_window = rule.context_window or 5  # 默認檢查前後 5 條消息
            
            # 獲取當前群組的消息歷史
            chat_id = message.chat.id if message.chat else (group_id if group_id else 0)
            group_history = self.message_history.get(chat_id, [])
            
            if not group_history:
                # 沒有歷史消息，只檢查當前消息
                return self._match_single_message_context(text, rule)
            
            # 找到當前消息在歷史中的位置
            current_index = -1
            for idx, hist_msg in enumerate(group_history):
                if hist_msg.id == message.id:
                    current_index = idx
                    break
            
            if current_index == -1:
                # 當前消息不在歷史中，添加到歷史並只檢查當前消息
                self._add_to_history(message)
                return self._match_single_message_context(text, rule)
            
            # 獲取上下文窗口內的消息（前後各 context_window 條）
            start_idx = max(0, current_index - context_window)
            end_idx = min(len(group_history), current_index + context_window + 1)
            context_messages = group_history[start_idx:end_idx]
            
            # 合併上下文消息文本
            context_texts = []
            for ctx_msg in context_messages:
                if ctx_msg.text:
                    context_texts.append(ctx_msg.text)
            
            combined_text = " ".join(context_texts)
            
            # 在合併的文本中匹配關鍵詞
            text_to_match = combined_text if rule.case_sensitive else combined_text.lower()
            matched_keywords = []
            
            for keyword in rule.keywords:
                keyword_to_match = keyword if rule.case_sensitive else keyword.lower()
                if keyword_to_match in text_to_match:
                    matched_keywords.append(keyword)
            
            if matched_keywords:
                return {
                    "matched_keywords": matched_keywords,
                    "match_type": "context",
                    "matched_text": text,
                    "context_window": context_window,
                    "context_messages_count": len(context_messages)
                }
        
        return None
    
    def _match_single_message_context(self, text: str, rule: KeywordTriggerRule) -> Optional[Dict[str, Any]]:
        """單條消息的上下文匹配（當沒有歷史消息時）"""
        text_to_match = text if rule.case_sensitive else text.lower()
        matched_keywords = []
        
        for keyword in rule.keywords:
            keyword_to_match = keyword if rule.case_sensitive else keyword.lower()
            if keyword_to_match in text_to_match:
                matched_keywords.append(keyword)
        
        if matched_keywords:
            return {
                "matched_keywords": matched_keywords,
                "match_type": "context",
                "matched_text": text,
                "context_window": 0,
                "context_messages_count": 1
            }
        
        return None
    
    def _add_to_history(self, message: Message):
        """將消息添加到歷史記錄"""
        if not message.chat:
            return
        
        group_id = message.chat.id
        if group_id not in self.message_history:
            self.message_history[group_id] = []
        
        # 添加消息到歷史
        self.message_history[group_id].append(message)
        
        # 限制歷史記錄大小（每個群組最多保留 100 條消息）
        max_history = 100
        if len(self.message_history[group_id]) > max_history:
            self.message_history[group_id] = self.message_history[group_id][-max_history:]
    
    def _cleanup_old_history(self, max_age_minutes: int = 60):
        """清理過期的歷史記錄"""
        from datetime import timedelta
        cutoff_time = datetime.now() - timedelta(minutes=max_age_minutes)
        
        for group_id in list(self.message_history.keys()):
            # 過濾掉過舊的消息（超過 max_age_minutes 分鐘）
            self.message_history[group_id] = [
                msg for msg in self.message_history[group_id]
                if msg.date and msg.date > cutoff_time
            ]
            
            # 如果歷史為空，移除該群組的記錄
            if not self.message_history[group_id]:
                del self.message_history[group_id]
    
    def check_conditions(
        self,
        message: Message,
        chat_id: int,
        rule: KeywordTriggerRule
    ) -> bool:
        """檢查觸發條件"""
        if not rule.conditions:
            return True
        
        conditions = rule.conditions
        
        # 檢查發送者
        if message.from_user:
            sender_id = message.from_user.id
            
            # 檢查黑名單
            if sender_id in conditions.sender_blacklist:
                return False
            
            # 檢查白名單
            if conditions.sender_ids and sender_id not in conditions.sender_ids:
                return False
        
        # 檢查時間範圍
        if conditions.time_range:
            current_time = datetime.now().time()
            start_time = datetime.strptime(conditions.time_range["start"], "%H:%M").time()
            end_time = datetime.strptime(conditions.time_range["end"], "%H:%M").time()
            
            if not (start_time <= current_time <= end_time):
                return False
        
        # 檢查星期
        if conditions.weekdays:
            current_weekday = datetime.now().weekday() + 1  # Python 的 weekday() 返回 0-6，我們需要 1-7
            if current_weekday not in conditions.weekdays:
                return False
        
        # 檢查群組
        if conditions.group_ids and chat_id not in conditions.group_ids:
            return False
        
        # 檢查消息長度
        text = message.text or ""
        text_length = len(text)
        if conditions.message_length_min and text_length < conditions.message_length_min:
            return False
        if conditions.message_length_max and text_length > conditions.message_length_max:
            return False
        
        # 檢查組合條件
        if conditions.conditions:
            # TODO: 實現組合條件檢查
            pass
        
        return True
    
    async def process_message(
        self,
        account_id: str,
        group_id: int,
        message: Message
    ) -> Optional[Dict[str, Any]]:
        """
        處理消息，檢查是否觸發關鍵詞規則
        
        Returns:
            觸發結果，包含匹配的規則和動作，如果未觸發則返回 None
        """
        # 將消息添加到歷史記錄（用於上下文匹配）
        self._add_to_history(message)
        
        # 定期清理過期歷史（每處理 10 條消息清理一次）
        if len(self.message_history.get(group_id, [])) % 10 == 0:
            self._cleanup_old_history()
        
        # 按優先級排序規則
        sorted_rules = sorted(
            [rule for rule in self.rules.values() if rule.enabled],
            key=lambda r: r.priority,
            reverse=True
        )
        
        for rule in sorted_rules:
            # 檢查條件
            if not self.check_conditions(message, group_id, rule):
                continue
            
            # 匹配關鍵詞
            match_result = self.match_keywords(message, rule, group_id)
            if match_result:
                # 觸發成功
                matched_keyword = match_result.get('matched_keyword') or match_result.get('matched_keywords', [])
                self.logger.info(
                    f"關鍵詞觸發成功: 規則 {rule.name} ({rule.id}), "
                    f"關鍵詞: {matched_keyword}, "
                    f"群組: {group_id}, "
                    f"匹配類型: {match_result.get('match_type', 'unknown')}"
                )
                
                return {
                    "rule_id": rule.id,
                    "rule_name": rule.name,
                    "match_result": match_result,
                    "actions": rule.actions,
                    "account_id": account_id,
                    "group_id": group_id,
                    "message_id": message.id
                }
        
        return None
    
    def get_rules(self, enabled_only: bool = False) -> List[KeywordTriggerRule]:
        """獲取所有規則"""
        rules = list(self.rules.values())
        if enabled_only:
            rules = [r for r in rules if r.enabled]
        return sorted(rules, key=lambda r: r.priority, reverse=True)
    
    def get_rule(self, rule_id: str) -> Optional[KeywordTriggerRule]:
        """獲取指定規則"""
        return self.rules.get(rule_id)
