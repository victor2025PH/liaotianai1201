# -*- coding: utf-8 -*-
"""
快速测试 Workers API
"""

import requests
import json

BASE_URL = "http://aikz.usdt2026.cc/api/v1/workers"

print("=" * 60)
print("测试 Workers API")
print("=" * 60)
print()

# 1. 测试获取 Workers 列表
print("[1] 测试 GET /api/v1/workers/")
try:
    response = requests.get(f"{BASE_URL}/", timeout=10)
    print(f"状态码: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Workers 数量: {len(data.get('workers', {}))}")
        for node_id, worker in data.get('workers', {}).items():
            print(f"  - {node_id}: {worker.get('status')} ({worker.get('account_count')} 账号)")
    else:
        print(f"错误: {response.text}")
except Exception as e:
    print(f"请求失败: {e}")

print()

# 2. 测试发送心跳
print("[2] 测试 POST /api/v1/workers/heartbeat")
try:
    response = requests.post(
        f"{BASE_URL}/heartbeat",
        json={
            "node_id": "computer_001",
            "status": "online",
            "account_count": 0,
            "accounts": []
        },
        timeout=10
    )
    print(f"状态码: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"成功: {data.get('message')}")
        print(f"待执行命令数: {len(data.get('pending_commands', []))}")
    else:
        print(f"错误: {response.text}")
except Exception as e:
    print(f"请求失败: {e}")

print()

# 3. 再次测试获取 Workers 列表（应该能看到 computer_001）
print("[3] 再次测试 GET /api/v1/workers/（应该能看到 computer_001）")
try:
    response = requests.get(f"{BASE_URL}/", timeout=10)
    print(f"状态码: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        workers = data.get('workers', {})
        print(f"Workers 数量: {len(workers)}")
        if 'computer_001' in workers:
            print("✓ computer_001 已出现在列表中")
            worker = workers['computer_001']
            print(f"  状态: {worker.get('status')}")
            print(f"  账号数: {worker.get('account_count')}")
            print(f"  最后心跳: {worker.get('last_heartbeat')}")
        else:
            print("✗ computer_001 未出现在列表中")
    else:
        print(f"错误: {response.text}")
except Exception as e:
    print(f"请求失败: {e}")

print()
print("=" * 60)
print("测试完成")
print("=" * 60)

