#!/usr/bin/env python3
"""
測試服務器操作API
"""
import requests
import json

API_BASE = "http://localhost:8000/api/v1"

def test_server_actions():
    """測試服務器操作"""
    node_id = "worker-01"
    
    print(f"\n{'='*60}")
    print(f"測試服務器操作: {node_id}")
    print(f"{'='*60}\n")
    
    # 測試獲取服務器列表
    print("[1] 測試獲取服務器列表...")
    try:
        response = requests.get(f"{API_BASE}/group-ai/servers/")
        if response.status_code == 200:
            servers = response.json()
            print(f"✅ 成功獲取 {len(servers)} 個服務器")
            for server in servers:
                print(f"  - {server['node_id']}: {server['status']}")
        else:
            print(f"❌ 失敗: HTTP {response.status_code}")
            print(f"   {response.text}")
    except Exception as e:
        print(f"❌ 錯誤: {e}")
    
    # 測試啟動服務
    print("\n[2] 測試啟動服務...")
    try:
        response = requests.post(
            f"{API_BASE}/group-ai/servers/{node_id}/action",
            json={"action": "start", "node_id": node_id}
        )
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 操作成功: {result.get('message')}")
            if 'output' in result:
                print(f"   輸出: {result['output']}")
        else:
            print(f"❌ 失敗: HTTP {response.status_code}")
            print(f"   {response.text}")
    except Exception as e:
        print(f"❌ 錯誤: {e}")
    
    # 測試獲取日誌
    print("\n[3] 測試獲取服務器日誌...")
    try:
        response = requests.get(f"{API_BASE}/group-ai/servers/{node_id}/logs?lines=10")
        if response.status_code == 200:
            logs = response.json()
            print(f"✅ 成功獲取 {len(logs)} 條日誌")
            for log in logs[:3]:  # 只顯示前3條
                print(f"  [{log.get('level', 'INFO')}] {log.get('message', '')[:50]}")
        else:
            print(f"❌ 失敗: HTTP {response.status_code}")
            print(f"   {response.text}")
    except Exception as e:
        print(f"❌ 錯誤: {e}")
    
    # 測試獲取服務器狀態
    print("\n[4] 測試獲取單個服務器狀態...")
    try:
        response = requests.get(f"{API_BASE}/group-ai/servers/{node_id}")
        if response.status_code == 200:
            server = response.json()
            print(f"✅ 服務器狀態:")
            print(f"  節點ID: {server.get('node_id')}")
            print(f"  狀態: {server.get('status')}")
            print(f"  服務狀態: {server.get('service_status')}")
            print(f"  帳號數: {server.get('accounts_count')}/{server.get('max_accounts')}")
        else:
            print(f"❌ 失敗: HTTP {response.status_code}")
            print(f"   {response.text}")
    except Exception as e:
        print(f"❌ 錯誤: {e}")

if __name__ == "__main__":
    test_server_actions()

