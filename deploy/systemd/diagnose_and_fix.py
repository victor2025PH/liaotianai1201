#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
诊断并修复前端和后端无法访问的问题
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

def diagnose(ssh, server_ip):
    """诊断问题"""
    print("\n" + "=" * 50)
    print("诊断服务状态")
    print("=" * 50)
    
    # 1. 检查服务状态
    print("\n[1] 检查服务状态...")
    stdin, stdout, stderr = ssh.exec_command("systemctl is-active smart-tg-backend smart-tg-frontend")
    status = stdout.read().decode('utf-8').strip()
    print(f"服务状态:\n{status}")
    
    # 2. 检查端口监听
    print("\n[2] 检查端口监听...")
    stdin, stdout, stderr = ssh.exec_command("sudo netstat -tlnp 2>/dev/null | grep -E ':8000|:3000' || echo '端口未被占用'")
    ports = stdout.read().decode('utf-8').strip()
    print(f"端口状态:\n{ports}")
    
    # 3. 检查防火墙
    print("\n[3] 检查防火墙...")
    stdin, stdout, stderr = ssh.exec_command("sudo ufw status 2>/dev/null || sudo iptables -L -n | grep -E '8000|3000' || echo '防火墙检查完成'")
    firewall = stdout.read().decode('utf-8').strip()
    print(f"防火墙状态:\n{firewall}")
    
    # 4. 检查服务日志
    print("\n[4] 后端服务日志（最近20行）...")
    stdin, stdout, stderr = ssh.exec_command("sudo journalctl -u smart-tg-backend -n 20 --no-pager")
    backend_logs = stdout.read().decode('utf-8')
    print(backend_logs)
    
    print("\n[5] 前端服务日志（最近20行）...")
    stdin, stdout, stderr = ssh.exec_command("sudo journalctl -u smart-tg-frontend -n 20 --no-pager")
    frontend_logs = stdout.read().decode('utf-8')
    print(frontend_logs)
    
    # 5. 本地健康检查
    print("\n[6] 本地健康检查...")
    stdin, stdout, stderr = ssh.exec_command("curl -s http://localhost:8000/health 2>/dev/null || echo '后端本地不可访问'")
    backend_local = stdout.read().decode('utf-8').strip()
    print(f"后端本地: {backend_local}")
    
    stdin, stdout, stderr = ssh.exec_command("curl -s -o /dev/null -w '%{http_code}' http://localhost:3000 2>/dev/null || echo '000'")
    frontend_local = stdout.read().decode('utf-8').strip()
    print(f"前端本地: HTTP {frontend_local}")
    
    # 6. 外部访问测试
    print(f"\n[7] 外部访问测试...")
    stdin, stdout, stderr = ssh.exec_command(f"curl -s -o /dev/null -w '%{{http_code}}' http://{server_ip}:8000/health 2>/dev/null || echo '后端外部不可访问'")
    backend_external = stdout.read().decode('utf-8').strip()
    print(f"后端外部 ({server_ip}:8000): {backend_external}")
    
    stdin, stdout, stderr = ssh.exec_command(f"curl -s -o /dev/null -w '%{{http_code}}' http://{server_ip}:3000 2>/dev/null || echo '000'")
    frontend_external = stdout.read().decode('utf-8').strip()
    print(f"前端外部 ({server_ip}:3000): HTTP {frontend_external}")

def fix_services(ssh, deploy_dir, username, server_ip):
    """修复服务"""
    print("\n" + "=" * 50)
    print("修复服务")
    print("=" * 50)
    
    # 1. 确保服务文件正确
    print("\n[1] 修复服务文件...")
    
    # 后端服务
    backend_service = f"""[Unit]
Description=Smart TG Backend API Service
After=network.target

[Service]
Type=notify
User={username}
Group={username}
WorkingDirectory={deploy_dir}/admin-backend
Environment="PATH={deploy_dir}/admin-backend/.venv/bin:/usr/local/bin:/usr/bin:/bin"
Environment="PYTHONPATH={deploy_dir}:{deploy_dir}/admin-backend"
EnvironmentFile=-{deploy_dir}/admin-backend/.env
ExecStart={deploy_dir}/admin-backend/.venv/bin/gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000 --timeout 120 --access-logfile - --error-logfile -
Restart=on-failure
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
"""
    
    stdin, stdout, stderr = ssh.exec_command(f"cat > /tmp/smart-tg-backend.service << 'EOFBACKEND'\n{backend_service}EOFBACKEND")
    stdout.read()
    ssh.exec_command("sudo cp /tmp/smart-tg-backend.service /etc/systemd/system/smart-tg-backend.service")
    ssh.exec_command("sudo chmod 644 /etc/systemd/system/smart-tg-backend.service")
    
    # 前端服务
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
    
    ssh.exec_command("sudo systemctl daemon-reload")
    print("[OK] 服务文件已修复")
    
    # 2. 配置防火墙
    print("\n[2] 配置防火墙...")
    ssh.exec_command("sudo ufw allow 8000/tcp 2>/dev/null || true")
    ssh.exec_command("sudo ufw allow 3000/tcp 2>/dev/null || true")
    print("[OK] 防火墙规则已配置")
    
    # 3. 重启服务
    print("\n[3] 重启服务...")
    ssh.exec_command("sudo systemctl stop smart-tg-backend smart-tg-frontend")
    
    import time
    time.sleep(2)
    
    ssh.exec_command("sudo systemctl start smart-tg-backend")
    ssh.exec_command("sudo systemctl enable smart-tg-backend")
    
    time.sleep(5)
    
    ssh.exec_command("sudo systemctl start smart-tg-frontend")
    ssh.exec_command("sudo systemctl enable smart-tg-frontend")
    
    time.sleep(3)
    
    print("[OK] 服务已重启")
    
    # 4. 验证
    print("\n[4] 验证服务状态...")
    stdin, stdout, stderr = ssh.exec_command("systemctl is-active smart-tg-backend smart-tg-frontend")
    status = stdout.read().decode('utf-8').strip()
    print(f"服务状态:\n{status}")
    
    stdin, stdout, stderr = ssh.exec_command("sudo netstat -tlnp 2>/dev/null | grep -E ':8000|:3000' || echo '端口未被占用'")
    ports = stdout.read().decode('utf-8').strip()
    print(f"\n端口监听:\n{ports}")
    
    print("\n健康检查:")
    time.sleep(2)
    stdin, stdout, stderr = ssh.exec_command("curl -s http://localhost:8000/health 2>/dev/null || echo '后端不可访问'")
    backend_health = stdout.read().decode('utf-8').strip()
    print(f"后端: {backend_health}")
    
    stdin, stdout, stderr = ssh.exec_command("curl -s -o /dev/null -w '%{http_code}' http://localhost:3000 2>/dev/null || echo '000'")
    frontend_code = stdout.read().decode('utf-8').strip()
    print(f"前端: HTTP {frontend_code}")

def main():
    config = load_config()
    ssh = connect_server(config['host'], config['user'], config['password'])
    
    try:
        # 诊断
        diagnose(ssh, config['host'])
        
        # 修复
        fix_services(ssh, config['deploy_dir'], config['user'], config['host'])
        
        print("\n" + "=" * 50)
        print("修复完成！")
        print("=" * 50)
        print(f"\n访问地址:")
        print(f"  后端: http://{config['host']}:8000")
        print(f"  前端: http://{config['host']}:3000")
        print(f"  API 文档: http://{config['host']}:8000/docs")
        print(f"\n如果仍然无法访问，请检查:")
        print(f"  1. 云服务器安全组是否开放 8000 和 3000 端口")
        print(f"  2. 服务器防火墙配置")
        print(f"  3. 服务日志: sudo journalctl -u smart-tg-backend -f")
        
    finally:
        ssh.close()

if __name__ == "__main__":
    main()

