#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复前端代码并重新构建
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
    
    try:
        deploy_dir = config['deploy_dir']
        frontend_dir = f"{deploy_dir}/saas-demo"
        
        print("\n" + "=" * 50)
        print("修复前端代码并重新构建")
        print("=" * 50)
        
        # 1. 确保使用 Node.js 20
        print("\n[1] 检查 Node.js 版本...")
        stdin, stdout, stderr = ssh.exec_command("source ~/.nvm/nvm.sh && nvm use 20 && node --version")
        node_version = stdout.read().decode('utf-8').strip()
        print(f"  Node.js 版本: {node_version}")
        
        if "20" not in node_version:
            print("  切换到 Node.js 20...")
            stdin, stdout, stderr = ssh.exec_command("source ~/.nvm/nvm.sh && nvm install 20 && nvm use 20 && nvm alias default 20")
            stdout.read()
            print("[OK] 已切换到 Node.js 20")
        
        # 2. 停止前端服务
        print("\n[2] 停止前端服务...")
        ssh.exec_command("sudo systemctl stop smart-tg-frontend")
        time.sleep(2)
        print("[OK] 服务已停止")
        
        # 3. 修复 layout-wrapper.tsx
        print("\n[3] 修复 layout-wrapper.tsx...")
        fix_script = """#!/bin/bash
cd /home/ubuntu/saas-demo
source ~/.nvm/nvm.sh
nvm use 20

# 备份原文件
cp src/components/layout-wrapper.tsx src/components/layout-wrapper.tsx.bak

# 读取文件内容
python3 << 'PYTHON_SCRIPT'
import sys

file_path = 'src/components/layout-wrapper.tsx'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 修复1: 在未登录重定向前设置 checking 为 false
old1 = '      if (!isLoginPage && !authenticated) {\n        // 未登錄且不在登入頁，強制重定向到登入頁\n        if (window.location.pathname !== "/login") {'
new1 = '      if (!isLoginPage && !authenticated) {\n        setChecking(false); // 先停止檢查狀態，避免卡住\n        // 未登錄且不在登入頁，強制重定向到登入頁\n        if (window.location.pathname !== "/login") {'
content = content.replace(old1, new1)

# 修复2: 无论是否认证都停止检查状态
old2 = '      if (isLoginPage || authenticated) {\n        setChecking(false);\n      }'
new2 = '      // 無論是否認證，都應該停止檢查狀態\n      setChecking(false);'
content = content.replace(old2, new2)

# 修复3: 添加 authState 到依赖数组
old3 = '  }, [pathname, router, isLoginPage]);'
new3 = '  }, [pathname, router, isLoginPage, authState]);'
content = content.replace(old3, new3)

# 写回文件
with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("修复完成")
PYTHON_SCRIPT

echo "[OK] 代码修复完成"
"""
        
        stdin, stdout, stderr = ssh.exec_command(fix_script)
        stdout.channel.recv_exit_status()
        output = stdout.read().decode('utf-8')
        error = stderr.read().decode('utf-8')
        if output:
            print(output)
        if error and "修复完成" not in error:
            print(f"[WARNING] {error}")
        
        # 4. 重新构建前端
        print("\n[4] 重新构建前端...")
        build_cmd = f"""cd {frontend_dir} && source ~/.nvm/nvm.sh && nvm use 20 && npm run build"""
        stdin, stdout, stderr = ssh.exec_command(build_cmd)
        
        print("  构建中，请稍候...")
        build_output = []
        while True:
            if stdout.channel.exit_status_ready():
                break
            line = stdout.readline()
            if line:
                line = line.strip()
                if line:
                    build_output.append(line)
                    if len(build_output) <= 20 or "error" in line.lower() or "warning" in line.lower():
                        print(f"  {line}")
            time.sleep(0.1)
        
        exit_status = stdout.channel.recv_exit_status()
        remaining = stdout.read().decode('utf-8')
        if remaining:
            for line in remaining.split('\n'):
                if line.strip():
                    print(f"  {line}")
        
        error_output = stderr.read().decode('utf-8')
        if error_output:
            print(f"[ERROR] {error_output}")
        
        if exit_status != 0:
            print(f"\n[ERROR] 构建失败 (退出码: {exit_status})")
            return
        
        print("[OK] 构建完成")
        
        # 5. 重启前端服务
        print("\n[5] 重启前端服务...")
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
        
        print("\n" + "=" * 50)
        print("修复完成！")
        print("=" * 50)
        print(f"\n请清除浏览器缓存后访问: http://{config['host']}:3000")
        print("如果仍然卡在认证检查，请:")
        print("  1. 按 F12 打开浏览器控制台查看错误")
        print("  2. 清除 localStorage: localStorage.clear()")
        print("  3. 刷新页面")
        
    finally:
        ssh.close()

if __name__ == "__main__":
    main()

