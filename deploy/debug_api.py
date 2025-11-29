#!/usr/bin/env python3
"""
調試 API 路由問題
"""

import paramiko
import sys

SERVER = "165.154.233.55"
USERNAME = "ubuntu"
PASSWORD = "Along2025!!!"
PROJECT_DIR = "/home/ubuntu/liaotian"

def create_ssh_client():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(SERVER, username=USERNAME, password=PASSWORD, timeout=30)
    return client

def run_command(client, command, description=""):
    if description:
        print(f"\n>>> {description}")
    
    stdin, stdout, stderr = client.exec_command(command, timeout=120)
    exit_code = stdout.channel.recv_exit_status()
    
    output = stdout.read().decode('utf-8', errors='ignore')
    error = stderr.read().decode('utf-8', errors='ignore')
    
    if output:
        for line in output.strip().split('\n'):
            print(f"  {line}")
    if error:
        print(f"  (stderr) {error[:500]}")
    
    return exit_code == 0, output

def debug():
    client = None
    try:
        client = create_ssh_client()
        print("✓ SSH 連接成功!")
        
        # 檢查 API 路由文件
        run_command(client, f"cat {PROJECT_DIR}/admin-backend/app/api/__init__.py", "檢查 API 路由配置")
        
        # 檢查 workers.py 是否存在
        run_command(client, f"ls -la {PROJECT_DIR}/admin-backend/app/api/workers.py", "檢查 workers.py 文件")
        
        # 檢查後端日誌
        run_command(client, "sudo journalctl -u liaotian-backend -n 30 --no-pager | grep -i error", "檢查錯誤日誌")
        
        # 測試 openapi.json 中是否有 workers 端點
        run_command(client, "curl -s http://localhost:8000/openapi.json | grep -o 'workers' | head -5", "檢查 OpenAPI 中的 workers")
        
        return True
        
    except Exception as e:
        print(f"❌ 錯誤: {e}")
        return False
    finally:
        if client:
            client.close()

if __name__ == "__main__":
    debug()

