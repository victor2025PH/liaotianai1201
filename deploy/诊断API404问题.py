# -*- coding: utf-8 -*-
"""诊断 API 404 错误"""
import paramiko
import sys
import io

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

SERVER = "165.154.233.55"
USERNAME = "ubuntu"
PASSWORD = "Along2025!!!"

def exec_cmd(ssh, cmd):
    stdin, stdout, stderr = ssh.exec_command(cmd)
    output = stdout.read().decode('utf-8', errors='ignore')
    error = stderr.read().decode('utf-8', errors='ignore')
    return output.strip(), error.strip()

print("=" * 60)
print("诊断 API 404 错误")
print("=" * 60)
print()

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(SERVER, username=USERNAME, password=PASSWORD, timeout=30)
    print("[OK] 已连接服务器\n")
    
    # 1. 检查后端服务状态
    print(">>> [1] 检查后端服务状态...")
    output, _ = exec_cmd(ssh, "sudo systemctl status liaotian-backend --no-pager | head -15")
    print(output)
    print()
    
    # 2. 检查后端是否监听端口 8000
    print(">>> [2] 检查后端端口监听...")
    output, _ = exec_cmd(ssh, "sudo ss -tlnp | grep :8000")
    print(output if output else "后端未监听端口 8000")
    print()
    
    # 3. 测试后端 API 端点（直接访问）
    print(">>> [3] 测试后端 API 端点（直接访问 localhost:8000）...")
    endpoints = [
        "/api/v1/dashboard",
        "/api/v1/users/me",
        "/api/v1/notifications?skip=0&limit=20",
        "/health"
    ]
    
    for endpoint in endpoints:
        output, _ = exec_cmd(ssh, f"curl -s -o /dev/null -w '%{{http_code}}' http://localhost:8000{endpoint} 2>&1")
        print(f"  {endpoint}: {output}")
    print()
    
    # 4. 检查 Nginx API 路由配置
    print(">>> [4] 检查 Nginx API 路由配置...")
    output, _ = exec_cmd(ssh, "sudo grep -A 10 'location /api/' /etc/nginx/sites-available/aikz.usdt2026.cc")
    print(output)
    print()
    
    # 5. 测试通过 Nginx 访问 API
    print(">>> [5] 测试通过 Nginx 访问 API...")
    output, _ = exec_cmd(ssh, "curl -s -o /dev/null -w '%{http_code}' http://localhost/api/v1/health 2>&1")
    print(f"  /api/v1/health: {output}")
    print()
    
    # 6. 检查后端日志
    print(">>> [6] 检查后端日志（最近 20 行）...")
    output, _ = exec_cmd(ssh, "sudo journalctl -u liaotian-backend -n 20 --no-pager | tail -10")
    print(output if output else "无日志")
    print()
    
    # 7. 检查 Nginx 错误日志
    print(">>> [7] 检查 Nginx 错误日志（最近 10 行）...")
    output, _ = exec_cmd(ssh, "sudo tail -10 /var/log/nginx/error.log 2>&1")
    print(output if output else "无错误日志")
    print()
    
    # 8. 检查后端进程
    print(">>> [8] 检查后端进程...")
    output, _ = exec_cmd(ssh, "ps aux | grep -E 'uvicorn|python.*main.py|liaotian-backend' | grep -v grep")
    print(output if output else "未找到后端进程")
    print()
    
    print("=" * 60)
    print("诊断完成")
    print("=" * 60)
    print("\n可能的原因：")
    print("1. 后端服务未运行或崩溃")
    print("2. Nginx 配置中的 API 路由有问题")
    print("3. 后端服务监听地址不正确")
    print("4. 防火墙阻止了连接")
    
    ssh.close()
    
except Exception as e:
    print(f"\n[错误] {e}")
    import traceback
    traceback.print_exc()

print("\n完成！")

