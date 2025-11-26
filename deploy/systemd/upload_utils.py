#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
上传 utils 模块
"""

import json
import paramiko
import sys
import os
import tarfile
import tempfile
import time as time_module
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
        project_root = Path(__file__).parent.parent.parent
        deploy_dir = config['deploy_dir']
        
        # 检查本地是否有 utils 目录
        utils_dirs = []
        if (project_root / "admin-backend" / "utils").exists():
            utils_dirs.append(("admin-backend/utils", f"{deploy_dir}/admin-backend/utils"))
        if (project_root / "utils").exists():
            utils_dirs.append(("utils", f"{deploy_dir}/utils"))
        if (project_root / "group_ai_service" / "utils").exists():
            utils_dirs.append(("group_ai_service/utils", f"{deploy_dir}/group_ai_service/utils"))
        
        if not utils_dirs:
            print("[ERROR] 本地找不到 utils 目录")
            return
        
        print("上传 utils 模块...")
        
        # 使用 tar 打包并上传
        local_temp = tempfile.NamedTemporaryFile(delete=False, suffix='.tar.gz')
        local_temp.close()
        
        try:
            with tarfile.open(local_temp.name, 'w:gz') as tar:
                for local_path, remote_path in utils_dirs:
                    full_local = project_root / local_path
                    if full_local.exists():
                        for root, dirs, files in os.walk(full_local):
                            for file in files:
                                if file.endswith('.pyc') or file.startswith('.'):
                                    continue
                                file_path = Path(root) / file
                                arcname = Path(local_path) / file_path.relative_to(full_local)
                                tar.add(file_path, arcname=arcname)
            
            print(f"[OK] 已打包: {os.path.getsize(local_temp.name) / 1024:.2f} KB")
            
            # 上传
            temp_tar = f"/tmp/utils-{int(time_module.time())}.tar.gz"
            sftp = ssh.open_sftp()
            sftp.put(local_temp.name, temp_tar)
            sftp.close()
            
            # 解压
            ssh.exec_command(f"mkdir -p {deploy_dir}/admin-backend/utils {deploy_dir}/utils {deploy_dir}/group_ai_service/utils")
            ssh.exec_command(f"tar -xzf {temp_tar} -C {deploy_dir}")
            ssh.exec_command(f"rm -f {temp_tar}")
            
            print("[OK] utils 模块已上传")
            
            # 重启后端服务
            print("\n重启后端服务...")
            ssh.exec_command("sudo systemctl restart smart-tg-backend")
            
            time_module.sleep(8)
            
            stdin, stdout, stderr = ssh.exec_command("sudo systemctl is-active smart-tg-backend")
            status = stdout.read().decode('utf-8').strip()
            print(f"后端服务状态: {status}")
            
            if status == 'active':
                print("[OK] 后端服务已启动")
                time_module.sleep(3)
                stdin, stdout, stderr = ssh.exec_command("curl -s http://localhost:8000/health")
                health = stdout.read().decode('utf-8').strip()
                print(f"健康检查: {health}")
            else:
                print("\n后端服务日志:")
                stdin, stdout, stderr = ssh.exec_command("sudo journalctl -u smart-tg-backend -n 30 --no-pager")
                print(stdout.read().decode('utf-8'))
            
            os.unlink(local_temp.name)
            
        except Exception as e:
            print(f"[ERROR] 上传失败: {e}")
            if os.path.exists(local_temp.name):
                os.unlink(local_temp.name)
        
    finally:
        ssh.close()

if __name__ == "__main__":
    main()

