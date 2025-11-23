"""
系統啟動測試腳本
用於驗證系統是否可以正常啟動
"""
import sys
import time
import requests
from pathlib import Path

def test_backend_health():
    """測試後端健康檢查"""
    print("\n[1/4] 測試後端健康檢查...")
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            print("[OK] 後端服務正常運行")
            print(f"   響應: {response.json()}")
            return True
        else:
            print(f"[ERROR] 後端響應異常: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("[ERROR] 無法連接到後端服務 (http://localhost:8000)")
        print("   請確保後端服務已啟動")
        return False
    except Exception as e:
        print(f"[ERROR] 測試失敗: {e}")
        return False

def test_backend_api():
    """測試後端 API 端點"""
    print("\n[2/4] 測試後端 API 端點...")
    
    endpoints = [
        ("/api/v1/group-ai/accounts/", "賬號列表"),
        ("/api/v1/group-ai/scripts/", "劇本列表"),
        ("/api/v1/group-ai/monitor/system", "系統監控"),
    ]
    
    success_count = 0
    for endpoint, name in endpoints:
        try:
            response = requests.get(f"http://localhost:8000{endpoint}", timeout=5)
            if response.status_code == 200:
                print(f"[OK] {name} API 正常")
                success_count += 1
            else:
                print(f"[ERROR] {name} API 異常: {response.status_code}")
        except Exception as e:
            print(f"[ERROR] {name} API 測試失敗: {e}")
    
    if success_count == len(endpoints):
        print(f"[OK] 所有 API 端點測試通過 ({success_count}/{len(endpoints)})")
        return True
    else:
        print(f"[WARN] 部分 API 端點測試失敗 ({success_count}/{len(endpoints)})")
        return False

def test_frontend():
    """測試前端服務"""
    print("\n[3/4] 測試前端服務...")
    try:
        response = requests.get("http://localhost:3000", timeout=5)
        if response.status_code == 200:
            print("[OK] 前端服務正常運行")
            return True
        else:
            print(f"[ERROR] 前端響應異常: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("[ERROR] 無法連接到前端服務 (http://localhost:3000)")
        print("   請確保前端服務已啟動")
        return False
    except Exception as e:
        print(f"[ERROR] 測試失敗: {e}")
        return False

def check_environment():
    """檢查環境配置"""
    print("\n[4/4] 檢查環境配置...")
    
    root_dir = Path(__file__).parent.parent
    env_file = root_dir / ".env"
    sessions_dir = root_dir / "sessions"
    
    checks = []
    
    # 檢查 .env 文件
    if env_file.exists():
        print("[OK] 找到 .env 文件")
        checks.append(True)
    else:
        print("[WARN] 未找到 .env 文件（如果使用環境變量則可忽略）")
        checks.append(False)
    
    # 檢查 sessions 目錄
    if sessions_dir.exists():
        session_files = list(sessions_dir.glob("*.session"))
        if session_files:
            print(f"[OK] 找到 {len(session_files)} 個 session 文件")
            checks.append(True)
        else:
            print("[WARN] sessions 目錄中沒有 .session 文件")
            checks.append(False)
    else:
        print("[WARN] sessions 目錄不存在")
        checks.append(False)
    
    return any(checks)

def main():
    """主函數"""
    print("="*60)
    print("系統啟動測試")
    print("="*60)
    print("\n請確保後端和前端服務已啟動：")
    print("  後端: http://localhost:8000")
    print("  前端: http://localhost:3000")
    print("\n等待 3 秒後開始測試...")
    time.sleep(3)
    
    results = []
    
    # 測試後端
    results.append(test_backend_health())
    results.append(test_backend_api())
    
    # 測試前端
    results.append(test_frontend())
    
    # 檢查環境
    results.append(check_environment())
    
    # 總結
    print("\n" + "="*60)
    print("測試結果總結")
    print("="*60)
    
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"[OK] 所有測試通過 ({passed}/{total})")
        print("\n系統已準備就緒，可以開始使用！")
        return 0
    else:
        print(f"[WARN] 部分測試未通過 ({passed}/{total})")
        print("\n請檢查上述錯誤並修復後重試")
        return 1

if __name__ == "__main__":
    sys.exit(main())

