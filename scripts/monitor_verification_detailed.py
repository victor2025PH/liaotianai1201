#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
详细监控验证码验证过程
"""
import requests
import json
import time
from datetime import datetime
from typing import Optional

BASE_URL = "http://localhost:8000/api/v1"
USERNAME = "admin@example.com"
PASSWORD = "changeme123"

def login() -> str:
    """登录获取token"""
    response = requests.post(
        f"{BASE_URL}/auth/login",
        data={"username": USERNAME, "password": PASSWORD}
    )
    response.raise_for_status()
    return response.json()["access_token"]

def get_registration_details(token: str, registration_id: str) -> dict:
    """获取注册详情"""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(
        f"{BASE_URL}/telegram-registration/{registration_id}",
        headers=headers
    )
    response.raise_for_status()
    return response.json()

def monitor_registration(token: str, phone: str):
    """监控注册过程"""
    headers = {"Authorization": f"Bearer {token}"}
    
    print("=" * 80)
    print("验证码验证过程详细监控")
    print("=" * 80)
    print(f"监控手机号: {phone}")
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    print()
    
    last_registration_id = None
    last_phone_code_hash = None
    last_status = None
    
    while True:
        try:
            # 获取所有注册记录
            response = requests.get(
                f"{BASE_URL}/telegram-registration/list",
                headers=headers,
                params={"limit": 10}
            )
            response.raise_for_status()
            registrations = response.json()
            
            # 查找匹配的注册记录
            matching_regs = [
                r for r in registrations 
                if r.get('phone') == phone or r.get('phone') == phone.replace('+', '')
            ]
            
            if matching_regs:
                reg = matching_regs[0]  # 取最新的
                reg_id = reg['id']
                
                # 获取详细信息
                details = get_registration_details(token, reg_id)
                
                current_hash = details.get('phone_code_hash')
                current_status = details.get('status')
                current_updated = details.get('updated_at')
                
                # 检测变化
                if reg_id != last_registration_id:
                    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 🔍 发现新注册记录")
                    print(f"   注册ID: {reg_id}")
                    print(f"   手机号: {details.get('phone')}")
                    print(f"   状态: {current_status}")
                    print(f"   服务器: {details.get('node_id')}")
                    last_registration_id = reg_id
                
                if current_hash != last_phone_code_hash:
                    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 🔑 Phone Code Hash 变化")
                    print(f"   旧Hash: {last_phone_code_hash}")
                    print(f"   新Hash: {current_hash}")
                    last_phone_code_hash = current_hash
                
                if current_status != last_status:
                    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 📊 状态变化")
                    print(f"   旧状态: {last_status}")
                    print(f"   新状态: {current_status}")
                    if details.get('error_message'):
                        print(f"   错误信息: {details.get('error_message')}")
                    last_status = current_status
                
                # 如果状态是 code_sent，显示详细信息
                if current_status == 'code_sent':
                    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] ✅ 验证码已发送")
                    print(f"   Phone Code Hash: {current_hash}")
                    print(f"   更新时间: {current_updated}")
                    if details.get('expires_at'):
                        print(f"   过期时间: {details.get('expires_at')}")
                
                # 如果状态是 failed，显示错误
                if current_status == 'failed':
                    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] ❌ 注册失败")
                    print(f"   错误信息: {details.get('error_message')}")
                    print(f"   重试次数: {details.get('retry_count', 0)}")
                    print(f"   使用的 Hash: {current_hash}")
                
                # 如果状态是 completed，显示成功信息
                if current_status == 'completed':
                    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 🎉 注册成功")
                    if details.get('session_file'):
                        print(f"   Session文件: {details.get('session_file', {}).get('file_path')}")
                    break
            else:
                if last_registration_id:
                    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] ⚠️  注册记录未找到")
            
            time.sleep(2)
            
        except KeyboardInterrupt:
            print("\n\n监控已停止")
            break
        except Exception as e:
            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] ❌ 监控错误: {e}")
            time.sleep(5)

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("用法: python monitor_verification_detailed.py <phone>")
        print("示例: python monitor_verification_detailed.py +639542360349")
        sys.exit(1)
    
    phone = sys.argv[1]
    
    try:
        token = login()
        print("✅ 登录成功")
        monitor_registration(token, phone)
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()

