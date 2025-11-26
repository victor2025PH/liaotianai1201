#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查部署状态
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
    
    manila_config = config.get('servers', {}).get('manila', {})
    
    return {
        'host': manila_config.get('host', '165.154.233.55'),
        'user': manila_config.get('user', 'ubuntu'),
        'password': manila_config.get('password', 'Along2025!!!'),
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
    
    return output

def main():
    config = load_config()
    
    print("=" * 70)
    print("检查马尼拉服务器部署状态")
    print("=" * 70)
    
    ssh = connect_server(config['host'], config['user'], config['password'])
    
    try:
        # 1. 检查代码目录
        print("\n[1] 检查上传的代码...")
        execute_command(ssh, "ls -lh /home/ubuntu/liaotian20251126/ 2>/dev/null | head -15", "代码目录内容")
        
        # 2. 检查服务目录
        print("\n[2] 检查服务目录...")
        execute_command(ssh, "ls -la /home/ubuntu/ | grep -E 'admin-backend|saas-demo'", "服务目录")
        execute_command(ssh, "test -d /home/ubuntu/admin-backend && echo '后端目录存在' || echo '后端目录不存在'", "后端目录")
        execute_command(ssh, "test -d /home/ubuntu/saas-demo && echo '前端目录存在' || echo '前端目录不存在'", "前端目录")
        
        # 3. 检查服务状态
        print("\n[3] 检查服务状态...")
        execute_command(ssh, "systemctl status admin-backend smart-tg-frontend --no-pager -l | head -30", "systemd 服务状态")
        execute_command(ssh, "ps aux | grep -E 'gunicorn|next-server|uvicorn' | grep -v grep", "运行中的进程")
        execute_command(ssh, "sudo ss -tlnp | grep -E ':8000|:3000'", "端口监听")
        
        # 4. 检查代码版本
        print("\n[4] 检查代码版本...")
        execute_command(ssh, "test -f /home/ubuntu/admin-backend/app/main.py && echo '后端代码存在' || echo '后端代码不存在'", "后端代码")
        execute_command(ssh, "test -f /home/ubuntu/saas-demo/package.json && echo '前端代码存在' || echo '前端代码不存在'", "前端代码")
        
        # 5. 健康检查
        print("\n[5] 健康检查...")
        execute_command(ssh, "curl -s http://localhost:8000/health || echo '后端不可用'", "后端健康")
        execute_command(ssh, "curl -s -o /dev/null -w 'HTTP %{http_code}' http://localhost:3000 || echo '前端不可用'", "前端健康")
        
        print("\n" + "=" * 70)
        print("检查完成")
        print("=" * 70)
        print("\n当前状态:")
        print("  - 代码已上传到: /home/ubuntu/liaotian20251126/")
        print("  - 需要部署:")
        print("    1. 后端: 从 full-backend-deploy 或 admin-backend-deploy 部署到 /home/ubuntu/admin-backend")
        print("    2. 前端: 从 frontend.zip 解压到 /home/ubuntu/saas-demo")
        print("    3. 安装依赖、构建、配置服务")
        
    finally:
        ssh.close()

if __name__ == "__main__":
    main()

