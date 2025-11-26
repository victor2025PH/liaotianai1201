#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复后端 .env 文件路径问题
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
        env_file = f"{deploy_dir}/admin-backend/.env"
        
        # 检查 .env 文件是否存在
        print("检查 .env 文件...")
        stdin, stdout, stderr = ssh.exec_command(f"test -f {env_file} && echo 'exists' || echo 'not_exists'")
        exists = stdout.read().decode('utf-8').strip()
        print(f".env 文件: {exists}")
        
        if exists == 'not_exists':
            print("创建 .env 文件...")
            env_content = """# 数据库配置
DATABASE_URL=sqlite:///./admin.db

# 安全密钥
SECRET_KEY=your-secret-key-here-change-this-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS 配置
CORS_ORIGINS=["http://localhost:3000","http://localhost:8000","http://165.154.254.99:3000","http://165.154.254.99:8000"]

# 环境
ENVIRONMENT=production
"""
            stdin, stdout, stderr = ssh.exec_command(f"cat > {env_file} << 'EOF'\n{env_content}EOF")
            stdout.read()
            print("[OK] .env 文件已创建")
        
        # 检查文件内容
        print("\n.env 文件内容:")
        stdin, stdout, stderr = ssh.exec_command(f"cat {env_file}")
        print(stdout.read().decode('utf-8'))
        
        # 修复服务文件，使 EnvironmentFile 可选
        print("\n修复服务文件...")
        backend_service = f"""[Unit]
Description=Smart TG Backend API Service
After=network.target

[Service]
Type=notify
User={config['user']}
Group={config['user']}
WorkingDirectory={deploy_dir}/admin-backend
Environment="PATH={deploy_dir}/admin-backend/.venv/bin:/usr/local/bin:/usr/bin:/bin"
Environment="PYTHONPATH={deploy_dir}:{deploy_dir}/admin-backend"
EnvironmentFile=-{env_file}
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
        print("[OK] 服务文件已修复（EnvironmentFile 使用 - 前缀，文件不存在时不报错）")
        
        # 重启服务
        print("\n重启后端服务...")
        ssh.exec_command("sudo systemctl restart smart-tg-backend")
        
        import time
        time.sleep(3)
        
        stdin, stdout, stderr = ssh.exec_command("sudo systemctl is-active smart-tg-backend")
        status = stdout.read().decode('utf-8').strip()
        print(f"后端服务状态: {status}")
        
        if status != 'active':
            print("\n后端服务日志:")
            stdin, stdout, stderr = ssh.exec_command("sudo journalctl -u smart-tg-backend -n 30 --no-pager")
            print(stdout.read().decode('utf-8'))
        else:
            print("[OK] 后端服务已启动")
            
            # 健康检查
            print("\n健康检查:")
            stdin, stdout, stderr = ssh.exec_command("sleep 2 && curl -s http://localhost:8000/health 2>/dev/null || echo '后端不可访问'")
            health = stdout.read().decode('utf-8').strip()
            print(f"后端: {health}")
        
    finally:
        ssh.close()

if __name__ == "__main__":
    main()

