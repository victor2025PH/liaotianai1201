#!/usr/bin/env python3
"""
自動部署腳本 - 部署到馬尼拉服務器
服務器: 165.154.233.55
"""

import paramiko
import sys
import time

# 服務器配置
SERVER = "165.154.233.55"
USERNAME = "ubuntu"
PASSWORD = "Along2025!!!"
GITHUB_REPO = "https://github.com/victor2025PH/loaotian1127.git"
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
    print(f"$ {command[:100]}..." if len(command) > 100 else f"$ {command}")
    
    stdin, stdout, stderr = client.exec_command(command, timeout=300)
    exit_code = stdout.channel.recv_exit_status()
    
    output = stdout.read().decode('utf-8', errors='ignore')
    error = stderr.read().decode('utf-8', errors='ignore')
    
    if output:
        # 只顯示最後 20 行
        lines = output.strip().split('\n')
        if len(lines) > 20:
            print(f"... ({len(lines) - 20} 行省略)")
        for line in lines[-20:]:
            print(f"  {line}")
    
    if error and exit_code != 0:
        print(f"錯誤: {error[:500]}")
    
    return exit_code == 0, output, error

def deploy():
    """執行部署"""
    client = None
    try:
        client = create_ssh_client()
        
        # 1. 更新系統和安裝基礎工具
        print("\n" + "="*60)
        print("步驟 1: 更新系統和安裝基礎工具")
        print("="*60)
        
        run_command(client, "sudo apt-get update -qq", "更新軟體源")
        run_command(client, "sudo apt-get install -y git curl unzip python3-venv python3-pip", "安裝基礎工具")
        
        # 2. 安裝 Node.js 20.x
        print("\n" + "="*60)
        print("步驟 2: 安裝 Node.js 20.x")
        print("="*60)
        
        run_command(client, """
if ! command -v node &> /dev/null || [[ $(node -v | cut -d. -f1 | tr -d 'v') -lt 20 ]]; then
    curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
    sudo apt-get install -y nodejs
fi
node -v && npm -v
""", "安裝/檢查 Node.js")
        
        # 3. 克隆或更新代碼
        print("\n" + "="*60)
        print("步驟 3: 從 GitHub 獲取代碼")
        print("="*60)
        
        run_command(client, f"""
if [ -d "{PROJECT_DIR}" ]; then
    cd {PROJECT_DIR} && git fetch --all && git reset --hard origin/master && git pull
else
    git clone {GITHUB_REPO} {PROJECT_DIR}
fi
""", "克隆/更新代碼")
        
        # 4. 配置後端
        print("\n" + "="*60)
        print("步驟 4: 配置後端環境")
        print("="*60)
        
        run_command(client, f"""
cd {PROJECT_DIR}/admin-backend
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
""", "創建虛擬環境並安裝依賴")
        
        # 創建後端 .env 文件
        run_command(client, f"""
cat > {PROJECT_DIR}/admin-backend/.env << 'EOF'
DATABASE_URL=sqlite:///./admin.db
JWT_SECRET=$(openssl rand -hex 32)
ADMIN_DEFAULT_EMAIL=admin@example.com
ADMIN_DEFAULT_PASSWORD=changeme123
CORS_ORIGINS=http://localhost:3000,http://165.154.233.55:3000,http://165.154.233.55
EOF
""", "創建後端 .env 配置")
        
        # 初始化數據庫
        run_command(client, f"""
cd {PROJECT_DIR}/admin-backend
source .venv/bin/activate
python reset_admin_user.py
""", "初始化數據庫和管理員用戶")
        
        # 5. 配置前端
        print("\n" + "="*60)
        print("步驟 5: 配置前端環境")
        print("="*60)
        
        run_command(client, f"""
cd {PROJECT_DIR}/saas-demo
npm install
""", "安裝前端依賴")
        
        # 創建前端 .env.local 文件
        run_command(client, f"""
cat > {PROJECT_DIR}/saas-demo/.env.local << 'EOF'
NEXT_PUBLIC_API_BASE_URL=http://165.154.233.55:8000/api/v1
EOF
""", "創建前端 .env.local 配置")
        
        run_command(client, f"""
cd {PROJECT_DIR}/saas-demo
npm run build
""", "構建前端應用")
        
        # 6. 創建 systemd 服務
        print("\n" + "="*60)
        print("步驟 6: 配置 systemd 服務")
        print("="*60)
        
        # 後端服務
        run_command(client, f"""
sudo tee /etc/systemd/system/liaotian-backend.service > /dev/null << 'EOF'
[Unit]
Description=Liaotian Backend API
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory={PROJECT_DIR}/admin-backend
Environment=PATH={PROJECT_DIR}/admin-backend/.venv/bin:/usr/bin:/bin
ExecStart={PROJECT_DIR}/admin-backend/.venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF
""", "創建後端服務文件")
        
        # 前端服務
        run_command(client, f"""
sudo tee /etc/systemd/system/liaotian-frontend.service > /dev/null << 'EOF'
[Unit]
Description=Liaotian Frontend
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory={PROJECT_DIR}/saas-demo
Environment=PORT=3000
ExecStart=/usr/bin/npm start
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF
""", "創建前端服務文件")
        
        # 7. 啟動服務
        print("\n" + "="*60)
        print("步驟 7: 啟動服務")
        print("="*60)
        
        run_command(client, """
sudo systemctl daemon-reload
sudo systemctl enable liaotian-backend liaotian-frontend
sudo systemctl restart liaotian-backend
sleep 3
sudo systemctl restart liaotian-frontend
""", "重新加載並啟動服務")
        
        # 8. 驗證部署
        print("\n" + "="*60)
        print("步驟 8: 驗證部署")
        print("="*60)
        
        time.sleep(5)
        
        run_command(client, "sudo systemctl status liaotian-backend --no-pager -l | head -20", "後端服務狀態")
        run_command(client, "sudo systemctl status liaotian-frontend --no-pager -l | head -20", "前端服務狀態")
        
        run_command(client, "curl -s http://localhost:8000/health || echo '後端健康檢查失敗'", "後端健康檢查")
        run_command(client, "curl -s -o /dev/null -w '%{http_code}' http://localhost:3000 || echo '前端檢查失敗'", "前端狀態碼")
        
        print("\n" + "="*60)
        print("✅ 部署完成!")
        print("="*60)
        print(f"""
訪問地址：
  前端: http://{SERVER}:3000
  後端 API: http://{SERVER}:8000
  API 文檔: http://{SERVER}:8000/docs

登錄帳號：
  郵箱: admin@example.com
  密碼: changeme123
""")
        
        return True
        
    except paramiko.AuthenticationException:
        print("❌ SSH 認證失敗，請檢查用戶名和密碼")
        return False
    except paramiko.SSHException as e:
        print(f"❌ SSH 連接錯誤: {e}")
        return False
    except Exception as e:
        print(f"❌ 部署失敗: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        if client:
            client.close()

if __name__ == "__main__":
    success = deploy()
    sys.exit(0 if success else 1)

