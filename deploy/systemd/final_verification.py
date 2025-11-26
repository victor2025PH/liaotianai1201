#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
最终验证服务可访问性
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
    }

def connect_server(host, user, password):
    """连接服务器"""
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(host, username=user, password=password, timeout=10)
    return ssh

def main():
    config = load_config()
    ssh = connect_server(config['host'], config['user'], config['password'])
    
    try:
        print("=" * 50)
        print("最终服务验证")
        print("=" * 50)
        
        # 1. 服务状态
        print("\n[1] 服务状态:")
        stdin, stdout, stderr = ssh.exec_command("systemctl is-active smart-tg-backend smart-tg-frontend")
        status = stdout.read().decode('utf-8').strip()
        print(status)
        
        # 2. 端口监听
        print("\n[2] 端口监听:")
        stdin, stdout, stderr = ssh.exec_command("sudo ss -tlnp | grep -E ':8000|:3000'")
        ports = stdout.read().decode('utf-8').strip()
        print(ports)
        
        # 3. 进程检查
        print("\n[3] 进程检查:")
        stdin, stdout, stderr = ssh.exec_command("ps aux | grep -E 'gunicorn|next-server' | grep -v grep | head -3")
        processes = stdout.read().decode('utf-8').strip()
        if processes:
            print(processes)
        else:
            print("未找到相关进程")
        
        # 4. 本地健康检查
        print("\n[4] 本地健康检查:")
        stdin, stdout, stderr = ssh.exec_command("curl -s http://localhost:8000/health")
        backend_health = stdout.read().decode('utf-8').strip()
        print(f"后端: {backend_health}")
        
        stdin, stdout, stderr = ssh.exec_command("curl -s -o /dev/null -w '%{http_code}' http://localhost:3000 2>/dev/null || echo '000'")
        frontend_code = stdout.read().decode('utf-8').strip()
        print(f"前端: HTTP {frontend_code}")
        
        # 5. 检查前端服务日志
        print("\n[5] 前端服务最新日志:")
        stdin, stdout, stderr = ssh.exec_command("sudo journalctl -u smart-tg-frontend -n 10 --no-pager | tail -8")
        logs = stdout.read().decode('utf-8')
        for line in logs.split('\n'):
            if line.strip():
                print(f"  {line}")
        
        # 6. 网络连接测试
        print(f"\n[6] 网络连接测试:")
        print(f"从服务器测试外部访问...")
        stdin, stdout, stderr = ssh.exec_command(f"timeout 5 curl -s -o /dev/null -w '%{{http_code}}' http://{config['host']}:3000 2>&1 || echo 'TIMEOUT'")
        external_test = stdout.read().decode('utf-8').strip()
        print(f"外部访问测试: {external_test}")
        
        print("\n" + "=" * 50)
        print("验证结果")
        print("=" * 50)
        
        backend_ok = 'ok' in backend_health.lower()
        frontend_ok = frontend_code == '200'
        
        if backend_ok and frontend_ok:
            print("\n✅ 服务配置正确！")
            print(f"\n访问地址:")
            print(f"  后端: http://{config['host']}:8000")
            print(f"  前端: http://{config['host']}:3000")
            print(f"  API 文档: http://{config['host']}:8000/docs")
            
            if external_test == 'TIMEOUT' or external_test == '000':
                print(f"\n⚠️  如果仍然无法从外部访问前端，请:")
                print(f"  1. 确认防火墙规则已保存并生效（等待 1-2 分钟）")
                print(f"  2. 清除浏览器缓存")
                print(f"  3. 尝试使用无痕模式访问")
                print(f"  4. 检查是否有其他防火墙或代理阻止")
            else:
                print(f"\n✅ 外部访问测试通过！")
        else:
            print("\n⚠️  服务需要进一步检查")
            if not backend_ok:
                print("  - 后端服务异常")
            if not frontend_ok:
                print("  - 前端服务异常")
        
    finally:
        ssh.close()

if __name__ == "__main__":
    main()

