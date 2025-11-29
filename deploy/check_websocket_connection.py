#!/usr/bin/env python3
"""
检查并修复 WebSocket 连接问题
"""
import paramiko
import json

SERVER = "165.154.233.55"
USERNAME = "ubuntu"
PASSWORD = "Along2025!!!"

# 设置 UTF-8 编码
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

print("=" * 60)
print("WebSocket 连接问题诊断和修复")
print("=" * 60)

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(SERVER, username=USERNAME, password=PASSWORD, timeout=30)
print("[OK] SSH 连接成功!\n")

# 1. 检查后端服务状态
print(">>> 1. 检查后端服务状态...")
stdin, stdout, stderr = client.exec_command("sudo systemctl status liaotian-backend --no-pager | head -20")
output = stdout.read().decode()
print(output)

# 2. 检查后端日志中的 WebSocket 相关错误
print("\n>>> 2. 检查后端日志（最近 50 行，包含 WebSocket 相关）...")
stdin, stdout, stderr = client.exec_command("sudo journalctl -u liaotian-backend -n 50 --no-pager | grep -i -E 'websocket|ws|notifications' || echo '无 WebSocket 相关日志'")
output = stdout.read().decode()
print(output)

# 3. 检查 Nginx 配置
print("\n>>> 3. 检查 Nginx 配置...")
stdin, stdout, stderr = client.exec_command("sudo cat /etc/nginx/sites-available/aikz.usdt2026.cc")
nginx_config = stdout.read().decode()
print(nginx_config)

# 4. 检查 Nginx 配置语法
print("\n>>> 4. 检查 Nginx 配置语法...")
stdin, stdout, stderr = client.exec_command("sudo nginx -t")
test_output = stdout.read().decode()
error_output = stderr.read().decode()
print(test_output)
if error_output:
    print(f"错误: {error_output}")

# 5. 检查后端路由注册
print("\n>>> 5. 检查后端路由注册...")
stdin, stdout, stderr = client.exec_command("cd /home/ubuntu/liaotian/admin-backend && grep -r 'notifications' app/main.py app/api/__init__.py | head -10")
output = stdout.read().decode()
print(output if output else "未找到相关路由注册")

# 6. 测试后端 WebSocket 端点（如果可能）
print("\n>>> 6. 检查后端端口监听...")
stdin, stdout, stderr = client.exec_command("sudo netstat -tlnp | grep :8000 || sudo ss -tlnp | grep :8000")
output = stdout.read().decode()
print(output if output else "端口 8000 未监听")

# 7. 检查前端服务状态
print("\n>>> 7. 检查前端服务状态...")
stdin, stdout, stderr = client.exec_command("sudo systemctl status liaotian-frontend --no-pager 2>/dev/null | head -15 || pm2 list 2>/dev/null | head -10 || echo '前端服务状态未知'")
output = stdout.read().decode()
print(output)

print("\n" + "=" * 60)
print("诊断完成！")
print("=" * 60)

# 分析问题并提供修复建议
print("\n>>> 问题分析和修复建议：\n")

issues = []
fixes = []

# 检查 Nginx WebSocket 配置
if "/api/v1/notifications/ws" not in nginx_config:
    issues.append("❌ Nginx 配置中缺少 WebSocket 专用 location")
    fixes.append("需要在 Nginx 配置中添加 /api/v1/notifications/ws 的 WebSocket 支持")

if "proxy_set_header Upgrade" not in nginx_config or "proxy_set_header Connection" not in nginx_config:
    issues.append("❌ Nginx 配置中缺少 WebSocket 必需的 Upgrade 和 Connection 头")
    fixes.append("需要添加 proxy_set_header Upgrade 和 Connection 头")

if "proxy_read_timeout 86400" not in nginx_config:
    issues.append("⚠️  Nginx WebSocket 超时设置可能不足")
    fixes.append("建议设置 proxy_read_timeout 86400 以支持长连接")

if not issues:
    print("[OK] Nginx 配置看起来正常")
else:
    print("发现的问题：")
    for issue in issues:
        print(f"  {issue}")
    print("\n修复建议：")
    for i, fix in enumerate(fixes, 1):
        print(f"  {i}. {fix}")

client.close()

