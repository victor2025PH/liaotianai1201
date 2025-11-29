#!/usr/bin/env python3
"""
配置域名綁定 - aikz.usdt2026.cc
"""

import paramiko
import sys

# 服務器配置
SERVER = "165.154.233.55"
USERNAME = "ubuntu"
PASSWORD = "Along2025!!!"
DOMAIN = "aikz.usdt2026.cc"
PROJECT_DIR = "/home/ubuntu/liaotian"

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
    
    stdin, stdout, stderr = client.exec_command(command, timeout=180)
    exit_code = stdout.channel.recv_exit_status()
    
    output = stdout.read().decode('utf-8', errors='ignore')
    error = stderr.read().decode('utf-8', errors='ignore')
    
    if output:
        for line in output.strip().split('\n')[-20:]:
            print(f"  {line}")
    if error and exit_code != 0:
        print(f"  錯誤: {error[:500]}")
    
    return exit_code == 0, output

def setup_domain():
    """配置域名"""
    client = None
    try:
        client = create_ssh_client()
        
        # 1. 安裝 Nginx
        print("\n" + "="*60)
        print("步驟 1: 安裝 Nginx")
        print("="*60)
        
        run_command(client, "sudo apt-get update -qq && sudo apt-get install -y nginx", "安裝 Nginx")
        
        # 2. 創建 Nginx 配置文件
        print("\n" + "="*60)
        print("步驟 2: 配置 Nginx 反向代理")
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

    # 後端 API
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
        
        # 寫入配置文件
        run_command(client, f"""
cat > /tmp/nginx-liaotian.conf << 'NGINX_EOF'
{nginx_config}
NGINX_EOF
sudo mv /tmp/nginx-liaotian.conf /etc/nginx/sites-available/{DOMAIN}
sudo ln -sf /etc/nginx/sites-available/{DOMAIN} /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
""", "創建 Nginx 配置文件")
        
        # 測試 Nginx 配置
        run_command(client, "sudo nginx -t", "測試 Nginx 配置")
        
        # 重啟 Nginx
        run_command(client, "sudo systemctl restart nginx && sudo systemctl enable nginx", "重啟 Nginx")
        
        # 3. 更新前端環境變量
        print("\n" + "="*60)
        print("步驟 3: 更新前端環境變量")
        print("="*60)
        
        run_command(client, f"""
cat > {PROJECT_DIR}/saas-demo/.env.local << 'EOF'
NEXT_PUBLIC_API_BASE_URL=http://{DOMAIN}/api/v1
EOF
cat {PROJECT_DIR}/saas-demo/.env.local
""", "更新前端 API 地址")
        
        # 重新構建前端
        run_command(client, f"""
cd {PROJECT_DIR}/saas-demo
npm run build
""", "重新構建前端")
        
        # 重啟前端服務
        run_command(client, "sudo systemctl restart liaotian-frontend", "重啟前端服務")
        
        # 4. 更新後端 CORS
        print("\n" + "="*60)
        print("步驟 4: 更新後端 CORS 配置")
        print("="*60)
        
        run_command(client, f"""
cat > {PROJECT_DIR}/admin-backend/.env << 'EOF'
DATABASE_URL=sqlite:///./admin.db
JWT_SECRET=$(cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 32 | head -n 1)
ADMIN_DEFAULT_EMAIL=admin@example.com
ADMIN_DEFAULT_PASSWORD=changeme123
CORS_ORIGINS=http://{DOMAIN},https://{DOMAIN},http://localhost:3000,http://165.154.233.55:3000,*
EOF
""", "更新 CORS 配置")
        
        run_command(client, "sudo systemctl restart liaotian-backend", "重啟後端服務")
        
        # 5. 開放 80 端口
        print("\n" + "="*60)
        print("步驟 5: 開放 80 端口")
        print("="*60)
        
        run_command(client, "sudo ufw allow 80/tcp", "開放 HTTP 端口")
        
        # 6. 驗證配置
        print("\n" + "="*60)
        print("步驟 6: 驗證服務狀態")
        print("="*60)
        
        run_command(client, "sudo systemctl status nginx --no-pager | head -10", "Nginx 狀態")
        run_command(client, "sudo systemctl status liaotian-backend --no-pager | head -5", "後端狀態")
        run_command(client, "sudo systemctl status liaotian-frontend --no-pager | head -5", "前端狀態")
        
        print("\n" + "="*60)
        print("✅ 域名配置完成!")
        print("="*60)
        print(f"""
⚠️  重要：請確保 DNS 已配置！

請在您的域名 DNS 管理面板中添加以下記錄：
  類型: A
  主機: aikz
  值: {SERVER}
  TTL: 600

配置完成後，您可以通過以下地址訪問：
  🌐 前端: http://{DOMAIN}
  🔧 API: http://{DOMAIN}/api/v1
  📚 文檔: http://{DOMAIN}/docs

登錄帳號：
  📧 郵箱: admin@example.com
  🔑 密碼: changeme123
""")
        
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
    success = setup_domain()
    sys.exit(0 if success else 1)

