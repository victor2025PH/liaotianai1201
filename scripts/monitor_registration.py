#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
监控 Telegram 注册流程的日志和状态
"""
import requests
import json
import time
from datetime import datetime

API_BASE = "http://localhost:8000/api/v1"
LOGIN_URL = f"{API_BASE}/auth/login"
REGISTRATION_STATUS_URL = f"{API_BASE}/telegram-registration/status"

def get_auth_token():
    """获取认证 token"""
    response = requests.post(
        LOGIN_URL,
        data={"username": "admin@example.com", "password": "changeme123"}
    )
    if response.status_code == 200:
        return response.json()["access_token"]
    return None

def monitor_registration(registration_id: str, token: str):
    """监控注册状态"""
    headers = {"Authorization": f"Bearer {token}"}
    
    print(f"\n{'='*60}")
    print(f"开始监控注册流程: {registration_id}")
    print(f"{'='*60}\n")
    
    last_status = None
    check_count = 0
    
    while True:
        try:
            response = requests.get(
                f"{REGISTRATION_STATUS_URL}/{registration_id}",
                headers=headers,
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                current_status = data.get("status")
                check_count += 1
                
                # 只在状态变化时打印
                if current_status != last_status:
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    print(f"\n[{timestamp}] 状态变化:")
                    print(f"   状态: {current_status}")
                    print(f"   手机号: {data.get('phone')}")
                    print(f"   服务器: {data.get('node_id')}")
                    
                    if data.get("phone_code_hash"):
                        print(f"   Phone Code Hash: {data.get('phone_code_hash')}")
                    
                    if data.get("error_message"):
                        print(f"   错误: {data.get('error_message')}")
                    
                    if data.get("mock_mode"):
                        print(f"   模拟模式: True")
                        print(f"   模拟验证码: {data.get('mock_code')}")
                    
                    last_status = current_status
                
                # 如果状态是 completed 或 failed，停止监控
                if current_status in ["completed", "failed"]:
                    print(f"\n注册流程结束，状态: {current_status}")
                    break
            else:
                print(f"获取状态失败: {response.status_code}")
                
        except Exception as e:
            print(f"监控错误: {e}")
        
        time.sleep(3)  # 每3秒检查一次

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("用法: python monitor_registration.py <registration_id>")
        print("或者: python monitor_registration.py latest  # 监控最新的注册")
        sys.exit(1)
    
    token = get_auth_token()
    if not token:
        print("获取认证 token 失败")
        sys.exit(1)
    
    registration_id = sys.argv[1]
    
    if registration_id == "latest":
        # 获取最新的注册记录（这里简化处理，使用已知的 ID）
        registration_id = "dfbf5a49-bfc0-43d8-a3a9-50b61ca61f65"
    
    monitor_registration(registration_id, token)

