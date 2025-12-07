#!/usr/bin/env python3
"""
前端功能自動化驗證腳本
使用 Playwright 進行 E2E 測試驗證
"""
import os
import sys
import subprocess
import time
import requests
from pathlib import Path

# 項目路徑
project_root = Path(__file__).parent.parent.parent
backend_dir = project_root / "admin-backend"
frontend_dir = project_root / "saas-demo"

def check_service_running(url: str, timeout: int = 5) -> bool:
    """檢查服務是否運行"""
    try:
        response = requests.get(url, timeout=timeout)
        return response.status_code == 200
    except:
        return False

def wait_for_service(url: str, max_wait: int = 60, interval: int = 2) -> bool:
    """等待服務啟動"""
    print(f"等待服務啟動: {url}")
    for i in range(0, max_wait, interval):
        if check_service_running(url):
            print(f"✅ 服務已啟動: {url}")
            return True
        print(f"⏳ 等待中... ({i}/{max_wait}秒)")
        time.sleep(interval)
    return False

def run_playwright_tests() -> bool:
    """運行 Playwright E2E 測試"""
    print("=" * 60)
    print("🧪 運行前端 E2E 測試")
    print("=" * 60)
    print()
    
    # 檢查 Playwright 是否安裝
    try:
        result = subprocess.run(
            ["npx", "playwright", "--version"],
            cwd=frontend_dir,
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode != 0:
            print("⚠️  Playwright 未安裝，正在安裝...")
            subprocess.run(["npm", "install", "@playwright/test"], cwd=frontend_dir)
            subprocess.run(["npx", "playwright", "install"], cwd=frontend_dir)
    except Exception as e:
        print(f"⚠️  檢查 Playwright 時出錯: {e}")
        return False
    
    # 運行測試
    print("運行 E2E 測試...")
    try:
        result = subprocess.run(
            ["npm", "run", "test:e2e"],
            cwd=frontend_dir,
            timeout=300,  # 5 分鐘超時
            capture_output=False
        )
        
        if result.returncode == 0:
            print("✅ E2E 測試通過")
            return True
        else:
            print("❌ E2E 測試失敗")
            return False
    except subprocess.TimeoutExpired:
        print("❌ E2E 測試超時")
        return False
    except Exception as e:
        print(f"❌ 運行 E2E 測試時出錯: {e}")
        return False

def verify_api_endpoints() -> bool:
    """驗證 API 端點"""
    print("=" * 60)
    print("🔍 驗證 API 端點")
    print("=" * 60)
    print()
    
    base_url = "http://localhost:8000"
    endpoints = [
        "/health",
        "/healthz",
        "/docs",
        "/api/v1/auth/login",
    ]
    
    all_passed = True
    for endpoint in endpoints:
        url = f"{base_url}{endpoint}"
        try:
            response = requests.get(url, timeout=5)
            if response.status_code in [200, 401, 405]:  # 401/405 也算正常（需要認證或方法不對）
                print(f"✅ {endpoint} - 狀態碼: {response.status_code}")
            else:
                print(f"⚠️  {endpoint} - 狀態碼: {response.status_code}")
                all_passed = False
        except Exception as e:
            print(f"❌ {endpoint} - 錯誤: {e}")
            all_passed = False
    
    return all_passed

def main():
    """主函數"""
    print("=" * 60)
    print("🚀 前端功能自動化驗證")
    print("=" * 60)
    print()
    
    # 檢查後端服務
    backend_url = "http://localhost:8000/health"
    if not check_service_running(backend_url):
        print("⚠️  後端服務未運行，請先啟動後端服務：")
        print("   cd admin-backend")
        print("   python -m uvicorn app.main:app --host 0.0.0.0 --port 8000")
        print()
        if not wait_for_service(backend_url):
            print("❌ 無法連接到後端服務，請檢查服務是否正常運行")
            return 1
    
    # 檢查前端服務
    frontend_url = "http://localhost:3000"
    if not check_service_running(frontend_url):
        print("⚠️  前端服務未運行，請先啟動前端服務：")
        print("   cd saas-demo")
        print("   npm run dev")
        print()
        if not wait_for_service(frontend_url):
            print("❌ 無法連接到前端服務，請檢查服務是否正常運行")
            return 1
    
    print()
    
    # 驗證 API 端點
    api_ok = verify_api_endpoints()
    print()
    
    # 運行 E2E 測試
    e2e_ok = run_playwright_tests()
    print()
    
    # 總結
    print("=" * 60)
    print("📊 驗證結果總結")
    print("=" * 60)
    print(f"API 端點驗證: {'✅ 通過' if api_ok else '❌ 失敗'}")
    print(f"E2E 測試: {'✅ 通過' if e2e_ok else '❌ 失敗'}")
    print()
    
    if api_ok and e2e_ok:
        print("✅ 所有自動化驗證通過！")
        print()
        print("⚠️  注意：部分功能需要手動驗證，請參考：")
        print("   admin-backend/前端功能驗證清單.md")
        return 0
    else:
        print("❌ 部分驗證失敗，請檢查上述問題")
        return 1

if __name__ == "__main__":
    sys.exit(main())

