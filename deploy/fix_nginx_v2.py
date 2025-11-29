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

# 使用 heredoc 寫入配置
cmd = '''
cat > /tmp/nginx-liaotian.conf << 'ENDCONFIG'
server {
    listen 80;
    server_name aikz.usdt2026.cc;

    # Workers API - 轉發 /api/workers 到 /api/v1/workers
    location ~ ^/api/workers(/.*)?$ {
        set $worker_path $1;
        if ($worker_path = "") {
            set $worker_path "/";
        }
        proxy_pass http://127.0.0.1:8000/api/v1/workers$worker_path;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    # 後端 API
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
ENDCONFIG
sudo mv /tmp/nginx-liaotian.conf /etc/nginx/sites-available/aikz.usdt2026.cc
'''

print("\n>>> 寫入 Nginx 配置")
stdin, stdout, stderr = client.exec_command(cmd)
stdout.channel.recv_exit_status()
print(stderr.read().decode() or "OK")

print("\n>>> 測試配置")
stdin, stdout, stderr = client.exec_command("sudo nginx -t 2>&1")
print(stdout.read().decode())

print("\n>>> 重載 Nginx")
stdin, stdout, stderr = client.exec_command("sudo systemctl reload nginx")
stdout.channel.recv_exit_status()

import time
time.sleep(1)

print("\n>>> 測試 /api/workers/")
stdin, stdout, stderr = client.exec_command("curl -sv http://127.0.0.1/api/workers/ 2>&1 | tail -20")
print(stdout.read().decode())

client.close()

