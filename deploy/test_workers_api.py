#!/usr/bin/env python3
import paramiko

SERVER = "165.154.233.55"
USERNAME = "ubuntu"
PASSWORD = "Along2025!!!"

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(SERVER, username=USERNAME, password=PASSWORD, timeout=30)
print("✓ SSH 連接成功!")

# 測試不同的路徑
tests = [
    ("本地 /api/v1/workers", "curl -s http://localhost:8000/api/v1/workers"),
    ("本地 /api/workers", "curl -s http://localhost:8000/api/workers"),
    ("Nginx /api/workers/", "curl -s http://127.0.0.1/api/workers/"),
    ("Nginx /api/v1/workers", "curl -s http://127.0.0.1/api/v1/workers"),
]

for name, cmd in tests:
    print(f"\n>>> {name}")
    stdin, stdout, stderr = client.exec_command(cmd)
    result = stdout.read().decode()[:200]
    print(f"  {result}")

# 檢查 Nginx 配置
print("\n>>> Nginx 配置中的 workers 部分")
stdin, stdout, stderr = client.exec_command("grep -A5 'api/workers' /etc/nginx/sites-available/aikz.usdt2026.cc")
print(stdout.read().decode())

client.close()

