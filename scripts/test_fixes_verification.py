"""
验证所有修复的测试脚本

测试内容：
1. 路由修复：scan-sessions 和 upload-session 端点
2. 剧本创建和测试功能
3. 错误消息处理
4. Session文件管理

使用方法：
    python scripts/test_fixes_verification.py
"""

import sys
import os
import asyncio
import requests
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 配置
BASE_URL = "http://localhost:8000/api/v1"
ACCOUNTS_URL = f"{BASE_URL}/group-ai/accounts"
SCRIPTS_URL = f"{BASE_URL}/group-ai/scripts"


def print_header(title: str):
    """打印测试标题"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def print_result(test_name: str, success: bool, message: str = ""):
    """打印测试结果"""
    status = "[PASS]" if success else "[FAIL]"
    print(f"  {status}: {test_name}")
    if message:
        print(f"    {message}")


def test_scan_sessions():
    """测试扫描Session文件端点"""
    print_header("测试1: 扫描Session文件端点")
    
    try:
        response = requests.get(f"{ACCOUNTS_URL}/scan-sessions", timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            print_result("扫描Session文件", True, f"找到 {data.get('count', 0)} 个文件")
            return True
        else:
            print_result("扫描Session文件", False, f"HTTP {response.status_code}: {response.text}")
            return False
    except requests.exceptions.ConnectionError:
        print_result("扫描Session文件", False, "无法连接到后端服务，请确保后端已启动")
        return False
    except Exception as e:
        print_result("扫描Session文件", False, f"错误: {str(e)}")
        return False


def test_upload_session():
    """测试上传Session文件端点"""
    print_header("测试2: 上传Session文件端点")
    
    # 检查是否有测试session文件
    sessions_dir = project_root / "sessions"
    test_files = list(sessions_dir.glob("*.session")) if sessions_dir.exists() else []
    
    if not test_files:
        print_result("上传Session文件", False, "没有找到测试session文件")
        return False
    
    test_file = test_files[0]
    
    try:
        with open(test_file, 'rb') as f:
            files = {'file': (test_file.name, f, 'application/octet-stream')}
            response = requests.post(f"{ACCOUNTS_URL}/upload-session", files=files, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print_result("上传Session文件", True, f"文件已上传: {data.get('filename', 'N/A')}")
            return True
        else:
            print_result("上传Session文件", False, f"HTTP {response.status_code}: {response.text}")
            return False
    except Exception as e:
        print_result("上传Session文件", False, f"错误: {str(e)}")
        return False


def test_create_script():
    """测试创建剧本功能"""
    print_header("测试3: 创建剧本功能")
    
    # 测试YAML内容（包含自动修复的场景）
    test_yaml = """
script_id: test_script_001
version: "1.0"
description: "测试剧本"
scenes:
  - id: scene_1
    triggers:
      - type: message
        keywords: ["测试"]
    responses:
      - template: "这是一个测试回复"
"""
    
    try:
        response = requests.post(
            f"{SCRIPTS_URL}/",
            json={
                "script_id": "test_script_001",
                "name": "测试剧本",
                "version": "1.0",
                "description": "测试剧本",
                "yaml_content": test_yaml
            },
            timeout=10
        )
        
        if response.status_code == 201:
            data = response.json()
            print_result("创建剧本", True, f"剧本ID: {data.get('script_id', 'N/A')}")
            return True, data.get('script_id')
        else:
            print_result("创建剧本", False, f"HTTP {response.status_code}: {response.text}")
            return False, None
    except Exception as e:
        print_result("创建剧本", False, f"错误: {str(e)}")
        return False, None


def test_script_with_missing_triggers():
    """测试缺少triggers的剧本（应该自动修复）"""
    print_header("测试4: 自动修复缺少triggers的剧本")
    
    # 测试YAML内容（缺少triggers）
    test_yaml = """
script_id: test_script_002
version: "1.0"
description: "测试自动修复"
scenes:
  - id: scene_1
    responses:
      - template: "这是一个测试回复"
"""
    
    try:
        response = requests.post(
            f"{SCRIPTS_URL}/",
            json={
                "script_id": "test_script_002",
                "name": "测试自动修复剧本",
                "version": "1.0",
                "description": "测试自动修复",
                "yaml_content": test_yaml
            },
            timeout=10
        )
        
        if response.status_code == 201:
            print_result("自动修复缺少triggers", True, "系统自动添加了默认trigger")
            return True
        else:
            print_result("自动修复缺少triggers", False, f"HTTP {response.status_code}: {response.text}")
            return False
    except Exception as e:
        print_result("自动修复缺少triggers", False, f"错误: {str(e)}")
        return False


def test_script_test_endpoint(script_id: str):
    """测试剧本测试端点"""
    print_header("测试5: 剧本测试端点")
    
    try:
        response = requests.post(
            f"{SCRIPTS_URL}/{script_id}/test",
            json={
                "message_text": "测试消息"
            },
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            reply = data.get('reply', 'N/A')
            print_result("测试剧本", True, f"回复: {reply}")
            return True
        else:
            error_detail = response.json().get('detail', response.text) if response.headers.get('content-type', '').startswith('application/json') else response.text
            print_result("测试剧本", False, f"HTTP {response.status_code}: {error_detail}")
            return False
    except Exception as e:
        print_result("测试剧本", False, f"错误: {str(e)}")
        return False


def test_list_scripts():
    """测试列出剧本"""
    print_header("测试6: 列出剧本")
    
    try:
        response = requests.get(f"{SCRIPTS_URL}/", timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            scripts = data if isinstance(data, list) else data.get('items', [])
            print_result("列出剧本", True, f"找到 {len(scripts)} 个剧本")
            return True
        else:
            print_result("列出剧本", False, f"HTTP {response.status_code}: {response.text}")
            return False
    except Exception as e:
        print_result("列出剧本", False, f"错误: {str(e)}")
        return False


def test_list_accounts():
    """测试列出账号"""
    print_header("测试7: 列出账号")
    
    try:
        response = requests.get(f"{ACCOUNTS_URL}/", timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            accounts = data.get('items', []) if isinstance(data, dict) else data
            print_result("列出账号", True, f"找到 {len(accounts)} 个账号")
            return True
        else:
            print_result("列出账号", False, f"HTTP {response.status_code}: {response.text}")
            return False
    except Exception as e:
        print_result("列出账号", False, f"错误: {str(e)}")
        return False


def cleanup_test_scripts():
    """清理测试剧本"""
    print_header("清理测试数据")
    
    test_script_ids = ["test_script_001", "test_script_002"]
    
    for script_id in test_script_ids:
        try:
            response = requests.delete(f"{SCRIPTS_URL}/{script_id}", timeout=5)
            if response.status_code in [200, 204, 404]:
                print(f"  已删除测试剧本: {script_id}")
        except Exception as e:
            print(f"  删除测试剧本 {script_id} 失败: {str(e)}")


def main():
    """主测试函数"""
    print("\n" + "=" * 60)
    print("  修复验证测试套件")
    print("=" * 60)
    print("\n请确保后端服务已启动 (http://localhost:8000)")
    print("等待3秒后自动开始测试...")
    import time
    time.sleep(3)
    
    results = []
    
    # 测试路由修复
    results.append(("扫描Session文件", test_scan_sessions()))
    results.append(("上传Session文件", test_upload_session()))
    
    # 测试剧本功能
    results.append(("列出剧本", test_list_scripts()))
    success, script_id = test_create_script()
    results.append(("创建剧本", success))
    
    if script_id:
        results.append(("测试剧本", test_script_test_endpoint(script_id)))
    
    results.append(("自动修复功能", test_script_with_missing_triggers()))
    
    # 测试账号功能
    results.append(("列出账号", test_list_accounts()))
    
    # 清理测试数据
    cleanup_test_scripts()
    
    # 打印总结
    print_header("测试总结")
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "[OK]" if success else "[X]"
        print(f"  {status} {test_name}")
    
    print(f"\n  总计: {passed}/{total} 测试通过")
    
    if passed == total:
        print("\n  [SUCCESS] 所有测试通过！修复验证成功。")
    else:
        print(f"\n  [WARNING] {total - passed} 个测试失败，请检查后端服务状态。")
    
    return passed == total


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n测试已取消")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n测试过程中发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


