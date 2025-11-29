# -*- coding: utf-8 -*-
"""修复 Nginx 配置：删除重复 location 并修正 proxy_pass"""
import paramiko
import sys
import io
import difflib

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
print("修复 Nginx WebSocket 配置")
print("=" * 60)
print()

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(SERVER, username=USERNAME, password=PASSWORD, timeout=30)
    print("[OK] 已连接服务器\n")
    
    # 1. 读取当前配置
    print(">>> [1] 读取当前配置...")
    stdin, stdout, stderr = ssh.exec_command("sudo cat /etc/nginx/sites-available/aikz.usdt2026.cc")
    original_config = stdout.read().decode('utf-8', errors='ignore')
    original_lines = original_config.split('\n')
    print(f"已读取 {len(original_lines)} 行配置\n")
    
    # 2. 备份
    print(">>> [2] 备份配置...")
    exec_cmd(ssh, "sudo cp /etc/nginx/sites-available/aikz.usdt2026.cc /etc/nginx/sites-available/aikz.usdt2026.cc.bak.$(date +%Y%m%d_%H%M%S)")
    print("[OK] 已备份\n")
    
    # 3. 修复配置
    print(">>> [3] 修复配置...")
    
    # 找到所有 location 块
    location_indices = []
    for i, line in enumerate(original_lines):
        if 'location /api/v1/notifications/ws' in line:
            location_indices.append(i)
    
    print(f"找到 {len(location_indices)} 个 location 块（行号：{[i+1 for i in location_indices]}）")
    
    new_lines = original_lines.copy()
    
    # 删除重复的 location 块（保留第一个）
    if len(location_indices) > 1:
        print(f"删除 {len(location_indices)-1} 个重复的 location 块...")
        
        # 从后往前删除，避免索引变化
        for idx in reversed(location_indices[1:]):
            # 向前查找注释
            block_start = idx
            for j in range(max(0, idx-3), idx):
                if '# WebSocket' in new_lines[j] or ('#' in new_lines[j] and 'WebSocket' in new_lines[j]):
                    block_start = j
                    break
            
            # 向后查找结束的 }
            brace_count = 0
            block_end = idx
            found_open = False
            
            for j in range(idx, len(new_lines)):
                if '{' in new_lines[j]:
                    brace_count += new_lines[j].count('{')
                    found_open = True
                if '}' in new_lines[j]:
                    brace_count -= new_lines[j].count('}')
                    if found_open and brace_count == 0:
                        block_end = j
                        break
            
            print(f"  删除行 {block_start+1} 到 {block_end+1}")
            new_lines = new_lines[:block_start] + new_lines[block_end+1:]
    
    # 修复第一个 location 块中的 proxy_pass
    if len(location_indices) > 0:
        # 找到第一个 location 块（在删除重复后，索引可能已变化）
        first_location_idx = None
        for i, line in enumerate(new_lines):
            if 'location /api/v1/notifications/ws' in line:
                first_location_idx = i
                break
        
        if first_location_idx is not None:
            # 在第一个 location 块中查找 proxy_pass
            for i in range(first_location_idx, min(first_location_idx + 20, len(new_lines))):
                if 'proxy_pass' in new_lines[i] and 'notifications/ws' in new_lines[i]:
                    # 检查是否需要修改（如果没有末尾斜杠）
                    if new_lines[i].strip().endswith(';') and not new_lines[i].strip().endswith('/;'):
                        old_line = new_lines[i]
                        # 替换 proxy_pass，确保末尾有斜杠
                        if 'http://127.0.0.1:8000/api/v1/notifications/ws;' in new_lines[i]:
                            new_lines[i] = new_lines[i].replace(
                                'http://127.0.0.1:8000/api/v1/notifications/ws;',
                                'http://127.0.0.1:8000/api/v1/notifications/ws/;'
                            )
                            print(f"  修改 proxy_pass（行 {i+1}）")
                            print(f"    旧: {old_line.strip()}")
                            print(f"    新: {new_lines[i].strip()}")
                    break
    
    # 4. 生成 diff
    print("\n>>> [4] 配置变更对比（diff）：")
    print("=" * 60)
    
    diff = difflib.unified_diff(
        original_lines,
        new_lines,
        fromfile='原配置',
        tofile='新配置',
        lineterm='',
        n=3
    )
    
    diff_output = list(diff)
    if diff_output:
        for line in diff_output:
            print(line)
    else:
        print("无变更")
    
    print("=" * 60)
    
    # 5. 写入新配置
    print("\n>>> [5] 写入新配置...")
    new_config = '\n'.join(new_lines)
    
    sftp = ssh.open_sftp()
    temp_file = '/tmp/nginx_fixed.conf'
    with sftp.file(temp_file, 'w') as f:
        f.write(new_config)
    sftp.close()
    
    exec_cmd(ssh, f"sudo mv {temp_file} /etc/nginx/sites-available/aikz.usdt2026.cc && sudo chown root:root /etc/nginx/sites-available/aikz.usdt2026.cc")
    print("[OK] 新配置已写入\n")
    
    # 6. 验证配置
    print(">>> [6] 验证配置...")
    output, error = exec_cmd(ssh, "sudo nginx -t")
    print(output)
    if error:
        print(f"错误: {error}")
    
    # 7. 显示最终配置
    print("\n>>> [7] 最终 WebSocket 配置：")
    output, _ = exec_cmd(ssh, "sudo grep -A 15 'location /api/v1/notifications/ws' /etc/nginx/sites-available/aikz.usdt2026.cc")
    print(output)
    
    # 8. 验证 location 数量
    output, _ = exec_cmd(ssh, "sudo grep -c 'location /api/v1/notifications/ws' /etc/nginx/sites-available/aikz.usdt2026.cc")
    print(f"\nLocation 块数量: {output}")
    
    print("\n" + "=" * 60)
    print("修复完成！")
    print("=" * 60)
    print("\n请执行以下命令应用配置：")
    print("sudo nginx -t && sudo systemctl reload nginx")
    print("\n或者重启 Nginx（如果 reload 失败）：")
    print("sudo systemctl restart nginx")
    
    ssh.close()
    
except Exception as e:
    print(f"\n[错误] {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n完成！")

