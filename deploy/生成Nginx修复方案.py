# -*- coding: utf-8 -*-
"""生成 Nginx 修复方案"""
import paramiko
import sys
import io

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

SERVER = "165.154.233.55"
USERNAME = "ubuntu"
PASSWORD = "Along2025!!!"

def exec_cmd(ssh, cmd):
    stdin, stdout, stderr = ssh.exec_command(cmd)
    output = stdout.read().decode('utf-8', errors='ignore')
    error = stderr.read().decode('utf-8', errors='ignore')
    return output.strip(), error.strip()

print("=" * 60)
print("生成 Nginx 修复方案")
print("=" * 60)
print()

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(SERVER, username=USERNAME, password=PASSWORD, timeout=30)
    print("[OK] 已连接服务器\n")
    
    # 读取当前配置
    print(">>> 读取当前配置...")
    stdin, stdout, stderr = ssh.exec_command("sudo cat /etc/nginx/sites-available/aikz.usdt2026.cc")
    original_config = stdout.read().decode('utf-8', errors='ignore')
    
    # 保存原配置
    with open('deploy/nginx_original.conf', 'w', encoding='utf-8') as f:
        f.write(original_config)
    print(f"原配置已保存到: deploy/nginx_original.conf\n")
    
    # 检查端口
    print(">>> 检查服务端口...")
    output, _ = exec_cmd(ssh, "sudo ss -tlnp | grep -E ':8000|:3000'")
    print(f"监听端口: {output if output else '使用默认端口'}\n")
    
    # 生成修复后的配置
    print(">>> 生成修复后的配置...")
    
    # 构建正确的 server 配置
    fixed_config = """server {
    listen 80;
    server_name aikz.usdt2026.cc;

    # WebSocket 支持 - 通知服务（必须在 /api/ 之前，优先级最高）
    location /api/v1/notifications/ws {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 86400;
        proxy_send_timeout 86400;
        proxy_buffering off;
    }

    # 后端 API（必须在 / 之前，优先级高于前端）
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300;
    }

    # 前端（最后，最低优先级）
    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_read_timeout 86400;
    }
}
"""
    
    # 保存新配置
    with open('deploy/nginx_fixed.conf', 'w', encoding='utf-8') as f:
        f.write(fixed_config)
    print(f"新配置已保存到: deploy/nginx_fixed.conf\n")
    
    # 显示配置
    print("=" * 60)
    print("修复后的完整 server 配置：")
    print("=" * 60)
    print(fixed_config)
    print("=" * 60)
    
    print("\n关键修复点：")
    print("1. WebSocket location: proxy_pass http://127.0.0.1:8000; (不包含路径)")
    print("2. API location: proxy_pass http://127.0.0.1:8000; (不包含路径)")
    print("3. 前端 location: proxy_pass http://127.0.0.1:3000;")
    print("4. location 顺序：WebSocket > API > 前端（优先级从高到低）")
    
    ssh.close()
    
except Exception as e:
    print(f"\n[错误] {e}")
    import traceback
    traceback.print_exc()

print("\n完成！")

