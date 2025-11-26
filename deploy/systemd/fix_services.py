#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复服务启动问题
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

def check_and_fix_services(ssh, deploy_dir):
    """检查并修复服务"""
    print("\n检查服务文件...")
    
    # 检查服务文件是否存在
    stdin, stdout, stderr = ssh.exec_command("test -f /etc/systemd/system/smart-tg-backend.service && echo 'exists' || echo 'not_exists'")
    backend_exists = stdout.read().decode('utf-8').strip()
    
    stdin, stdout, stderr = ssh.exec_command("test -f /etc/systemd/system/smart-tg-frontend.service && echo 'exists' || echo 'not_exists'")
    frontend_exists = stdout.read().decode('utf-8').strip()
    
    print(f"后端服务文件: {backend_exists}")
    print(f"前端服务文件: {frontend_exists}")
    
    # 如果服务文件不存在，需要创建
    if backend_exists == 'not_exists' or frontend_exists == 'not_exists':
        print("\n服务文件不存在，需要创建...")
        
        # 上传服务文件
        script_dir = Path(__file__).parent
        sftp = ssh.open_sftp()
        
        if backend_exists == 'not_exists':
            local_backend = script_dir / "smart-tg-backend.service"
            if local_backend.exists():
                # 读取并替换路径
                with open(local_backend, 'r', encoding='utf-8') as f:
                    content = f.read()
                    content = content.replace('/opt/smart-tg', deploy_dir)
                    content = content.replace('/path/to', deploy_dir)
                
                # 写入临时文件并上传
                temp_file = "/tmp/smart-tg-backend.service"
                stdin, stdout, stderr = ssh.exec_command(f"cat > {temp_file} << 'EOF'\n{content}EOF")
                stdout.read()
                
                # 复制到 systemd 目录
                ssh.exec_command(f"sudo cp {temp_file} /etc/systemd/system/smart-tg-backend.service")
                ssh.exec_command(f"sudo chmod 644 /etc/systemd/system/smart-tg-backend.service")
                print("[OK] 后端服务文件已创建")
        
        if frontend_exists == 'not_exists':
            local_frontend = script_dir / "smart-tg-frontend.service"
            if local_frontend.exists():
                # 读取并替换路径
                with open(local_frontend, 'r', encoding='utf-8') as f:
                    content = f.read()
                    content = content.replace('/opt/smart-tg', deploy_dir)
                    content = content.replace('/path/to', deploy_dir)
                
                # 写入临时文件并上传
                temp_file = "/tmp/smart-tg-frontend.service"
                stdin, stdout, stderr = ssh.exec_command(f"cat > {temp_file} << 'EOF'\n{content}EOF")
                stdout.read()
                
                # 复制到 systemd 目录
                ssh.exec_command(f"sudo cp {temp_file} /etc/systemd/system/smart-tg-frontend.service")
                ssh.exec_command(f"sudo chmod 644 /etc/systemd/system/smart-tg-frontend.service")
                print("[OK] 前端服务文件已创建")
        
        # 重新加载 systemd
        ssh.exec_command("sudo systemctl daemon-reload")
        print("[OK] systemd 已重新加载")
    
    # 检查服务文件内容
    print("\n检查服务文件配置...")
    stdin, stdout, stderr = ssh.exec_command("sudo cat /etc/systemd/system/smart-tg-backend.service | grep -E 'WorkingDirectory|ExecStart'")
    backend_config = stdout.read().decode('utf-8')
    print("后端服务配置:")
    print(backend_config)
    
    stdin, stdout, stderr = ssh.exec_command("sudo cat /etc/systemd/system/smart-tg-frontend.service | grep -E 'WorkingDirectory|ExecStart'")
    frontend_config = stdout.read().decode('utf-8')
    print("前端服务配置:")
    print(frontend_config)
    
    # 检查目录和文件是否存在
    print("\n检查目录和文件...")
    stdin, stdout, stderr = ssh.exec_command(f"test -d {deploy_dir}/admin-backend && echo 'exists' || echo 'not_exists'")
    backend_dir = stdout.read().decode('utf-8').strip()
    print(f"后端目录: {backend_dir}")
    
    stdin, stdout, stderr = ssh.exec_command(f"test -d {deploy_dir}/saas-demo && echo 'exists' || echo 'not_exists'")
    frontend_dir = stdout.read().decode('utf-8').strip()
    print(f"前端目录: {frontend_dir}")
    
    # 检查虚拟环境
    stdin, stdout, stderr = ssh.exec_command(f"test -d {deploy_dir}/admin-backend/.venv && echo 'exists' || echo 'not_exists'")
    venv_exists = stdout.read().decode('utf-8').strip()
    print(f"虚拟环境: {venv_exists}")
    
    # 检查 .next 目录
    stdin, stdout, stderr = ssh.exec_command(f"test -d {deploy_dir}/saas-demo/.next && echo 'exists' || echo 'not_exists'")
    next_exists = stdout.read().decode('utf-8').strip()
    print(f"前端构建目录: {next_exists}")
    
    # 尝试启动服务并查看详细错误
    print("\n尝试启动后端服务...")
    ssh.exec_command("sudo systemctl start smart-tg-backend")
    stdin, stdout, stderr = ssh.exec_command("sudo systemctl status smart-tg-backend --no-pager -l")
    backend_status = stdout.read().decode('utf-8')
    print(backend_status)
    
    print("\n尝试启动前端服务...")
    ssh.exec_command("sudo systemctl start smart-tg-frontend")
    stdin, stdout, stderr = ssh.exec_command("sudo systemctl status smart-tg-frontend --no-pager -l")
    frontend_status = stdout.read().decode('utf-8')
    print(frontend_status)
    
    # 查看详细日志
    print("\n后端服务最新日志:")
    stdin, stdout, stderr = ssh.exec_command("sudo journalctl -u smart-tg-backend -n 20 --no-pager")
    backend_logs = stdout.read().decode('utf-8')
    print(backend_logs)
    
    print("\n前端服务最新日志:")
    stdin, stdout, stderr = ssh.exec_command("sudo journalctl -u smart-tg-frontend -n 20 --no-pager")
    frontend_logs = stdout.read().decode('utf-8')
    print(frontend_logs)

def main():
    config = load_config()
    ssh = connect_server(config['host'], config['user'], config['password'])
    
    try:
        check_and_fix_services(ssh, config['deploy_dir'])
    finally:
        ssh.close()

if __name__ == "__main__":
    main()

