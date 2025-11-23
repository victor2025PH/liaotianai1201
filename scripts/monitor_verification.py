#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
实时监控验证码验证过程
"""
import requests
import time
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

def monitor_verification(phone: str):
    """监控验证过程"""
    token = get_auth_token()
    if not token:
        print("获取认证 token 失败")
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    
    print(f"\n{'='*60}")
    print(f"开始监控验证过程: {phone}")
    print(f"{'='*60}\n")
    
    last_status = None
    last_error = None
    check_count = 0
    
    while True:
        try:
            # 获取最近的注册记录
            response = requests.get(
                f"{API_BASE}/telegram-registration/list",
                headers=headers,
                params={"limit": 10}
            )
            
            if response.status_code == 200:
                registrations = response.json()
                target_regs = [r for r in registrations if phone in r.get('phone', '')]
                
                if target_regs:
                    reg = target_regs[0]  # 取最新的
                    current_status = reg.get('status')
                    current_error = reg.get('error_message')
                    check_count += 1
                    
                    # 状态变化时打印
                    if current_status != last_status or current_error != last_error:
                        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        print(f"\n[{timestamp}] 状态更新:")
                        print(f"   注册 ID: {reg['id']}")
                        print(f"   手机号: {reg['phone']}")
                        print(f"   状态: {current_status}")
                        print(f"   服务器: {reg.get('node_id', 'N/A')}")
                        print(f"   重试次数: {reg.get('retry_count', 0)}")
                        
                        if reg.get('phone_code_hash'):
                            hash_preview = reg['phone_code_hash'][:30] + "..." if len(reg['phone_code_hash']) > 30 else reg['phone_code_hash']
                            print(f"   Phone Code Hash: {hash_preview}")
                        
                        if current_error:
                            print(f"   ❌ 错误: {current_error}")
                        
                        # 获取详细状态
                        status_response = requests.get(
                            f"{API_BASE}/telegram-registration/status/{reg['id']}",
                            headers=headers
                        )
                        if status_response.status_code == 200:
                            status_data = status_response.json()
                            if status_data.get('expires_at'):
                                print(f"   过期时间: {status_data['expires_at']}")
                        
                        last_status = current_status
                        last_error = current_error
                    
                    # 如果状态是 completed 或 failed，继续监控一段时间
                    if current_status in ["completed", "failed"]:
                        if check_count > 3:  # 再监控3次后退出
                            print(f"\n验证流程结束，最终状态: {current_status}")
                            break
                else:
                    if check_count == 0:
                        print("等待注册记录出现...")
                    check_count += 1
            else:
                print(f"获取注册记录失败: {response.status_code}")
                
        except Exception as e:
            print(f"监控错误: {e}")
        
        time.sleep(2)  # 每2秒检查一次

if __name__ == "__main__":
    import sys
    
    phone = sys.argv[1] if len(sys.argv) > 1 else "+639542360349"
    monitor_verification(phone)

