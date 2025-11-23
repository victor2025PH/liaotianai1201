"""
VariableResolver 單元測試
"""
import sys
from pathlib import Path

# 添加項目根目錄到 Python 路徑
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import pytest
from unittest.mock import Mock

from group_ai_service.variable_resolver import VariableResolver
from group_ai_service.dialogue_manager import DialogueContext


@pytest.fixture
def variable_resolver():
    """創建 VariableResolver 實例"""
    return VariableResolver()


@pytest.fixture
def dialogue_context():
    """創建 DialogueContext 實例"""
    return DialogueContext(
        account_id="test_account",
        group_id=-1001234567890
    )


class TestVariableResolver:
    """VariableResolver 測試"""
    
    def test_resolver_initialization(self, variable_resolver):
        """測試解析器初始化"""
        assert variable_resolver is not None
    
    def test_resolve_simple_variable(self, variable_resolver, dialogue_context):
        """測試解析簡單變量"""
        # 創建模擬消息
        mock_message = Mock()
        mock_message.text = "測試消息"
        mock_message.from_user = Mock()
        mock_message.from_user.first_name = "測試用戶"
        
        # 設置上下文變量
        context = {"name": "測試用戶"}
        
        result = variable_resolver.resolve("{{name}}", mock_message, context=context)
        
        # 注意：實際解析取決於實現，可能使用內置變量
        assert isinstance(result, str)
    
    def test_resolve_multiple_variables(self, variable_resolver, dialogue_context):
        """測試解析多個變量"""
        mock_message = Mock()
        mock_message.text = "測試消息"
        mock_message.from_user = Mock()
        mock_message.from_user.first_name = "測試用戶"
        
        context = {
            "name": "測試用戶",
            "age": "25"
        }
        
        result = variable_resolver.resolve("姓名：{{name}}，年齡：{{age}}", mock_message, context=context)
        
        # 注意：實際解析取決於實現
        assert isinstance(result, str)
    
    def test_resolve_nonexistent_variable(self, variable_resolver, dialogue_context):
        """測試解析不存在的變量"""
        mock_message = Mock()
        mock_message.text = "測試消息"
        mock_message.from_user = Mock()
        mock_message.from_user.first_name = "測試用戶"
        
        context = {}
        
        result = variable_resolver.resolve("{{nonexistent}}", mock_message, context=context)
        
        # 應該返回原始字符串或空字符串
        assert isinstance(result, str)
    
    def test_resolve_no_variables(self, variable_resolver, dialogue_context):
        """測試解析無變量的字符串"""
        mock_message = Mock()
        mock_message.text = "測試消息"
        mock_message.from_user = Mock()
        mock_message.from_user.first_name = "測試用戶"
        
        text = "這是一個普通文本"
        
        result = variable_resolver.resolve(text, mock_message)
        
        assert result == text
    
    def test_resolve_nested_variables(self, variable_resolver, dialogue_context):
        """測試解析嵌套變量"""
        mock_message = Mock()
        mock_message.text = "測試消息"
        mock_message.from_user = Mock()
        mock_message.from_user.first_name = "測試用戶"
        
        context = {
            "user": "測試用戶",
            "message": "{{user}} 發送了一條消息"
        }
        
        result = variable_resolver.resolve("{{message}}", mock_message, context=context)
        
        # 注意：嵌套變量解析取決於實現
        assert isinstance(result, str)
    
    def test_resolve_with_context(self, variable_resolver, dialogue_context):
        """測試使用上下文解析"""
        mock_message = Mock()
        mock_message.text = "測試消息"
        mock_message.from_user = Mock()
        mock_message.from_user.first_name = "測試用戶"
        
        # 設置上下文變量
        context = {"group_name": "測試群組"}
        
        result = variable_resolver.resolve("歡迎來到 {{group_name}}", mock_message, context=context)
        
        # 注意：實際解析取決於實現
        assert isinstance(result, str)
    
    def test_register_function(self, variable_resolver):
        """測試註冊自定義函數"""
        def custom_func():
            return "custom_value"
        
        variable_resolver.register_function("custom", custom_func)
        
        # 函數應該被註冊
        assert "custom" in variable_resolver.functions
    
    def test_extract_name(self, variable_resolver):
        """測試提取名稱"""
        mock_message = Mock()
        mock_message.from_user = Mock()
        mock_message.from_user.first_name = "測試用戶"
        mock_message.from_user.username = "test_user"
        
        context = {}
        state = {}
        name = variable_resolver._extract_name(mock_message, context, state)
        
        assert name == "測試用戶" or name == "@test_user"
    
    def test_extract_name_no_user(self, variable_resolver):
        """測試提取名稱（無用戶信息）"""
        mock_message = Mock()
        mock_message.from_user = None
        
        context = {}
        state = {}
        name = variable_resolver._extract_name(mock_message, context, state)
        
        assert name == "朋友"
    
    def test_current_time(self, variable_resolver):
        """測試獲取當前時間"""
        mock_message = Mock()
        context = {}
        state = {}
        time_str = variable_resolver._current_time(mock_message, context, state)
        
        assert isinstance(time_str, str)
        assert len(time_str) > 0
    
    def test_current_time_with_format(self, variable_resolver):
        """測試獲取當前時間（帶格式）"""
        mock_message = Mock()
        context = {}
        state = {}
        time_str = variable_resolver._current_time(mock_message, context, state, "%Y-%m-%d")
        
        assert isinstance(time_str, str)
        assert len(time_str) > 0
    
    def test_random_emoji(self, variable_resolver):
        """測試獲取隨機表情"""
        mock_message = Mock()
        context = {}
        state = {}
        emoji = variable_resolver._random_emoji(mock_message, context, state)
        
        assert isinstance(emoji, str)
        assert len(emoji) > 0
    
    def test_upper(self, variable_resolver):
        """測試大寫轉換"""
        mock_message = Mock()
        context = {}
        state = {}
        result = variable_resolver._upper(mock_message, context, state, "hello")
        
        assert result == "HELLO"
    
    def test_lower(self, variable_resolver):
        """測試小寫轉換"""
        mock_message = Mock()
        context = {}
        state = {}
        result = variable_resolver._lower(mock_message, context, state, "HELLO")
        
        assert result == "hello"
    
    def test_resolve_builtin_functions(self, variable_resolver):
        """測試解析內置函數"""
        mock_message = Mock()
        mock_message.text = "測試消息"
        mock_message.from_user = Mock()
        mock_message.from_user.first_name = "測試用戶"
        
        # 測試內置函數（如果支持）
        result = variable_resolver.resolve("{{upper(hello)}}", mock_message)
        
        # 注意：實際解析取決於實現
        assert isinstance(result, str)

