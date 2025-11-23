#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查最近的注册记录和错误信息
"""
import requests
import json
from datetime import datetime

API_BASE = "http://localhost:8000/api/v1"
LOGIN_URL = f"{API_BASE}/auth/login"

def get_auth_token():
    """获取认证 token"""
    response = requests.post(
        LOGIN_URL,
        data={"username": "admin@example.com", "password": "changeme123"}
    )
    if response.status_code == 200:
        return response.json()["access_token"]
    return None

def check_recent_registrations(token: str):
    """检查最近的注册记录"""
    headers = {"Authorization": f"Bearer {token}"}
    
    # 获取最近的注册记录
    response = requests.get(
        f"{API_BASE}/telegram-registration/list",
        headers=headers,
        params={"limit": 10}
    )
    
    if response.status_code != 200:
        print(f"获取注册记录失败: {response.status_code}")
        return
    
    registrations = response.json()
    
    print(f"\n{'='*60}")
    print(f"最近的注册记录 (共 {len(registrations)} 条)")
    print(f"{'='*60}\n")
    
    for reg in registrations:
        print(f"注册 ID: {reg['id']}")
        print(f"手机号: {reg['phone']}")
        print(f"状态: {reg['status']}")
        print(f"服务器: {reg.get('node_id', 'N/A')}")
        print(f"API ID: {reg.get('api_id', 'N/A')}")
        print(f"创建时间: {reg.get('created_at', 'N/A')}")
        print(f"更新时间: {reg.get('updated_at', 'N/A')}")
        
        if reg.get('error_message'):
            print(f"❌ 错误信息: {reg['error_message']}")
        
        if reg.get('phone_code_hash'):
            print(f"Phone Code Hash: {reg['phone_code_hash']}")
        
        print(f"{'-'*60}\n")

if __name__ == "__main__":
    token = get_auth_token()
    if not token:
        print("获取认证 token 失败")
        exit(1)
    
    check_recent_registrations(token)

