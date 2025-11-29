# -*- coding: utf-8 -*-
import paramiko
import subprocess
import sys

SERVER = "165.154.233.55"
USERNAME = "ubuntu"
PASSWORD = "Along2025!!!"

def run_and_print(cmd, ssh):
    """执行命令并打印输出"""
    stdin, stdout, stderr = ssh.exec_command(cmd)
    output = stdout.read().decode('utf-8', errors='ignore')
    error = stderr.read().decode('utf-8', errors='ignore')
    if output:
        print(output)
    if error:
        print(f"错误: {error}")
    return output

print("=" * 60)
print("全自动修复 WebSocket 配置")
print("=" * 60)
print()

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(SERVER, username=USERNAME, password=PASSWORD, timeout=30)
    print("[OK] 连接成功\n")
    
    # 检查
    print(">>> 检查配置...")
    count = run_and_print("sudo grep -c 'location /api/v1/notifications/ws' /etc/nginx/sites-available/aikz.usdt2026.cc", ssh).strip()
    print(f"Location 块数量: {count}\n")
    
    if count == "1":
        print("[OK] 配置正常，只有一个 location 块")
        print(">>> 测试配置...")
        run_and_print("sudo nginx -t", ssh)
        ssh.close()
        sys.exit(0)
    
    # 备份
    print(">>> 备份配置...")
    run_and_print("sudo cp /etc/nginx/sites-available/aikz.usdt2026.cc /etc/nginx/sites-available/aikz.usdt2026.cc.bak.auto", ssh)
    print("[OK] 已备份\n")
    
    # 修复
    print(">>> 执行修复...")
    fix_script = '''import re
with open('/etc/nginx/sites-available/aikz.usdt2026.cc', 'r', encoding='utf-8') as f:
    lines = f.readlines()
location_indices = [i for i, line in enumerate(lines) if 'location /api/v1/notifications/ws' in line]
print(f'找到 {len(location_indices)} 个 location')
if len(location_indices) > 1:
    for idx in reversed(location_indices[1:]):
        block_start = idx
        for i in range(max(0, idx-3), idx):
            if '# WebSocket' in lines[i] or ('#' in lines[i] and 'WebSocket' in lines[i]):
                block_start = i
                break
        brace_count = 0
        block_end = idx
        found_open = False
        for i in range(idx, len(lines)):
            if '{' in lines[i]:
                brace_count += lines[i].count('{')
                found_open = True
            if '}' in lines[i]:
                brace_count -= lines[i].count('}')
                if found_open and brace_count == 0:
                    block_end = i
                    break
        print(f'删除行 {block_start+1} 到 {block_end+1}')
        lines = lines[:block_start] + lines[block_end+1:]
    with open('/etc/nginx/sites-available/aikz.usdt2026.cc', 'w', encoding='utf-8') as f:
        f.writelines(lines)
    print('修复完成')
else:
    print('无需修复')
'''
    
    sftp = ssh.open_sftp()
    with sftp.file('/tmp/fix.py', 'w') as f:
        f.write(fix_script)
    sftp.close()
    
    run_and_print("sudo python3 /tmp/fix.py", ssh)
    run_and_print("rm /tmp/fix.py", ssh)
    
    # 验证
    print("\n>>> 验证修复...")
    new_count = run_and_print("sudo grep -c 'location /api/v1/notifications/ws' /etc/nginx/sites-available/aikz.usdt2026.cc", ssh).strip()
    print(f"剩余 location 数量: {new_count}\n")
    
    if new_count == "1":
        print(">>> 测试配置...")
        run_and_print("sudo nginx -t", ssh)
        print("\n>>> 重载 Nginx...")
        run_and_print("sudo systemctl reload nginx", ssh)
        print("\n[OK] 修复完成！")
    else:
        print(f"[错误] 仍有 {new_count} 个 location")
    
    ssh.close()
    
except Exception as e:
    print(f"错误: {e}")
    import traceback
    traceback.print_exc()

print("\n完成！")

