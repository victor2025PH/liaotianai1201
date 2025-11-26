#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 API 连接和认证端点
"""

import json
import paramiko
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
        server_ip = config['host']
        api_base = f"http://{server_ip}:8000/api/v1"
        
        print("=" * 50)
        print("测试 API 连接")
        print("=" * 50)
        
        # 1. 测试健康检查
        print("\n[1] 健康检查:")
        stdin, stdout, stderr = ssh.exec_command("curl -s http://localhost:8000/health")
        health = stdout.read().decode('utf-8').strip()
        print(f"  {health}")
        
        # 2. 测试 API 根路径
        print(f"\n[2] API 根路径:")
        stdin, stdout, stderr = ssh.exec_command(f"curl -s {api_base}/")
        api_root = stdout.read().decode('utf-8').strip()
        print(f"  {api_root}")
        
        # 3. 测试认证端点（不需要认证的）
        print(f"\n[3] 测试认证端点:")
        endpoints = [
            "/auth/login",
            "/auth/register",
            "/auth/me",
        ]
        
        for endpoint in endpoints:
            stdin, stdout, stderr = ssh.exec_command(f"curl -s -o /dev/null -w '%{{http_code}}' {api_base}{endpoint} 2>/dev/null || echo '000'")
            code = stdout.read().decode('utf-8').strip()
            print(f"  {endpoint}: HTTP {code}")
        
        # 4. 测试 CORS
        print(f"\n[4] 测试 CORS:")
        frontend_url = f"http://{server_ip}:3000"
        stdin, stdout, stderr = ssh.exec_command(f"curl -s -X OPTIONS {api_base}/auth/me -H 'Origin: {frontend_url}' -H 'Access-Control-Request-Method: GET' -v 2>&1 | grep -i 'access-control'")
        cors = stdout.read().decode('utf-8').strip()
        if cors:
            print("  CORS 响应头:")
            for line in cors.split('\n'):
                if line.strip():
                    print(f"    {line}")
        else:
            print("  [WARNING] 未找到 CORS 响应头")
        
        # 5. 检查前端环境变量
        print(f"\n[5] 前端环境变量:")
        stdin, stdout, stderr = ssh.exec_command("cat /home/ubuntu/saas-demo/.env.local")
        env = stdout.read().decode('utf-8').strip()
        print(f"  {env}")
        
        # 6. 测试从外部访问 API
        print(f"\n[6] 外部访问测试:")
        stdin, stdout, stderr = ssh.exec_command(f"curl -s -o /dev/null -w '%{{http_code}}' {api_base}/auth/login 2>/dev/null || echo '000'")
        external_code = stdout.read().decode('utf-8').strip()
        print(f"  外部访问 API: HTTP {external_code}")
        
        print("\n" + "=" * 50)
        print("测试完成")
        print("=" * 50)
        
        if external_code == '200' or external_code == '405' or external_code == '422':
            print("\n✅ API 可以正常访问")
            print(f"\n如果前端仍然卡在认证检查，可能是:")
            print(f"  1. 前端 JavaScript 执行错误（检查浏览器控制台 F12）")
            print(f"  2. localStorage 中有旧的 token 导致检查逻辑卡住")
            print(f"  3. 前端代码需要重新构建")
        else:
            print(f"\n⚠️  API 访问可能有问题 (HTTP {external_code})")
        
    finally:
        ssh.close()

if __name__ == "__main__":
    main()

