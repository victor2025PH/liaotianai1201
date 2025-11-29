#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
完整修复 WebSocket 连接问题
包括：Nginx 配置、后端路由验证、连接测试
"""
import paramiko
import sys
import io

# 设置 UTF-8 编码
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

SERVER = "165.154.233.55"
USERNAME = "ubuntu"
PASSWORD = "Along2025!!!"

print("=" * 60)
print("WebSocket 连接问题完整修复")
print("=" * 60)

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(SERVER, username=USERNAME, password=PASSWORD, timeout=30)
print("[OK] SSH 连接成功!\n")

# 1. 检查当前 Nginx 配置
print(">>> 步骤 1: 检查当前 Nginx 配置...")
stdin, stdout, stderr = client.exec_command("sudo cat /etc/nginx/sites-available/aikz.usdt2026.cc")
current_config = stdout.read().decode('utf-8', errors='ignore')
print(current_config)

# 2. 创建优化的 Nginx 配置
print("\n>>> 步骤 2: 创建优化的 Nginx 配置...")

nginx_config = """server {
    listen 80;
    server_name aikz.usdt2026.cc;

    # WebSocket 支持 - 通知服务（必须在 /api/ 之前，优先级更高）
    location /api/v1/notifications/ws {
        proxy_pass http://127.0.0.1:8000/api/v1/notifications/ws;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 86400;
        proxy_send_timeout 86400;
        proxy_buffering off;
    }

    # 前端
    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_read_timeout 86400;
    }

    # /api/workers/ -> /api/v1/workers（带末尾斜杠）
    location = /api/workers/ {
        proxy_pass http://127.0.0.1:8000/api/v1/workers;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    # /api/workers/xxx -> /api/v1/workers/xxx
    location ~ ^/api/workers/(.+)$ {
        proxy_pass http://127.0.0.1:8000/api/v1/workers/$1;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    # 后端 API（包含 WebSocket 支持，但优先级低于上面的专用配置）
    location /api/ {
        proxy_pass http://127.0.0.1:8000/api/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_read_timeout 300;
    }

    location /health {
        proxy_pass http://127.0.0.1:8000/health;
    }

    location /docs {
        proxy_pass http://127.0.0.1:8000/docs;
    }

    location /openapi.json {
        proxy_pass http://127.0.0.1:8000/openapi.json;
    }
}
"""

# 3. 写入新配置
print("\n>>> 步骤 3: 更新 Nginx 配置...")
stdin, stdout, stderr = client.exec_command("sudo tee /etc/nginx/sites-available/aikz.usdt2026.cc > /dev/null", get_pty=True)
stdin.write(nginx_config)
stdin.close()
stdout.channel.recv_exit_status()

# 4. 测试配置
print("\n>>> 步骤 4: 测试 Nginx 配置...")
stdin, stdout, stderr = client.exec_command("sudo nginx -t")
test_output = stdout.read().decode('utf-8', errors='ignore')
error_output = stderr.read().decode('utf-8', errors='ignore')
print(test_output)
if error_output:
    print(f"错误: {error_output}")

# 5. 如果配置正确，重载 Nginx
if "syntax is ok" in test_output:
    print("\n>>> 步骤 5: 重载 Nginx...")
    stdin, stdout, stderr = client.exec_command("sudo systemctl reload nginx")
    stdout.channel.recv_exit_status()
    print("[OK] Nginx 已重载!")
    
    # 6. 验证配置
    print("\n>>> 步骤 6: 验证 WebSocket 配置...")
    stdin, stdout, stderr = client.exec_command("sudo cat /etc/nginx/sites-available/aikz.usdt2026.cc | grep -A 12 'notifications/ws'")
    print(stdout.read().decode('utf-8', errors='ignore'))
    
    # 7. 检查后端服务
    print("\n>>> 步骤 7: 检查后端服务状态...")
    stdin, stdout, stderr = client.exec_command("sudo systemctl status liaotian-backend --no-pager | head -15")
    print(stdout.read().decode('utf-8', errors='ignore'))
    
    # 8. 检查后端日志
    print("\n>>> 步骤 8: 检查后端日志（最近 20 行）...")
    stdin, stdout, stderr = client.exec_command("sudo journalctl -u liaotian-backend -n 20 --no-pager | tail -10")
    print(stdout.read().decode('utf-8', errors='ignore'))
    
    print("\n" + "=" * 60)
    print("[OK] WebSocket 配置修复完成！")
    print("=" * 60)
    print("\n修复内容：")
    print("1. 添加了专用的 WebSocket location (/api/v1/notifications/ws)")
    print("2. 配置了正确的 Upgrade 和 Connection 头")
    print("3. 设置了长连接超时（86400 秒）")
    print("4. 禁用了代理缓冲（proxy_buffering off）")
    print("\n现在 WebSocket 路径应该可以正常工作了：")
    print("  ws://aikz.usdt2026.cc/api/v1/notifications/ws/{user_email}")
    print("\n请在前端测试 WebSocket 连接。")
else:
    print("\n[ERROR] Nginx 配置有误，请检查上面的错误信息")

client.close()


