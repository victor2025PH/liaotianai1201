#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
上传修复后的前端代码并重新构建
"""

import json
import paramiko
import sys
import time
import tarfile
import io
from pathlib import Path

# 设置 Windows 控制台编码
if sys.platform == 'win32':
    import io as io_module
    sys.stdout = io_module.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io_module.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

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

def main():
    config = load_config()
    ssh = connect_server(config['host'], config['user'], config['password'])
    sftp = ssh.open_sftp()
    
    try:
        project_root = Path(__file__).parent.parent.parent
        frontend_dir = project_root / "saas-demo"
        layout_file = frontend_dir / "src" / "components" / "layout-wrapper.tsx"
        
        print("\n" + "=" * 50)
        print("上传修复后的代码")
        print("=" * 50)
        
        # 1. 读取修复后的文件
        print("\n[1] 读取修复后的 layout-wrapper.tsx...")
        with open(layout_file, 'r', encoding='utf-8') as f:
            fixed_content = f.read()
        print("[OK] 文件读取成功")
        
        # 2. 停止前端服务
        print("\n[2] 停止前端服务...")
        ssh.exec_command("sudo systemctl stop smart-tg-frontend")
        time.sleep(2)
        print("[OK] 服务已停止")
        
        # 3. 上传文件
        print("\n[3] 上传修复后的文件...")
        remote_path = "/home/ubuntu/saas-demo/src/components/layout-wrapper.tsx"
        
        # 备份原文件
        ssh.exec_command(f"cp {remote_path} {remote_path}.bak")
        
        # 上传新文件
        with sftp.open(remote_path, 'w') as f:
            f.write(fixed_content)
        print("[OK] 文件上传成功")
        
        # 4. 确保使用 Node.js 20
        print("\n[4] 确保使用 Node.js 20...")
        stdin, stdout, stderr = ssh.exec_command("source ~/.nvm/nvm.sh && nvm use 20 && node --version")
        node_version = stdout.read().decode('utf-8').strip()
        print(f"  Node.js 版本: {node_version}")
        
        # 5. 重新构建前端
        print("\n[5] 重新构建前端...")
        build_cmd = "cd /home/ubuntu/saas-demo && source ~/.nvm/nvm.sh && nvm use 20 && npm run build"
        stdin, stdout, stderr = ssh.exec_command(build_cmd)
        
        print("  构建中...")
        # 读取构建输出
        build_lines = []
        while True:
            if stdout.channel.exit_status_ready():
                break
            line = stdout.readline()
            if line:
                line = line.strip()
                if line:
                    build_lines.append(line)
                    # 只显示重要信息
                    if any(keyword in line.lower() for keyword in ['error', 'warning', 'compiled', 'ready', 'route', 'page']):
                        print(f"  {line}")
            time.sleep(0.1)
        
        exit_status = stdout.channel.recv_exit_status()
        remaining = stdout.read().decode('utf-8')
        if remaining:
            for line in remaining.split('\n'):
                if line.strip() and any(keyword in line.lower() for keyword in ['error', 'warning', 'compiled', 'ready']):
                    print(f"  {line}")
        
        if exit_status != 0:
            print(f"\n[ERROR] 构建失败 (退出码: {exit_status})")
            error_output = stderr.read().decode('utf-8')
            if error_output:
                print(f"错误信息: {error_output[:500]}")
            return
        
        print("[OK] 构建完成")
        
        # 6. 重启前端服务
        print("\n[6] 重启前端服务...")
        ssh.exec_command("sudo systemctl restart smart-tg-frontend")
        time.sleep(3)
        
        # 检查服务状态
        stdin, stdout, stderr = ssh.exec_command("systemctl is-active smart-tg-frontend")
        status = stdout.read().decode('utf-8').strip()
        if status == "active":
            print("[OK] 前端服务已启动")
        else:
            print(f"[WARNING] 前端服务状态: {status}")
        
        print("\n" + "=" * 50)
        print("修复完成！")
        print("=" * 50)
        print(f"\n访问地址: http://{config['host']}:3000")
        print("\n如果仍然卡在认证检查，请:")
        print("  1. 清除浏览器缓存 (Ctrl+Shift+Delete)")
        print("  2. 清除 localStorage: 按 F12，在控制台输入 localStorage.clear()")
        print("  3. 刷新页面")
        
    finally:
        sftp.close()
        ssh.close()

if __name__ == "__main__":
    main()

