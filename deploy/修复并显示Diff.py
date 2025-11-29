# -*- coding: utf-8 -*-
"""修复 Nginx 配置并生成 diff"""
import paramiko
import sys
import io
import difflib
import os

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
    
    print(f"找到 {len(location_indices)} 个 location 块")
    
    new_lines = original_lines.copy()
    changes = []
    
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
            
            changes.append(f"删除行 {block_start+1}-{block_end+1}（重复的 location 块）")
            new_lines = new_lines[:block_start] + new_lines[block_end+1:]
    
    # 修复第一个 location 块中的 proxy_pass
    if len(location_indices) > 0:
        # 重新查找第一个 location（索引可能已变化）
        first_location_idx = None
        for i, line in enumerate(new_lines):
            if 'location /api/v1/notifications/ws' in line:
                first_location_idx = i
                break
        
        if first_location_idx is not None:
            # 在第一个 location 块中查找 proxy_pass
            for i in range(first_location_idx, min(first_location_idx + 20, len(new_lines))):
                if 'proxy_pass' in new_lines[i] and 'notifications/ws' in new_lines[i]:
                    old_line = new_lines[i]
                    # 修复 proxy_pass，确保末尾有斜杠
                    if 'http://127.0.0.1:8000/api/v1/notifications/ws;' in new_lines[i]:
                        new_lines[i] = new_lines[i].replace(
                            'http://127.0.0.1:8000/api/v1/notifications/ws;',
                            'http://127.0.0.1:8000/api/v1/notifications/ws/;'
                        )
                        changes.append(f"修改行 {i+1}：proxy_pass 添加末尾斜杠")
                    elif 'http://127.0.0.1:8000/api/v1/notifications/ws' in new_lines[i] and not new_lines[i].strip().endswith('/;'):
                        # 其他可能的格式
                        new_lines[i] = new_lines[i].replace(
                            'http://127.0.0.1:8000/api/v1/notifications/ws',
                            'http://127.0.0.1:8000/api/v1/notifications/ws/'
                        )
                        changes.append(f"修改行 {i+1}：proxy_pass 添加末尾斜杠")
                    break
    
    # 4. 生成 diff
    print("\n>>> [4] 配置变更：")
    print("=" * 60)
    for change in changes:
        print(f"  - {change}")
    print("=" * 60)
    
    # 生成详细 diff
    diff = list(difflib.unified_diff(
        original_lines,
        new_lines,
        fromfile='原配置 (/etc/nginx/sites-available/aikz.usdt2026.cc)',
        tofile='新配置',
        lineterm='',
        n=5
    ))
    
    # 保存 diff 到文件
    diff_file = 'deploy/nginx_config_diff.txt'
    with open(diff_file, 'w', encoding='utf-8') as f:
        f.write("Nginx 配置变更对比 (diff)\n")
        f.write("=" * 60 + "\n\n")
        for line in diff:
            f.write(line + "\n")
        f.write("\n" + "=" * 60 + "\n")
        f.write("变更摘要：\n")
        for change in changes:
            f.write(f"  - {change}\n")
    
    print(f"\n详细 diff 已保存到: {diff_file}\n")
    
    # 显示关键变更
    print("关键变更预览：")
    print("-" * 60)
    for line in diff:
        if line.startswith(('---', '+++', '@@', '-', '+')):
            print(line)
    print("-" * 60)
    
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
    print(">>> [6] 验证配置语法...")
    output, error = exec_cmd(ssh, "sudo nginx -t")
    print(output)
    if "syntax is ok" in output:
        print("[OK] 配置语法正确\n")
    else:
        print("[错误] 配置语法有误\n")
    
    # 7. 显示最终配置
    print(">>> [7] 最终 WebSocket 配置：")
    output, _ = exec_cmd(ssh, "sudo grep -A 15 'location /api/v1/notifications/ws' /etc/nginx/sites-available/aikz.usdt2026.cc")
    print(output)
    
    # 8. 验证 location 数量
    output, _ = exec_cmd(ssh, "sudo grep -c 'location /api/v1/notifications/ws' /etc/nginx/sites-available/aikz.usdt2026.cc")
    print(f"\nLocation 块数量: {output}（应该为 1）")
    
    print("\n" + "=" * 60)
    print("修复完成！")
    print("=" * 60)
    print("\n请执行以下命令应用配置：")
    print("sudo nginx -t && sudo systemctl reload nginx")
    print("\n如果 reload 失败，使用 restart：")
    print("sudo systemctl restart nginx")
    
    ssh.close()
    
except Exception as e:
    print(f"\n[错误] {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n完成！")

