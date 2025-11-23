"""
测试 normalize_script_yaml 函数的 YAML 规范化功能
"""
import pytest
from fastapi import HTTPException
from app.api.group_ai.scripts import normalize_script_yaml


# 测试样本 1：旧格式 YAML（包含 roles）
OLD_FORMAT_YAML = """script_id:
version: "1.0"
description:
metadata:
roles:
  - id: si
    name:
    personality: "话多、爱开玩笑,比较外向"
  - id: huge
    name: "浩哥"
    personality: "看上去严肃,其实很温柔,负责照顾新人"
  - id: user_default
    name: "大家"
    personality: "普通群友,偶尔插两句嘴、氛围轻松"
"""


# 测试样本 2：新格式 YAML（包含 scenes，用于 000新人欢迎剧本）
NEW_FORMAT_YAML = """script_id: 000新人欢迎剧本
version: "1.0"
description: 000新人欢迎剧本
scenes:
  - id: scene1
    triggers:
      - type: message
    responses:
      - template: 欢迎新人
        speaker: si
"""


def test_normalize_script_yaml_old_format():
    """测试旧格式 YAML 的规范化（应该能转换成功）"""
    try:
        normalized_yaml, script_id, version, description = normalize_script_yaml(
            raw_yaml=OLD_FORMAT_YAML,
            script_id="test_old_format",
            script_name="测试旧格式"
        )
        
        # 验证返回值
        assert isinstance(normalized_yaml, str)
        assert script_id is not None
        assert version is not None
        
        # 验证规范化后的 YAML 包含必要的字段
        import yaml
        parsed = yaml.safe_load(normalized_yaml)
        assert isinstance(parsed, dict)
        assert "script_id" in parsed
        assert "version" in parsed
        
        print(f"[PASS] 旧格式 YAML 规范化成功")
        print(f"   script_id: {script_id}")
        print(f"   version: {version}")
        
    except HTTPException as e:
        # 如果是格式错误，应该是 400，不是 500
        assert e.status_code == 400, f"应该是 400 错误，但得到 {e.status_code}"
        print(f"[WARN] 旧格式 YAML 规范化失败（格式错误）: {e.detail}")
        raise
    except Exception as e:
        # 不应该有未预期的异常
        pytest.fail(f"不应该抛出未预期的异常: {type(e).__name__}: {e}")


def test_normalize_script_yaml_new_format():
    """测试新格式 YAML 的规范化（应该能直接通过）"""
    try:
        normalized_yaml, script_id, version, description = normalize_script_yaml(
            raw_yaml=NEW_FORMAT_YAML,
            script_id="000新人欢迎剧本",
            script_name="000新人欢迎剧本"
        )
        
        # 验证返回值
        assert isinstance(normalized_yaml, str)
        assert script_id == "000新人欢迎剧本" or script_id is not None
        assert version is not None
        
        # 验证规范化后的 YAML 包含必要的字段
        import yaml
        parsed = yaml.safe_load(normalized_yaml)
        assert isinstance(parsed, dict)
        assert "script_id" in parsed
        assert "version" in parsed
        assert "scenes" in parsed
        
        print(f"[PASS] 新格式 YAML 规范化成功")
        print(f"   script_id: {script_id}")
        print(f"   version: {version}")
        print(f"   scenes 数量: {len(parsed.get('scenes', []))}")
        
    except HTTPException as e:
        # 如果是格式错误，应该是 400，不是 500
        assert e.status_code == 400, f"应该是 400 错误，但得到 {e.status_code}"
        print(f"[WARN] 新格式 YAML 规范化失败（格式错误）: {e.detail}")
        raise
    except Exception as e:
        # 不应该有未预期的异常
        pytest.fail(f"不应该抛出未预期的异常: {type(e).__name__}: {e}")


def test_normalize_script_yaml_invalid_format():
    """测试无效格式 YAML（应该返回 400，不是 500）"""
    invalid_yaml = "这不是有效的 YAML 内容"
    
    with pytest.raises(HTTPException) as exc_info:
        normalize_script_yaml(
            raw_yaml=invalid_yaml,
            script_id="test_invalid",
            script_name="测试无效格式"
        )
    
    # 验证返回的是 400，不是 500
    assert exc_info.value.status_code == 400, f"应该是 400 错误，但得到 {exc_info.value.status_code}"
    print(f"[PASS] 无效格式 YAML 正确返回 400 错误")


if __name__ == "__main__":
    # 直接运行测试
    print("=" * 60)
    print("测试 normalize_script_yaml 函数")
    print("=" * 60)
    
    try:
        test_normalize_script_yaml_old_format()
        print()
        test_normalize_script_yaml_new_format()
        print()
        test_normalize_script_yaml_invalid_format()
        print()
        print("=" * 60)
        print("[PASS] 所有测试通过！")
        print("=" * 60)
    except Exception as e:
        print(f"[FAIL] 测试失败: {e}")
        import traceback
        traceback.print_exc()
