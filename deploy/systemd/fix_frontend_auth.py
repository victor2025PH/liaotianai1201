#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检测并修复前端认证问题
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

def diagnose(ssh, server_ip):
    """诊断问题"""
    print("\n" + "=" * 50)
    print("诊断前端认证问题")
    print("=" * 50)
    
    # 1. 检查服务状态
    print("\n[1] 检查服务状态...")
    stdin, stdout, stderr = ssh.exec_command("systemctl is-active smart-tg-backend smart-tg-frontend")
    status = stdout.read().decode('utf-8').strip()
    print(f"服务状态:\n{status}")
    
    # 2. 检查端口监听
    print("\n[2] 检查端口监听...")
    stdin, stdout, stderr = ssh.exec_command("sudo ss -tlnp | grep -E ':8000|:3000'")
    ports = stdout.read().decode('utf-8').strip()
    print(f"端口监听:\n{ports}")
    
    # 3. 测试后端 API
    print("\n[3] 测试后端 API...")
    stdin, stdout, stderr = ssh.exec_command("curl -s http://localhost:8000/health")
    backend_health = stdout.read().decode('utf-8').strip()
    print(f"后端健康检查: {backend_health}")
    
    # 测试 API 端点
    stdin, stdout, stderr = ssh.exec_command("curl -s http://localhost:8000/api/v1/auth/me 2>&1 | head -5")
    auth_test = stdout.read().decode('utf-8').strip()
    print(f"认证端点测试: {auth_test[:100]}...")
    
    # 4. 检查前端环境变量
    print("\n[4] 检查前端环境变量...")
    stdin, stdout, stderr = ssh.exec_command("cat /home/ubuntu/saas-demo/.env.local 2>/dev/null || echo '文件不存在'")
    env_content = stdout.read().decode('utf-8').strip()
    print(f".env.local 内容:\n{env_content}")
    
    # 5. 检查 CORS 配置
    print("\n[5] 检查后端 CORS 配置...")
    stdin, stdout, stderr = ssh.exec_command("grep -i cors /home/ubuntu/admin-backend/.env 2>/dev/null || echo '未找到 CORS 配置'")
    cors_config = stdout.read().decode('utf-8').strip()
    print(f"CORS 配置: {cors_config}")
    
    # 6. 测试前端页面
    print("\n[6] 测试前端页面...")
    stdin, stdout, stderr = ssh.exec_command("curl -s http://localhost:3000 2>&1 | head -20")
    frontend_html = stdout.read().decode('utf-8').strip()
    if frontend_html:
        print("前端页面响应（前20行）:")
        print(frontend_html)
    
    # 7. 检查浏览器控制台可能出现的错误
    print("\n[7] 检查服务日志...")
    stdin, stdout, stderr = ssh.exec_command("sudo journalctl -u smart-tg-backend -n 20 --no-pager | grep -i 'error\|cors\|401\|403' || echo '未发现相关错误'")
    backend_errors = stdout.read().decode('utf-8').strip()
    if backend_errors:
        print("后端错误日志:")
        print(backend_errors)

def fix_issues(ssh, deploy_dir, server_ip):
    """修复问题"""
    print("\n" + "=" * 50)
    print("修复前端认证问题")
    print("=" * 50)
    
    # 1. 检查并更新前端环境变量
    print("\n[1] 检查前端环境变量...")
    env_file = f"{deploy_dir}/saas-demo/.env.local"
    
    stdin, stdout, stderr = ssh.exec_command(f"cat {env_file} 2>/dev/null")
    current_env = stdout.read().decode('utf-8').strip()
    
    api_url = f"http://{server_ip}:8000/api/v1"
    
    if api_url not in current_env:
        print("更新前端环境变量...")
        env_content = f"""# API 配置
NEXT_PUBLIC_API_BASE_URL={api_url}
"""
        stdin, stdout, stderr = ssh.exec_command(f"cat > {env_file} << 'EOF'\n{env_content}EOF")
        stdout.read()
        print(f"[OK] 已更新 .env.local，API 地址: {api_url}")
    else:
        print("[OK] 环境变量已正确配置")
    
    # 2. 检查后端 CORS 配置
    print("\n[2] 检查后端 CORS 配置...")
    backend_env = f"{deploy_dir}/admin-backend/.env"
    
    stdin, stdout, stderr = ssh.exec_command(f"grep -i 'CORS_ORIGINS' {backend_env} 2>/dev/null || echo '未找到'")
    cors_line = stdout.read().decode('utf-8').strip()
    
    frontend_url = f"http://{server_ip}:3000"
    if frontend_url not in cors_line:
        print("更新后端 CORS 配置...")
        # 读取现有配置
        stdin, stdout, stderr = ssh.exec_command(f"cat {backend_env}")
        env_content = stdout.read().decode('utf-8')
        
        # 更新 CORS_ORIGINS
        if 'CORS_ORIGINS' in env_content:
            # 替换现有的 CORS_ORIGINS
            import re
            new_cors = f'CORS_ORIGINS=["http://localhost:3000","http://localhost:8000","{frontend_url}","http://{server_ip}:8000"]'
            env_content = re.sub(r'CORS_ORIGINS=.*', new_cors, env_content)
        else:
            # 添加 CORS_ORIGINS
            env_content += f'\nCORS_ORIGINS=["http://localhost:3000","http://localhost:8000","{frontend_url}","http://{server_ip}:8000"]\n'
        
        stdin, stdout, stderr = ssh.exec_command(f"cat > {backend_env} << 'EOF'\n{env_content}EOF")
        stdout.read()
        print(f"[OK] 已更新 CORS 配置，包含: {frontend_url}")
        
        # 重启后端服务
        print("重启后端服务以应用 CORS 配置...")
        ssh.exec_command("sudo systemctl restart smart-tg-backend")
        time.sleep(5)
    else:
        print("[OK] CORS 配置已包含前端地址")
    
    # 3. 验证修复
    print("\n[3] 验证修复结果...")
    time.sleep(3)
    
    stdin, stdout, stderr = ssh.exec_command("curl -s http://localhost:8000/health")
    backend_health = stdout.read().decode('utf-8').strip()
    print(f"后端健康检查: {backend_health}")
    
    stdin, stdout, stderr = ssh.exec_command("curl -s -o /dev/null -w '%{http_code}' http://localhost:3000 2>/dev/null || echo '000'")
    frontend_code = stdout.read().decode('utf-8').strip()
    print(f"前端状态码: HTTP {frontend_code}")
    
    # 测试 API 连接
    print("\n测试 API 连接...")
    stdin, stdout, stderr = ssh.exec_command(f"curl -s -X OPTIONS http://localhost:8000/api/v1/auth/me -H 'Origin: {frontend_url}' -H 'Access-Control-Request-Method: GET' -v 2>&1 | grep -i 'access-control' || echo 'CORS 头未找到'")
    cors_headers = stdout.read().decode('utf-8').strip()
    if cors_headers:
        print("CORS 响应头:")
        print(cors_headers)
    else:
        print("[WARNING] 未检测到 CORS 响应头")

def main():
    config = load_config()
    ssh = connect_server(config['host'], config['user'], config['password'])
    
    try:
        # 诊断
        diagnose(ssh, config['host'])
        
        # 修复
        fix_issues(ssh, config['deploy_dir'], config['host'])
        
        print("\n" + "=" * 50)
        print("修复完成！")
        print("=" * 50)
        print(f"\n访问地址:")
        print(f"  后端: http://{config['host']}:8000")
        print(f"  前端: http://{config['host']}:3000")
        print(f"\n如果前端仍然卡在认证检查，请:")
        print(f"  1. 清除浏览器缓存")
        print(f"  2. 检查浏览器控制台的错误信息（F12）")
        print(f"  3. 确认后端 API 可访问: http://{config['host']}:8000/api/v1/auth/me")
        
    finally:
        ssh.close()

if __name__ == "__main__":
    main()

