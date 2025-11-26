#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
最终修复 - 检查代码完整性并重新构建
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

def check_backend_code(ssh, deploy_dir):
    """检查后端代码"""
    print("\n检查后端代码...")
    
    backend_dir = f"{deploy_dir}/admin-backend"
    
    # 检查 app 目录
    stdin, stdout, stderr = ssh.exec_command(f"test -d {backend_dir}/app && echo 'exists' || echo 'not_exists'")
    app_exists = stdout.read().decode('utf-8').strip()
    print(f"app 目录: {app_exists}")
    
    if app_exists == 'not_exists':
        print("[ERROR] app 目录不存在！后端代码可能未完整上传")
        print("请手动上传完整的后端代码到服务器")
        return False
    
    # 检查 app/main.py
    stdin, stdout, stderr = ssh.exec_command(f"test -f {backend_dir}/app/main.py && echo 'exists' || echo 'not_exists'")
    main_exists = stdout.read().decode('utf-8').strip()
    print(f"app/main.py: {main_exists}")
    
    if main_exists == 'not_exists':
        print("[ERROR] app/main.py 不存在！")
        return False
    
    # 列出 app 目录内容
    stdin, stdout, stderr = ssh.exec_command(f"ls -la {backend_dir}/app/ | head -20")
    app_files = stdout.read().decode('utf-8')
    print("app 目录内容:")
    print(app_files)
    
    return True

def rebuild_frontend(ssh, deploy_dir):
    """重新构建前端"""
    print("\n重新构建前端...")
    
    frontend_dir = f"{deploy_dir}/saas-demo"
    
    # 删除旧的构建
    print("清理旧的构建...")
    ssh.exec_command(f"rm -rf {frontend_dir}/.next")
    
    # 使用 nvm 重新构建
    build_cmd = f'''cd {frontend_dir} && \
export NVM_DIR="$HOME/.nvm" && \
[ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh" && \
nvm use 20 && \
npm run build
'''
    
    print("执行构建...")
    stdin, stdout, stderr = ssh.exec_command(build_cmd, timeout=600)
    
    # 实时输出
    while True:
        line = stdout.readline()
        if not line:
            break
        print(f"  {line.rstrip()}")
    
    # 检查构建结果
    stdin, stdout, stderr = ssh.exec_command(f"test -f {frontend_dir}/.next/BUILD_ID && echo 'success' || echo 'failed'")
    result = stdout.read().decode('utf-8').strip()
    
    if result == 'success':
        print("[OK] 前端构建成功")
        return True
    else:
        print("[ERROR] 前端构建失败")
        error_output = stderr.read().decode('utf-8')
        if error_output:
            print(f"错误: {error_output}")
        return False

def fix_backend_service(ssh, deploy_dir, username):
    """修复后端服务配置"""
    print("\n修复后端服务配置...")
    
    # 检查 Python 路径
    stdin, stdout, stderr = ssh.exec_command(f"{deploy_dir}/admin-backend/.venv/bin/python --version")
    python_version = stdout.read().decode('utf-8').strip()
    print(f"Python 版本: {python_version}")
    
    # 更新服务文件，使用正确的 Python 路径
    backend_service = f"""[Unit]
Description=Smart TG Backend API Service
After=network.target

[Service]
Type=notify
User={username}
Group={username}
WorkingDirectory={deploy_dir}/admin-backend
Environment="PATH={deploy_dir}/admin-backend/.venv/bin:/usr/local/bin:/usr/bin:/bin"
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
    print("[OK] 后端服务文件已更新")

def start_services(ssh):
    """启动服务"""
    print("\n启动服务...")
    
    # 启动后端
    print("启动后端服务...")
    ssh.exec_command("sudo systemctl start smart-tg-backend")
    ssh.exec_command("sudo systemctl enable smart-tg-backend")
    
    stdin, stdout, stderr = ssh.exec_command("sleep 3 && sudo systemctl is-active smart-tg-backend")
    backend_status = stdout.read().decode('utf-8').strip()
    print(f"后端服务状态: {backend_status}")
    
    if backend_status != 'active':
        print("后端服务日志:")
        stdin, stdout, stderr = ssh.exec_command("sudo journalctl -u smart-tg-backend -n 15 --no-pager")
        print(stdout.read().decode('utf-8'))
    
    # 启动前端
    print("启动前端服务...")
    ssh.exec_command("sudo systemctl start smart-tg-frontend")
    ssh.exec_command("sudo systemctl enable smart-tg-frontend")
    
    stdin, stdout, stderr = ssh.exec_command("sleep 3 && sudo systemctl is-active smart-tg-frontend")
    frontend_status = stdout.read().decode('utf-8').strip()
    print(f"前端服务状态: {frontend_status}")
    
    if frontend_status != 'active':
        print("前端服务日志:")
        stdin, stdout, stderr = ssh.exec_command("sudo journalctl -u smart-tg-frontend -n 15 --no-pager")
        print(stdout.read().decode('utf-8'))
    
    # 最终验证
    print("\n最终验证:")
    stdin, stdout, stderr = ssh.exec_command("systemctl is-active smart-tg-backend smart-tg-frontend")
    print(stdout.read().decode('utf-8'))
    
    print("\n健康检查:")
    stdin, stdout, stderr = ssh.exec_command("sleep 2 && curl -s http://localhost:8000/health || echo '后端不可访问'")
    print(f"后端: {stdout.read().decode('utf-8').strip()}")
    
    stdin, stdout, stderr = ssh.exec_command("curl -s -o /dev/null -w '%{http_code}' http://localhost:3000 || echo '前端不可访问'")
    print(f"前端: HTTP {stdout.read().decode('utf-8').strip()}")

def main():
    config = load_config()
    ssh = connect_server(config['host'], config['user'], config['password'])
    
    try:
        # 检查后端代码
        if not check_backend_code(ssh, config['deploy_dir']):
            print("\n[警告] 后端代码不完整，请先上传完整的后端代码")
            print("可以使用以下命令上传:")
            print(f"  scp -r admin-backend/* {config['user']}@{config['host']}:{config['deploy_dir']}/admin-backend/")
            return
        
        # 重新构建前端
        rebuild_frontend(ssh, config['deploy_dir'])
        
        # 修复后端服务
        fix_backend_service(ssh, config['deploy_dir'], config['user'])
        
        # 启动服务
        start_services(ssh)
        
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

