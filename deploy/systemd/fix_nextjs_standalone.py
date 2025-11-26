#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复 Next.js standalone 模式启动问题
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
    print(f"连接服务器: {host}...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(host, username=user, password=password, timeout=10)
    print("[OK] 连接成功")
    return ssh

def main():
    config = load_config()
    ssh = connect_server(config['host'], config['user'], config['password'])
    
    try:
        deploy_dir = config['deploy_dir']
        frontend_dir = f"{deploy_dir}/saas-demo"
        username = config['user']
        
        # 检查 standalone 目录是否存在
        print("\n检查 standalone 构建...")
        stdin, stdout, stderr = ssh.exec_command(f"test -d {frontend_dir}/.next/standalone && echo 'exists' || echo 'not_exists'")
        standalone_exists = stdout.read().decode('utf-8').strip()
        print(f"standalone 目录: {standalone_exists}")
        
        if standalone_exists == 'exists':
            print("\n使用 standalone 模式启动...")
            # 使用 standalone 服务器启动
            start_script = f"""#!/bin/bash
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"
cd {frontend_dir}
# 使用 standalone 服务器，绑定到 0.0.0.0
PORT=3000 HOSTNAME=0.0.0.0 node .next/standalone/server.js
"""
        else:
            print("\n使用标准模式启动...")
            # 使用标准 next start，但确保绑定到 0.0.0.0
            start_script = f"""#!/bin/bash
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"
cd {frontend_dir}
# 使用 next start，绑定到 0.0.0.0
PORT=3000 HOSTNAME=0.0.0.0 npm start
"""
        
        print("更新启动脚本...")
        stdin, stdout, stderr = ssh.exec_command(f"cat > /tmp/start-frontend.sh << 'EOFFRONTEND'\n{start_script}EOFFRONTEND")
        stdout.read()
        ssh.exec_command("chmod +x /tmp/start-frontend.sh")
        print("[OK] 启动脚本已更新")
        
        # 更新服务文件
        print("更新服务文件...")
        frontend_service = f"""[Unit]
Description=Smart TG Frontend Service (Next.js)
After=network.target smart-tg-backend.service

[Service]
Type=simple
User={username}
Group={username}
WorkingDirectory={frontend_dir}
Environment="PATH=/usr/local/bin:/usr/bin:/bin"
Environment="NVM_DIR=$HOME/.nvm"
Environment="PORT=3000"
Environment="HOSTNAME=0.0.0.0"
EnvironmentFile={frontend_dir}/.env.local
ExecStart=/bin/bash /tmp/start-frontend.sh
Restart=on-failure
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
"""
        
        stdin, stdout, stderr = ssh.exec_command(f"cat > /tmp/smart-tg-frontend.service << 'EOFFRONTEND'\n{frontend_service}EOFFRONTEND")
        stdout.read()
        ssh.exec_command("sudo cp /tmp/smart-tg-frontend.service /etc/systemd/system/smart-tg-frontend.service")
        ssh.exec_command("sudo chmod 644 /etc/systemd/system/smart-tg-frontend.service")
        ssh.exec_command("sudo systemctl daemon-reload")
        print("[OK] 服务文件已更新")
        
        # 重启服务
        print("\n重启前端服务...")
        ssh.exec_command("sudo systemctl stop smart-tg-frontend")
        time.sleep(2)
        ssh.exec_command("sudo systemctl start smart-tg-frontend")
        
        print("等待服务启动...")
        time.sleep(8)
        
        # 验证
        print("\n验证服务状态...")
        stdin, stdout, stderr = ssh.exec_command("sudo systemctl is-active smart-tg-frontend")
        status = stdout.read().decode('utf-8').strip()
        print(f"服务状态: {status}")
        
        stdin, stdout, stderr = ssh.exec_command("sudo ss -tlnp | grep :3000")
        ports = stdout.read().decode('utf-8').strip()
        if ports:
            print(f"端口监听:\n{ports}")
        
        print("\n检查服务日志...")
        stdin, stdout, stderr = ssh.exec_command("sudo journalctl -u smart-tg-frontend -n 15 --no-pager")
        logs = stdout.read().decode('utf-8')
        for line in logs.split('\n'):
            if 'Local' in line or 'Network' in line or 'Ready' in line or 'Error' in line or 'error' in line:
                print(f"  {line}")
        
        time.sleep(2)
        print("\n健康检查:")
        stdin, stdout, stderr = ssh.exec_command("curl -s -o /dev/null -w '%{http_code}' http://localhost:3000 2>/dev/null || echo '000'")
        local_code = stdout.read().decode('utf-8').strip()
        print(f"本地访问: HTTP {local_code}")
        
        print("\n" + "=" * 50)
        print("修复完成！")
        print("=" * 50)
        print(f"\n访问地址:")
        print(f"  后端: http://{config['host']}:8000")
        print(f"  前端: http://{config['host']}:3000")
        print(f"\n如果仍然无法访问，请:")
        print(f"  1. 检查云服务器安全组是否开放 3000 端口（TCP）")
        print(f"  2. 等待 10-20 秒让服务完全启动")
        print(f"  3. 清除浏览器缓存并重试")
        
    finally:
        ssh.close()

if __name__ == "__main__":
    main()

