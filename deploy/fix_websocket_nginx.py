#!/usr/bin/env python3
"""
修复 Nginx WebSocket 配置
"""
import paramiko

SERVER = "165.154.233.55"
USERNAME = "ubuntu"
PASSWORD = "Along2025!!!"

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(SERVER, username=USERNAME, password=PASSWORD, timeout=30)
print("✓ SSH 连接成功!")

# 读取当前 Nginx 配置
print("\n>>> 读取当前 Nginx 配置...")
stdin, stdout, stderr = client.exec_command("sudo cat /etc/nginx/sites-available/aikz.usdt2026.cc")
current_config = stdout.read().decode()
print(current_config)

# 检查是否已有 WebSocket 配置
if "proxy_http_version 1.1" in current_config and "Upgrade" in current_config:
    print("\n✓ WebSocket 配置已存在")
else:
    print("\n>>> 更新 Nginx 配置以支持 WebSocket...")
    
    # 新的 Nginx 配置（支持 WebSocket）
    nginx_config = """server {
    listen 80;
    server_name aikz.usdt2026.cc;

    # WebSocket 支持 - 通知服务
    location /api/v1/notifications/ws {
        proxy_pass http://localhost:8000/api/v1/notifications/ws;
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

    # API 路由
    location /api/v1/ {
        proxy_pass http://localhost:8000/api/v1/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # 前端路由
    location / {
        proxy_pass http://localhost:3000/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
"""
    
    # 写入配置文件
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
    else:
        print("❌ Nginx 配置有误，请检查")

# 检查后端服务状态
print("\n>>> 检查后端服务状态...")
stdin, stdout, stderr = client.exec_command("sudo systemctl status liaotian-backend --no-pager | head -15")
print(stdout.read().decode())

# 检查后端日志中的 WebSocket 相关错误
print("\n>>> 检查后端日志（最近 20 行）...")
stdin, stdout, stderr = client.exec_command("sudo journalctl -u liaotian-backend -n 20 --no-pager | grep -i websocket || echo '无 WebSocket 相关日志'")
print(stdout.read().decode())

print("\n✅ WebSocket 配置检查完成！")
client.close()


