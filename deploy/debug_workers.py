#!/usr/bin/env python3
import paramiko

SERVER = "165.154.233.55"
USERNAME = "ubuntu"
PASSWORD = "Along2025!!!"

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(SERVER, username=USERNAME, password=PASSWORD, timeout=30)
print("✓ SSH 連接成功!")

print("\n>>> 後端日志（最新 20 行）")
stdin, stdout, stderr = client.exec_command("sudo journalctl -u liaotian-backend --no-pager -n 20")
print(stdout.read().decode())

print("\n>>> main.py 中 workers 相關")
stdin, stdout, stderr = client.exec_command("grep -n 'workers' /home/ubuntu/liaotian/admin-backend/app/main.py")
print(stdout.read().decode())

print("\n>>> 測試本地 /api/workers")
stdin, stdout, stderr = client.exec_command("curl -sv http://localhost:8000/api/workers 2>&1 | tail -30")
print(stdout.read().decode())

print("\n>>> 列出所有路由")
stdin, stdout, stderr = client.exec_command("curl -s http://localhost:8000/openapi.json | python3 -c 'import json,sys; d=json.load(sys.stdin); print(\"\\n\".join(sorted(d.get(\"paths\",{}).keys())))' | grep -i worker | head -10")
print(stdout.read().decode())

client.close()

