"""
ScriptParser 單元測試
"""
import sys
from pathlib import Path

# 添加項目根目錄到 Python 路徑
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import pytest
from unittest.mock import Mock, patch, mock_open
import tempfile
import os

from group_ai_service.script_parser import ScriptParser, Script, Scene, Trigger, Response


@pytest.fixture
def script_parser():
    """創建 ScriptParser 實例"""
    return ScriptParser()


@pytest.fixture
def sample_script_yaml():
    """創建示例劇本 YAML 內容"""
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
  - id: scene2
    triggers:
      - type: keyword
        keywords: ["觸發詞2"]
    responses:
      - template: "回復2"
"""


class TestScriptParser:
    """ScriptParser 測試"""
    
    def test_parser_initialization(self, script_parser):
        """測試解析器初始化"""
        assert script_parser is not None
        assert hasattr(script_parser, 'scripts')
        assert isinstance(script_parser.scripts, dict)
    
    def test_load_script_file_not_found(self, script_parser):
        """測試加載不存在的劇本文件"""
        with pytest.raises(FileNotFoundError):
            script_parser.load_script("nonexistent_script.yaml")
    
    def test_load_script_from_file(self, script_parser, sample_script_yaml):
        """測試從文件加載劇本"""
        # 創建臨時文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False, encoding='utf-8') as f:
            f.write(sample_script_yaml)
            temp_path = f.name
        
        try:
            script = script_parser.load_script(temp_path)
            
            assert script is not None
            assert script.script_id == "test_script"
            assert script.version == "1.0.0"
            assert "scene1" in script.scenes
            assert "scene2" in script.scenes
        finally:
            # 清理臨時文件
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    def test_load_script_invalid_yaml(self, script_parser):
        """測試加載無效的 YAML"""
        # 創建包含無效 YAML 的臨時文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False, encoding='utf-8') as f:
            f.write("invalid: yaml: content: [")
            temp_path = f.name
        
        try:
            # 應該拋出異常或返回 None
            with pytest.raises(Exception):
                script_parser.load_script(temp_path)
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    def test_validate_script_structure(self, script_parser):
        """測試驗證劇本結構"""
        # 創建一個有效的劇本
        script = Script(
            script_id="test",
            version="1.0.0",
            scenes={
                "scene1": Scene(
                    id="scene1",
                    triggers=[Trigger(type="keyword", keywords=["test"])],
                    responses=[Response(template="reply")]
                )
            }
        )
        
        # 應該不會報錯
        assert script is not None
        assert script.script_id == "test"

