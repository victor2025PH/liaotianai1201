#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查并修复马尼拉服务器部署
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
    
    manila_config = config.get('servers', {}).get('manila', {})
    
    return {
        'host': manila_config.get('host', '165.154.233.55'),
        'user': manila_config.get('user', 'ubuntu'),
        'password': manila_config.get('password', 'Along2025!!!'),
        'deploy_dir': manila_config.get('deploy_dir', '/home/ubuntu'),
    }

def connect_server(host, user, password):
    """连接服务器"""
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(host, username=user, password=password, timeout=15)
    return ssh

def execute_command(ssh, command, description):
    """执行命令"""
    print(f"\n{description}...")
    stdin, stdout, stderr = ssh.exec_command(command)
    exit_status = stdout.channel.recv_exit_status()
    
    output = stdout.read().decode('utf-8', errors='replace').strip()
    error = stderr.read().decode('utf-8', errors='replace').strip()
    
    if output:
        for line in output.split('\n')[:30]:
            if line.strip():
                print(f"  {line}")
    if error and exit_status != 0:
        for line in error.split('\n')[:10]:
            if line.strip():
                print(f"  [ERROR] {line}")
    
    return exit_status == 0, output, error

def main():
    config = load_config()
    
    print("=" * 70)
    print("检查马尼拉服务器部署状态")
    print("=" * 70)
    
    ssh = connect_server(config['host'], config['user'], config['password'])
    
    try:
        # 1. 检查上传的代码目录
        print("\n[1] 检查上传的代码...")
        execute_command(ssh, "ls -la /home/ubuntu/ | grep liaotian", "查找代码目录")
        execute_command(ssh, "ls -la /home/ubuntu/liaotian20251126/ 2>/dev/null | head -20", "查看代码目录内容")
        
        # 2. 检查当前运行的服务
        print("\n[2] 检查当前运行的服务...")
        execute_command(ssh, "ps aux | grep -E 'gunicorn|next-server|python.*main' | grep -v grep", "运行中的进程")
        execute_command(ssh, "sudo ss -tlnp | grep -E ':8000|:3000'", "端口监听")
        
        # 3. 检查服务目录
        print("\n[3] 检查服务目录...")
        execute_command(ssh, "ls -la /home/ubuntu/ | grep -E 'admin-backend|saas-demo|smart-tg'", "查找服务目录")
        
        # 4. 检查 systemd 服务
        print("\n[4] 检查 systemd 服务...")
        execute_command(ssh, "systemctl list-units | grep -E 'smart-tg|backend|frontend'", "systemd 服务")
        
        # 5. 检查代码结构
        print("\n[5] 检查代码结构...")
        execute_command(ssh, "find /home/ubuntu/liaotian20251126 -maxdepth 2 -type d -name 'admin-backend*' -o -name 'saas-demo*' -o -name 'frontend*' 2>/dev/null", "查找后端和前端目录")
        
        # 6. 检查压缩包
        print("\n[6] 检查压缩包...")
        execute_command(ssh, "ls -lh /home/ubuntu/liaotian20251126/*.zip 2>/dev/null", "查找压缩包")
        
        print("\n" + "=" * 70)
        print("检查完成")
        print("=" * 70)
        print("\n根据检查结果，需要:")
        print("1. 确定正确的后端目录（可能是 admin-backend-deploy 或 full-backend-deploy）")
        print("2. 确定正确的前端目录（可能需要从 frontend.zip 解压）")
        print("3. 配置并启动服务")
        
    finally:
        ssh.close()

if __name__ == "__main__":
    main()

