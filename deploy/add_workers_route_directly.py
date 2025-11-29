#!/usr/bin/env python3
"""
直接在後端 main.py 添加 /api/workers 路由
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

# 在 main.py 中添加額外的路由
print("\n>>> 修改 main.py 添加 /api/workers 路由")
cmd = f'''
cd {PROJECT_DIR}/admin-backend

# 備份
cp app/main.py app/main.py.bak2

# 檢查是否已經添加
if ! grep -q "prefix=.*/api/workers" app/main.py; then
    # 在 app.include_router(api_router, prefix="/api/v1") 之後添加
    sed -i '/app.include_router(api_router, prefix="\\/api\\/v1")/a\\
# 額外添加 /api/workers 路由（兼容前端）\\
from app.api import workers as workers_api\\
app.include_router(workers_api.router, prefix="/api/workers", tags=["workers-compat"])' app/main.py
    echo "已添加 /api/workers 路由"
else
    echo "/api/workers 路由已存在"
fi

# 顯示修改後的內容
grep -A2 'api/workers' app/main.py | head -10
'''

stdin, stdout, stderr = client.exec_command(cmd)
print(stdout.read().decode())
print(stderr.read().decode())

# 重啟後端
print("\n>>> 重啟後端服務")
stdin, stdout, stderr = client.exec_command("sudo systemctl restart liaotian-backend && sleep 3 && sudo systemctl status liaotian-backend --no-pager | head -10")
print(stdout.read().decode())

# 測試
print("\n>>> 測試 /api/workers/")
stdin, stdout, stderr = client.exec_command("curl -s http://localhost:8000/api/workers/ | head -c 200")
print(stdout.read().decode())

print("\n>>> 測試 /api/workers（無斜杠）")
stdin, stdout, stderr = client.exec_command("curl -s http://localhost:8000/api/workers | head -c 200")
print(stdout.read().decode())

print("\n✅ 完成!")
client.close()

