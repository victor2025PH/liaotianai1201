#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复服务权限和配置问题
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
    print(f"连接服务器: {host}...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(host, username=user, password=password, timeout=10)
    print("[OK] 连接成功")
    return ssh

def fix_services(ssh, deploy_dir, username):
    """修复服务配置"""
    print("\n修复服务配置...")
    
    # 检查 gunicorn 路径
    print("检查 gunicorn 路径...")
    stdin, stdout, stderr = ssh.exec_command(f"test -f {deploy_dir}/admin-backend/.venv/bin/gunicorn && echo 'exists' || echo 'not_exists'")
    gunicorn_exists = stdout.read().decode('utf-8').strip()
    print(f"Gunicorn: {gunicorn_exists}")
    
    if gunicorn_exists == 'not_exists':
        print("Gunicorn 不存在，检查 Python 路径...")
        stdin, stdout, stderr = ssh.exec_command(f"ls -la {deploy_dir}/admin-backend/.venv/bin/ | grep python")
        python_files = stdout.read().decode('utf-8')
        print(python_files)
    
    # 检查 npm 路径
    print("检查 npm 路径...")
    stdin, stdout, stderr = ssh.exec_command("which npm")
    npm_path = stdout.read().decode('utf-8').strip()
    print(f"NPM 路径: {npm_path}")
    
    # 使用 nvm 的 npm
    stdin, stdout, stderr = ssh.exec_command('export NVM_DIR="$HOME/.nvm" && [ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh" && which npm')
    nvm_npm_path = stdout.read().decode('utf-8').strip()
    if nvm_npm_path:
        print(f"NVM NPM 路径: {nvm_npm_path}")
        npm_path = nvm_npm_path
    
    # 修复后端服务文件
    print("\n修复后端服务文件...")
    backend_service = f"""[Unit]
Description=Smart TG Backend API Service
After=network.target

[Service]
Type=notify
User={username}
Group={username}
WorkingDirectory={deploy_dir}/admin-backend
Environment="PATH={deploy_dir}/admin-backend/.venv/bin:/usr/local/bin:/usr/bin:/bin"
Environment="NVM_DIR=$HOME/.nvm"
Environment="[ -s \\"$NVM_DIR/nvm.sh\\" ] && . \\"$NVM_DIR/nvm.sh\\""
ExecStart={deploy_dir}/admin-backend/.venv/bin/gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000 --timeout 120 --access-logfile - --error-logfile -
Restart=on-failure
RestartSec=5
StandardOutput=journal
StandardError=journal
EnvironmentFile={deploy_dir}/admin-backend/.env

[Install]
WantedBy=multi-user.target
"""
    
    stdin, stdout, stderr = ssh.exec_command(f"cat > /tmp/smart-tg-backend.service << 'EOFBACKEND'\n{backend_service}EOFBACKEND")
    stdout.read()
    ssh.exec_command("sudo cp /tmp/smart-tg-backend.service /etc/systemd/system/smart-tg-backend.service")
    ssh.exec_command("sudo chmod 644 /etc/systemd/system/smart-tg-backend.service")
    print("[OK] 后端服务文件已更新")
    
    # 修复前端服务文件
    print("修复前端服务文件...")
    # 创建启动脚本
    start_script = f"""#!/bin/bash
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"
cd {deploy_dir}/saas-demo
npm start
"""
    
    stdin, stdout, stderr = ssh.exec_command(f"cat > /tmp/start-frontend.sh << 'EOFFRONTEND'\n{start_script}EOFFRONTEND")
    stdout.read()
    ssh.exec_command("chmod +x /tmp/start-frontend.sh")
    
    frontend_service = f"""[Unit]
Description=Smart TG Frontend Service (Next.js)
After=network.target smart-tg-backend.service

[Service]
Type=simple
User={username}
Group={username}
WorkingDirectory={deploy_dir}/saas-demo
Environment="PATH=/usr/local/bin:/usr/bin:/bin"
Environment="NVM_DIR=$HOME/.nvm"
EnvironmentFile={deploy_dir}/saas-demo/.env.local
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
    print("[OK] 前端服务文件已更新")
    
    # 修复目录权限
    print("\n修复目录权限...")
    ssh.exec_command(f"sudo chown -R {username}:{username} {deploy_dir}")
    ssh.exec_command(f"sudo chmod -R 755 {deploy_dir}")
    print("[OK] 目录权限已修复")
    
    # 重新加载 systemd
    print("重新加载 systemd...")
    ssh.exec_command("sudo systemctl daemon-reload")
    print("[OK] systemd 已重新加载")
    
    # 启动服务
    print("\n启动后端服务...")
    ssh.exec_command("sudo systemctl start smart-tg-backend")
    ssh.exec_command("sudo systemctl enable smart-tg-backend")
    
    stdin, stdout, stderr = ssh.exec_command("sleep 2 && sudo systemctl is-active smart-tg-backend")
    backend_status = stdout.read().decode('utf-8').strip()
    print(f"后端服务状态: {backend_status}")
    
    if backend_status != 'active':
        print("后端服务启动失败，查看日志:")
        stdin, stdout, stderr = ssh.exec_command("sudo journalctl -u smart-tg-backend -n 20 --no-pager")
        print(stdout.read().decode('utf-8'))
    
    print("\n启动前端服务...")
    ssh.exec_command("sudo systemctl start smart-tg-frontend")
    ssh.exec_command("sudo systemctl enable smart-tg-frontend")
    
    stdin, stdout, stderr = ssh.exec_command("sleep 2 && sudo systemctl is-active smart-tg-frontend")
    frontend_status = stdout.read().decode('utf-8').strip()
    print(f"前端服务状态: {frontend_status}")
    
    if frontend_status != 'active':
        print("前端服务启动失败，查看日志:")
        stdin, stdout, stderr = ssh.exec_command("sudo journalctl -u smart-tg-frontend -n 20 --no-pager")
        print(stdout.read().decode('utf-8'))
    
    # 最终状态检查
    print("\n最终服务状态:")
    stdin, stdout, stderr = ssh.exec_command("systemctl is-active smart-tg-backend smart-tg-frontend")
    print(stdout.read().decode('utf-8'))
    
    print("\n健康检查:")
    stdin, stdout, stderr = ssh.exec_command("sleep 3 && curl -s http://localhost:8000/health || echo '后端不可访问'")
    print(f"后端: {stdout.read().decode('utf-8').strip()}")
    
    stdin, stdout, stderr = ssh.exec_command("curl -s -o /dev/null -w '%{http_code}' http://localhost:3000 || echo '前端不可访问'")
    print(f"前端: HTTP {stdout.read().decode('utf-8').strip()}")

def main():
    config = load_config()
    ssh = connect_server(config['host'], config['user'], config['password'])
    
    try:
        fix_services(ssh, config['deploy_dir'], config['user'])
    finally:
        ssh.close()

if __name__ == "__main__":
    main()

