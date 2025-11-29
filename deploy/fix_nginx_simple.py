#!/usr/bin/env python3
import paramiko

SERVER = "165.154.233.55"
USERNAME = "ubuntu"
PASSWORD = "Along2025!!!"

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(SERVER, username=USERNAME, password=PASSWORD, timeout=30)
print("✓ SSH 連接成功!")

# 簡單的 Nginx 配置 - 用 rewrite 規則
nginx_cmd = '''
cat > /tmp/nginx-liaotian.conf << 'ENDNGINX'
server {
    listen 80;
    server_name aikz.usdt2026.cc;

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
ENDNGINX

sudo mv /tmp/nginx-liaotian.conf /etc/nginx/sites-available/aikz.usdt2026.cc
sudo nginx -t && sudo systemctl reload nginx
'''

print("\n>>> 更新 Nginx")
stdin, stdout, stderr = client.exec_command(nginx_cmd)
print(stdout.read().decode())
print(stderr.read().decode())

import time
time.sleep(2)

# 測試
print("\n>>> 測試 Nginx /api/workers/")
stdin, stdout, stderr = client.exec_command("curl -s http://127.0.0.1/api/workers/ | head -c 400")
print(stdout.read().decode())

print("\n>>> 測試從域名")
stdin, stdout, stderr = client.exec_command("curl -s http://aikz.usdt2026.cc/api/workers/ | head -c 400")
print(stdout.read().decode())

print("\n✅ 完成!")
client.close()

