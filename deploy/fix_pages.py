#!/usr/bin/env python3
"""
修復缺失的頁面和重新部署
"""
import paramiko
import os
import tarfile
import io

SERVER = "165.154.233.55"
USERNAME = "ubuntu"
PASSWORD = "Along2025!!!"
PROJECT_DIR = "/home/ubuntu/liaotian"

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(SERVER, username=USERNAME, password=PASSWORD, timeout=30)
print("✓ SSH 連接成功!")

sftp = client.open_sftp()

# 本地前端目錄
local_base = r"E:\002-工作文件\重要程序\聊天AI群聊程序\saas-demo"
remote_base = f"{PROJECT_DIR}/saas-demo"

# 需要上傳的關鍵頁面文件
pages_to_upload = [
    "src/app/sessions/page.tsx",
    "src/app/sessions/[id]/page.tsx",
    "src/app/logs/page.tsx",
    "src/app/monitoring/page.tsx",
    "src/app/permissions/page.tsx",
    "src/app/permissions/roles/page.tsx",
    "src/app/permissions/users/page.tsx",
    "src/app/permissions/audit-logs/page.tsx",
]

print("\n>>> 上傳缺失的頁面文件")
for page_file in pages_to_upload:
    local_path = os.path.join(local_base, page_file)
    remote_path = f"{remote_base}/{page_file}"
    
    if os.path.exists(local_path):
        # 確保遠程目錄存在
        remote_dir = os.path.dirname(remote_path)
        stdin, stdout, stderr = client.exec_command(f"mkdir -p {remote_dir}")
        stdout.channel.recv_exit_status()
        
        print(f"  上傳: {page_file}")
        sftp.put(local_path, remote_path)
    else:
        print(f"  跳過（本地不存在）: {page_file}")

# 上傳 hooks
hooks_to_upload = [
    "src/hooks/useSessionsWithFilters.ts",
    "src/hooks/useSessions.ts",
]

print("\n>>> 上傳 hooks")
for hook_file in hooks_to_upload:
    local_path = os.path.join(local_base, hook_file)
    remote_path = f"{remote_base}/{hook_file}"
    
    if os.path.exists(local_path):
        print(f"  上傳: {hook_file}")
        sftp.put(local_path, remote_path)

# 上傳 mock 數據
mocks_to_upload = [
    "src/mock/sessions.ts",
    "src/mock/logs.ts",
    "src/mock/stats.ts",
]

print("\n>>> 上傳 mock 數據")
for mock_file in mocks_to_upload:
    local_path = os.path.join(local_base, mock_file)
    remote_path = f"{remote_base}/{mock_file}"
    
    if os.path.exists(local_path):
        remote_dir = os.path.dirname(remote_path)
        stdin, stdout, stderr = client.exec_command(f"mkdir -p {remote_dir}")
        stdout.channel.recv_exit_status()
        print(f"  上傳: {mock_file}")
        sftp.put(local_path, remote_path)

# 重新構建
print("\n>>> 重新構建前端（完整構建）")
stdin, stdout, stderr = client.exec_command(f"""
cd {remote_base}
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"
nvm use 20 || true

# 清理舊的構建
rm -rf .next

# 重新安裝依賴並構建
npm install --silent
npm run build 2>&1 | tail -30
""", timeout=600)

exit_code = stdout.channel.recv_exit_status()
output = stdout.read().decode()
print(output)

if exit_code != 0:
    print(f"❌ 構建失敗，退出碼: {exit_code}")
    error_output = stderr.read().decode()
    if error_output:
        print(f"錯誤: {error_output[:500]}")
else:
    print("✓ 構建成功!")

# 重啟服務
print("\n>>> 重啟前端服務")
stdin, stdout, stderr = client.exec_command("sudo systemctl restart liaotian-frontend && sleep 5 && sudo systemctl status liaotian-frontend --no-pager | head -15")
print(stdout.read().decode())

print("\n✅ 部署完成！")
sftp.close()
client.close()

