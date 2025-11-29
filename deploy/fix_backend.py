#!/usr/bin/env python3
"""
修復後端服務啟動問題
"""

import paramiko
import sys
import time

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
    print(f"$ {command[:100]}..." if len(command) > 100 else f"$ {command}")
    
    stdin, stdout, stderr = client.exec_command(command, timeout=300)
    exit_code = stdout.channel.recv_exit_status()
    
    output = stdout.read().decode('utf-8', errors='ignore')
    error = stderr.read().decode('utf-8', errors='ignore')
    
    if output:
        lines = output.strip().split('\n')
        for line in lines[-30:]:
            print(f"  {line}")
    
    if error:
        print(f"錯誤輸出: {error[:1000]}")
    
    return exit_code == 0, output, error

def fix_backend():
    """修復後端服務"""
    client = None
    try:
        client = create_ssh_client()
        
        # 1. 檢查後端服務日誌
        print("\n" + "="*60)
        print("步驟 1: 檢查後端服務日誌")
        print("="*60)
        
        run_command(client, "sudo journalctl -u liaotian-backend -n 50 --no-pager", "後端服務日誌")
        
        # 2. 安裝缺少的依賴
        print("\n" + "="*60)
        print("步驟 2: 安裝額外依賴")
        print("="*60)
        
        run_command(client, f"""
cd {PROJECT_DIR}/admin-backend
source .venv/bin/activate
pip install pyrogram pyyaml openai TgCrypto
""", "安裝 pyrogram, pyyaml, openai, TgCrypto")
        
        # 3. 重新啟動後端服務
        print("\n" + "="*60)
        print("步驟 3: 重新啟動後端服務")
        print("="*60)
        
        run_command(client, """
sudo systemctl restart liaotian-backend
sleep 5
sudo systemctl status liaotian-backend --no-pager -l
""", "重新啟動並檢查狀態")
        
        # 4. 測試健康檢查
        print("\n" + "="*60)
        print("步驟 4: 測試健康檢查")
        print("="*60)
        
        run_command(client, "curl -s http://localhost:8000/health", "後端健康檢查")
        run_command(client, "curl -s http://localhost:8000/", "後端根路徑")
        
        # 5. 檢查服務日誌
        print("\n" + "="*60)
        print("步驟 5: 最新服務日誌")
        print("="*60)
        
        run_command(client, "sudo journalctl -u liaotian-backend -n 30 --no-pager", "最新後端日誌")
        
        print("\n" + "="*60)
        print("修復完成")
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
    success = fix_backend()
    sys.exit(0 if success else 1)

