#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
监控远程验证日志
"""
import requests
import json
import time
from datetime import datetime
import sys

BASE_URL = "http://localhost:8000/api/v1"
USERNAME = "admin@example.com"
PASSWORD = "changeme123"

def login():
    """登录获取token"""
    try:
        response = requests.post(
            f"{BASE_URL}/auth/login",
            data={"username": USERNAME, "password": PASSWORD},
            timeout=5
        )
        response.raise_for_status()
        return response.json()["access_token"]
    except Exception as e:
        print(f"❌ 登录失败: {e}")
        return None

def get_recent_logs(token, search_term="远程验证", limit=50):
    """获取最近的日志"""
    headers = {"Authorization": f"Bearer {token}"}
    try:
        response = requests.get(
            f"{BASE_URL}/group-ai/logs",
            headers=headers,
            params={"q": search_term, "page_size": limit},
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"❌ 获取日志失败: {e}")
        return None

def get_registration_details(token, registration_id):
    """获取注册详情"""
    headers = {"Authorization": f"Bearer {token}"}
    try:
        response = requests.get(
            f"{BASE_URL}/telegram-registration/status/{registration_id}",
            headers=headers,
            timeout=5
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"❌ 获取注册详情失败: {e}")
        return None

def check_server_connection():
    """检查服务器连接"""
    print("=" * 80)
    print("检查服务器连接")
    print("=" * 80)
    
    try:
        import json
        from pathlib import Path
        
        config_path = Path("data/master_config.json")
        if not config_path.exists():
            print("❌ 服务器配置文件不存在: data/master_config.json")
            return False
        
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        servers = config.get('servers', {})
        if not servers:
            print("❌ 未找到服务器配置")
            return False
        
        print(f"✅ 找到 {len(servers)} 个服务器配置")
        print()
        
        for node_id, server_config in servers.items():
            host = server_config.get('host', '')
            user = server_config.get('user', 'ubuntu')
            
            print(f"服务器: {node_id}")
            print(f"  主机: {host}")
            print(f"  用户: {user}")
            
            # 尝试 SSH 连接
            try:
                import paramiko
                ssh = paramiko.SSHClient()
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                ssh.connect(
                    host,
                    username=user,
                    password=server_config.get('password', ''),
                    timeout=5
                )
                print(f"  ✅ SSH 连接成功")
                
                # 检查验证脚本
                stdin, stdout, stderr = ssh.exec_command(
                    "ls -lt /tmp/verify_session_*.py 2>/dev/null | head -5"
                )
                scripts = stdout.read().decode('utf-8').strip()
                if scripts:
                    print(f"  📝 最近的验证脚本:")
                    for line in scripts.split('\n')[:3]:
                        if line.strip():
                            print(f"     {line.strip()}")
                else:
                    print(f"  ℹ️  未找到验证脚本")
                
                ssh.close()
            except ImportError:
                print(f"  ⚠️  paramiko 未安装，无法测试 SSH 连接")
            except Exception as e:
                print(f"  ❌ SSH 连接失败: {e}")
            
            print()
        
        return True
    except Exception as e:
        print(f"❌ 检查服务器连接失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def monitor_verification_logs(phone=None):
    """监控验证日志"""
    print("=" * 80)
    print("监控远程验证日志")
    print("=" * 80)
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    if phone:
        print(f"监控手机号: {phone}")
    print("=" * 80)
    print()
    
    token = login()
    if not token:
        return
    
    print("✅ 登录成功")
    print()
    
    # 检查服务器连接
    check_server_connection()
    print()
    
    # 获取最近的日志
    print("=" * 80)
    print("最近的远程验证日志")
    print("=" * 80)
    
    logs_data = get_recent_logs(token, search_term="远程验证", limit=30)
    if logs_data and logs_data.get('items'):
        logs = logs_data['items']
        print(f"找到 {len(logs)} 条相关日志\n")
        
        for log in logs[:20]:  # 只显示最近20条
            timestamp = log.get('timestamp', '')
            level = log.get('level', '')
            message = log.get('message', '')
            source = log.get('source', '')
            
            # 高亮显示错误
            if 'ERROR' in message or 'PhoneCodeExpired' in message or 'PhoneCodeInvalid' in message:
                print(f"❌ [{timestamp}] [{level}] {source}")
                print(f"   {message}")
            elif 'SUCCESS' in message or '验证成功' in message:
                print(f"✅ [{timestamp}] [{level}] {source}")
                print(f"   {message}")
            else:
                print(f"ℹ️  [{timestamp}] [{level}] {source}")
                print(f"   {message}")
            print()
    else:
        print("ℹ️  未找到相关日志")
        print("   可能原因:")
        print("   - 最近没有验证尝试")
        print("   - 日志系统未启用")
        print("   - 日志已被清理")
    
    print()
    print("=" * 80)
    print("监控完成")
    print("=" * 80)

if __name__ == "__main__":
    phone = sys.argv[1] if len(sys.argv) > 1 else None
    monitor_verification_logs(phone)

