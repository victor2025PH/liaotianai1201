#!/usr/bin/env python3
import paramiko

HOST = '165.154.233.55'
USER = 'ubuntu'

CMD = """
echo "=== 测试后端 API 路由 (本地) ==="
echo "1. 测试带斜杠 /api/v1/notifications/"
curl -I http://127.0.0.1:8000/api/v1/notifications/

echo ""
echo "2. 测试不带斜杠 /api/v1/notifications"
curl -I http://127.0.0.1:8000/api/v1/notifications

echo ""
echo "=== 测试 Nginx 转发 (域名) ==="
echo "3. 测试域名 /api/v1/notifications/"
curl -I -H "Host: aikz.usdt2026.cc" http://127.0.0.1/api/v1/notifications/

echo ""
echo "4. 测试域名 /api/v1/notifications"
curl -I -H "Host: aikz.usdt2026.cc" http://127.0.0.1/api/v1/notifications
"""

try:
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER)
    
    stdin, stdout, stderr = client.exec_command(CMD, get_pty=True)
    for line in iter(stdout.readline, ""):
        print(line, end="")
        
    client.close()
except Exception as e:
    print(f"❌ 错误: {e}")

