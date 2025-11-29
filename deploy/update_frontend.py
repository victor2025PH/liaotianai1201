#!/usr/bin/env python3
"""
更新前端到服務器
"""
import paramiko
import os
import tarfile
import io

SERVER = "165.154.233.55"
USERNAME = "ubuntu"
PASSWORD = "Along2025!!!"
PROJECT_DIR = "/home/ubuntu/liaotian"

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
    
    stdin, stdout, stderr = client.exec_command(command, timeout=300)
    exit_code = stdout.channel.recv_exit_status()
    
    output = stdout.read().decode('utf-8', errors='ignore')
    error = stderr.read().decode('utf-8', errors='ignore')
    
    if output:
        for line in output.strip().split('\n')[-10:]:
            print(f"  {line}")
    if error and exit_code != 0:
        print(f"  錯誤: {error[:300]}")
    
    return exit_code == 0, output

def main():
    client = None
    try:
        client = create_ssh_client()
        sftp = client.open_sftp()
        
        print("\n" + "="*60)
        print("上傳前端優化代碼")
        print("="*60)
        
        # 本地路徑
        local_base = r"E:\002-工作文件\重要程序\聊天AI群聊程序\saas-demo"
        remote_base = f"{PROJECT_DIR}/saas-demo"
        
        # 需要更新的文件
        files_to_update = [
            ("src/components/layout-wrapper.tsx", "src/components/layout-wrapper.tsx"),
            ("src/components/sidebar.tsx", "src/components/sidebar.tsx"),
            ("src/lib/api-cache.ts", "src/lib/api-cache.ts"),
            ("src/hooks/useDashboardData.ts", "src/hooks/useDashboardData.ts"),
            ("src/app/group-ai/nodes/page.tsx", "src/app/group-ai/nodes/page.tsx"),
            ("src/app/page.tsx", "src/app/page.tsx"),
            ("next.config.ts", "next.config.ts"),
        ]
        
        for local_file, remote_file in files_to_update:
            local_path = os.path.join(local_base, local_file)
            remote_path = f"{remote_base}/{remote_file}"
            
            if os.path.exists(local_path):
                print(f"  上傳: {local_file}")
                
                # 確保遠程目錄存在
                remote_dir = os.path.dirname(remote_path)
                run_command(client, f"mkdir -p {remote_dir}")
                
                sftp.put(local_path, remote_path)
            else:
                print(f"  跳過（不存在）: {local_file}")
        
        print("\n" + "="*60)
        print("重新構建前端")
        print("="*60)
        
        # 重新構建
        run_command(client, f"""
cd {remote_base}
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"
nvm use 20 || true
npm run build 2>&1 | tail -20
""", "構建前端")
        
        # 重啟服務
        run_command(client, "sudo systemctl restart liaotian-frontend", "重啟前端服務")
        
        import time
        time.sleep(3)
        
        # 檢查狀態
        run_command(client, "sudo systemctl status liaotian-frontend --no-pager | head -10", "檢查服務狀態")
        
        print("\n" + "="*60)
        print("✅ 前端更新完成！")
        print("="*60)
        
        sftp.close()
        
    except Exception as e:
        print(f"❌ 錯誤: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if client:
            client.close()

if __name__ == "__main__":
    main()

