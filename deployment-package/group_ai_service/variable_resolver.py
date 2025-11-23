"""
變量解析器 - 解析和替換劇本模板中的變量
"""
import re
import logging
from typing import Dict, Any, Optional, Callable
from datetime import datetime

from pyrogram.types import Message, User

logger = logging.getLogger(__name__)


class VariableResolver:
    """變量解析器"""
    
    def __init__(self):
        self.functions: Dict[str, Callable] = {}
        self._register_builtin_functions()
    
    def _register_builtin_functions(self):
        """註冊內置函數"""
        self.functions["extract_name"] = self._extract_name
        self.functions["detect_topic"] = self._detect_topic
        self.functions["current_time"] = self._current_time
        self.functions["random_emoji"] = self._random_emoji
        self.functions["upper"] = self._upper
        self.functions["lower"] = self._lower
    
    def resolve(
        self,
        template: str,
        message: Message,
        context: Optional[Dict[str, Any]] = None,
        state: Optional[Dict[str, Any]] = None
    ) -> str:
        """解析模板中的變量"""
        if not template:
            return template
        
        context = context or {}
        state = state or {}
        
        # 匹配 {{function_name}} 或 {{variable_name}}
        pattern = r'\{\{([^}]+)\}\}'
        
        def replace_var(match):
            var_expr = match.group(1).strip()
            return self._resolve_variable(var_expr, message, context, state)
        
        result = re.sub(pattern, replace_var, template)
        return result
    
    def _resolve_variable(
        self,
        var_expr: str,
        message: Message,
        context: Dict[str, Any],
        state: Dict[str, Any]
    ) -> str:
        """解析單個變量表達式"""
        # 支持函數調用: function_name(arg1, arg2)
        if '(' in var_expr:
            func_name, args_str = var_expr.split('(', 1)
            func_name = func_name.strip()
            args_str = args_str.rstrip(')').strip()
            
            # 解析參數（簡單實現，支持字符串參數）
            args = []
            if args_str:
                # 簡單分割（不支持嵌套引號）
                for arg in args_str.split(','):
                    arg = arg.strip().strip('"').strip("'")
                    args.append(arg)
            
            if func_name in self.functions:
                try:
                    result = self.functions[func_name](message, context, state, *args)
                    return str(result) if result is not None else ""
                except Exception as e:
                    logger.error(f"執行函數 {func_name} 失敗: {e}")
                    return ""
            else:
                logger.warning(f"未知函數: {func_name}")
                return ""
        
        # 普通變量
        # 1. 從 context 中查找
        if var_expr in context:
            return str(context[var_expr])
        
        # 2. 從 state 中查找
        if var_expr in state:
            return str(state[var_expr])
        
        # 3. 內置變量
        builtin_vars = {
            "user_name": self._extract_name(message, context, state),
            "user_id": str(message.from_user.id) if message.from_user else "",
            "chat_id": str(message.chat.id) if message.chat else "",
            "message_text": message.text or "",
            "message_length": str(len(message.text or "")),
        }
        
        if var_expr in builtin_vars:
            return builtin_vars[var_expr]
        
        # 未找到，返回原表達式
        logger.debug(f"未找到變量: {var_expr}")
        return f"{{{{{var_expr}}}}}"
    
    def register_function(self, name: str, func: Callable):
        """註冊自定義函數"""
        self.functions[name] = func
        logger.info(f"註冊自定義函數: {name}")
    
    # 內置函數實現
    
    def _extract_name(
        self,
        message: Message,
        context: Dict[str, Any],
        state: Dict[str, Any],
        *args
    ) -> str:
        """提取用戶名稱"""
        if message.from_user:
            if message.from_user.first_name:
                return message.from_user.first_name
            if message.from_user.username:
                return f"@{message.from_user.username}"
        return "朋友"
    
    def _detect_topic(
        self,
        message: Message,
        context: Dict[str, Any],
        state: Dict[str, Any],
        *args
    ) -> str:
        """檢測話題（簡單實現）"""
        text = (message.text or "").lower()
        
        # 簡單關鍵詞匹配
        topics = {
            "天氣": ["天氣", "下雨", "晴天", "溫度"],
            "工作": ["工作", "上班", "項目", "任務"],
            "娛樂": ["電影", "遊戲", "音樂", "娛樂"],
            "生活": ["吃飯", "睡覺", "購物", "生活"],
        }
        
        for topic, keywords in topics.items():
            if any(keyword in text for keyword in keywords):
                return topic
        
        return "日常"
    
    def _current_time(
        self,
        message: Message,
        context: Dict[str, Any],
        state: Dict[str, Any],
        *args
    ) -> str:
        """獲取當前時間"""
        format_str = args[0] if args else "%H:%M"
        return datetime.now().strftime(format_str)
    
    def _random_emoji(
        self,
        message: Message,
        context: Dict[str, Any],
        state: Dict[str, Any],
        *args
    ) -> str:
        """隨機表情"""
        import random
        emojis = ["😊", "😄", "😃", "😁", "😆", "😅", "😂", "🤣", "😊", "😉"]
        return random.choice(emojis)
    
    def _upper(
        self,
        message: Message,
        context: Dict[str, Any],
        state: Dict[str, Any],
        *args
    ) -> str:
        """轉大寫"""
        text = args[0] if args else ""
        return text.upper()
    
    def _lower(
        self,
        message: Message,
        context: Dict[str, Any],
        state: Dict[str, Any],
        *args
    ) -> str:
        """轉小寫"""
        text = args[0] if args else ""
        return text.lower()

