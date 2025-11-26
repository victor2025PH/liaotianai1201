#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用 SCP 上传修复后的文件
"""

import json
import subprocess
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
    }

def main():
    config = load_config()
    project_root = Path(__file__).parent.parent.parent
    
    local_file = project_root / "saas-demo" / "src" / "components" / "layout-wrapper.tsx"
    remote_path = f"/home/ubuntu/saas-demo/src/components/layout-wrapper.tsx"
    
    if not local_file.exists():
        print(f"[ERROR] 文件不存在: {local_file}")
        return
    
    print("=" * 50)
    print("上传修复后的文件")
    print("=" * 50)
    
    print(f"\n本地文件: {local_file}")
    print(f"远程路径: {config['user']}@{config['host']}:{remote_path}")
    
    # 使用 sshpass 或直接 SCP
    print("\n[1] 尝试使用 SCP 上传...")
    
    # Windows PowerShell 中使用 scp
    scp_cmd = [
        "scp",
        str(local_file),
        f"{config['user']}@{config['host']}:{remote_path}"
    ]
    
    print(f"执行命令: {' '.join(scp_cmd)}")
    print("提示: 如果要求输入密码，请输入服务器密码")
    
    try:
        result = subprocess.run(scp_cmd, check=False)
        if result.returncode == 0:
            print("[OK] 文件上传成功！")
            print("\n下一步:")
            print("1. SSH 连接到服务器:")
            print(f"   ssh {config['user']}@{config['host']}")
            print("2. 执行以下命令:")
            print("   cd /home/ubuntu/saas-demo")
            print("   source ~/.nvm/nvm.sh")
            print("   nvm use 20")
            print("   npm run build")
            print("   sudo systemctl restart smart-tg-frontend")
        else:
            print(f"[ERROR] 上传失败 (退出码: {result.returncode})")
            print("\n替代方案:")
            print("1. 手动使用 SCP 命令:")
            print(f"   scp \"{local_file}\" {config['user']}@{config['host']}:{remote_path}")
            print("\n2. 或使用云服务器控制台的 Web SSH 上传文件")
            print("\n3. 或使用 FTP/SFTP 客户端（如 FileZilla）")
    except FileNotFoundError:
        print("[ERROR] 未找到 scp 命令")
        print("\n请使用以下方法之一:")
        print("1. 安装 OpenSSH 客户端（Windows 10/11 通常已包含）")
        print("2. 使用 PuTTY 的 pscp.exe")
        print("3. 使用云服务器控制台的 Web SSH")
        print("4. 使用 FTP/SFTP 客户端")
    
    print("\n" + "=" * 50)

if __name__ == "__main__":
    main()

