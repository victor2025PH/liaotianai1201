#!/usr/bin/env python3
"""
修復 CORS 配置
"""

import paramiko
import sys

# 服務器配置
SERVER = "165.154.233.55"
USERNAME = "ubuntu"
PASSWORD = "Along2025!!!"
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
    print(f"$ {command[:80]}..." if len(command) > 80 else f"$ {command}")
    
    stdin, stdout, stderr = client.exec_command(command, timeout=120)
    exit_code = stdout.channel.recv_exit_status()
    
    output = stdout.read().decode('utf-8', errors='ignore')
    error = stderr.read().decode('utf-8', errors='ignore')
    
    if output:
        for line in output.strip().split('\n')[-15:]:
            print(f"  {line}")
    if error and exit_code != 0:
        print(f"  (stderr) {error[:300]}")
    
    return exit_code == 0, output

def fix_cors():
    """修復 CORS 配置"""
    client = None
    try:
        client = create_ssh_client()
        
        # 更新 .env 文件中的 CORS 配置
        print("\n" + "="*60)
        print("修復 CORS 配置")
        print("="*60)
        
        run_command(client, f"""
cat > {PROJECT_DIR}/admin-backend/.env << 'EOF'
DATABASE_URL=sqlite:///./admin.db
JWT_SECRET=$(cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 32 | head -n 1)
ADMIN_DEFAULT_EMAIL=admin@example.com
ADMIN_DEFAULT_PASSWORD=changeme123
CORS_ORIGINS=http://165.154.233.55:3000,http://165.154.233.55,http://localhost:3000,*
EOF
cat {PROJECT_DIR}/admin-backend/.env
""", "更新 .env 文件")
        
        # 重啟後端服務
        run_command(client, """
sudo systemctl restart liaotian-backend
sleep 3
sudo systemctl status liaotian-backend --no-pager | head -15
""", "重啟後端服務")
        
        # 測試 API
        run_command(client, "curl -s http://localhost:8000/", "測試後端 API")
        run_command(client, "curl -s http://localhost:8000/health", "測試健康檢查")
        
        print("\n" + "="*60)
        print("CORS 配置已修復")
        print("="*60)
        
        return True
        
    except Exception as e:
        print(f"❌ 錯誤: {e}")
        return False
    finally:
        if client:
            client.close()

if __name__ == "__main__":
    success = fix_cors()
    sys.exit(0 if success else 1)

