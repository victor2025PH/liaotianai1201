"""
劇本解析器單元測試
"""
import pytest
import tempfile
from pathlib import Path

from group_ai_service.script_parser import ScriptParser, Script, Scene


@pytest.fixture
def parser():
    """創建解析器實例"""
    return ScriptParser()


@pytest.fixture
def sample_script_yaml():
    """示例劇本 YAML 內容"""
    return """
script_id: test_script
version: 1.0
description: 測試劇本

scenes:
  - id: greeting
    triggers:
      - type: keyword
        keywords: ["你好", "hello"]
    responses:
      - template: "你好！"
    next_scene: conversation

  - id: conversation
    triggers:
      - type: message
        min_length: 5
    responses:
      - template: "{{contextual_reply}}"
        ai_generate: true
    next_scene: conversation

variables:
  user_name: "{{extract_name}}"
"""


def test_load_script(parser, sample_script_yaml):
    """測試加載劇本"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(sample_script_yaml)
        temp_path = f.name
    
    try:
        script = parser.load_script(temp_path)
        
        assert script.script_id == "test_script"
        assert script.version == "1.0"
        assert len(script.scenes) == 2
        assert "greeting" in script.scenes
        assert "conversation" in script.scenes
    finally:
        Path(temp_path).unlink()


def test_parse_scene(parser, sample_script_yaml):
    """測試解析場景"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(sample_script_yaml)
        temp_path = f.name
    
    try:
        script = parser.load_script(temp_path)
        greeting_scene = script.scenes["greeting"]
        
        assert greeting_scene.id == "greeting"
        assert len(greeting_scene.triggers) == 1
        assert greeting_scene.triggers[0].type == "keyword"
        assert "你好" in greeting_scene.triggers[0].keywords
        assert greeting_scene.next_scene == "conversation"
    finally:
        Path(temp_path).unlink()


def test_validate_script(parser, sample_script_yaml):
    """測試劇本驗證"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(sample_script_yaml)
        temp_path = f.name
    
    try:
        script = parser.load_script(temp_path)
        errors = parser.validate_script(script)
        
        assert len(errors) == 0
    finally:
        Path(temp_path).unlink()


def test_validate_script_invalid_reference(parser):
    """測試驗證無效的場景引用"""
    invalid_yaml = """
script_id: invalid_script
version: 1.0
scenes:
  - id: scene1
    next_scene: non_existent_scene
"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(invalid_yaml)
        temp_path = f.name
    
    try:
        script = parser.load_script(temp_path)
        errors = parser.validate_script(script)
        
        assert len(errors) > 0
        assert any("non_existent_scene" in error for error in errors)
    finally:
        Path(temp_path).unlink()

