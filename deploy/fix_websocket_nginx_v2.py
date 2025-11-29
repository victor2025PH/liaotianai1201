#!/usr/bin/env python3
"""
修复 Nginx WebSocket 配置 - 添加专门的 WebSocket location
"""
import paramiko

SERVER = "165.154.233.55"
USERNAME = "ubuntu"
PASSWORD = "Along2025!!!"

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(SERVER, username=USERNAME, password=PASSWORD, timeout=30)
print("✓ SSH 连接成功!")

# 新的 Nginx 配置（在 /api/ 之前添加 WebSocket 专用配置）
nginx_config = """server {
    listen 80;
    server_name aikz.usdt2026.cc;

    # WebSocket 支持 - 通知服务（必须在 /api/ 之前）
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

    # /api/workers/ -> /api/v1/workers（帶末尾斜杠）
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

    # 後端 API（包含 WebSocket 支持）
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

print("\n>>> 更新 Nginx 配置...")
stdin, stdout, stderr = client.exec_command("sudo tee /etc/nginx/sites-available/aikz.usdt2026.cc > /dev/null", get_pty=True)
stdin.write(nginx_config)
stdin.close()
stdout.channel.recv_exit_status()

# 测试配置
print("\n>>> 测试 Nginx 配置...")
stdin, stdout, stderr = client.exec_command("sudo nginx -t")
test_output = stdout.read().decode()
error_output = stderr.read().decode()
print(test_output)
if error_output:
    print(f"错误: {error_output}")

# 如果配置正确，重载 Nginx
if "syntax is ok" in test_output:
    print("\n>>> 重载 Nginx...")
    stdin, stdout, stderr = client.exec_command("sudo systemctl reload nginx")
    stdout.channel.recv_exit_status()
    print("✓ Nginx 已重载!")
    
    # 验证配置
    print("\n>>> 验证 Nginx 配置...")
    stdin, stdout, stderr = client.exec_command("sudo cat /etc/nginx/sites-available/aikz.usdt2026.cc | grep -A 10 'notifications/ws'")
    print(stdout.read().decode())
else:
    print("❌ Nginx 配置有误，请检查")

print("\n✅ WebSocket 配置更新完成！")
print("\n现在 WebSocket 路径应该可以正常工作了：")
print("  ws://aikz.usdt2026.cc/api/v1/notifications/ws/{user_email}")

client.close()


