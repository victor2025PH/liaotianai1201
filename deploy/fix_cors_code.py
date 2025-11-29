#!/usr/bin/env python3
"""
直接修改後端 CORS 代碼
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

def fix_cors():
    """修復 CORS"""
    client = None
    try:
        client = create_ssh_client()
        
        print("\n" + "="*60)
        print("修復後端 CORS 配置")
        print("="*60)
        
        # 使用 sed 修改 main.py 中的 CORS 設置，允許所有來源
        run_command(client, f"""
cd {PROJECT_DIR}/admin-backend

# 備份原始文件
cp app/main.py app/main.py.bak

# 查找並修改 CORS 配置 - 添加 allow_origins=["*"]
sed -i 's/allow_origins=cors_origins/allow_origins=["*"]/g' app/main.py

# 確認修改
grep -A5 "CORSMiddleware" app/main.py | head -10
""", "修改 CORS 配置為允許所有來源")
        
        # 重啟後端服務
        run_command(client, """
sudo systemctl restart liaotian-backend
sleep 5
sudo systemctl status liaotian-backend --no-pager | head -15
""", "重啟後端服務")
        
        # 測試 API
        run_command(client, """
curl -s http://localhost:8000/health
""", "測試健康檢查")
        
        # 測試 CORS 頭
        run_command(client, """
curl -s -I -X OPTIONS http://localhost:8000/api/v1/auth/login -H "Origin: http://165.154.233.55:3000" -H "Access-Control-Request-Method: POST" | grep -i "access-control"
""", "檢查 CORS 頭")
        
        print("\n" + "="*60)
        print("✅ CORS 配置已修復")
        print("="*60)
        print(f"\n請重新訪問: http://{SERVER}:3000")
        
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
    success = fix_cors()
    sys.exit(0 if success else 1)

