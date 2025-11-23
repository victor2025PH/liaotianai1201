"""
測試劇本審核與發布流程
"""
import sys
import json
from pathlib import Path

# 添加項目根目錄到路徑
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import requests
import time

API_BASE = "http://localhost:8000/api/v1/group-ai/scripts"

# 測試劇本ID
TEST_SCRIPT_ID = "test_review_script"

def print_section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")

def test_create_script():
    """創建測試劇本"""
    print_section("1. 創建測試劇本")
    
    script_content = """script_id: test_review_script
version: "1.0.0"
name: 測試審核劇本
description: 用於測試審核流程的劇本
scenes:
  scene1:
    triggers:
      - keywords: ["你好", "hello"]
    responses:
      - text: "你好！很高興見到你。"
"""
    
    data = {
        "script_id": TEST_SCRIPT_ID,
        "name": "測試審核劇本",
        "version": "1.0.0",
        "description": "用於測試審核流程的劇本",
        "yaml_content": script_content
    }
    
    response = requests.post(API_BASE + "/", json=data)
    print(f"創建劇本狀態: {response.status_code}")
    if response.status_code == 201:
        result = response.json()
        print(f"劇本ID: {result.get('script_id')}")
        print(f"狀態: {result.get('status', 'N/A')}")
        return True
    else:
        print(f"錯誤: {response.text}")
        return False

def test_list_scripts():
    """列出劇本"""
    print_section("2. 列出所有劇本")
    
    response = requests.get(API_BASE + "/")
    print(f"列表劇本狀態: {response.status_code}")
    if response.status_code == 200:
        scripts = response.json()
        print(f"找到 {len(scripts)} 個劇本")
        for script in scripts:
            if script.get('script_id') == TEST_SCRIPT_ID:
                print(f"  - {script.get('script_id')}: {script.get('name')} (狀態: {script.get('status', 'N/A')})")
        return True
    else:
        print(f"錯誤: {response.text}")
        return False

def test_submit_review():
    """提交審核"""
    print_section("3. 提交審核（草稿 → 審核中）")
    
    data = {
        "change_summary": "首次提交審核"
    }
    
    response = requests.post(f"{API_BASE}/{TEST_SCRIPT_ID}/submit-review", json=data)
    print(f"提交審核狀態: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"劇本ID: {result.get('script_id')}")
        print(f"狀態: {result.get('status')} ({result.get('status_text')})")
        print(f"消息: {result.get('message')}")
        return result.get('status') == 'reviewing'
    else:
        print(f"錯誤: {response.text}")
        return False

def test_review_approve():
    """審核通過"""
    print_section("4. 審核通過（審核中 → 已審核通過）")
    
    data = {
        "decision": "approve",
        "review_comment": "劇本內容良好，可以發布"
    }
    
    response = requests.post(f"{API_BASE}/{TEST_SCRIPT_ID}/review", json=data)
    print(f"審核通過狀態: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"劇本ID: {result.get('script_id')}")
        print(f"狀態: {result.get('status')} ({result.get('status_text')})")
        print(f"審核者: {result.get('reviewed_by')}")
        print(f"審核時間: {result.get('reviewed_at')}")
        return result.get('status') == 'approved'
    else:
        print(f"錯誤: {response.text}")
        return False

def test_publish():
    """發布劇本"""
    print_section("5. 發布劇本（已審核通過 → 已發布）")
    
    data = {
        "change_summary": "正式發布到生產環境"
    }
    
    response = requests.post(f"{API_BASE}/{TEST_SCRIPT_ID}/publish", json=data)
    print(f"發布狀態: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"劇本ID: {result.get('script_id')}")
        print(f"狀態: {result.get('status')} ({result.get('status_text')})")
        print(f"發布時間: {result.get('published_at')}")
        return result.get('status') == 'published'
    else:
        print(f"錯誤: {response.text}")
        return False

def test_disable():
    """停用劇本"""
    print_section("6. 停用劇本（已發布 → 已停用）")
    
    response = requests.post(f"{API_BASE}/{TEST_SCRIPT_ID}/disable")
    print(f"停用狀態: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"劇本ID: {result.get('script_id')}")
        print(f"狀態: {result.get('status')} ({result.get('status_text')})")
        return result.get('status') == 'disabled'
    else:
        print(f"錯誤: {response.text}")
        return False

def test_revert_to_draft():
    """撤回為草稿"""
    print_section("7. 撤回為草稿（已停用 → 草稿）")
    
    response = requests.post(f"{API_BASE}/{TEST_SCRIPT_ID}/revert-to-draft")
    print(f"撤回狀態: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"劇本ID: {result.get('script_id')}")
        print(f"狀態: {result.get('status')} ({result.get('status_text')})")
        return result.get('status') == 'draft'
    else:
        print(f"錯誤: {response.text}")
        return False

def test_review_reject():
    """測試審核拒絕流程"""
    print_section("8. 測試審核拒絕（草稿 → 審核中 → 已拒絕）")
    
    # 先提交審核
    requests.post(f"{API_BASE}/{TEST_SCRIPT_ID}/submit-review", json={"change_summary": "重新提交審核"})
    time.sleep(0.5)
    
    # 審核拒絕
    data = {
        "decision": "reject",
        "review_comment": "需要改進內容"
    }
    
    response = requests.post(f"{API_BASE}/{TEST_SCRIPT_ID}/review", json=data)
    print(f"審核拒絕狀態: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"劇本ID: {result.get('script_id')}")
        print(f"狀態: {result.get('status')} ({result.get('status_text')})")
        return result.get('status') == 'rejected'
    else:
        print(f"錯誤: {response.text}")
        return False

def main():
    """運行所有測試"""
    print("\n" + "="*60)
    print("  劇本審核與發布流程測試")
    print("="*60)
    
    results = []
    
    # 1. 創建劇本
    results.append(("創建劇本", test_create_script()))
    time.sleep(0.5)
    
    # 2. 列出劇本
    results.append(("列出劇本", test_list_scripts()))
    time.sleep(0.5)
    
    # 3. 提交審核
    results.append(("提交審核", test_submit_review()))
    time.sleep(0.5)
    
    # 4. 審核通過
    results.append(("審核通過", test_review_approve()))
    time.sleep(0.5)
    
    # 5. 發布劇本
    results.append(("發布劇本", test_publish()))
    time.sleep(0.5)
    
    # 6. 停用劇本
    results.append(("停用劇本", test_disable()))
    time.sleep(0.5)
    
    # 7. 撤回為草稿
    results.append(("撤回為草稿", test_revert_to_draft()))
    time.sleep(0.5)
    
    # 8. 測試審核拒絕
    results.append(("審核拒絕", test_review_reject()))
    
    # 輸出結果
    print_section("測試結果")
    passed = 0
    failed = 0
    for name, result in results:
        status = "✓ 通過" if result else "✗ 失敗"
        print(f"{name}: {status}")
        if result:
            passed += 1
        else:
            failed += 1
    
    print(f"\n總計: {passed} 通過, {failed} 失敗")
    
    if failed == 0:
        print("\n🎉 所有測試通過！")
    else:
        print(f"\n⚠️  有 {failed} 個測試失敗")
    
    return failed == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

