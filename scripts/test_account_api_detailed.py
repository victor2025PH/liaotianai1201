"""
詳細測試帳號 API，獲取完整錯誤信息
"""
import requests
import json
import sys

API_BASE = "http://localhost:8000/api/v1"

def test_accounts_api():
    """測試帳號 API 並獲取詳細錯誤信息"""
    print("="*60)
    print("測試帳號 API")
    print("="*60)
    
    try:
        print("\n發送請求到 /group-ai/accounts/...")
        response = requests.get(f"{API_BASE}/group-ai/accounts/", timeout=10)
        
        print(f"狀態碼: {response.status_code}")
        print(f"響應頭: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n✅ 成功！")
            print(f"帳號總數: {data.get('total', 0)}")
            print(f"返回項目數: {len(data.get('items', []))}")
            return True
        else:
            print(f"\n❌ 錯誤狀態碼: {response.status_code}")
            try:
                error_data = response.json()
                print(f"錯誤響應: {json.dumps(error_data, indent=2, ensure_ascii=False)}")
            except:
                print(f"錯誤響應（文本）: {response.text[:500]}")
            return False
            
    except requests.exceptions.ConnectionError as e:
        print(f"\n❌ 連接錯誤: {e}")
        print("後端服務可能未運行")
        return False
    except requests.exceptions.Timeout as e:
        print(f"\n❌ 請求超時: {e}")
        return False
    except Exception as e:
        print(f"\n❌ 未知錯誤: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_accounts_api()
    sys.exit(0 if success else 1)

