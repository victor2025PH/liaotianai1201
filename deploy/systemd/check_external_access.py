#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查外部访问问题
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
        print("检查端口监听地址...")
        stdin, stdout, stderr = ssh.exec_command("sudo ss -tlnp | grep -E ':8000|:3000'")
        ports = stdout.read().decode('utf-8')
        print(ports)
        
        print("\n检查前端服务日志...")
        stdin, stdout, stderr = ssh.exec_command("sudo journalctl -u smart-tg-frontend -n 20 --no-pager")
        logs = stdout.read().decode('utf-8')
        for line in logs.split('\n'):
            if 'Local' in line or 'Network' in line or 'Ready' in line:
                print(f"  {line}")
        
        print(f"\n测试外部访问...")
        print(f"后端: http://{config['host']}:8000/health")
        print(f"前端: http://{config['host']}:3000")
        
        print("\n如果外部无法访问，请检查:")
        print("1. 云服务器安全组是否开放 8000 和 3000 端口")
        print("2. 服务器防火墙: sudo ufw status")
        print("3. 服务是否绑定到 0.0.0.0（而不是 127.0.0.1）")
        
    finally:
        ssh.close()

if __name__ == "__main__":
    main()

