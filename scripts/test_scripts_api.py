"""
劇本管理 API 測試腳本
"""
import asyncio
import sys
import io
import json
from pathlib import Path

# 設置 UTF-8 編碼（Windows 兼容）
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 添加項目根目錄到 Python 路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import requests

API_BASE = "http://localhost:8000/api/v1/group-ai/scripts"


def test_create_script():
    """測試創建劇本"""
    print("="*60)
    print("測試 1: 創建劇本")
    print("="*60)
    
    yaml_content = """
script_id: test_script_api
version: 1.0
description: API 測試劇本

scenes:
  - id: greeting
    triggers:
      - type: keyword
        keywords: ["你好", "hello"]
    responses:
      - template: "你好！很高興認識你"
    next_scene: conversation

  - id: conversation
    triggers:
      - type: message
        min_length: 5
    responses:
      - template: "{{contextual_reply}}"
        ai_generate: true
    next_scene: conversation
"""
    
    data = {
        "script_id": "test_script_api",
        "name": "API 測試劇本",
        "version": "1.0",
        "description": "用於測試 API 的劇本",
        "yaml_content": yaml_content
    }
    
    try:
        response = requests.post(API_BASE + "/", json=data)
        print(f"狀態碼: {response.status_code}")
        if response.status_code == 201:
            result = response.json()
            print(f"[OK] 劇本創建成功")
            print(f"  Script ID: {result.get('script_id')}")
            print(f"  場景數: {result.get('scene_count')}")
            return result.get('script_id')
        else:
            print(f"[FAIL] 創建失敗: {response.text}")
            return None
    except Exception as e:
        print(f"[FAIL] 請求失敗: {e}")
        return None


def test_list_scripts():
    """測試列出劇本"""
    print("\n" + "="*60)
    print("測試 2: 列出劇本")
    print("="*60)
    
    try:
        response = requests.get(API_BASE + "/")
        print(f"狀態碼: {response.status_code}")
        if response.status_code == 200:
            scripts = response.json()
            print(f"[OK] 找到 {len(scripts)} 個劇本")
            for script in scripts:
                print(f"  - {script.get('script_id')}: {script.get('name')} (v{script.get('version')})")
            return scripts
        else:
            print(f"[FAIL] 列出失敗: {response.text}")
            return []
    except Exception as e:
        print(f"[FAIL] 請求失敗: {e}")
        return []


def test_get_script(script_id: str):
    """測試獲取劇本詳情"""
    print("\n" + "="*60)
    print("測試 3: 獲取劇本詳情")
    print("="*60)
    
    try:
        response = requests.get(f"{API_BASE}/{script_id}")
        print(f"狀態碼: {response.status_code}")
        if response.status_code == 200:
            script = response.json()
            print(f"[OK] 劇本詳情獲取成功")
            print(f"  Script ID: {script.get('script_id')}")
            print(f"  名稱: {script.get('name')}")
            print(f"  版本: {script.get('version')}")
            print(f"  場景數: {script.get('scene_count')}")
            print(f"  場景列表:")
            for scene in script.get('scenes', []):
                print(f"    - {scene.get('id')} (觸發: {scene.get('triggers_count')}, 回復: {scene.get('responses_count')})")
            return script
        else:
            print(f"[FAIL] 獲取失敗: {response.text}")
            return None
    except Exception as e:
        print(f"[FAIL] 請求失敗: {e}")
        return None


def test_test_script(script_id: str):
    """測試劇本測試接口"""
    print("\n" + "="*60)
    print("測試 4: 測試劇本")
    print("="*60)
    
    try:
        response = requests.post(
            f"{API_BASE}/{script_id}/test",
            params={"test_message": "你好"}
        )
        print(f"狀態碼: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"[OK] 劇本測試成功")
            print(f"  測試消息: {result.get('test_message')}")
            print(f"  回復: {result.get('reply')}")
            print(f"  當前場景: {result.get('current_scene')}")
            return result
        else:
            print(f"[FAIL] 測試失敗: {response.text}")
            return None
    except Exception as e:
        print(f"[FAIL] 請求失敗: {e}")
        return None


def test_update_script(script_id: str):
    """測試更新劇本"""
    print("\n" + "="*60)
    print("測試 5: 更新劇本")
    print("="*60)
    
    data = {
        "name": "更新後的劇本名稱",
        "description": "更新後的描述"
    }
    
    try:
        response = requests.put(f"{API_BASE}/{script_id}", json=data)
        print(f"狀態碼: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"[OK] 劇本更新成功")
            print(f"  名稱: {result.get('name')}")
            print(f"  描述: {result.get('description')}")
            return result
        else:
            print(f"[FAIL] 更新失敗: {response.text}")
            return None
    except Exception as e:
        print(f"[FAIL] 請求失敗: {e}")
        return None


def test_delete_script(script_id: str):
    """測試刪除劇本"""
    print("\n" + "="*60)
    print("測試 6: 刪除劇本")
    print("="*60)
    
    try:
        response = requests.delete(f"{API_BASE}/{script_id}")
        print(f"狀態碼: {response.status_code}")
        if response.status_code == 204:
            print(f"[OK] 劇本刪除成功")
            return True
        else:
            print(f"[FAIL] 刪除失敗: {response.text}")
            return False
    except Exception as e:
        print(f"[FAIL] 請求失敗: {e}")
        return False


def main():
    """主測試流程"""
    print("\n" + "="*60)
    print("劇本管理 API 測試")
    print("="*60)
    print(f"\nAPI 地址: {API_BASE}")
    print("[INFO] 請確保後端服務正在運行 (http://localhost:8000)\n")
    
    # 測試創建
    script_id = test_create_script()
    if not script_id:
        print("\n[WARN] 創建劇本失敗，跳過後續測試")
        return
    
    # 測試列出
    test_list_scripts()
    
    # 測試獲取詳情
    test_get_script(script_id)
    
    # 測試劇本測試接口
    test_test_script(script_id)
    
    # 測試更新
    test_update_script(script_id)
    
    # 測試刪除
    test_delete_script(script_id)
    
    print("\n" + "="*60)
    print("測試完成")
    print("="*60)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n測試已中斷")
    except Exception as e:
        print(f"\n\n測試過程中發生錯誤: {e}")
        import traceback
        traceback.print_exc()

