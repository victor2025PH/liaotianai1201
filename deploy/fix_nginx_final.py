#!/usr/bin/env python3
import paramiko

SERVER = "165.154.233.55"
USERNAME = "ubuntu"
PASSWORD = "Along2025!!!"
DOMAIN = "aikz.usdt2026.cc"

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(SERVER, username=USERNAME, password=PASSWORD, timeout=30)
print("✓ SSH 連接成功!")

# 更新 Nginx 配置
nginx_config = f'''
server {{
    listen 80;
    server_name {DOMAIN};

    # Workers API（專門處理，放在最前面）
    location ~ ^/api/workers(/.*)?$ {{
        proxy_pass http://127.0.0.1:8000/api/v1/workers$1;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }}

    # 後端所有 API
    location /api/ {{
        proxy_pass http://127.0.0.1:8000/api/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        proxy_read_timeout 300;
    }}

    # 前端應用
    location / {{
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        proxy_read_timeout 86400;
    }}

    # 後端健康檢查
    location /health {{
        proxy_pass http://127.0.0.1:8000/health;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
    }}

    # 後端 API 文檔
    location /docs {{
        proxy_pass http://127.0.0.1:8000/docs;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
    }}

    location /openapi.json {{
        proxy_pass http://127.0.0.1:8000/openapi.json;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
    }}
}}
'''

print("\n>>> 更新 Nginx 配置")
stdin, stdout, stderr = client.exec_command(f"echo '{nginx_config}' | sudo tee /etc/nginx/sites-available/{DOMAIN}")
stdout.channel.recv_exit_status()

print("\n>>> 測試 Nginx 配置")
stdin, stdout, stderr = client.exec_command("sudo nginx -t")
print(stderr.read().decode())

print("\n>>> 重新加載 Nginx")
stdin, stdout, stderr = client.exec_command("sudo systemctl reload nginx")
stdout.channel.recv_exit_status()

print("\n>>> 測試 /api/workers/")
stdin, stdout, stderr = client.exec_command("curl -s http://127.0.0.1/api/workers/ | head -c 300")
print(stdout.read().decode())

print("\n✅ 完成!")
client.close()

