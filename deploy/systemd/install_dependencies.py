#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
安装后端缺失的依赖
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
        deploy_dir = config['deploy_dir']
        backend_dir = f"{deploy_dir}/admin-backend"
        
        print("安装后端依赖...")
        install_cmd = f'''cd {backend_dir} && \
source .venv/bin/activate && \
pip install -r requirements.txt
'''
        
        stdin, stdout, stderr = ssh.exec_command(install_cmd, timeout=600)
        
        # 实时输出
        while True:
            line = stdout.readline()
            if not line:
                break
            print(f"  {line.rstrip()}")
        
        print("\n[OK] 依赖安装完成")
        
        # 重启服务
        print("\n重启后端服务...")
        ssh.exec_command("sudo systemctl restart smart-tg-backend")
        
        import time
        time.sleep(5)
        
        stdin, stdout, stderr = ssh.exec_command("sudo systemctl is-active smart-tg-backend")
        status = stdout.read().decode('utf-8').strip()
        print(f"后端服务状态: {status}")
        
        if status == 'active':
            print("[OK] 后端服务已启动")
            
            # 健康检查
            print("\n健康检查:")
            stdin, stdout, stderr = ssh.exec_command("sleep 2 && curl -s http://localhost:8000/health 2>/dev/null || echo '后端不可访问'")
            health = stdout.read().decode('utf-8').strip()
            print(f"后端: {health}")
        else:
            print("\n后端服务日志:")
            stdin, stdout, stderr = ssh.exec_command("sudo journalctl -u smart-tg-backend -n 30 --no-pager")
            print(stdout.read().decode('utf-8'))
        
    finally:
        ssh.close()

if __name__ == "__main__":
    main()

