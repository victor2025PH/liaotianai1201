# -*- coding: utf-8 -*-
"""精确修复 Nginx 配置 - 替换整个 server 块"""
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
print("精确修复 Nginx 配置")
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
    original_content = stdout.read().decode('utf-8', errors='ignore')
    original_lines = original_content.split('\n')
    print(f"已读取 {len(original_lines)} 行\n")
    
    # 查找 server 块
    print(">>> 分析 server 块...")
    server_start = None
    server_end = None
    brace_count = 0
    
    for i, line in enumerate(original_lines):
        if 'server_name aikz.usdt2026.cc' in line:
            # 向前查找 server {
            for j in range(max(0, i-10), i+1):
                if 'server {' in original_lines[j] or 'server{' in original_lines[j]:
                    server_start = j
                    break
            if server_start is None:
                server_start = i
            
            # 向后查找结束的 }
            brace_count = 0
            found_open = False
            for j in range(server_start, len(original_lines)):
                if '{' in original_lines[j]:
                    brace_count += original_lines[j].count('{')
                    found_open = True
                if '}' in original_lines[j]:
                    brace_count -= original_lines[j].count('}')
                    if found_open and brace_count == 0:
                        server_end = j
                        break
            break
    
    if server_start is None or server_end is None:
        print("[错误] 未找到 server 块")
        ssh.close()
        sys.exit(1)
    
    print(f"找到 server 块：行 {server_start+1} 到 {server_end+1}\n")
    
    # 生成新配置
    new_server_config = """    # WebSocket 支持 - 通知服务（必须在 /api/ 之前，优先级最高）
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
    }"""
    
    # 构建新配置
    new_lines = []
    new_lines.extend(original_lines[:server_start])  # server 块之前的内容
    
    # 添加 server 块开始
    new_lines.append("server {")
    new_lines.append("    listen 80;")
    new_lines.append("    server_name aikz.usdt2026.cc;")
    new_lines.append("")
    
    # 添加 location 配置
    new_lines.extend(new_server_config.split('\n'))
    new_lines.append("")
    new_lines.append("}")
    
    new_lines.extend(original_lines[server_end+1:])  # server 块之后的内容
    
    # 保存到文件
    new_config_content = '\n'.join(new_lines)
    with open('deploy/nginx_fixed_full.conf', 'w', encoding='utf-8') as f:
        f.write(new_config_content)
    print("新配置已保存到: deploy/nginx_fixed_full.conf\n")
    
    # 显示 server 块
    print("=" * 60)
    print("修复后的 server 块：")
    print("=" * 60)
    for i in range(server_start, server_start + len(new_server_config.split('\n')) + 5):
        if i < len(new_lines):
            print(new_lines[i])
    print("=" * 60)
    print()
    
    # 生成 diff（只显示 server 块部分）
    print("配置变更对比（server 块部分）：")
    print("-" * 60)
    print("原配置（server 块）：")
    for i in range(server_start, min(server_start+10, server_end+1)):
        print(f"  {original_lines[i]}")
    print("\n新配置（server 块）：")
    for i in range(server_start, server_start + len(new_server_config.split('\n')) + 5):
        if i < len(new_lines):
            print(f"  {new_lines[i]}")
    print("-" * 60)
    
    print("\n" + "=" * 60)
    print("修复方案已生成")
    print("=" * 60)
    print("\n关键修复点：")
    print("1. location /api/ 的 proxy_pass: http://127.0.0.1:8000 (不包含路径)")
    print("2. location 顺序：WebSocket > API > 前端")
    print("3. 确保没有重复的 location 块")
    
    ssh.close()
    
except Exception as e:
    print(f"\n[错误] {e}")
    import traceback
    traceback.print_exc()

print("\n完成！")

