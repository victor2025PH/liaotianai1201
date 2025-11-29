# -*- coding: utf-8 -*-
"""分析并修复 Nginx 配置 - 解决 API 404 问题"""
import paramiko
import sys
import io
import difflib
import re

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
print("分析并修复 Nginx 配置")
print("=" * 60)
print()

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(SERVER, username=USERNAME, password=PASSWORD, timeout=30)
    print("[OK] 已连接服务器\n")
    
    # 1. 读取当前配置
    print(">>> [1] 读取当前 Nginx 配置...")
    stdin, stdout, stderr = ssh.exec_command("sudo cat /etc/nginx/sites-available/aikz.usdt2026.cc")
    original_config = stdout.read().decode('utf-8', errors='ignore')
    original_lines = original_config.split('\n')
    print(f"已读取 {len(original_lines)} 行配置\n")
    
    # 2. 检查后端服务端口
    print(">>> [2] 检查后端服务端口...")
    output, _ = exec_cmd(ssh, "sudo systemctl cat liaotian-backend 2>&1 | grep -E 'ExecStart|--port|PORT' | head -5")
    print(output if output else "无法确定端口，使用默认 8000")
    
    # 检查实际监听端口
    output, _ = exec_cmd(ssh, "sudo ss -tlnp | grep -E ':8000|:3000'")
    print(f"监听端口: {output if output else '未检测到'}\n")
    
    # 3. 分析当前配置
    print(">>> [3] 分析当前配置...")
    
    # 查找 server 块
    server_start = None
    server_end = None
    brace_count = 0
    
    for i, line in enumerate(original_lines):
        if 'server_name aikz.usdt2026.cc' in line or (server_start is not None and 'server {' in line):
            if server_start is None:
                # 向前查找 server {
                for j in range(max(0, i-5), i+1):
                    if 'server {' in original_lines[j]:
                        server_start = j
                        break
                if server_start is None:
                    server_start = i
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
            if server_end:
                break
    
    if server_start is None:
        print("[错误] 未找到 server 块")
        ssh.close()
        sys.exit(1)
    
    print(f"找到 server 块：行 {server_start+1} 到 {server_end+1}\n")
    
    # 4. 检查现有的 location
    print(">>> [4] 检查现有 location 配置...")
    locations = {
        '/': None,
        '/api/': None,
        '/api/v1/notifications/ws': None
    }
    
    for i in range(server_start, server_end+1):
        line = original_lines[i]
        if 'location /' in line and '{' in line:
            if 'location / ' in line or line.strip() == 'location / {':
                locations['/'] = i
            elif 'location /api/' in line:
                if '/api/v1/notifications/ws' in line:
                    locations['/api/v1/notifications/ws'] = i
                elif '/api/' in line:
                    locations['/api/'] = i
    
    for loc, idx in locations.items():
        if idx:
            print(f"  找到 {loc}: 行 {idx+1}")
        else:
            print(f"  缺少 {loc}")
    print()
    
    # 5. 生成修复后的配置
    print(">>> [5] 生成修复后的配置...")
    
    # 提取 server 块外的内容
    before_server = original_lines[:server_start]
    after_server = original_lines[server_end+1:]
    server_lines = original_lines[server_start:server_end+1]
    
    # 构建新的 server 配置
    new_server_lines = []
    new_server_lines.append("server {")
    new_server_lines.append("    listen 80;")
    new_server_lines.append("    server_name aikz.usdt2026.cc;")
    new_server_lines.append("")
    
    # WebSocket location（必须在 /api/ 之前，优先级最高）
    new_server_lines.append("    # WebSocket 支持 - 通知服务（优先级最高）")
    new_server_lines.append("    location /api/v1/notifications/ws {")
    new_server_lines.append("        proxy_pass http://127.0.0.1:8000;")
    new_server_lines.append("        proxy_http_version 1.1;")
    new_server_lines.append("        proxy_set_header Upgrade $http_upgrade;")
    new_server_lines.append("        proxy_set_header Connection \"upgrade\";")
    new_server_lines.append("        proxy_set_header Host $host;")
    new_server_lines.append("        proxy_set_header X-Real-IP $remote_addr;")
    new_server_lines.append("        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;")
    new_server_lines.append("        proxy_set_header X-Forwarded-Proto $scheme;")
    new_server_lines.append("        proxy_read_timeout 86400;")
    new_server_lines.append("        proxy_send_timeout 86400;")
    new_server_lines.append("        proxy_buffering off;")
    new_server_lines.append("    }")
    new_server_lines.append("")
    
    # API location
    new_server_lines.append("    # 后端 API")
    new_server_lines.append("    location /api/ {")
    new_server_lines.append("        proxy_pass http://127.0.0.1:8000;")
    new_server_lines.append("        proxy_http_version 1.1;")
    new_server_lines.append("        proxy_set_header Host $host;")
    new_server_lines.append("        proxy_set_header X-Real-IP $remote_addr;")
    new_server_lines.append("        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;")
    new_server_lines.append("        proxy_set_header X-Forwarded-Proto $scheme;")
    new_server_lines.append("        proxy_read_timeout 300;")
    new_server_lines.append("    }")
    new_server_lines.append("")
    
    # 前端 location（最后，最低优先级）
    new_server_lines.append("    # 前端")
    new_server_lines.append("    location / {")
    new_server_lines.append("        proxy_pass http://127.0.0.1:3000;")
    new_server_lines.append("        proxy_http_version 1.1;")
    new_server_lines.append("        proxy_set_header Upgrade $http_upgrade;")
    new_server_lines.append("        proxy_set_header Connection \"upgrade\";")
    new_server_lines.append("        proxy_set_header Host $host;")
    new_server_lines.append("        proxy_set_header X-Real-IP $remote_addr;")
    new_server_lines.append("        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;")
    new_server_lines.append("        proxy_read_timeout 86400;")
    new_server_lines.append("    }")
    new_server_lines.append("")
    
    # 其他 location（如果有）
    # 检查是否有其他 location（如 /health, /docs 等）
    other_locations = []
    in_location = False
    location_lines = []
    
    for i in range(server_start, server_end+1):
        line = original_lines[i]
        if 'location /' in line and '{' in line:
            if '/api/' not in line and '/api/v1/notifications/ws' not in line:
                # 其他 location
                in_location = True
                location_lines = [line]
                brace_count = line.count('{')
        elif in_location:
            location_lines.append(line)
            brace_count += line.count('{') - line.count('}')
            if brace_count == 0:
                other_locations.extend(location_lines)
                other_locations.append("")
                in_location = False
                location_lines = []
    
    if other_locations:
        new_server_lines.extend(other_locations)
    
    new_server_lines.append("}")
    
    # 组合新配置
    new_lines = before_server + new_server_lines + after_server
    
    # 6. 生成 diff
    print(">>> [6] 生成配置变更对比（diff）...")
    print("=" * 60)
    
    diff = list(difflib.unified_diff(
        original_lines,
        new_lines,
        fromfile='原配置 (/etc/nginx/sites-available/aikz.usdt2026.cc)',
        tofile='新配置',
        lineterm='',
        n=3
    ))
    
    # 保存 diff 到文件
    diff_file = 'deploy/nginx_config_fix_diff.txt'
    with open(diff_file, 'w', encoding='utf-8') as f:
        f.write("Nginx 配置修复 - 变更对比 (diff)\n")
        f.write("=" * 60 + "\n\n")
        for line in diff:
            f.write(line + "\n")
    
    # 显示关键变更
    print("关键变更：")
    print("-" * 60)
    for line in diff:
        if line.startswith(('---', '+++', '@@', '-', '+')):
            print(line)
    print("-" * 60)
    print(f"\n完整 diff 已保存到: {diff_file}\n")
    
    # 7. 保存新配置到文件（供用户查看）
    new_config_file = 'deploy/nginx_config_fixed.conf'
    with open(new_config_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(new_lines))
    print(f"新配置已保存到: {new_config_file}\n")
    
    # 8. 显示完整的 server 块
    print(">>> [7] 修复后的完整 server 配置：")
    print("=" * 60)
    for line in new_server_lines:
        print(line)
    print("=" * 60)
    print()
    
    print("=" * 60)
    print("分析完成")
    print("=" * 60)
    print("\n修复要点：")
    print("1. WebSocket location (/api/v1/notifications/ws) - 优先级最高")
    print("2. API location (/api/) - 代理到后端 8000 端口")
    print("3. 前端 location (/) - 代理到前端 3000 端口")
    print("4. proxy_pass 不包含路径，让 Nginx 自动传递完整路径")
    print("\n请查看 diff 文件确认变更，然后执行修复命令。")
    
    ssh.close()
    
except Exception as e:
    print(f"\n[错误] {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n完成！")

