#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查验证状态和服务器连接
"""
import requests
import json
import sys
from datetime import datetime

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
        print(f"Login failed: {e}")
        return None

def check_server_connection():
    """检查服务器连接"""
    print("=" * 80)
    print("Checking Server Connections")
    print("=" * 80)
    
    try:
        import json
        from pathlib import Path
        
        config_path = Path("data/master_config.json")
        if not config_path.exists():
            print("ERROR: Server config file not found: data/master_config.json")
            return False
        
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        servers = config.get('servers', {})
        if not servers:
            print("ERROR: No server configurations found")
            return False
        
        print(f"Found {len(servers)} server configurations")
        print()
        
        for node_id, server_config in servers.items():
            host = server_config.get('host', '')
            user = server_config.get('user', 'ubuntu')
            
            print(f"Server: {node_id}")
            print(f"  Host: {host}")
            print(f"  User: {user}")
            
            # Try SSH connection
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
                print(f"  OK: SSH connection successful")
                
                # Check verification scripts
                stdin, stdout, stderr = ssh.exec_command(
                    "ls -lt /tmp/verify_session_*.py 2>/dev/null | head -5"
                )
                scripts = stdout.read().decode('utf-8').strip()
                if scripts:
                    print(f"  Recent verification scripts:")
                    for line in scripts.split('\n')[:3]:
                        if line.strip():
                            print(f"    {line.strip()}")
                
                # Check script execution logs
                stdin, stdout, stderr = ssh.exec_command(
                    "tail -20 /tmp/verify_session_*.log 2>/dev/null | head -20"
                )
                logs = stdout.read().decode('utf-8').strip()
                if logs:
                    print(f"  Recent script logs:")
                    for line in logs.split('\n')[:5]:
                        if line.strip():
                            print(f"    {line.strip()}")
                
                ssh.close()
            except ImportError:
                print(f"  WARNING: paramiko not installed, cannot test SSH")
            except Exception as e:
                print(f"  ERROR: SSH connection failed: {e}")
            
            print()
        
        return True
    except Exception as e:
        print(f"ERROR: Failed to check server connections: {e}")
        import traceback
        traceback.print_exc()
        return False

def get_registration_by_phone(token, phone):
    """通过手机号获取注册记录"""
    headers = {"Authorization": f"Bearer {token}"}
    
    # 尝试通过 API 获取（如果有 list 接口）
    # 否则需要通过数据库查询
    
    # 先尝试获取最近的注册记录
    try:
        # 这里需要根据实际 API 调整
        # 假设有一个查询接口
        response = requests.get(
            f"{BASE_URL}/telegram-registration/status/dummy",  # 占位符
            headers=headers,
            timeout=5
        )
    except:
        pass
    
    return None

def check_verification_status(phone=None):
    """检查验证状态"""
    print("=" * 80)
    print("Verification Status Check")
    print("=" * 80)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    if phone:
        print(f"Phone: {phone}")
    print("=" * 80)
    print()
    
    token = login()
    if not token:
        print("ERROR: Failed to login")
        return
    
    print("OK: Login successful")
    print()
    
    # Check server connections
    check_server_connection()
    print()
    
    # Try to get logs via API
    print("=" * 80)
    print("Recent Verification Logs (via API)")
    print("=" * 80)
    
    headers = {"Authorization": f"Bearer {token}"}
    try:
        response = requests.get(
            f"{BASE_URL}/group-ai/logs",
            headers=headers,
            params={"q": "remote verification", "page_size": 20},
            timeout=10
        )
        if response.status_code == 200:
            logs_data = response.json()
            if logs_data.get('items'):
                logs = logs_data['items']
                print(f"Found {len(logs)} related logs\n")
                for log in logs[:10]:
                    print(f"[{log.get('timestamp', '')}] {log.get('level', '')} - {log.get('message', '')}")
            else:
                print("No related logs found")
        else:
            print(f"API returned status {response.status_code}")
    except Exception as e:
        print(f"ERROR: Failed to get logs: {e}")
    
    print()
    print("=" * 80)
    print("Check Complete")
    print("=" * 80)

if __name__ == "__main__":
    phone = sys.argv[1] if len(sys.argv) > 1 else None
    check_verification_status(phone)

