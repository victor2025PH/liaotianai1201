#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
最终检查服务状态
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
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(host, username=user, password=password, timeout=10)
    return ssh

def main():
    config = load_config()
    ssh = connect_server(config['host'], config['user'], config['password'])
    
    try:
        print("等待服务完全启动...")
        time.sleep(5)
        
        print("\n" + "=" * 50)
        print("最终服务状态检查")
        print("=" * 50)
        
        # 服务状态
        print("\n[1] 服务状态:")
        stdin, stdout, stderr = ssh.exec_command("systemctl is-active smart-tg-backend smart-tg-frontend")
        status = stdout.read().decode('utf-8').strip()
        print(status)
        
        # 端口监听
        print("\n[2] 端口监听:")
        stdin, stdout, stderr = ssh.exec_command("sudo ss -tlnp | grep -E ':8000|:3000'")
        ports = stdout.read().decode('utf-8').strip()
        if ports:
            print(ports)
        else:
            print("端口未被占用")
        
        # 后端健康检查
        print("\n[3] 后端健康检查:")
        stdin, stdout, stderr = ssh.exec_command("curl -s http://localhost:8000/health 2>/dev/null || echo '后端不可访问'")
        backend_health = stdout.read().decode('utf-8').strip()
        print(f"  {backend_health}")
        
        # 前端状态
        print("\n[4] 前端状态:")
        stdin, stdout, stderr = ssh.exec_command("curl -s -o /dev/null -w '%{http_code}' http://localhost:3000 2>/dev/null || echo '000'")
        frontend_code = stdout.read().decode('utf-8').strip()
        print(f"  HTTP {frontend_code}")
        
        # 外部访问测试
        print(f"\n[5] 外部访问测试:")
        stdin, stdout, stderr = ssh.exec_command(f"curl -s -o /dev/null -w '%{{http_code}}' http://{config['host']}:8000/health 2>/dev/null || echo '000'")
        backend_external = stdout.read().decode('utf-8').strip()
        print(f"  后端 ({config['host']}:8000): HTTP {backend_external}")
        
        stdin, stdout, stderr = ssh.exec_command(f"curl -s -o /dev/null -w '%{{http_code}}' http://{config['host']}:3000 2>/dev/null || echo '000'")
        frontend_external = stdout.read().decode('utf-8').strip()
        print(f"  前端 ({config['host']}:3000): HTTP {frontend_external}")
        
        print("\n" + "=" * 50)
        print("部署状态总结")
        print("=" * 50)
        
        backend_ok = backend_health and 'ok' in backend_health.lower()
        frontend_ok = frontend_code == '200'
        
        if backend_ok and frontend_ok:
            print("\n✅ 部署成功！前端和后端都已正常运行")
        elif frontend_ok:
            print("\n⚠️  前端正常运行，后端需要检查")
        else:
            print("\n❌ 服务需要进一步检查")
        
        print(f"\n访问地址:")
        print(f"  后端: http://{config['host']}:8000")
        print(f"  前端: http://{config['host']}:3000")
        print(f"  API 文档: http://{config['host']}:8000/docs")
        
        if backend_external == '000' or frontend_external == '000':
            print(f"\n⚠️  外部无法访问，请检查:")
            print(f"  1. 云服务器安全组是否开放 8000 和 3000 端口")
            print(f"  2. 服务器防火墙配置")
            print(f"  3. 服务是否绑定到 0.0.0.0（而不是 127.0.0.1）")
        
    finally:
        ssh.close()

if __name__ == "__main__":
    main()

