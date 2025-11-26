#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 SSH 连接
"""

import json
import paramiko
import sys
import socket
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

def test_port(host, port, timeout=5):
    """测试端口是否开放"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except Exception as e:
        print(f"  端口测试错误: {e}")
        return False

def test_ssh_connection(host, user, password):
    """测试 SSH 连接"""
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        # 设置超时
        ssh.connect(
            host, 
            username=user, 
            password=password, 
            timeout=10,
            allow_agent=False,
            look_for_keys=False
        )
        
        # 测试执行命令
        stdin, stdout, stderr = ssh.exec_command("echo 'SSH连接成功' && hostname && whoami")
        output = stdout.read().decode('utf-8').strip()
        ssh.close()
        
        return True, output
    except paramiko.AuthenticationException:
        return False, "认证失败：用户名或密码错误"
    except paramiko.SSHException as e:
        return False, f"SSH 错误: {str(e)}"
    except socket.timeout:
        return False, "连接超时：服务器可能无响应或防火墙阻止"
    except socket.gaierror:
        return False, "DNS 解析失败：无法解析主机名"
    except Exception as e:
        return False, f"连接错误: {str(e)}"

def main():
    config = load_config()
    
    print("=" * 50)
    print("SSH 连接诊断")
    print("=" * 50)
    
    host = config['host']
    user = config['user']
    
    # 1. 测试端口
    print(f"\n[1] 测试 SSH 端口 (22)...")
    if test_port(host, 22):
        print(f"  ✅ 端口 22 开放")
    else:
        print(f"  ❌ 端口 22 未开放或无法连接")
        print(f"  可能原因:")
        print(f"    - 服务器防火墙阻止")
        print(f"    - 云服务器安全组未开放 22 端口")
        print(f"    - 服务器 SSH 服务未运行")
        return
    
    # 2. 测试 SSH 连接
    print(f"\n[2] 测试 SSH 连接...")
    print(f"  主机: {host}")
    print(f"  用户: {user}")
    
    success, message = test_ssh_connection(host, user, config['password'])
    
    if success:
        print(f"  ✅ SSH 连接成功")
        print(f"  服务器信息:")
        for line in message.split('\n'):
            if line.strip():
                print(f"    {line}")
    else:
        print(f"  ❌ SSH 连接失败")
        print(f"  错误: {message}")
        print(f"\n解决方案:")
        print(f"  1. 检查服务器是否运行")
        print(f"  2. 检查云服务器安全组是否开放 22 端口")
        print(f"  3. 检查用户名和密码是否正确")
        print(f"  4. 尝试使用其他 SSH 客户端（如 PuTTY）")
        print(f"  5. 检查服务器 SSH 服务状态")
    
    # 3. 提供替代方案
    print(f"\n[3] 替代连接方案:")
    print(f"  如果 SSH 无法连接，可以使用以下方法部署:")
    print(f"  方法1: 使用 Python 脚本自动部署（已创建）")
    print(f"  方法2: 使用 FTP/SFTP 客户端上传文件")
    print(f"  方法3: 使用云服务器控制台的 Web SSH")
    
    print("\n" + "=" * 50)

if __name__ == "__main__":
    main()

