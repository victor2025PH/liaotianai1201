#!/usr/bin/env python3
"""
修復 Nginx 配置以支持 Worker API
"""

import paramiko
import sys

# 服務器配置
SERVER = "165.154.233.55"
USERNAME = "ubuntu"
PASSWORD = "Along2025!!!"
DOMAIN = "aikz.usdt2026.cc"

def create_ssh_client():
    """創建 SSH 客戶端"""
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    print(f"正在連接服務器 {SERVER}...")
    client.connect(SERVER, username=USERNAME, password=PASSWORD, timeout=30)
    print("✓ SSH 連接成功!")
    return client

def run_command(client, command, description=""):
    """執行遠程命令"""
    if description:
        print(f"\n>>> {description}")
    
    stdin, stdout, stderr = client.exec_command(command, timeout=120)
    exit_code = stdout.channel.recv_exit_status()
    
    output = stdout.read().decode('utf-8', errors='ignore')
    error = stderr.read().decode('utf-8', errors='ignore')
    
    if output:
        for line in output.strip().split('\n')[-20:]:
            print(f"  {line}")
    if error and exit_code != 0:
        print(f"  錯誤: {error[:500]}")
    
    return exit_code == 0, output

def fix_nginx():
    """修復 Nginx 配置"""
    client = None
    try:
        client = create_ssh_client()
        
        print("\n" + "="*60)
        print("更新 Nginx 配置")
        print("="*60)
        
        # 更新 Nginx 配置
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

    # 後端所有 API（包括 /api/v1 和 /api/workers）
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
        
        # 測試直接訪問後端
        run_command(client, """
echo "直接測試後端 Worker API..."
curl -s -X POST http://localhost:8000/api/workers/heartbeat \\
    -H "Content-Type: application/json" \\
    -d '{"computer_id": "test", "status": "online", "accounts": []}'
""", "測試後端 Worker API")
        
        print("\n" + "="*60)
        print("✅ Nginx 配置已更新")
        print("="*60)
        
        return True
        
    except Exception as e:
        print(f"❌ 錯誤: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        if client:
            client.close()

if __name__ == "__main__":
    success = fix_nginx()
    sys.exit(0 if success else 1)

