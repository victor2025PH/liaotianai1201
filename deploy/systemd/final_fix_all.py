#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
最终修复所有问题
"""

import json
import paramiko
import sys
import os
import tarfile
import tempfile
from pathlib import Path
from datetime import datetime

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

def upload_frontend_code(ssh, deploy_dir, project_root):
    """上传前端代码"""
    print("\n[1/5] 上传前端代码...")
    
    frontend_dir = project_root / "saas-demo"
    if not frontend_dir.exists():
        print("[ERROR] 本地前端目录不存在")
        return False
    
    # 检查 app 目录
    app_dir = frontend_dir / "src" / "app"
    if not app_dir.exists():
        print("[ERROR] 本地前端 app 目录不存在")
        return False
    
    # 使用 tar 打包并上传
    print("打包前端代码...")
    
    local_temp = tempfile.NamedTemporaryFile(delete=False, suffix='.tar.gz')
    local_temp.close()
    
    try:
        with tarfile.open(local_temp.name, 'w:gz') as tar:
            exclude_patterns = [
                '.git', '__pycache__', '*.pyc', '.venv', 'venv',
                '.env', '.env.local', '*.log', '.pytest_cache',
                'node_modules', '.next', 'dist', 'build', '.pytest_cache'
            ]
            
            for root, dirs, files in os.walk(frontend_dir):
                # 过滤目录
                dirs[:] = [d for d in dirs if not any(d.startswith(p) for p in exclude_patterns)]
                
                for file in files:
                    if any(file.endswith(p.replace('*', '')) for p in exclude_patterns):
                        continue
                    
                    file_path = Path(root) / file
                    arcname = Path("saas-demo") / file_path.relative_to(frontend_dir)
                    tar.add(file_path, arcname=arcname)
        
        print(f"[OK] 已打包: {os.path.getsize(local_temp.name) / 1024 / 1024:.2f} MB")
        
        # 上传 tar 包
        print("上传到服务器...")
        temp_tar = f"/tmp/frontend-{datetime.now().strftime('%Y%m%d-%H%M%S')}.tar.gz"
        sftp = ssh.open_sftp()
        sftp.put(local_temp.name, temp_tar)
        sftp.close()
        print("[OK] 上传完成")
        
        # 解压到目标目录
        print("解压到目标目录...")
        ssh.exec_command(f"mkdir -p {deploy_dir}")
        ssh.exec_command(f"tar -xzf {temp_tar} -C {deploy_dir}")
        
        import time
        time.sleep(2)
        
        # 验证上传
        stdin, stdout, stderr = ssh.exec_command(f"test -d {deploy_dir}/saas-demo/src/app && echo 'exists' || echo 'not_exists'")
        app_exists = stdout.read().decode('utf-8').strip()
        
        if app_exists == 'exists':
            print("[OK] 前端代码上传成功")
            ssh.exec_command(f"rm -f {temp_tar}")
            os.unlink(local_temp.name)
            return True
        else:
            print("[ERROR] src/app 目录不存在，上传可能失败")
            return False
            
    except Exception as e:
        print(f"[ERROR] 上传失败: {e}")
        if os.path.exists(local_temp.name):
            os.unlink(local_temp.name)
        return False

def create_backend_env(ssh, deploy_dir):
    """创建后端 .env 文件"""
    print("\n[2/5] 创建后端 .env 文件...")
    
    env_file = f"{deploy_dir}/admin-backend/.env"
    
    # 检查文件是否存在
    stdin, stdout, stderr = ssh.exec_command(f"test -f {env_file} && echo 'exists' || echo 'not_exists'")
    exists = stdout.read().decode('utf-8').strip()
    
    if exists == 'exists':
        print("[INFO] .env 文件已存在")
        return True
    
    # 创建基本 .env 文件
    env_content = """# 数据库配置
DATABASE_URL=sqlite:///./admin.db

# 安全密钥（请修改）
SECRET_KEY=your-secret-key-here-change-this-in-production-$(date +%s)
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Redis 配置（可选）
# REDIS_URL=redis://localhost:6379/0

# CORS 配置
CORS_ORIGINS=["http://localhost:3000","http://localhost:8000","http://165.154.254.99:3000","http://165.154.254.99:8000"]

# 环境
ENVIRONMENT=production
"""
    
    stdin, stdout, stderr = ssh.exec_command(f"cat > {env_file} << 'EOF'\n{env_content}EOF")
    stdout.read()
    print("[OK] .env 文件已创建")
    return True

def rebuild_frontend(ssh, deploy_dir):
    """重新构建前端"""
    print("\n[3/5] 重新构建前端...")
    
    frontend_dir = f"{deploy_dir}/saas-demo"
    
    # 清理旧的构建
    ssh.exec_command(f"rm -rf {frontend_dir}/.next")
    
    # 使用 nvm 重新构建
    build_cmd = f'''cd {frontend_dir} && \
export NVM_DIR="$HOME/.nvm" && \
[ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh" && \
nvm use 20 && \
npm run build 2>&1
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
        return False

def fix_and_start_services(ssh, deploy_dir, username):
    """修复并启动服务"""
    print("\n[4/5] 修复并启动服务...")
    
    # 修复后端服务文件
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
    
    # 修复前端服务文件
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
    
    # 重新加载 systemd
    ssh.exec_command("sudo systemctl daemon-reload")
    print("[OK] 服务文件已修复")
    
    # 启动服务
    print("启动服务...")
    ssh.exec_command("sudo systemctl stop smart-tg-backend smart-tg-frontend")
    
    ssh.exec_command("sudo systemctl start smart-tg-backend")
    ssh.exec_command("sudo systemctl enable smart-tg-backend")
    
    import time
    time.sleep(3)
    
    stdin, stdout, stderr = ssh.exec_command("sudo systemctl is-active smart-tg-backend")
    backend_status = stdout.read().decode('utf-8').strip()
    print(f"后端服务状态: {backend_status}")
    
    ssh.exec_command("sudo systemctl start smart-tg-frontend")
    ssh.exec_command("sudo systemctl enable smart-tg-frontend")
    
    time.sleep(3)
    
    stdin, stdout, stderr = ssh.exec_command("sudo systemctl is-active smart-tg-frontend")
    frontend_status = stdout.read().decode('utf-8').strip()
    print(f"前端服务状态: {frontend_status}")

def verify_deployment(ssh, server_ip):
    """验证部署"""
    print("\n[5/5] 验证部署...")
    
    import time
    time.sleep(3)
    
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
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent
    
    ssh = connect_server(config['host'], config['user'], config['password'])
    
    try:
        # 1. 上传前端代码
        upload_frontend_code(ssh, config['deploy_dir'], project_root)
        
        # 2. 创建后端 .env
        create_backend_env(ssh, config['deploy_dir'])
        
        # 3. 重新构建前端
        rebuild_frontend(ssh, config['deploy_dir'])
        
        # 4. 修复并启动服务
        fix_and_start_services(ssh, config['deploy_dir'], config['user'])
        
        # 5. 验证部署
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

