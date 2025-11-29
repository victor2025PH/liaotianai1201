#!/usr/bin/env python3
"""
開放防火牆端口
"""

import paramiko
import sys

# 服務器配置
SERVER = "165.154.233.55"
USERNAME = "ubuntu"
PASSWORD = "Along2025!!!"

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
    print(f"$ {command}")
    
    stdin, stdout, stderr = client.exec_command(command, timeout=60)
    exit_code = stdout.channel.recv_exit_status()
    
    output = stdout.read().decode('utf-8', errors='ignore')
    error = stderr.read().decode('utf-8', errors='ignore')
    
    if output:
        for line in output.strip().split('\n'):
            print(f"  {line}")
    if error:
        print(f"  (stderr) {error[:500]}")
    
    return exit_code == 0, output

def open_ports():
    """開放防火牆端口"""
    client = None
    try:
        client = create_ssh_client()
        
        # 檢查防火牆狀態
        print("\n" + "="*60)
        print("檢查和配置防火牆")
        print("="*60)
        
        run_command(client, "sudo ufw status", "防火牆狀態")
        
        # 開放端口
        run_command(client, "sudo ufw allow 22/tcp", "允許 SSH")
        run_command(client, "sudo ufw allow 80/tcp", "允許 HTTP")
        run_command(client, "sudo ufw allow 443/tcp", "允許 HTTPS")
        run_command(client, "sudo ufw allow 3000/tcp", "允許前端端口 3000")
        run_command(client, "sudo ufw allow 8000/tcp", "允許後端端口 8000")
        
        # 啟用防火牆（如果未啟用）
        run_command(client, "echo 'y' | sudo ufw enable 2>/dev/null || true", "啟用防火牆")
        
        # 顯示最終狀態
        run_command(client, "sudo ufw status verbose", "最終防火牆狀態")
        
        # 檢查 iptables
        run_command(client, "sudo iptables -L INPUT -n | head -20", "iptables 規則")
        
        print("\n" + "="*60)
        print("端口已開放")
        print("="*60)
        print(f"""
請訪問：
  前端: http://{SERVER}:3000
  後端: http://{SERVER}:8000

注意：如果仍然無法訪問，可能需要在雲服務商控制台的安全組中開放端口：
  - 3000 (TCP) - 前端
  - 8000 (TCP) - 後端 API
""")
        
        return True
        
    except Exception as e:
        print(f"❌ 錯誤: {e}")
        return False
    finally:
        if client:
            client.close()

if __name__ == "__main__":
    success = open_ports()
    sys.exit(0 if success else 1)

