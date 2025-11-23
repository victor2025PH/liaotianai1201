#!/usr/bin/env python3
"""
網頁自檢腳本
檢查所有前端頁面和API端點是否正常工作
"""
import requests
import json
import sys
from typing import Dict, List, Tuple

API_BASE = "http://localhost:8000/api/v1"
FRONTEND_BASE = "http://localhost:3000"

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'

def print_success(msg: str):
    print(f"{Colors.GREEN}✅ {msg}{Colors.RESET}")

def print_error(msg: str):
    print(f"{Colors.RED}❌ {msg}{Colors.RESET}")

def print_warning(msg: str):
    print(f"{Colors.YELLOW}⚠️  {msg}{Colors.RESET}")

def print_info(msg: str):
    print(f"{Colors.BLUE}ℹ️  {msg}{Colors.RESET}")

def test_api_endpoint(name: str, method: str, url: str, data: Dict = None) -> Tuple[bool, str]:
    """測試API端點"""
    try:
        if method == "GET":
            response = requests.get(url, timeout=5)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=5)
        else:
            return False, f"不支持的HTTP方法: {method}"
        
        if response.status_code == 200:
            return True, f"HTTP {response.status_code}"
        else:
            return False, f"HTTP {response.status_code}: {response.text[:100]}"
    except requests.exceptions.ConnectionError:
        return False, "連接失敗（服務可能未啟動）"
    except Exception as e:
        return False, str(e)

def test_frontend_page(name: str, path: str) -> Tuple[bool, str]:
    """測試前端頁面"""
    try:
        url = f"{FRONTEND_BASE}{path}"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            return True, f"HTTP {response.status_code}"
        else:
            return False, f"HTTP {response.status_code}"
    except requests.exceptions.ConnectionError:
        return False, "連接失敗（前端服務可能未啟動）"
    except Exception as e:
        return False, str(e)

def main():
    print(f"\n{'='*60}")
    print("網頁自檢開始")
    print(f"{'='*60}\n")
    
    results = {
        "api": [],
        "frontend": [],
        "server_management": []
    }
    
    # 測試後端API
    print(f"{Colors.BLUE}【後端API測試】{Colors.RESET}")
    print("-" * 60)
    
    api_tests = [
        ("服務器列表", "GET", f"{API_BASE}/group-ai/servers/"),
        ("單個服務器狀態", "GET", f"{API_BASE}/group-ai/servers/worker-01"),
    ]
    
    for name, method, url in api_tests:
        success, msg = test_api_endpoint(name, method, url)
        results["api"].append((name, success, msg))
        if success:
            print_success(f"{name}: {msg}")
        else:
            print_error(f"{name}: {msg}")
    
    # 測試服務器管理功能
    print(f"\n{Colors.BLUE}【服務器管理功能測試】{Colors.RESET}")
    print("-" * 60)
    
    # 獲取服務器列表
    try:
        response = requests.get(f"{API_BASE}/group-ai/servers/", timeout=5)
        if response.status_code == 200:
            servers = response.json()
            print_success(f"獲取服務器列表: {len(servers)} 個服務器")
            
            if servers:
                server = servers[0]
                node_id = server.get('node_id')
                
                # 測試服務器操作
                action_tests = [
                    ("獲取服務器狀態", "GET", f"{API_BASE}/group-ai/servers/{node_id}"),
                    ("獲取服務器日誌", "GET", f"{API_BASE}/group-ai/servers/{node_id}/logs?lines=10"),
                ]
                
                for name, method, url in action_tests:
                    success, msg = test_api_endpoint(name, method, url)
                    results["server_management"].append((name, success, msg))
                    if success:
                        print_success(f"{name}: {msg}")
                    else:
                        print_warning(f"{name}: {msg}")
        else:
            print_error(f"獲取服務器列表失敗: HTTP {response.status_code}")
    except Exception as e:
        print_error(f"服務器管理測試失敗: {e}")
    
    # 測試前端頁面
    print(f"\n{Colors.BLUE}【前端頁面測試】{Colors.RESET}")
    print("-" * 60)
    
    frontend_tests = [
        ("首頁", "/"),
        ("服務器管理", "/group-ai/servers"),
        ("賬號管理", "/group-ai/accounts"),
        ("劇本管理", "/group-ai/scripts"),
    ]
    
    for name, path in frontend_tests:
        success, msg = test_frontend_page(name, path)
        results["frontend"].append((name, success, msg))
        if success:
            print_success(f"{name}: {msg}")
        else:
            print_warning(f"{name}: {msg}")
    
    # 總結
    print(f"\n{'='*60}")
    print("自檢總結")
    print(f"{'='*60}\n")
    
    total_tests = sum(len(tests) for tests in results.values())
    passed_tests = sum(sum(1 for _, success, _ in tests if success) for tests in results.values())
    
    print_info(f"總測試數: {total_tests}")
    print_success(f"通過: {passed_tests}")
    print_error(f"失敗: {total_tests - passed_tests}")
    
    if passed_tests == total_tests:
        print_success("\n🎉 所有測試通過！")
        return 0
    else:
        print_warning("\n⚠️  部分測試失敗，請檢查上述錯誤信息")
        return 1

if __name__ == "__main__":
    sys.exit(main())

