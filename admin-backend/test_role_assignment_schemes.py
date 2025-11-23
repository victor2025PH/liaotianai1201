"""
測試角色分配方案管理功能
"""
import requests
import json
from typing import Dict, Any

BASE_URL = "http://localhost:8000/api/v1/group-ai"

def print_section(title: str):
    """打印分節標題"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def test_create_scheme() -> Dict[str, Any]:
    """測試創建分配方案"""
    print_section("測試創建分配方案")
    
    # 首先需要獲取一個劇本和賬號
    try:
        scripts_resp = requests.get(f"{BASE_URL}/scripts/", timeout=5)
        if scripts_resp.status_code != 200:
            print(f"⚠ 獲取劇本列表失敗: {scripts_resp.status_code}")
            return None
        scripts = scripts_resp.json()
        if isinstance(scripts, dict) and 'items' in scripts:
            scripts = scripts['items']
        
        if not scripts or len(scripts) == 0:
            print("⚠ 沒有可用的劇本，跳過創建方案測試")
            return None
        
        script = scripts[0]
        script_id = script.get('script_id') or script.get('id')
        print(f"使用劇本: {script.get('name', script_id)}")
        
        accounts_resp = requests.get(f"{BASE_URL}/accounts/", timeout=5)
        if accounts_resp.status_code != 200:
            print(f"⚠ 獲取賬號列表失敗: {accounts_resp.status_code}")
            return None
        accounts_data = accounts_resp.json()
        if isinstance(accounts_data, dict):
            accounts = accounts_data.get('items', accounts_data.get('accounts', []))
        else:
            accounts = accounts_data
        
        if not accounts or len(accounts) == 0:
            print("⚠ 沒有可用的賬號，跳過創建方案測試")
            return None
        
        account_ids = [acc.get('account_id') or acc.get('id') for acc in accounts[:3]]
        print(f"使用賬號: {account_ids}")
        
        # 創建一個簡單的分配方案
        scheme_data = {
            "name": "測試方案_001",
            "description": "這是一個測試方案",
            "script_id": script_id,
            "assignments": [
                {
                    "role_id": f"role_{i+1}",
                    "account_id": account_ids[i % len(account_ids)],
                    "weight": 1.0
                }
                for i in range(min(3, len(account_ids)))
            ],
            "mode": "auto",
            "account_ids": account_ids[:3]
        }
        
        response = requests.post(
            f"{BASE_URL}/role-assignment-schemes/",
            json=scheme_data,
            timeout=10
        )
        
        if response.status_code == 201:
            scheme = response.json()
            print(f"✓ 創建成功: {scheme.get('name')} (ID: {scheme.get('id')})")
            return scheme
        else:
            print(f"✗ 創建失敗: {response.status_code}")
            print(f"  響應: {response.text[:200]}")
            return None
    
    except requests.exceptions.ConnectionError:
        print("✗ 無法連接到服務器，請確保後端服務器正在運行")
        return None
    except requests.exceptions.Timeout:
        print("✗ 請求超時")
        return None
    except Exception as e:
        print(f"✗ 創建方案時發生錯誤: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_list_schemes():
    """測試列出方案"""
    print_section("測試列出分配方案")
    
    try:
        response = requests.get(
            f"{BASE_URL}/role-assignment-schemes/?page=1&page_size=20",
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            schemes = data.get('items', [])
            total = data.get('total', 0)
            print(f"✓ 獲取成功: 共 {total} 個方案")
            for scheme in schemes[:5]:  # 只顯示前5個
                print(f"  - {scheme.get('name')} (劇本: {scheme.get('script_id')})")
            return schemes
        else:
            print(f"✗ 獲取失敗: {response.status_code}")
            print(f"  響應: {response.text[:200]}")
            return []
    
    except Exception as e:
        print(f"✗ 列出方案時發生錯誤: {e}")
        return []

def test_get_scheme(scheme_id: str):
    """測試獲取方案詳情"""
    print_section(f"測試獲取方案詳情: {scheme_id}")
    
    try:
        response = requests.get(
            f"{BASE_URL}/role-assignment-schemes/{scheme_id}",
            timeout=5
        )
        
        if response.status_code == 200:
            scheme = response.json()
            print(f"✓ 獲取成功: {scheme.get('name')}")
            print(f"  描述: {scheme.get('description', '無')}")
            print(f"  劇本: {scheme.get('script_name', scheme.get('script_id'))}")
            print(f"  分配數量: {len(scheme.get('assignments', []))}")
            return scheme
        else:
            print(f"✗ 獲取失敗: {response.status_code}")
            print(f"  響應: {response.text[:200]}")
            return None
    
    except Exception as e:
        print(f"✗ 獲取方案時發生錯誤: {e}")
        return None

def test_update_scheme(scheme_id: str):
    """測試更新方案"""
    print_section(f"測試更新方案: {scheme_id}")
    
    try:
        update_data = {
            "name": "測試方案_001_已更新",
            "description": "這是更新後的描述"
        }
        
        response = requests.put(
            f"{BASE_URL}/role-assignment-schemes/{scheme_id}",
            json=update_data,
            timeout=5
        )
        
        if response.status_code == 200:
            scheme = response.json()
            print(f"✓ 更新成功: {scheme.get('name')}")
            return scheme
        else:
            print(f"✗ 更新失敗: {response.status_code}")
            print(f"  響應: {response.text[:200]}")
            return None
    
    except Exception as e:
        print(f"✗ 更新方案時發生錯誤: {e}")
        return None

def test_apply_scheme(scheme_id: str):
    """測試應用方案"""
    print_section(f"測試應用方案: {scheme_id}")
    
    try:
        apply_data = {}
        
        response = requests.post(
            f"{BASE_URL}/role-assignment-schemes/{scheme_id}/apply",
            json=apply_data,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✓ 應用成功: {result.get('message')}")
            print(f"  應用數量: {result.get('applied_count', 0)}")
            return result
        else:
            print(f"✗ 應用失敗: {response.status_code}")
            print(f"  響應: {response.text[:200]}")
            return None
    
    except Exception as e:
        print(f"✗ 應用方案時發生錯誤: {e}")
        return None

def test_get_history(scheme_id: str):
    """測試獲取應用歷史"""
    print_section(f"測試獲取應用歷史: {scheme_id}")
    
    try:
        response = requests.get(
            f"{BASE_URL}/role-assignment-schemes/{scheme_id}/history?page=1&page_size=20",
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            histories = data.get('items', [])
            total = data.get('total', 0)
            print(f"✓ 獲取成功: 共 {total} 條歷史記錄")
            for history in histories[:3]:  # 只顯示前3條
                print(f"  賬號: {history.get('account_id')}, 角色: {history.get('role_id')}, 時間: {history.get('applied_at')}")
            return histories
        else:
            print(f"✗ 獲取失敗: {response.status_code}")
            print(f"  響應: {response.text[:200]}")
            return []
    
    except Exception as e:
        print(f"✗ 獲取歷史時發生錯誤: {e}")
        return []

def main():
    """主測試函數"""
    print("\n" + "="*60)
    print("  角色分配方案管理功能測試")
    print("="*60)
    
    # 測試創建方案
    scheme = test_create_scheme()
    
    if not scheme:
        print("\n⚠ 無法創建測試方案，跳過後續測試")
        return
    
    scheme_id = scheme.get('id')
    
    # 測試列出方案
    schemes = test_list_schemes()
    
    # 測試獲取方案詳情
    test_get_scheme(scheme_id)
    
    # 測試更新方案
    test_update_scheme(scheme_id)
    
    # 測試應用方案（可選，因為需要實際的賬號）
    # test_apply_scheme(scheme_id)
    
    # 測試獲取歷史（如果已應用過）
    # test_get_history(scheme_id)
    
    print("\n" + "="*60)
    print("  測試完成")
    print("="*60)

if __name__ == "__main__":
    main()

