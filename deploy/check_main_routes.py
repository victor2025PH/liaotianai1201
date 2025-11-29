#!/usr/bin/env python3
import paramiko

SERVER = "165.154.233.55"
USERNAME = "ubuntu"
PASSWORD = "Along2025!!!"
PROJECT_DIR = "/home/ubuntu/liaotian"

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(SERVER, username=USERNAME, password=PASSWORD, timeout=30)
print("✓ SSH 連接成功!")

# 檢查 main.py 中的路由前綴
stdin, stdout, stderr = client.exec_command(f"grep -n 'include_router\\|prefix' {PROJECT_DIR}/admin-backend/app/main.py | head -20")
print("\n主路由配置:")
print(stdout.read().decode())

# 測試不同的 API 路徑
print("\n測試不同的路徑:")
tests = [
    "curl -s http://localhost:8000/api/workers/heartbeat -X POST -H 'Content-Type: application/json' -d '{}'",
    "curl -s http://localhost:8000/api/v1/workers/heartbeat -X POST -H 'Content-Type: application/json' -d '{}'",
    "curl -s http://localhost:8000/workers/heartbeat -X POST -H 'Content-Type: application/json' -d '{}'",
]

for test in tests:
    stdin, stdout, stderr = client.exec_command(test)
    result = stdout.read().decode()
    print(f"  {test.split('localhost:8000')[1].split(' ')[0]} -> {result[:100]}")

client.close()

