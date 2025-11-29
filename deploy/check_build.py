#!/usr/bin/env python3
"""
檢查服務器上的構建情況
"""
import paramiko

SERVER = "165.154.233.55"
USERNAME = "ubuntu"
PASSWORD = "Along2025!!!"
PROJECT_DIR = "/home/ubuntu/liaotian"

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(SERVER, username=USERNAME, password=PASSWORD, timeout=30)
print("✓ SSH 連接成功!")

# 檢查 sessions 頁面是否存在
print("\n>>> 檢查 sessions 頁面文件")
stdin, stdout, stderr = client.exec_command(f"ls -la {PROJECT_DIR}/saas-demo/src/app/sessions/")
print(stdout.read().decode())
print(stderr.read().decode())

# 檢查構建輸出
print("\n>>> 檢查構建輸出")
stdin, stdout, stderr = client.exec_command(f"ls -la {PROJECT_DIR}/saas-demo/.next/server/app/sessions/ 2>/dev/null || echo '目錄不存在'")
print(stdout.read().decode())

# 重新構建並顯示完整輸出
print("\n>>> 完整重新構建前端")
stdin, stdout, stderr = client.exec_command(f"""
cd {PROJECT_DIR}/saas-demo
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"
nvm use 20 || true
rm -rf .next
npm run build 2>&1
""", timeout=600)

output = stdout.read().decode()
for line in output.split('\n'):
    if 'sessions' in line.lower() or 'error' in line.lower() or '○' in line or '●' in line or '├' in line or '└' in line:
        print(line)

print("\n>>> 重啟服務")
stdin, stdout, stderr = client.exec_command("sudo systemctl restart liaotian-frontend && sleep 3 && sudo systemctl status liaotian-frontend --no-pager | head -5")
print(stdout.read().decode())

client.close()
print("\n✅ 完成")

