#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查后端服务状态
"""

import json
import paramiko
import sys
from pathlib import Path

# 设置 Windows 控制台编码
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

def load_config():
    """加载服务器配置"""
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent
    config_path = project_root / "data" / "master_config.json"
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    servers = config.get('servers', {})
    server_name = list(servers.keys())[0]
    server_config = servers[server_name]
    
    return {
        'host': server_config['host'],
        'user': server_config.get('user', 'ubuntu'),
        'password': server_config.get('password', ''),
        'deploy_dir': server_config.get('deploy_dir', '/opt/smart-tg')
    }

def connect_server(host, user, password):
    """连接服务器"""
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(host, username=user, password=password, timeout=10)
    return ssh

def main():
    config = load_config()
    ssh = connect_server(config['host'], config['user'], config['password'])
    
    try:
        print("后端服务状态:")
        stdin, stdout, stderr = ssh.exec_command("sudo systemctl status smart-tg-backend --no-pager -l")
        print(stdout.read().decode('utf-8'))
        
        print("\n后端服务最新日志:")
        stdin, stdout, stderr = ssh.exec_command("sudo journalctl -u smart-tg-backend -n 50 --no-pager")
        print(stdout.read().decode('utf-8'))
        
        print("\n前端服务状态:")
        stdin, stdout, stderr = ssh.exec_command("sudo systemctl status smart-tg-frontend --no-pager -l")
        print(stdout.read().decode('utf-8'))
        
        print("\n健康检查:")
        stdin, stdout, stderr = ssh.exec_command("curl -s http://localhost:8000/health 2>/dev/null || echo '后端不可访问'")
        print(f"后端: {stdout.read().decode('utf-8').strip()}")
        
        stdin, stdout, stderr = ssh.exec_command("curl -s -o /dev/null -w '%{http_code}' http://localhost:3000 2>/dev/null || echo '000'")
        print(f"前端: HTTP {stdout.read().decode('utf-8').strip()}")
        
    finally:
        ssh.close()

if __name__ == "__main__":
    main()

