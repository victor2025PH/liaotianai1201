#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
安装所有缺失的依赖并启动服务
"""

import json
import paramiko
import sys
import time
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
        
        # 安装所有可能缺失的依赖
        print("安装缺失的依赖...")
        deps = ['pyyaml', 'pyrogram']
        
        for dep in deps:
            print(f"\n安装 {dep}...")
            install_cmd = f"cd {backend_dir} && source .venv/bin/activate && pip install {dep}"
            stdin, stdout, stderr = ssh.exec_command(install_cmd, timeout=300)
            
            # 等待完成
            while True:
                line = stdout.readline()
                if not line:
                    break
                if 'Successfully installed' in line or 'Requirement already satisfied' in line:
                    print(f"  {line.rstrip()}")
        
        print("\n[OK] 依赖安装完成")
        
        # 重启后端服务
        print("\n重启后端服务...")
        ssh.exec_command("sudo systemctl stop smart-tg-backend")
        time.sleep(3)
        ssh.exec_command("sudo systemctl start smart-tg-backend")
        ssh.exec_command("sudo systemctl enable smart-tg-backend")
        
        # 等待启动
        print("等待服务启动...")
        time.sleep(8)
        
        # 检查状态
        print("\n检查服务状态...")
        stdin, stdout, stderr = ssh.exec_command("sudo systemctl is-active smart-tg-backend")
        backend_status = stdout.read().decode('utf-8').strip()
        print(f"后端服务状态: {backend_status}")
        
        if backend_status == 'active':
            print("[OK] 后端服务已启动")
        else:
            print("\n后端服务日志:")
            stdin, stdout, stderr = ssh.exec_command("sudo journalctl -u smart-tg-backend -n 40 --no-pager")
            print(stdout.read().decode('utf-8'))
        
        # 检查端口
        print("\n检查端口监听...")
        stdin, stdout, stderr = ssh.exec_command("sudo netstat -tlnp 2>/dev/null | grep -E ':8000|:3000' || ss -tlnp | grep -E ':8000|:3000'")
        ports = stdout.read().decode('utf-8').strip()
        if ports:
            print(f"端口监听:\n{ports}")
        else:
            print("端口未被占用")
        
        # 健康检查
        print("\n健康检查:")
        time.sleep(2)
        stdin, stdout, stderr = ssh.exec_command("curl -s http://localhost:8000/health 2>/dev/null || echo '后端不可访问'")
        backend_health = stdout.read().decode('utf-8').strip()
        print(f"后端: {backend_health}")
        
        stdin, stdout, stderr = ssh.exec_command("curl -s -o /dev/null -w '%{http_code}' http://localhost:3000 2>/dev/null || echo '000'")
        frontend_code = stdout.read().decode('utf-8').strip()
        print(f"前端: HTTP {frontend_code}")
        
        print("\n" + "=" * 50)
        print("完成！")
        print("=" * 50)
        print(f"\n访问地址:")
        print(f"  后端: http://{config['host']}:8000")
        print(f"  前端: http://{config['host']}:3000")
        print(f"  API 文档: http://{config['host']}:8000/docs")
        
    finally:
        ssh.close()

if __name__ == "__main__":
    main()

