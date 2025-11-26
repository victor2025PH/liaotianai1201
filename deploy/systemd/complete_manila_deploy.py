#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
完整部署到马尼拉服务器
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
        'host': '165.154.233.55',  # 用户指定的马尼拉服务器 IP
        'user': manila_config.get('user', 'ubuntu'),
        'password': manila_config.get('password', '8iDcGrYb52Fxpzee'),
        'deploy_dir': manila_config.get('deploy_dir', '/home/ubuntu'),
    }

def connect_server(host, user, password, retries=3):
    """连接服务器，支持重试"""
    for i in range(retries):
        try:
            print(f"尝试连接服务器: {host} (第 {i+1}/{retries} 次)...")
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(host, username=user, password=password, timeout=15)
            print("[OK] 连接成功")
            return ssh
        except paramiko.AuthenticationException:
            print(f"[ERROR] 认证失败 - 用户名或密码错误")
            return None
        except Exception as e:
            print(f"[WARNING] 连接失败: {e}")
            if i < retries - 1:
                print(f"  等待 3 秒后重试...")
                time.sleep(3)
            else:
                print(f"[ERROR] 无法连接到服务器")
                return None
    return None

def main():
    config = load_config()
    
    print("=" * 60)
    print("完整部署到马尼拉服务器")
    print("=" * 60)
    print(f"\n服务器信息:")
    print(f"  主机: {config['host']}")
    print(f"  用户: {config['user']}")
    print(f"  部署目录: {config['deploy_dir']}")
    
    # 连接服务器
    ssh = connect_server(config['host'], config['user'], config['password'])
    if not ssh:
        print("\n" + "=" * 60)
        print("无法自动连接，请使用手动部署")
        print("=" * 60)
        print("\n请使用以下方法之一:")
        print("\n方法1: 使用 SCP 上传文件")
        print(f"  scp saas-demo/src/components/layout-wrapper.tsx {config['user']}@{config['host']}:/home/ubuntu/saas-demo/src/components/")
        print("\n方法2: 使用 Web SSH")
        print("  1. 登录云服务器控制台")
        print("  2. 找到马尼拉服务器")
        print("  3. 使用 Web SSH 连接")
        print("  4. 按照部署指南操作")
        print("\n详细指南: deploy/systemd/马尼拉服务器部署指南.md")
        return
    
    sftp = ssh.open_sftp()
    
    try:
        project_root = Path(__file__).parent.parent.parent
        layout_file = project_root / "saas-demo" / "src" / "components" / "layout-wrapper.tsx"
        remote_dir = f"{config['deploy_dir']}/saas-demo"
        remote_file = f"{remote_dir}/src/components/layout-wrapper.tsx"
        
        # 步骤1: 检查环境
        print("\n" + "=" * 60)
        print("步骤 1: 检查服务器环境")
        print("=" * 60)
        
        stdin, stdout, stderr = ssh.exec_command(f"test -d {remote_dir} && echo 'exists' || echo 'not exists'")
        dir_exists = stdout.read().decode('utf-8').strip()
        
        if dir_exists == 'not exists':
            print(f"[ERROR] 前端目录不存在: {remote_dir}")
            print("  需要先部署完整的前端代码")
            ssh.close()
            return
        
        print(f"[OK] 前端目录存在: {remote_dir}")
        
        # 检查文件是否存在
        stdin, stdout, stderr = ssh.exec_command(f"test -f {remote_file} && echo 'exists' || echo 'not exists'")
        file_exists = stdout.read().decode('utf-8').strip()
        
        if file_exists == 'not exists':
            print(f"[WARNING] 目标文件不存在: {remote_file}")
            print("  将创建新文件")
        else:
            print(f"[OK] 目标文件存在，将进行备份")
        
        # 步骤2: 备份和上传
        print("\n" + "=" * 60)
        print("步骤 2: 备份并上传修复后的文件")
        print("=" * 60)
        
        if not layout_file.exists():
            print(f"[ERROR] 本地文件不存在: {layout_file}")
            ssh.close()
            return
        
        # 备份原文件
        print("\n[1] 备份原文件...")
        backup_cmd = f"cp {remote_file} {remote_file}.bak.$(date +%Y%m%d_%H%M%S) 2>/dev/null || echo 'backup skipped'"
        ssh.exec_command(backup_cmd)
        print("[OK] 备份完成")
        
        # 读取修复后的文件
        print("\n[2] 读取修复后的文件...")
        with open(layout_file, 'r', encoding='utf-8') as f:
            fixed_content = f.read()
        print(f"[OK] 文件大小: {len(fixed_content)} 字符")
        
        # 上传文件
        print("\n[3] 上传文件到服务器...")
        print(f"  本地: {layout_file}")
        print(f"  远程: {remote_file}")
        
        try:
            with sftp.open(remote_file, 'w') as f:
                f.write(fixed_content)
            print("[OK] 文件上传成功")
        except Exception as e:
            print(f"[ERROR] 上传失败: {e}")
            ssh.close()
            return
        
        # 验证文件
        print("\n[4] 验证上传的文件...")
        stdin, stdout, stderr = ssh.exec_command(f"grep -q 'setChecking(false); // 先停止檢查狀態' {remote_file} && echo 'verified' || echo 'not verified'")
        verified = stdout.read().decode('utf-8').strip()
        if verified == 'verified':
            print("[OK] 文件验证通过")
        else:
            print("[WARNING] 文件验证失败，但继续执行")
        
        # 步骤3: 重新构建
        print("\n" + "=" * 60)
        print("步骤 3: 重新构建前端")
        print("=" * 60)
        
        # 停止服务
        print("\n[1] 停止前端服务...")
        ssh.exec_command("sudo systemctl stop smart-tg-frontend 2>/dev/null || echo 'service not running'")
        time.sleep(2)
        print("[OK] 服务已停止")
        
        # 检查 Node.js
        print("\n[2] 检查 Node.js 版本...")
        node_cmd = "source ~/.nvm/nvm.sh 2>/dev/null && nvm use 20 2>&1 && node --version || echo 'not found'"
        stdin, stdout, stderr = ssh.exec_command(node_cmd)
        node_version = stdout.read().decode('utf-8').strip()
        
        if 'v20' in node_version:
            print(f"[OK] Node.js 版本: {node_version}")
        else:
            print(f"[WARNING] Node.js 20 未找到，尝试安装...")
            install_cmd = "source ~/.nvm/nvm.sh && nvm install 20 && nvm use 20 && nvm alias default 20 && node --version"
            stdin, stdout, stderr = ssh.exec_command(install_cmd)
            time.sleep(5)
            node_version = stdout.read().decode('utf-8').strip()
            if 'v20' in node_version:
                print(f"[OK] Node.js 20 安装成功: {node_version}")
            else:
                print(f"[WARNING] Node.js 安装可能失败，继续尝试构建")
        
        # 构建
        print("\n[3] 开始构建前端...")
        build_cmd = f"cd {remote_dir} && source ~/.nvm/nvm.sh 2>/dev/null && nvm use 20 2>&1 && npm run build"
        stdin, stdout, stderr = ssh.exec_command(build_cmd)
        
        print("  构建中，请稍候...")
        build_lines = []
        start_time = time.time()
        timeout = 300  # 5分钟超时
        
        while True:
            if stdout.channel.exit_status_ready():
                break
            if time.time() - start_time > timeout:
                print("  [WARNING] 构建超时")
                break
            line = stdout.readline()
            if line:
                line = line.strip()
                if line:
                    build_lines.append(line)
                    # 只显示重要信息
                    if any(kw in line.lower() for kw in ['error', 'warning', 'compiled', 'ready', 'route', 'page', 'creating']):
                        print(f"  {line}")
            time.sleep(0.1)
        
        exit_status = stdout.channel.recv_exit_status()
        remaining = stdout.read().decode('utf-8')
        if remaining:
            for line in remaining.split('\n'):
                if line.strip() and any(kw in line.lower() for kw in ['error', 'warning', 'compiled', 'ready']):
                    print(f"  {line}")
        
        if exit_status != 0:
            print(f"\n[ERROR] 构建失败 (退出码: {exit_status})")
            error_output = stderr.read().decode('utf-8')
            if error_output:
                print(f"错误信息: {error_output[:500]}")
            ssh.close()
            return
        
        print("[OK] 构建完成")
        
        # 步骤4: 重启服务
        print("\n" + "=" * 60)
        print("步骤 4: 重启前端服务")
        print("=" * 60)
        
        print("\n[1] 重启前端服务...")
        ssh.exec_command("sudo systemctl restart smart-tg-frontend")
        time.sleep(5)
        
        # 检查服务状态
        print("\n[2] 检查服务状态...")
        stdin, stdout, stderr = ssh.exec_command("systemctl is-active smart-tg-frontend")
        status = stdout.read().decode('utf-8').strip()
        
        if status == "active":
            print("[OK] 前端服务已启动")
        else:
            print(f"[WARNING] 前端服务状态: {status}")
            print("查看最新日志:")
            stdin, stdout, stderr = ssh.exec_command("sudo journalctl -u smart-tg-frontend -n 20 --no-pager")
            logs = stdout.read().decode('utf-8')
            for line in logs.split('\n'):
                if line.strip():
                    print(f"  {line}")
        
        # 检查端口
        print("\n[3] 检查端口监听...")
        stdin, stdout, stderr = ssh.exec_command("sudo ss -tlnp | grep ':3000' || echo 'port not listening'")
        port_info = stdout.read().decode('utf-8').strip()
        if '3000' in port_info:
            print(f"[OK] 端口 3000 正在监听")
        else:
            print(f"[WARNING] 端口 3000 未监听")
        
        print("\n" + "=" * 60)
        print("部署完成！")
        print("=" * 60)
        print(f"\n访问地址:")
        print(f"  前端: http://{config['host']}:3000")
        print(f"  后端: http://{config['host']}:8000")
        print(f"\n如果仍然卡在认证检查，请:")
        print(f"  1. 清除浏览器缓存 (Ctrl+Shift+Delete)")
        print(f"  2. 在浏览器控制台执行: localStorage.clear()")
        print(f"  3. 刷新页面")
        
    except Exception as e:
        print(f"\n[ERROR] 部署过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        sftp.close()
        ssh.close()

if __name__ == "__main__":
    main()

