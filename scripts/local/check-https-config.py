#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查 HTTPS 配置
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
    
    manila_config = config.get('servers', {}).get('manila', {})
    
    return {
        'host': '165.154.233.55',
        'user': manila_config.get('user', 'ubuntu'),
        'password': manila_config.get('password', 'Along2025!!!'),
    }

def main():
    """主函数"""
    print("="*60)
    print("🔍 检查 HTTPS 配置")
    print("="*60)
    print()
    
    config = load_config()
    client = None
    
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(config['host'], username=config['user'], password=config['password'], timeout=30)
        print("✅ SSH 连接成功!")
        
        # 检查 HTTPS 配置
        stdin, stdout, stderr = client.exec_command('sudo nginx -T 2>/dev/null | grep -B 5 -A 30 "listen.*443"', get_pty=True)
        output = ''.join(stdout.readlines())
        
        if output.strip():
            print("\n找到 HTTPS 配置:")
            print(output)
        else:
            print("\n⚠️  未找到 HTTPS 配置")
            print("用户访问的是 https://，但服务器只配置了 HTTP (80端口)")
            print("\n解决方案:")
            print("1. 配置 HTTPS (需要 SSL 证书)")
            print("2. 或者将 HTTP 请求重定向到 HTTPS")
            print("3. 或者让用户访问 http://aikz.usdt2026.cc")
        
        # 检查是否有 Let's Encrypt 证书
        stdin, stdout, stderr = client.exec_command('sudo ls -la /etc/letsencrypt/live/aikz.usdt2026.cc/ 2>/dev/null || echo "未找到证书"', get_pty=True)
        cert_output = ''.join(stdout.readlines())
        print("\n检查 SSL 证书:")
        print(cert_output)
        
    except Exception as e:
        print(f"❌ 错误: {e}")
        return 1
    finally:
        if client:
            client.close()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

