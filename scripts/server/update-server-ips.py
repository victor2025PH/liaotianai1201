#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
服务器IP检测和更新工具
帮助用户找到正确的服务器IP并更新配置文件
"""

import json
import sys
import socket
import paramiko
from pathlib import Path
from typing import Dict, Optional, Tuple

# 设置 Windows 控制台编码
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

def get_project_root() -> Path:
    """获取项目根目录"""
    script_dir = Path(__file__).parent
    return script_dir.parent.parent

def load_config() -> Dict:
    """加载配置文件"""
    project_root = get_project_root()
    config_path = project_root / "data" / "master_config.json"
    
    if not config_path.exists():
        print(f"[ERROR] 配置文件不存在: {config_path}")
        sys.exit(1)
    
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_config(config: Dict):
    """保存配置文件"""
    project_root = get_project_root()
    config_path = project_root / "data" / "master_config.json"
    
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    
    print(f"[OK] 配置文件已保存: {config_path}")

def test_connection(host: str, port: int = 22, timeout: int = 3) -> bool:
    """测试TCP连接"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except Exception:
        return False

def test_ssh_login(host: str, user: str, password: str, timeout: int = 3) -> Tuple[bool, str]:
    """测试SSH登录"""
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(host, username=user, password=password, timeout=timeout)
        
        # 获取服务器实际IP
        stdin, stdout, stderr = ssh.exec_command("hostname -I | awk '{print $1}'")
        actual_ip = stdout.read().decode('utf-8').strip()
        
        # 获取服务器主机名
        stdin, stdout, stderr = ssh.exec_command("hostname")
        hostname = stdout.read().decode('utf-8').strip()
        
        ssh.close()
        return True, f"[OK] 连接成功 | 主机名: {hostname} | 实际IP: {actual_ip}"
    except paramiko.AuthenticationException:
        return False, "[ERROR] SSH认证失败（用户名或密码错误）"
    except paramiko.SSHException as e:
        return False, f"[ERROR] SSH连接错误: {str(e)}"
    except socket.timeout:
        return False, "[ERROR] 连接超时（IP可能错误或服务器不可达）"
    except Exception as e:
        return False, f"[ERROR] 连接失败: {str(e)}"

def get_current_server_ip() -> Optional[str]:
    """获取当前服务器的实际IP"""
    try:
        # 方法1: 通过hostname -I获取
        import subprocess
        result = subprocess.run(['hostname', '-I'], capture_output=True, text=True, timeout=2)
        if result.returncode == 0:
            ips = result.stdout.strip().split()
            if ips:
                return ips[0]
    except:
        pass
    
    try:
        # 方法2: 通过socket连接外部服务获取
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        pass
    
    return None

def main():
    print("=" * 60)
    print("服务器IP检测和更新工具")
    print("=" * 60)
    print()
    
    # 加载配置
    config = load_config()
    servers = config.get('servers', {})
    
    if not servers:
        print("❌ 配置文件中没有服务器信息")
        sys.exit(1)
    
    # 获取当前服务器IP（如果脚本在服务器上运行）
    current_ip = get_current_server_ip()
    if current_ip:
        print(f"[INFO] 当前服务器IP: {current_ip}")
        print()
    
    print("开始检测服务器连接状态...")
    print("-" * 60)
    
    updated = False
    results = []
    
    for node_id, server_config in servers.items():
        host = server_config.get('host', '')
        user = server_config.get('user', 'ubuntu')
        password = server_config.get('password', '')
        
        print(f"\n[检测] 服务器: {node_id}")
        print(f"   配置IP: {host}")
        
        # 测试TCP连接
        tcp_ok = test_connection(host, 22, timeout=3)
        if not tcp_ok:
            print(f"   [WARN] TCP连接失败（端口22不可达）")
            results.append({
                'node_id': node_id,
                'old_ip': host,
                'status': 'tcp_failed',
                'suggestion': None
            })
            continue
        
        # 测试SSH登录
        ssh_ok, message = test_ssh_login(host, user, password, timeout=3)
        print(f"   {message}")
        
        if ssh_ok:
            results.append({
                'node_id': node_id,
                'old_ip': host,
                'status': 'ok',
                'suggestion': None
            })
        else:
            results.append({
                'node_id': node_id,
                'old_ip': host,
                'status': 'ssh_failed',
                'suggestion': None
            })
    
    print("\n" + "=" * 60)
    print("检测结果汇总")
    print("=" * 60)
    
    failed_servers = [r for r in results if r['status'] != 'ok']
    
    if not failed_servers:
        print("[OK] 所有服务器连接正常！")
        return
    
    print(f"\n[WARN] 发现 {len(failed_servers)} 个服务器连接失败：")
    for result in failed_servers:
        print(f"   - {result['node_id']}: {result['old_ip']} ({result['status']})")
    
    print("\n" + "=" * 60)
    print("如何修复？")
    print("=" * 60)
    print("\n方法1: 手动更新配置文件")
    print("   编辑文件: data/master_config.json")
    print("   找到对应的服务器节点，更新 'host' 字段为正确的IP地址")
    print()
    print("方法2: 交互式更新（需要手动输入）")
    print("   运行此脚本后，根据提示输入正确的IP地址")
    print()
    print("方法3: 在服务器上查找IP")
    print("   登录到服务器，运行以下命令获取IP：")
    print("   - hostname -I")
    print("   - ip addr show")
    print("   - curl ifconfig.me  (获取公网IP)")
    print()
    
    # 交互式更新
    update_choice = input("\n是否现在更新失败的服务器IP？(y/n): ").strip().lower()
    if update_choice == 'y':
        for result in failed_servers:
            if result['status'] != 'ok':
                node_id = result['node_id']
                old_ip = result['old_ip']
                print(f"\n服务器: {node_id}")
                print(f"当前IP: {old_ip}")
                new_ip = input(f"请输入正确的IP地址（直接回车跳过）: ").strip()
                
                if new_ip:
                    # 验证新IP格式
                    try:
                        socket.inet_aton(new_ip)
                        servers[node_id]['host'] = new_ip
                        updated = True
                        print(f"[OK] 已更新 {node_id} 的IP: {old_ip} -> {new_ip}")
                    except socket.error:
                        print(f"[ERROR] IP地址格式无效: {new_ip}")
        
        if updated:
            save_config(config)
            print("\n[OK] 配置已更新！请重新运行此脚本验证连接。")
        else:
            print("\n[WARN] 没有更新任何配置。")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n[WARN] 用户中断操作")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] 发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

