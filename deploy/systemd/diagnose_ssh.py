#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
详细诊断 SSH 连接问题
"""

import json
import socket
import subprocess
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
    }

def test_ping(host):
    """测试 ping"""
    print(f"\n[1] 测试网络连通性 (Ping)...")
    try:
        if sys.platform == 'win32':
            result = subprocess.run(['ping', '-n', '4', host], 
                                  capture_output=True, text=True, timeout=10)
        else:
            result = subprocess.run(['ping', '-c', '4', host], 
                                  capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            print(f"  ✅ 服务器可访问")
            # 提取延迟信息
            output = result.stdout
            if 'time=' in output or '时间=' in output:
                print(f"  网络延迟正常")
            return True
        else:
            print(f"  ❌ 无法 ping 通服务器")
            print(f"  这可能是服务器问题或网络问题")
            return False
    except Exception as e:
        print(f"  ⚠️  Ping 测试失败: {e}")
        return None

def test_port(host, port, timeout=5):
    """测试端口是否开放"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except Exception as e:
        return False

def test_ssh_port(host):
    """测试 SSH 端口"""
    print(f"\n[2] 测试 SSH 端口 (22)...")
    if test_port(host, 22, timeout=5):
        print(f"  ✅ 端口 22 开放")
        return True
    else:
        print(f"  ❌ 端口 22 未开放或无法连接")
        print(f"  可能原因:")
        print(f"    - 服务器 SSH 服务未运行")
        print(f"    - 云服务器安全组未开放 22 端口")
        print(f"    - 服务器防火墙阻止")
        return False

def test_ssh_banner(host, port=22):
    """尝试获取 SSH 横幅信息"""
    print(f"\n[3] 测试 SSH 服务响应...")
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        sock.connect((host, port))
        
        # 读取 SSH 横幅
        banner = sock.recv(1024).decode('utf-8', errors='ignore')
        sock.close()
        
        if 'SSH' in banner:
            print(f"  ✅ SSH 服务正在运行")
            print(f"  服务信息: {banner[:100]}...")
            return True
        else:
            print(f"  ⚠️  端口开放但可能不是 SSH 服务")
            return False
    except socket.timeout:
        print(f"  ❌ 连接超时 - 服务器可能无响应")
        return False
    except Exception as e:
        print(f"  ⚠️  无法获取 SSH 信息: {e}")
        return False

def test_ssh_command(host, user):
    """测试 SSH 命令"""
    print(f"\n[4] 测试 SSH 客户端...")
    try:
        # 测试 SSH 命令是否存在
        result = subprocess.run(['ssh', '-V'], capture_output=True, text=True, timeout=5)
        if result.returncode == 0 or 'OpenSSH' in result.stderr or 'OpenSSH' in result.stdout:
            print(f"  ✅ SSH 客户端可用")
            print(f"  版本信息: {result.stderr or result.stdout}")
        else:
            print(f"  ⚠️  SSH 客户端可能有问题")
    except FileNotFoundError:
        print(f"  ❌ 未找到 SSH 客户端")
        print(f"  请安装 OpenSSH 客户端")
        return False
    except Exception as e:
        print(f"  ⚠️  测试失败: {e}")
    
    # 测试连接（带超时）
    print(f"\n[5] 尝试 SSH 连接（5秒超时）...")
    print(f"  命令: ssh -o ConnectTimeout=5 -o StrictHostKeyChecking=no {user}@{host}")
    print(f"  提示: 如果卡住，按 Ctrl+C 中断")
    
    return True

def check_firewall_rules():
    """检查可能的防火墙问题"""
    print(f"\n[6] 防火墙/安全组检查建议...")
    print(f"  请检查以下项目:")
    print(f"  1. 云服务器控制台 -> 安全组规则")
    print(f"     - 确保入站规则允许 TCP 22 端口")
    print(f"     - 源地址: 0.0.0.0/0 或您的 IP")
    print(f"  2. 服务器内部防火墙 (UFW/iptables)")
    print(f"     - 如果可以通过 Web SSH 访问，检查: sudo ufw status")
    print(f"  3. SSH 服务状态")
    print(f"     - 如果可以通过 Web SSH 访问，检查: sudo systemctl status sshd")

def main():
    config = load_config()
    host = config['host']
    user = config['user']
    
    print("=" * 60)
    print("SSH 连接问题详细诊断")
    print("=" * 60)
    print(f"\n服务器信息:")
    print(f"  主机: {host}")
    print(f"  用户: {user}")
    
    # 1. Ping 测试
    ping_ok = test_ping(host)
    
    # 2. 端口测试
    port_ok = test_ssh_port(host)
    
    # 3. SSH 服务测试
    if port_ok:
        ssh_service_ok = test_ssh_banner(host)
    else:
        ssh_service_ok = False
    
    # 4. SSH 客户端测试
    ssh_client_ok = test_ssh_command(host, user)
    
    # 5. 防火墙检查建议
    check_firewall_rules()
    
    # 总结
    print("\n" + "=" * 60)
    print("诊断总结")
    print("=" * 60)
    
    if not ping_ok:
        print("\n❌ 问题: 服务器网络不可达")
        print("  可能原因:")
        print("    - 服务器已关机")
        print("    - 网络连接问题")
        print("    - 服务器 IP 地址错误")
        print("  建议: 检查云服务器控制台，确认服务器状态")
    
    elif not port_ok:
        print("\n❌ 问题: SSH 端口未开放")
        print("  可能原因:")
        print("    - 云服务器安全组未开放 22 端口")
        print("    - 服务器 SSH 服务未运行")
        print("    - 服务器防火墙阻止")
        print("  建议:")
        print("    1. 登录云服务器控制台，检查安全组规则")
        print("    2. 使用 Web SSH 连接，检查 SSH 服务状态")
        print("    3. 如果可以通过 Web SSH，说明是安全组问题")
    
    elif not ssh_service_ok:
        print("\n⚠️  问题: SSH 服务可能异常")
        print("  建议: 使用 Web SSH 检查服务器状态")
    
    else:
        print("\n✅ 网络和端口测试通过")
        print("  如果仍然无法连接，可能是:")
        print("    - SSH 客户端配置问题")
        print("    - 认证方式问题")
        print("    - Windows SSH 客户端兼容性问题")
        print("  建议:")
        print("    1. 尝试使用云服务器控制台的 Web SSH")
        print("    2. 使用 PuTTY 或其他 SSH 客户端")
        print("    3. 检查是否有代理或 VPN 影响连接")
    
    print("\n" + "=" * 60)
    print("推荐解决方案")
    print("=" * 60)
    print("\n如果 SSH 无法连接，建议使用以下方法:")
    print("  1. 使用云服务器控制台的 Web SSH（最简单）")
    print("  2. 使用 SCP 直接上传文件（无需交互式 SSH）")
    print("  3. 使用 Python 脚本自动部署（已创建）")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    main()

