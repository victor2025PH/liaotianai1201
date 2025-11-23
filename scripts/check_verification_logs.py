#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查验证码验证日志
"""
import requests
import json

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

def check_registration(token: str, phone: str):
    """检查指定手机号的注册记录"""
    headers = {"Authorization": f"Bearer {token}"}
    
    # 获取最近的注册记录
    response = requests.get(
        f"{API_BASE}/telegram-registration/list",
        headers=headers,
        params={"limit": 20}
    )
    
    if response.status_code != 200:
        print(f"获取注册记录失败: {response.status_code}")
        return
    
    registrations = response.json()
    
    # 查找匹配的手机号
    target_regs = [r for r in registrations if phone in r.get('phone', '')]
    
    if not target_regs:
        print(f"未找到手机号 {phone} 的注册记录")
        return
    
    for reg in target_regs:
        print(f"\n{'='*60}")
        print(f"注册记录详情")
        print(f"{'='*60}")
        print(f"ID: {reg['id']}")
        print(f"手机号: {reg['phone']}")
        print(f"状态: {reg['status']}")
        print(f"服务器: {reg.get('node_id', 'N/A')}")
        print(f"API ID: {reg.get('api_id', 'N/A')}")
        print(f"Phone Code Hash: {reg.get('phone_code_hash', 'N/A')}")
        print(f"Session Name: {reg.get('session_name', 'N/A')}")
        print(f"创建时间: {reg.get('created_at', 'N/A')}")
        print(f"更新时间: {reg.get('updated_at', 'N/A')}")
        print(f"重试次数: {reg.get('retry_count', 0)}")
        
        if reg.get('error_message'):
            print(f"\n❌ 错误信息:")
            print(f"   {reg['error_message']}")
        
        # 获取详细状态
        status_response = requests.get(
            f"{API_BASE}/telegram-registration/status/{reg['id']}",
            headers=headers
        )
        if status_response.status_code == 200:
            status_data = status_response.json()
            print(f"\n详细状态:")
            print(json.dumps(status_data, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    import sys
    
    phone = sys.argv[1] if len(sys.argv) > 1 else "+639542360349"
    
    token = get_auth_token()
    if not token:
        print("获取认证 token 失败")
        exit(1)
    
    check_registration(token, phone)

