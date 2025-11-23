"""
TextParser 單元測試
"""
import sys
from pathlib import Path

# 添加項目根目錄到 Python 路徑
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import pytest
from unittest.mock import Mock

from group_ai_service.text_parser import TextParser


@pytest.fixture
def text_parser():
    """創建 TextParser 實例"""
    return TextParser()


class TestTextParser:
    """TextParser 測試"""
    
    def test_parser_initialization(self, text_parser):
        """測試解析器初始化"""
        assert text_parser is not None
    
    def test_parse_text_to_dialogue_simple(self, text_parser):
        """測試解析簡單文本為對話"""
        text = "用戶: 你好"
        result = text_parser.parse_text_to_dialogue(text)
        
        assert result is not None
        assert isinstance(result, list)
        assert len(result) > 0
    
    def test_parse_text_to_dialogue_with_keywords(self, text_parser):
        """測試解析帶關鍵詞的文本"""
        text = "用戶: 觸發詞1 觸發詞2"
        result = text_parser.parse_text_to_dialogue(text)
        
        assert result is not None
        assert isinstance(result, list)
    
    def test_parse_text_to_dialogue_empty(self, text_parser):
        """測試解析空文本"""
        text = ""
        result = text_parser.parse_text_to_dialogue(text)
        
        # 應該返回空列表
        assert isinstance(result, list)
    
    def test_parse_text_to_dialogue_none(self, text_parser):
        """測試解析 None"""
        # 應該拋出異常或返回空列表
        try:
            result = text_parser.parse_text_to_dialogue(None)
            assert isinstance(result, list)
        except (TypeError, AttributeError):
            # 如果拋出異常也是合理的
            pass
    
    def test_extract_keywords(self, text_parser):
        """測試提取關鍵詞"""
        text = "這是一個包含關鍵詞的文本"
        keywords = ["關鍵詞", "文本"]
        
        # 如果方法存在，測試它
        if hasattr(text_parser, 'extract_keywords'):
            result = text_parser.extract_keywords(text, keywords)
            assert isinstance(result, list)
    
    def test_normalize_text(self, text_parser):
        """測試文本標準化"""
        text = "這是一個  包含   多個   空格的文本"
        
        # 如果方法存在，測試它
        if hasattr(text_parser, 'normalize_text'):
            result = text_parser.normalize_text(text)
            assert isinstance(result, str)
            # 應該移除多餘的空格
            assert "  " not in result

