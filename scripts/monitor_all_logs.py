#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
监控所有日志：后端、前端、验证码验证流程
"""
import requests
import time
import json
from datetime import datetime
import sys

API_BASE = "http://localhost:8000/api/v1"
LOGIN_URL = f"{API_BASE}/auth/login"

def get_auth_token():
    """获取认证 token"""
    try:
        response = requests.post(
            LOGIN_URL,
            data={"username": "admin@example.com", "password": "changeme123"},
            timeout=5
        )
        if response.status_code == 200:
            return response.json()["access_token"]
    except Exception as e:
        print(f"获取 token 失败: {e}")
    return None

def monitor_registration(phone: str = None):
    """监控注册流程"""
    token = get_auth_token()
    if not token:
        print("无法获取认证 token，请检查后端服务是否运行")
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    
    print(f"\n{'='*60}")
    print(f"开始监控注册和验证流程")
    if phone:
        print(f"监控手机号: {phone}")
    print(f"{'='*60}\n")
    
    last_registrations = {}
    check_count = 0
    
    while True:
        try:
            # 获取最近的注册记录
            response = requests.get(
                f"{API_BASE}/telegram-registration/list",
                headers=headers,
                params={"limit": 10},
                timeout=5
            )
            
            if response.status_code == 200:
                registrations = response.json()
                
                # 如果指定了手机号，只监控该手机号
                if phone:
                    registrations = [r for r in registrations if phone in r.get('phone', '')]
                
                for reg in registrations:
                    reg_id = reg['id']
                    current_status = reg.get('status')
                    current_error = reg.get('error_message')
                    last_info = last_registrations.get(reg_id, {})
                    
                    # 状态或错误信息变化时打印
                    if (current_status != last_info.get('status') or 
                        current_error != last_info.get('error_message')):
                        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        print(f"\n[{timestamp}] 注册记录更新:")
                        print(f"   ID: {reg_id}")
                        print(f"   手机号: {reg.get('phone')}")
                        print(f"   状态: {current_status}")
                        print(f"   服务器: {reg.get('node_id', 'N/A')}")
                        print(f"   重试次数: {reg.get('retry_count', 0)}")
                        
                        if reg.get('phone_code_hash'):
                            hash_preview = reg['phone_code_hash'][:30] + "..." if len(reg['phone_code_hash']) > 30 else reg['phone_code_hash']
                            print(f"   Phone Code Hash: {hash_preview}")
                        
                        if current_error:
                            print(f"   ❌ 错误: {current_error}")
                        
                        # 获取详细状态
                        try:
                            status_response = requests.get(
                                f"{API_BASE}/telegram-registration/status/{reg_id}",
                                headers=headers,
                                timeout=5
                            )
                            if status_response.status_code == 200:
                                status_data = status_response.json()
                                if status_data.get('expires_at'):
                                    print(f"   过期时间: {status_data['expires_at']}")
                        except:
                            pass
                        
                        last_registrations[reg_id] = {
                            'status': current_status,
                            'error_message': current_error
                        }
            else:
                if check_count == 0:
                    print("等待注册记录...")
                check_count += 1
                
        except requests.exceptions.ConnectionError:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] 无法连接到后端服务，请检查后端是否运行")
        except Exception as e:
            print(f"监控错误: {e}")
        
        time.sleep(3)  # 每3秒检查一次

if __name__ == "__main__":
    phone = sys.argv[1] if len(sys.argv) > 1 else None
    monitor_registration(phone)

