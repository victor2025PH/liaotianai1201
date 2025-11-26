#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复服务配置并重新构建前端
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

def fix_backend_service(ssh, deploy_dir, username):
    """修复后端服务配置"""
    print("\n修复后端服务配置...")
    
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
EnvironmentFile={deploy_dir}/admin-backend/.env
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
    ssh.exec_command("sudo systemctl daemon-reload")
    print("[OK] 后端服务文件已修复")

def rebuild_frontend_with_logs(ssh, deploy_dir):
    """重新构建前端并显示详细日志"""
    print("\n重新构建前端...")
    
    frontend_dir = f"{deploy_dir}/saas-demo"
    
    # 清理旧的构建
    print("清理旧的构建...")
    ssh.exec_command(f"rm -rf {frontend_dir}/.next")
    
    # 使用 nvm 重新构建，并捕获所有输出
    build_cmd = f'''cd {frontend_dir} && \
export NVM_DIR="$HOME/.nvm" && \
[ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh" && \
nvm use 20 && \
npm run build 2>&1
'''
    
    print("执行构建（显示详细输出）...")
    stdin, stdout, stderr = ssh.exec_command(build_cmd, timeout=600)
    
    # 读取所有输出
    output_lines = []
    error_lines = []
    
    while True:
        line = stdout.readline()
        if not line:
            break
        line = line.rstrip()
        output_lines.append(line)
        print(f"  {line}")
        if 'error' in line.lower() or 'Error' in line or 'ERROR' in line:
            error_lines.append(line)
    
    # 读取错误输出
    error_output = stderr.read().decode('utf-8')
    if error_output:
        print("\n错误输出:")
        print(error_output)
        error_lines.extend(error_output.split('\n'))
    
    # 检查构建结果
    stdin, stdout, stderr = ssh.exec_command(f"test -f {frontend_dir}/.next/BUILD_ID && echo 'success' || echo 'failed'")
    result = stdout.read().decode('utf-8').strip()
    
    if result == 'success':
        print("\n[OK] 前端构建成功")
        return True
    else:
        print("\n[ERROR] 前端构建失败")
        if error_lines:
            print("\n关键错误信息:")
            for line in error_lines[-20:]:
                if line.strip():
                    print(f"  {line}")
        return False

def start_services(ssh):
    """启动服务"""
    print("\n启动服务...")
    
    # 停止现有服务
    ssh.exec_command("sudo systemctl stop smart-tg-backend smart-tg-frontend")
    
    # 启动后端
    print("启动后端服务...")
    ssh.exec_command("sudo systemctl start smart-tg-backend")
    ssh.exec_command("sudo systemctl enable smart-tg-backend")
    
    import time
    time.sleep(3)
    
    stdin, stdout, stderr = ssh.exec_command("sudo systemctl is-active smart-tg-backend")
    backend_status = stdout.read().decode('utf-8').strip()
    print(f"后端服务状态: {backend_status}")
    
    if backend_status != 'active':
        print("后端服务日志:")
        stdin, stdout, stderr = ssh.exec_command("sudo journalctl -u smart-tg-backend -n 30 --no-pager")
        print(stdout.read().decode('utf-8'))
    else:
        print("[OK] 后端服务已启动")
    
    # 启动前端
    print("启动前端服务...")
    ssh.exec_command("sudo systemctl start smart-tg-frontend")
    ssh.exec_command("sudo systemctl enable smart-tg-frontend")
    
    time.sleep(3)
    
    stdin, stdout, stderr = ssh.exec_command("sudo systemctl is-active smart-tg-frontend")
    frontend_status = stdout.read().decode('utf-8').strip()
    print(f"前端服务状态: {frontend_status}")
    
    if frontend_status != 'active':
        print("前端服务日志:")
        stdin, stdout, stderr = ssh.exec_command("sudo journalctl -u smart-tg-frontend -n 30 --no-pager")
        print(stdout.read().decode('utf-8'))
    else:
        print("[OK] 前端服务已启动")
    
    return backend_status == 'active' and frontend_status == 'active'

def verify_deployment(ssh, server_ip):
    """验证部署"""
    print("\n验证部署...")
    
    import time
    time.sleep(2)
    
    # 检查服务状态
    print("服务状态:")
    stdin, stdout, stderr = ssh.exec_command("systemctl is-active smart-tg-backend smart-tg-frontend")
    status = stdout.read().decode('utf-8').strip()
    print(status)
    
    # 健康检查
    print("\n健康检查:")
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
        # 1. 修复后端服务配置
        fix_backend_service(ssh, config['deploy_dir'], config['user'])
        
        # 2. 重新构建前端
        rebuild_frontend_with_logs(ssh, config['deploy_dir'])
        
        # 3. 启动服务
        start_services(ssh)
        
        # 4. 验证部署
        verify_deployment(ssh, config['host'])
        
        print("\n" + "=" * 50)
        print("部署完成！")
        print("=" * 50)
        print(f"\n访问地址:")
        print(f"  后端: http://{config['host']}:8000")
        print(f"  前端: http://{config['host']}:3000")
        print(f"  API 文档: http://{config['host']}:8000/docs")
        
    finally:
        ssh.close()

if __name__ == "__main__":
    main()

