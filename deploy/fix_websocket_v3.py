#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复 WebSocket 连接问题 - 简化版本
"""
import paramiko
import sys

# 强制使用 UTF-8
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

SERVER = "165.154.233.55"
USERNAME = "ubuntu"
PASSWORD = "Along2025!!!"

print("=" * 60)
print("WebSocket 连接问题修复")
print("=" * 60)
sys.stdout.flush()

try:
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(SERVER, username=USERNAME, password=PASSWORD, timeout=30)
    print("[OK] SSH 连接成功")
    sys.stdout.flush()
    
    # 检查当前配置
    print("\n>>> 检查当前 Nginx 配置...")
    sys.stdout.flush()
    stdin, stdout, stderr = client.exec_command("sudo cat /etc/nginx/sites-available/aikz.usdt2026.cc")
    current_config = stdout.read().decode('utf-8', errors='ignore')
    print(current_config)
    sys.stdout.flush()
    
    # 创建新配置
    nginx_config = """server {
    listen 80;
    server_name aikz.usdt2026.cc;

    # WebSocket 支持 - 通知服务（优先级最高）
    location /api/v1/notifications/ws {
        proxy_pass http://127.0.0.1:8000/api/v1/notifications/ws;
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

    # 前端
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

    # /api/workers/ -> /api/v1/workers（带末尾斜杠）
    location = /api/workers/ {
        proxy_pass http://127.0.0.1:8000/api/v1/workers;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    # /api/workers/xxx -> /api/v1/workers/xxx
    location ~ ^/api/workers/(.+)$ {
        proxy_pass http://127.0.0.1:8000/api/v1/workers/$1;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    # 后端 API
    location /api/ {
        proxy_pass http://127.0.0.1:8000/api/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_read_timeout 300;
    }

    location /health {
        proxy_pass http://127.0.0.1:8000/health;
    }

    location /docs {
        proxy_pass http://127.0.0.1:8000/docs;
    }

    location /openapi.json {
        proxy_pass http://127.0.0.1:8000/openapi.json;
    }
}
"""
    
    print("\n>>> 更新 Nginx 配置...")
    sys.stdout.flush()
    
    # 使用 echo 和 tee 写入配置
    stdin, stdout, stderr = client.exec_command(
        'echo \'' + nginx_config.replace("'", "'\\''") + '\' | sudo tee /etc/nginx/sites-available/aikz.usdt2026.cc > /dev/null'
    )
    exit_status = stdout.channel.recv_exit_status()
    
    if exit_status == 0:
        print("[OK] 配置已写入")
        sys.stdout.flush()
        
        # 测试配置
        print("\n>>> 测试 Nginx 配置...")
        sys.stdout.flush()
        stdin, stdout, stderr = client.exec_command("sudo nginx -t")
        test_output = stdout.read().decode('utf-8', errors='ignore')
        error_output = stderr.read().decode('utf-8', errors='ignore')
        print(test_output)
        if error_output:
            print(f"错误: {error_output}")
        sys.stdout.flush()
        
        if "syntax is ok" in test_output:
            print("\n>>> 重载 Nginx...")
            sys.stdout.flush()
            stdin, stdout, stderr = client.exec_command("sudo systemctl reload nginx")
            stdout.channel.recv_exit_status()
            print("[OK] Nginx 已重载")
            sys.stdout.flush()
            
            print("\n" + "=" * 60)
            print("[OK] WebSocket 配置修复完成！")
            print("=" * 60)
            print("\n修复内容：")
            print("1. 添加了专用的 WebSocket location (/api/v1/notifications/ws)")
            print("2. 配置了正确的 Upgrade 和 Connection 头")
            print("3. 设置了长连接超时（86400 秒）")
            print("4. 禁用了代理缓冲")
            print("\nWebSocket 路径：")
            print("  ws://aikz.usdt2026.cc/api/v1/notifications/ws/{user_email}")
            sys.stdout.flush()
        else:
            print("\n[ERROR] Nginx 配置测试失败")
            sys.stdout.flush()
    else:
        print(f"[ERROR] 写入配置失败，退出码: {exit_status}")
        sys.stdout.flush()
    
    client.close()
    
except Exception as e:
    print(f"[ERROR] 发生错误: {e}")
    import traceback
    traceback.print_exc()
    sys.stdout.flush()

