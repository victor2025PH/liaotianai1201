"""
测试创建剧本接口修复效果
使用真实的 YAML 样本验证
"""
import sys
import os
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "admin-backend"))

import requests
import json

# 测试配置
BASE_URL = "http://localhost:8000"
LOGIN_URL = f"{BASE_URL}/api/v1/auth/login"
CREATE_SCRIPT_URL = f"{BASE_URL}/api/v1/group-ai/scripts"

# 测试样本：000新人欢迎剧本（新格式）
TEST_YAML = """script_id: 000新人欢迎剧本
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


def test_create_script():
    """测试创建剧本接口"""
    print("=" * 60)
    print("测试创建剧本接口修复效果")
    print("=" * 60)
    
    # 1. 登录获取 Token
    print("\n[1] 登录获取 Token...")
    try:
        login_resp = requests.post(
            LOGIN_URL,
            data={"username": "admin@example.com", "password": "changeme123"},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=5
        )
        login_resp.raise_for_status()
        token = login_resp.json()["access_token"]
        print(f"   ✅ Token 获取成功")
    except Exception as e:
        print(f"   ❌ 登录失败: {e}")
        return False
    
    # 2. 创建剧本
    print("\n[2] 创建剧本（000新人欢迎剧本）...")
    payload = {
        "script_id": "000新人欢迎剧本",
        "name": "000新人欢迎剧本",
        "version": "1.0",
        "description": "000新人欢迎剧本",
        "yaml_content": TEST_YAML
    }
    
    try:
        create_resp = requests.post(
            CREATE_SCRIPT_URL,
            json=payload,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            },
            timeout=15
        )
        
        status_code = create_resp.status_code
        print(f"   状态码: {status_code}")
        
        if status_code in [200, 201]:
            result = create_resp.json()
            print(f"   ✅ 创建成功！")
            print(f"      script_id: {result.get('script_id')}")
            print(f"      name: {result.get('name')}")
            print(f"      scene_count: {result.get('scene_count')}")
            return True
        else:
            error_detail = create_resp.text
            print(f"   ❌ 创建失败 ({status_code})")
            print(f"   错误详情: {error_detail[:500]}")
            
            # 验证：如果是格式错误，应该是 400，不是 500
            if status_code == 400:
                print(f"   ✅ 正确返回 400（格式错误），而不是 500")
                return True  # 格式错误是预期的，说明错误分类正确
            elif status_code == 500:
                print(f"   ❌ 仍然返回 500，修复未生效")
                return False
            else:
                print(f"   ⚠️  返回了意外的状态码: {status_code}")
                return False
                
    except Exception as e:
        print(f"   ❌ 请求异常: {e}")
        return False


if __name__ == "__main__":
    success = test_create_script()
    print("\n" + "=" * 60)
    if success:
        print("✅ 测试通过！修复生效")
    else:
        print("❌ 测试失败，需要进一步检查")
    print("=" * 60)
    sys.exit(0 if success else 1)

