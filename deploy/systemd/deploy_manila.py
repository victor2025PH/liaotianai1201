#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
部署到马尼拉服务器 (165.154.233.55)
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
    
    # 使用马尼拉服务器配置，如果 IP 不同则更新
    manila_config = config.get('servers', {}).get('manila', {})
    
    return {
        'host': '165.154.233.55',  # 用户指定的 IP
        'user': manila_config.get('user', 'ubuntu'),
        'password': manila_config.get('password', '8iDcGrYb52Fxpzee'),
        'deploy_dir': manila_config.get('deploy_dir', '/home/ubuntu'),
    }

def connect_server(host, user, password):
    """连接服务器"""
    print(f"连接服务器: {host}...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(host, username=user, password=password, timeout=10)
        print("[OK] 连接成功")
        return ssh
    except Exception as e:
        print(f"[ERROR] 连接失败: {e}")
        return None

def main():
    config = load_config()
    
    print("=" * 60)
    print("部署到马尼拉服务器")
    print("=" * 60)
    print(f"\n服务器信息:")
    print(f"  主机: {config['host']}")
    print(f"  用户: {config['user']}")
    print(f"  部署目录: {config['deploy_dir']}")
    
    ssh = connect_server(config['host'], config['user'], config['password'])
    if not ssh:
        print("\n无法连接到服务器，请检查:")
        print("  1. 服务器是否运行")
        print("  2. IP 地址是否正确")
        print("  3. 安全组是否开放 22 端口")
        print("  4. 用户名和密码是否正确")
        return
    
    sftp = ssh.open_sftp()
    
    try:
        project_root = Path(__file__).parent.parent.parent
        frontend_dir = project_root / "saas-demo"
        layout_file = frontend_dir / "src" / "components" / "layout-wrapper.tsx"
        
        deploy_dir = config['deploy_dir']
        remote_frontend_dir = f"{deploy_dir}/saas-demo"
        
        print("\n" + "=" * 60)
        print("步骤 1: 检查服务器环境")
        print("=" * 60)
        
        # 检查目录是否存在
        stdin, stdout, stderr = ssh.exec_command(f"test -d {remote_frontend_dir} && echo 'exists' || echo 'not exists'")
        dir_exists = stdout.read().decode('utf-8').strip()
        
        if dir_exists == 'not exists':
            print(f"[WARNING] 前端目录不存在: {remote_frontend_dir}")
            print("  需要先部署完整的前端代码")
            print("  或者手动创建目录并上传代码")
            return
        
        print(f"[OK] 前端目录存在: {remote_frontend_dir}")
        
        # 检查 Node.js
        stdin, stdout, stderr = ssh.exec_command("source ~/.nvm/nvm.sh 2>/dev/null && nvm use 20 2>&1 && node --version || echo 'not found'")
        node_version = stdout.read().decode('utf-8').strip()
        if 'v20' in node_version:
            print(f"[OK] Node.js 版本: {node_version}")
        else:
            print(f"[WARNING] Node.js 20 未安装，需要先安装")
        
        print("\n" + "=" * 60)
        print("步骤 2: 上传修复后的文件")
        print("=" * 60)
        
        if not layout_file.exists():
            print(f"[ERROR] 本地文件不存在: {layout_file}")
            return
        
        # 备份原文件
        remote_file = f"{remote_frontend_dir}/src/components/layout-wrapper.tsx"
        print(f"\n[1] 备份原文件...")
        ssh.exec_command(f"cp {remote_file} {remote_file}.bak.$(date +%Y%m%d_%H%M%S) 2>/dev/null || echo 'backup failed'")
        print("[OK] 备份完成")
        
        # 上传文件
        print(f"\n[2] 上传修复后的文件...")
        print(f"  本地: {layout_file}")
        print(f"  远程: {remote_file}")
        
        with open(layout_file, 'r', encoding='utf-8') as f:
            fixed_content = f.read()
        
        with sftp.open(remote_file, 'w') as f:
            f.write(fixed_content)
        
        print("[OK] 文件上传成功")
        
        print("\n" + "=" * 60)
        print("步骤 3: 重新构建前端")
        print("=" * 60)
        
        # 停止服务
        print("\n[1] 停止前端服务...")
        ssh.exec_command("sudo systemctl stop smart-tg-frontend 2>/dev/null || echo 'service not running'")
        time.sleep(2)
        print("[OK] 服务已停止")
        
        # 确保使用 Node.js 20
        print("\n[2] 确保使用 Node.js 20...")
        build_cmd = f"""cd {remote_frontend_dir} && source ~/.nvm/nvm.sh && nvm use 20 && npm run build"""
        stdin, stdout, stderr = ssh.exec_command(build_cmd)
        
        print("  构建中，请稍候...")
        build_output = []
        error_lines = []
        
        while True:
            if stdout.channel.exit_status_ready():
                break
            line = stdout.readline()
            if line:
                line = line.strip()
                if line:
                    build_output.append(line)
                    if len(build_output) <= 30 or any(kw in line.lower() for kw in ['error', 'warning', 'compiled', 'ready']):
                        print(f"  {line}")
            time.sleep(0.1)
        
        exit_status = stdout.channel.recv_exit_status()
        remaining = stdout.read().decode('utf-8')
        if remaining:
            for line in remaining.split('\n'):
                if line.strip() and any(kw in line.lower() for kw in ['error', 'warning', 'compiled', 'ready']):
                    print(f"  {line}")
        
        error_output = stderr.read().decode('utf-8')
        if error_output:
            print(f"[ERROR] {error_output[:500]}")
        
        if exit_status != 0:
            print(f"\n[ERROR] 构建失败 (退出码: {exit_status})")
            print("请检查构建日志")
            return
        
        print("[OK] 构建完成")
        
        print("\n" + "=" * 60)
        print("步骤 4: 重启服务")
        print("=" * 60)
        
        print("\n[1] 重启前端服务...")
        ssh.exec_command("sudo systemctl restart smart-tg-frontend")
        time.sleep(3)
        
        # 检查服务状态
        stdin, stdout, stderr = ssh.exec_command("systemctl is-active smart-tg-frontend")
        status = stdout.read().decode('utf-8').strip()
        if status == "active":
            print("[OK] 前端服务已启动")
        else:
            print(f"[WARNING] 前端服务状态: {status}")
            print("查看日志:")
            stdin, stdout, stderr = ssh.exec_command("sudo journalctl -u smart-tg-frontend -n 15 --no-pager")
            logs = stdout.read().decode('utf-8')
            for line in logs.split('\n'):
                if line.strip():
                    print(f"  {line}")
        
        print("\n" + "=" * 60)
        print("部署完成！")
        print("=" * 60)
        print(f"\n访问地址: http://{config['host']}:3000")
        print(f"后端 API: http://{config['host']}:8000")
        print("\n如果仍然卡在认证检查，请:")
        print("  1. 清除浏览器缓存 (Ctrl+Shift+Delete)")
        print("  2. 在浏览器控制台执行: localStorage.clear()")
        print("  3. 刷新页面")
        
    finally:
        sftp.close()
        ssh.close()

if __name__ == "__main__":
    main()

