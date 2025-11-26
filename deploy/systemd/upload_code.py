#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
上传代码到服务器
"""

import json
import paramiko
import os
import sys
from pathlib import Path
import tarfile
import tempfile

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

def upload_code(ssh, deploy_dir):
    """上传代码"""
    print(f"\n上传代码到: {deploy_dir}")
    
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent
    
    # 创建目录
    ssh.exec_command(f"sudo mkdir -p {deploy_dir}/{{admin-backend,saas-demo,data,logs}}")
    ssh.exec_command(f"sudo chown -R $USER:$USER {deploy_dir}")
    
    # 使用 SCP 上传
    sftp = ssh.open_sftp()
    
    # 上传后端关键文件
    print("上传后端代码...")
    backend_files = [
        "admin-backend/requirements.txt",
        "admin-backend/pyproject.toml",
        "admin-backend/alembic.ini",
    ]
    
    for rel_path in backend_files:
        local_path = project_root / rel_path
        if local_path.exists():
            remote_path = f"{deploy_dir}/{rel_path}"
            remote_dir = os.path.dirname(remote_path)
            ssh.exec_command(f"mkdir -p {remote_dir}")
            try:
                sftp.put(str(local_path), remote_path)
                print(f"  [OK] {rel_path}")
            except Exception as e:
                print(f"  [ERROR] {rel_path}: {e}")
    
    # 上传前端关键文件
    print("上传前端代码...")
    frontend_files = [
        "saas-demo/package.json",
        "saas-demo/package-lock.json",
    ]
    
    for rel_path in frontend_files:
        local_path = project_root / rel_path
        if local_path.exists():
            remote_path = f"{deploy_dir}/{rel_path}"
            remote_dir = os.path.dirname(remote_path)
            ssh.exec_command(f"mkdir -p {remote_dir}")
            try:
                sftp.put(str(local_path), remote_path)
                print(f"  [OK] {rel_path}")
            except Exception as e:
                print(f"  [ERROR] {rel_path}: {e}")
    
    sftp.close()
    
    print("\n[注意] 由于文件较多，建议使用以下方式上传完整代码:")
    print(f"  scp -r admin-backend/* user@{deploy_dir}/admin-backend/")
    print(f"  scp -r saas-demo/* user@{deploy_dir}/saas-demo/")

def main():
    config = load_config()
    ssh = connect_server(config['host'], config['user'], config['password'])
    
    try:
        upload_code(ssh, config['deploy_dir'])
    finally:
        ssh.close()

if __name__ == "__main__":
    main()

