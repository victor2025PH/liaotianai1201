"""
YAMLValidator 單元測試
"""
import sys
from pathlib import Path

# 添加項目根目錄到 Python 路徑
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import pytest
from unittest.mock import Mock
import tempfile
import os
import yaml

from group_ai_service.yaml_validator import YAMLValidator


@pytest.fixture
def yaml_validator():
    """創建 YAMLValidator 實例"""
    return YAMLValidator()


@pytest.fixture
def valid_yaml_content():
    """創建有效的 YAML 內容"""
    return """
script_id: test_script
version: "1.0.0"
description: 測試劇本
scenes:
  - id: scene1
    triggers:
      - type: keyword
        keywords: ["觸發詞1"]
    responses:
      - template: "回復1"
"""


@pytest.fixture
def invalid_yaml_content():
    """創建無效的 YAML 內容"""
    return """
script_id: test_script
version: "1.0.0"
description: 測試劇本
scenes:
  invalid: yaml: content: [
"""


class TestYAMLValidator:
    """YAMLValidator 測試"""
    
    def test_validator_initialization(self, yaml_validator):
        """測試驗證器初始化"""
        assert yaml_validator is not None
    
    def test_validate_and_fix_yaml_content_valid(self, yaml_validator, valid_yaml_content):
        """測試驗證和修復有效的 YAML"""
        fixed_content, warnings = YAMLValidator.validate_and_fix_yaml_content(valid_yaml_content)
        
        # 應該返回修復後的內容和警告列表
        assert isinstance(fixed_content, str)
        assert isinstance(warnings, list)
    
    def test_validate_and_fix_yaml_content_invalid(self, yaml_validator, invalid_yaml_content):
        """測試驗證和修復無效的 YAML"""
        fixed_content, warnings = YAMLValidator.validate_and_fix_yaml_content(invalid_yaml_content)
        
        # 應該返回原始內容和警告列表
        assert isinstance(fixed_content, str)
        assert isinstance(warnings, list)
    
    def test_validate_and_fix_yaml_content_empty(self, yaml_validator):
        """測試驗證和修復空 YAML"""
        fixed_content, warnings = YAMLValidator.validate_and_fix_yaml_content("")
        
        # 應該返回原始內容和警告列表
        assert isinstance(fixed_content, str)
        assert isinstance(warnings, list)
    
    def test_validate_and_fix_yaml_content_none(self, yaml_validator):
        """測試驗證和修復 None"""
        # 應該拋出異常或返回 None
        try:
            fixed_content, warnings = YAMLValidator.validate_and_fix_yaml_content(None)
            # 如果沒有拋出異常，應該返回字符串和警告列表
            assert fixed_content is None or isinstance(fixed_content, str)
            assert isinstance(warnings, list)
        except (TypeError, AttributeError, yaml.YAMLError):
            # 如果拋出異常也是合理的
            pass
    
    def test_validate_and_fix_yaml_file(self, yaml_validator, valid_yaml_content):
        """測試驗證和修復文件"""
        # 創建臨時文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False, encoding='utf-8') as f:
            f.write(valid_yaml_content)
            temp_path = f.name
        
        try:
            fixed_content, warnings = YAMLValidator.validate_and_fix_yaml_file(temp_path)
            assert isinstance(fixed_content, str)
            assert isinstance(warnings, list)
        finally:
            # 清理臨時文件
            if os.path.exists(temp_path):
                os.unlink(temp_path)

