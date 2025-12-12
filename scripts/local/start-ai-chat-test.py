#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
启动 AI 聊天测试脚本
让指定数量的在线账号开始聊天
"""

import requests
import json
import sys
from typing import List, Dict, Any

# API 配置
API_BASE_URL = "http://localhost:8000/api/v1"
# 如果是在生产环境，使用相对路径
if len(sys.argv) > 1 and sys.argv[1] == "--prod":
    API_BASE_URL = "/api/v1"

# 认证信息（需要从环境变量或配置文件读取）
# 这里使用默认的测试账号，实际使用时应该从环境变量读取
EMAIL = "admin@example.com"
PASSWORD = "changeme123"  # 默认密码，生产环境应该修改

def get_auth_token() -> str:
    """获取认证 token"""
    try:
        response = requests.post(
            f"{API_BASE_URL}/auth/login",
            json={"email": EMAIL, "password": PASSWORD},
            headers={"Content-Type": "application/json"}
        )
        if response.status_code == 200:
            data = response.json()
            return data.get("access_token", "")
        else:
            print(f"❌ 登录失败: {response.status_code}")
            print(f"响应: {response.text}")
            return ""
    except Exception as e:
        print(f"❌ 登录异常: {e}")
        return ""

def get_online_accounts(token: str, max_accounts: int = 6) -> List[Dict[str, Any]]:
    """获取在线账号列表"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        
        # 获取账号列表，筛选在线状态
        response = requests.get(
            f"{API_BASE_URL}/group-ai/accounts/",
            params={"status_filter": "online", "page_size": 100},
            headers=headers
        )
        
        if response.status_code == 200:
            data = response.json()
            accounts = data.get("items", [])
            
            # 筛选在线账号
            online_accounts = [
                acc for acc in accounts 
                if acc.get("status") == "online"
            ]
            
            print(f"✅ 找到 {len(online_accounts)} 个在线账号")
            
            # 限制数量
            if len(online_accounts) > max_accounts:
                online_accounts = online_accounts[:max_accounts]
                print(f"⚠️  限制为前 {max_accounts} 个账号")
            
            return online_accounts
        else:
            print(f"❌ 获取账号列表失败: {response.status_code}")
            print(f"响应: {response.text}")
            return []
    except Exception as e:
        print(f"❌ 获取账号列表异常: {e}")
        return []

def start_chat_for_accounts(token: str, account_ids: List[str], group_id: int = None) -> Dict[str, bool]:
    """为多个账号启动聊天"""
    results = {}
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    for account_id in account_ids:
        try:
            # 使用 chat-features API 启动聊天
            params = {}
            if group_id:
                params["group_id"] = group_id
                
            response = requests.post(
                f"{API_BASE_URL}/group-ai/chat-features/chat/start",
                params=params,
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    results[account_id] = True
                    print(f"  ✅ 账号 {account_id} 聊天已启动")
                else:
                    results[account_id] = False
                    print(f"  ⚠️  账号 {account_id} 启动失败: {data.get('message', '未知错误')}")
            else:
                results[account_id] = False
                print(f"  ❌ 账号 {account_id} 启动失败: HTTP {response.status_code}")
                print(f"     响应: {response.text[:200]}")
        except Exception as e:
            results[account_id] = False
            print(f"  ❌ 账号 {account_id} 启动异常: {e}")
    
    return results

def main():
    print("=" * 60)
    print("AI 聊天测试启动脚本")
    print("=" * 60)
    print()
    
    # 1. 登录获取 token
    print("[1/3] 登录获取认证 token...")
    token = get_auth_token()
    if not token:
        print("❌ 无法获取认证 token，退出")
        return 1
    print("✅ 登录成功")
    print()
    
    # 2. 获取在线账号
    print("[2/3] 获取在线账号列表...")
    max_accounts = 6
    if len(sys.argv) > 1 and sys.argv[1].isdigit():
        max_accounts = int(sys.argv[1])
    
    online_accounts = get_online_accounts(token, max_accounts)
    
    if not online_accounts:
        print("❌ 没有找到在线账号")
        print("   请确保：")
        print("   1. 账号已启动并在线")
        print("   2. 账号状态为 'online'")
        return 1
    
    print(f"✅ 找到 {len(online_accounts)} 个在线账号:")
    for acc in online_accounts:
        print(f"   - {acc.get('account_id')} ({acc.get('display_name', 'N/A')})")
    print()
    
    # 3. 启动聊天
    print("[3/3] 启动 AI 聊天...")
    account_ids = [acc.get("account_id") for acc in online_accounts]
    
    # 检查是否有指定群组 ID
    group_id = None
    if len(sys.argv) > 2 and sys.argv[2].isdigit():
        group_id = int(sys.argv[2])
        print(f"   指定群组 ID: {group_id}")
    
    results = start_chat_for_accounts(token, account_ids, group_id)
    
    # 统计结果
    success_count = sum(1 for v in results.values() if v)
    total_count = len(results)
    
    print()
    print("=" * 60)
    print("启动结果统计")
    print("=" * 60)
    print(f"成功: {success_count}/{total_count}")
    print(f"失败: {total_count - success_count}/{total_count}")
    print()
    
    if success_count == total_count:
        print("✅ 所有账号聊天已成功启动")
        return 0
    else:
        print("⚠️  部分账号启动失败，请检查日志")
        return 1

if __name__ == "__main__":
    exit(main())

