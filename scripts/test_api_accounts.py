"""
測試群組 AI 賬號管理 API

使用方法:
    py scripts/test_api_accounts.py
"""
import requests
import json
import sys
import io

# 設置 UTF-8 編碼（Windows 兼容）
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

BASE_URL = "http://localhost:8000/api/v1/group-ai/accounts"

def print_success(msg):
    print(f"[OK] {msg}")

def print_error(msg):
    print(f"[FAIL] {msg}")

def print_info(msg):
    print(f"[INFO] {msg}")

def test_list_accounts():
    """測試列出賬號"""
    print("\n[測試 1] 列出所有賬號")
    try:
        response = requests.get(BASE_URL)
        if response.status_code == 200:
            data = response.json()
            print_success(f"獲取成功，共 {data['total']} 個賬號")
            for account in data['items']:
                print(f"  - {account['account_id']}: {account['status']}")
            return True
        else:
            print_error(f"狀態碼: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print_error("無法連接到後端服務，請確保後端正在運行 (http://localhost:8000)")
        return False
    except Exception as e:
        print_error(f"請求失敗: {e}")
        return False

def test_create_account():
    """測試創建賬號"""
    print("\n[測試 2] 創建賬號")
    try:
        data = {
            "account_id": "test_api_account",
            "session_file": "sessions/test_session.session",
            "script_id": "test_script",
            "group_ids": [123456789],
            "active": True
        }
        response = requests.post(BASE_URL, json=data)
        if response.status_code == 201:
            account = response.json()
            print_success(f"賬號創建成功: {account['account_id']}")
            return account['account_id']
        else:
            print_error(f"狀態碼: {response.status_code}, 響應: {response.text}")
            return None
    except Exception as e:
        print_error(f"創建失敗: {e}")
        return None

def test_get_account(account_id: str):
    """測試獲取賬號詳情"""
    print(f"\n[測試 3] 獲取賬號詳情: {account_id}")
    try:
        response = requests.get(f"{BASE_URL}/{account_id}")
        if response.status_code == 200:
            account = response.json()
            print_success("獲取成功")
            print(f"  賬號 ID: {account['account_id']}")
            print(f"  狀態: {account['status']}")
            print(f"  劇本: {account['script_id']}")
            return True
        else:
            print_error(f"狀態碼: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"獲取失敗: {e}")
        return False

def test_get_status(account_id: str):
    """測試獲取賬號狀態"""
    print(f"\n[測試 4] 獲取賬號狀態: {account_id}")
    try:
        response = requests.get(f"{BASE_URL}/{account_id}/status")
        if response.status_code == 200:
            status_data = response.json()
            print_success("獲取成功")
            print(f"  狀態: {status_data['status']}")
            print(f"  在線: {status_data['online']}")
            print(f"  消息數: {status_data['message_count']}")
            return True
        else:
            print_error(f"狀態碼: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"獲取失敗: {e}")
        return False

def test_batch_import():
    """測試批量導入"""
    print("\n[測試 5] 批量導入賬號")
    try:
        data = {
            "directory": "sessions",
            "script_id": "batch_test",
            "group_ids": [123456789]
        }
        response = requests.post(f"{BASE_URL}/batch-import", json=data)
        if response.status_code == 200:
            result = response.json()
            print_success(f"批量導入成功，加載了 {result['loaded_count']} 個賬號")
            return True
        else:
            print_error(f"狀態碼: {response.status_code}, 響應: {response.text}")
            return False
    except Exception as e:
        print_error(f"批量導入失敗: {e}")
        return False

def main():
    print("="*60)
    print("群組 AI 賬號管理 API 測試")
    print("="*60)
    print(f"\nAPI 地址: {BASE_URL}")
    print_info("請確保後端服務正在運行 (http://localhost:8000)")
    
    # 測試列表
    test_list_accounts()
    
    # 測試創建
    account_id = test_create_account()
    
    if account_id:
        # 測試獲取詳情
        test_get_account(account_id)
        
        # 測試獲取狀態
        test_get_status(account_id)
    
    # 測試批量導入
    test_batch_import()
    
    # 再次列出所有賬號
    print("\n[測試 6] 最終賬號列表")
    test_list_accounts()
    
    print("\n" + "="*60)
    print("測試完成")
    print("="*60)
    print("\n提示:")
    print("  - 如需測試啟動/停止功能，請使用:")
    print(f"    POST {BASE_URL}/{{account_id}}/start")
    print(f"    POST {BASE_URL}/{{account_id}}/stop")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n測試已中斷")
    except Exception as e:
        print(f"\n\n測試過程中發生錯誤: {e}")
        import traceback
        traceback.print_exc()

