#!/usr/bin/env python3
"""
修復前端權限問題
"""
import paramiko
import os

SERVER = "165.154.233.55"
USERNAME = "ubuntu"
PASSWORD = "Along2025!!!"
PROJECT_DIR = "/home/ubuntu/liaotian"

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(SERVER, username=USERNAME, password=PASSWORD, timeout=30)
print("✓ SSH 連接成功!")

sftp = client.open_sftp()

# 上傳修復的文件
local_base = r"E:\002-工作文件\重要程序\聊天AI群聊程序\saas-demo"
remote_base = f"{PROJECT_DIR}/saas-demo"

files_to_update = [
    ("src/hooks/use-permissions.ts", "src/hooks/use-permissions.ts"),
    ("src/components/notification-center.tsx", "src/components/notification-center.tsx"),
]

print("\n>>> 上傳修復文件")
for local_file, remote_file in files_to_update:
    local_path = os.path.join(local_base, local_file)
    remote_path = f"{remote_base}/{remote_file}"
    
    if os.path.exists(local_path):
        print(f"  上傳: {local_file}")
        sftp.put(local_path, remote_path)

# 重新構建
print("\n>>> 重新構建前端")
stdin, stdout, stderr = client.exec_command(f"""
cd {remote_base}
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"
nvm use 20 || true
npm run build 2>&1 | tail -15
""", timeout=300)
print(stdout.read().decode())

# 重啟服務
print("\n>>> 重啟前端服務")
stdin, stdout, stderr = client.exec_command("sudo systemctl restart liaotian-frontend && sleep 3 && sudo systemctl status liaotian-frontend --no-pager | head -10")
print(stdout.read().decode())

print("\n✅ 修復完成！")
sftp.close()
client.close()

