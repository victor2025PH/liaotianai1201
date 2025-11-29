# -*- coding: utf-8 -*-
"""简单直接的修复重复 WebSocket location"""
import paramiko

SERVER = "165.154.233.55"
USERNAME = "ubuntu"
PASSWORD = "Along2025!!!"

print("=" * 60)
print("修复重复的 WebSocket location 配置")
print("=" * 60)

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(SERVER, username=USERNAME, password=PASSWORD, timeout=30)
    print("[OK] SSH 连接成功\n")
    
    # 备份
    print(">>> 备份配置...")
    ssh.exec_command("sudo cp /etc/nginx/sites-available/aikz.usdt2026.cc /etc/nginx/sites-available/aikz.usdt2026.cc.bak.dup 2>&1")
    print("[OK] 已备份\n")
    
    # 使用 sed 删除从第二个 "# WebSocket 支持" 注释开始到下一个 "}" 结束的块
    print(">>> 删除重复的配置块...")
    
    # 更简单：删除包含 "# WebSocket 支持 - 通知服务" 注释的第二个 location 块
    fix_cmd = """sudo python3 << 'PYEOF'
import re

with open('/etc/nginx/sites-available/aikz.usdt2026.cc', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# 找到所有包含 "location /api/v1/notifications/ws" 的行
ws_locations = []
for i, line in enumerate(lines):
    if 'location /api/v1/notifications/ws' in line:
        ws_locations.append(i)

if len(ws_locations) > 1:
    # 找到第二个 location 块的结束位置
    start_line = ws_locations[1]
    end_line = start_line
    brace_count = 0
    found_open = False
    
    for i in range(start_line, len(lines)):
        if '{' in lines[i]:
            brace_count += lines[i].count('{')
            found_open = True
        if '}' in lines[i]:
            brace_count -= lines[i].count('}')
        if found_open and brace_count == 0:
            end_line = i
            break
    
    # 删除从第二个 location 开始到结束的所有行（包括前面的注释）
    # 检查前面是否有注释
    delete_start = start_line
    if start_line > 0 and '# WebSocket' in lines[start_line - 1]:
        delete_start = start_line - 1
    
    # 删除这些行
    new_lines = lines[:delete_start] + lines[end_line + 1:]
    
    with open('/etc/nginx/sites-available/aikz.usdt2026.cc', 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    
    print(f'已删除重复的 location 块（行 {delete_start+1} 到 {end_line+1}）')
else:
    print('未发现重复配置')
PYEOF"""
    
    stdin, stdout, stderr = ssh.exec_command(fix_cmd)
    output = stdout.read().decode('utf-8', errors='ignore')
    error = stderr.read().decode('utf-8', errors='ignore')
    print(output)
    if error:
        print(f"错误: {error}")
    
    # 验证
    print("\n>>> 验证修复...")
    stdin, stdout, stderr = ssh.exec_command(
        "sudo grep -c 'location /api/v1/notifications/ws' /etc/nginx/sites-available/aikz.usdt2026.cc"
    )
    count = stdout.read().decode('utf-8', errors='ignore').strip()
    print(f"WebSocket location 数量: {count}")
    
    if count == "1":
        print("[OK] 重复已删除\n")
        
        # 测试
        print(">>> 测试配置...")
        stdin, stdout, stderr = ssh.exec_command("sudo nginx -t 2>&1")
        test_output = stdout.read().decode('utf-8', errors='ignore')
        print(test_output)
        
        if "syntax is ok" in test_output:
            print("\n>>> 重载 Nginx...")
            ssh.exec_command("sudo systemctl reload nginx 2>&1")
            print("[OK] Nginx 已重载")
            
            print("\n>>> 最终配置：")
            stdin, stdout, stderr = ssh.exec_command(
                "sudo grep -A 15 'location /api/v1/notifications/ws' /etc/nginx/sites-available/aikz.usdt2026.cc"
            )
            print(stdout.read().decode('utf-8', errors='ignore'))
            
            print("\n" + "=" * 60)
            print("[OK] 修复完成！")
            print("=" * 60)
    
    ssh.close()
    
except Exception as e:
    print(f"错误: {e}")
    import traceback
    traceback.print_exc()

