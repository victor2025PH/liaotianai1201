#!/usr/bin/env python3
"""
修復 Workers API 路由
"""

import paramiko
import sys

SERVER = "165.154.233.55"
USERNAME = "ubuntu"
PASSWORD = "Along2025!!!"
DOMAIN = "aikz.usdt2026.cc"

def create_ssh_client():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    print(f"正在連接服務器 {SERVER}...")
    client.connect(SERVER, username=USERNAME, password=PASSWORD, timeout=30)
    print("✓ SSH 連接成功!")
    return client

def run_command(client, command, description=""):
    if description:
        print(f"\n>>> {description}")
    
    stdin, stdout, stderr = client.exec_command(command, timeout=120)
    exit_code = stdout.channel.recv_exit_status()
    
    output = stdout.read().decode('utf-8', errors='ignore')
    error = stderr.read().decode('utf-8', errors='ignore')
    
    if output:
        for line in output.strip().split('\n')[-15:]:
            print(f"  {line}")
    if error and exit_code != 0:
        print(f"  錯誤: {error[:500]}")
    
    return exit_code == 0, output

def fix_route():
    client = None
    try:
        client = create_ssh_client()
        
        print("\n" + "="*60)
        print("更新 Nginx 配置 - 添加 /api/workers 路由")
        print("="*60)
        
        nginx_config = f'''
server {{
    listen 80;
    server_name {DOMAIN};

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

    # Workers API（不帶 /v1 前綴）- 轉發到 /api/v1/workers
    location /api/workers {{
        rewrite ^/api/workers(.*)$ /api/v1/workers$1 break;
        proxy_pass http://127.0.0.1:8000;
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
        
        run_command(client, f"""
cat > /tmp/nginx-liaotian.conf << 'NGINX_EOF'
{nginx_config}
NGINX_EOF
sudo mv /tmp/nginx-liaotian.conf /etc/nginx/sites-available/{DOMAIN}
""", "更新 Nginx 配置")
        
        run_command(client, "sudo nginx -t", "測試 Nginx 配置")
        run_command(client, "sudo systemctl reload nginx", "重新加載 Nginx")
        
        # 測試 API
        run_command(client, """
echo "測試 /api/workers/ 端點..."
curl -s http://localhost/api/workers/ | head -c 200
echo ""
""", "測試 Workers API")
        
        print("\n" + "="*60)
        print("✅ 路由已修復")
        print("="*60)
        
        return True
        
    except Exception as e:
        print(f"❌ 錯誤: {e}")
        return False
    finally:
        if client:
            client.close()

if __name__ == "__main__":
    fix_route()

