"""
條件表達式評估器
用於評估定時消息的條件觸發表達式
"""
import logging
import re
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class ConditionEvaluator:
    """條件表達式評估器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        # 支持的運算符
        self.operators = {
            '==': lambda a, b: a == b,
            '!=': lambda a, b: a != b,
            '>': lambda a, b: a > b,
            '>=': lambda a, b: a >= b,
            '<': lambda a, b: a < b,
            '<=': lambda a, b: a <= b,
            'in': lambda a, b: a in b,
            'not in': lambda a, b: a not in b,
            'contains': lambda a, b: b in a if isinstance(a, str) else False,
        }
    
    def evaluate(
        self,
        condition: str,
        context: Dict[str, Any]
    ) -> bool:
        """
        評估條件表達式
        
        支持的格式:
        - "group_activity < 5"
        - "message_count > 10"
        - "is_weekend == true"
        - "hour in [9, 10, 11, 14, 15, 16]"
        
        Args:
            condition: 條件表達式字符串
            context: 上下文變量字典
            
        Returns:
            評估結果（True/False）
        """
        if not condition or not condition.strip():
            return False
        
        try:
            # 清理條件字符串
            condition = condition.strip()
            
            # 解析條件表達式
            # 支持格式: "variable operator value"
            # 例如: "group_activity < 5"
            
            # 嘗試匹配各種運算符
            for op in ['>=', '<=', '!=', '==', 'not in', 'in', '>', '<', 'contains']:
                if op in condition:
                    parts = condition.split(op, 1)
                    if len(parts) == 2:
                        var_name = parts[0].strip()
                        value_str = parts[1].strip()
                        
                        # 獲取變量值
                        var_value = self._get_variable_value(var_name, context)
                        
                        # 解析右側值
                        right_value = self._parse_value(value_str, context)
                        
                        # 執行比較
                        if op in self.operators:
                            result = self.operators[op](var_value, right_value)
                            self.logger.debug(
                                f"條件評估: {condition} -> "
                                f"{var_name}({var_value}) {op} {right_value} = {result}"
                            )
                            return result
            
            # 如果沒有匹配到運算符，嘗試作為布爾表達式
            # 例如: "is_weekend" 表示 is_weekend == True
            var_value = self._get_variable_value(condition, context)
            if isinstance(var_value, bool):
                return var_value
            
            # 如果變量存在且非空，視為 True
            return var_value is not None and var_value != ""
            
        except Exception as e:
            self.logger.error(f"評估條件表達式失敗: {condition}, 錯誤: {e}", exc_info=True)
            return False
    
    def _get_variable_value(self, var_name: str, context: Dict[str, Any]) -> Any:
        """
        從上下文中獲取變量值
        
        支持嵌套變量，例如: "group.metrics.activity"
        """
        try:
            # 支持嵌套變量（使用點號分隔）
            parts = var_name.split('.')
            value = context
            
            for part in parts:
                if isinstance(value, dict):
                    value = value.get(part)
                elif hasattr(value, part):
                    value = getattr(value, part)
                else:
                    return None
            
            return value
        except Exception as e:
            self.logger.debug(f"獲取變量值失敗: {var_name}, 錯誤: {e}")
            return None
    
    def _parse_value(self, value_str: str, context: Dict[str, Any]) -> Any:
        """
        解析值字符串
        
        支持:
        - 數字: "5", "10.5"
        - 布爾值: "true", "false"
        - 字符串: "hello"
        - 列表: "[1, 2, 3]"
        - 變量引用: "${variable_name}"
        """
        value_str = value_str.strip()
        
        # 處理變量引用 ${variable_name}
        if value_str.startswith('${') and value_str.endswith('}'):
            var_name = value_str[2:-1]
            return self._get_variable_value(var_name, context)
        
        # 處理列表 [1, 2, 3]
        if value_str.startswith('[') and value_str.endswith(']'):
            list_str = value_str[1:-1]
            items = [item.strip() for item in list_str.split(',')]
            return [self._parse_value(item, context) for item in items]
        
        # 處理布爾值
        if value_str.lower() == 'true':
            return True
        if value_str.lower() == 'false':
            return False
        
        # 處理數字
        try:
            if '.' in value_str:
                return float(value_str)
            else:
                return int(value_str)
        except ValueError:
            pass
        
        # 處理字符串（移除引號）
        if (value_str.startswith('"') and value_str.endswith('"')) or \
           (value_str.startswith("'") and value_str.endswith("'")):
            return value_str[1:-1]
        
        # 默認返回字符串
        return value_str
    
    def validate_condition(self, condition: str) -> tuple[bool, Optional[str]]:
        """
        驗證條件表達式是否有效
        
        Returns:
            (是否有效, 錯誤消息)
        """
        if not condition or not condition.strip():
            return False, "條件表達式為空"
        
        try:
            # 簡單驗證：檢查是否包含運算符
            has_operator = any(op in condition for op in self.operators.keys())
            
            if not has_operator:
                # 可能是簡單的變量名，這是允許的
                return True, None
            
            # 嘗試解析（不執行）
            # 這裡可以添加更複雜的語法檢查
            return True, None
            
        except Exception as e:
            return False, f"條件表達式無效: {e}"
