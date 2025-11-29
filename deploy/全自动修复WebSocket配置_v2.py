# -*- coding: utf-8 -*-
"""
全自动修复重复的 WebSocket location 配置 - 带详细输出
"""
import paramiko
import sys
import os

# 设置输出编码
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

SERVER = "165.154.233.55"
USERNAME = "ubuntu"
PASSWORD = "Along2025!!!"

log_messages = []

def log(msg):
    print(msg)
    log_messages.append(msg)
    sys.stdout.flush()

log("=" * 60)
log("全自动修复 WebSocket location 重复配置")
log("=" * 60)
log("")

try:
    # SSH 连接
    log(">>> 1. 连接服务器...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(SERVER, username=USERNAME, password=PASSWORD, timeout=30)
    log("[OK] SSH 连接成功\n")
    
    # 检查当前配置
    log(">>> 2. 检查当前配置...")
    stdin, stdout, stderr = ssh.exec_command(
        "sudo grep -n 'location /api/v1/notifications/ws' /etc/nginx/sites-available/aikz.usdt2026.cc 2>&1"
    )
    locations_output = stdout.read().decode('utf-8', errors='ignore')
    log(locations_output if locations_output.strip() else "未找到 location 块")
    
    stdin, stdout, stderr = ssh.exec_command(
        "sudo grep -c 'location /api/v1/notifications/ws' /etc/nginx/sites-available/aikz.usdt2026.cc 2>&1"
    )
    count = stdout.read().decode('utf-8', errors='ignore').strip()
    log(f"当前 location 块数量: {count}\n")
    
    if count == "1" or count == "0":
        log("[OK] 配置正常，只有一个或零个 location 块")
        log(">>> 测试配置...")
        stdin, stdout, stderr = ssh.exec_command("sudo nginx -t 2>&1")
        test_output = stdout.read().decode('utf-8', errors='ignore')
        log(test_output)
        ssh.close()
        sys.exit(0)
    
    # 备份配置
    log(">>> 3. 备份配置...")
    stdin, stdout, stderr = ssh.exec_command(
        "sudo cp /etc/nginx/sites-available/aikz.usdt2026.cc /etc/nginx/sites-available/aikz.usdt2026.cc.bak.auto 2>&1"
    )
    stdout.channel.recv_exit_status()
    log("[OK] 配置已备份\n")
    
    # 使用 Python 脚本在服务器上修复
    log(">>> 4. 执行修复脚本...")
    
    fix_script = '''import re

with open('/etc/nginx/sites-available/aikz.usdt2026.cc', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# 找到所有 location 行
location_indices = []
for i, line in enumerate(lines):
    if 'location /api/v1/notifications/ws' in line:
        location_indices.append(i)

print(f'找到 {len(location_indices)} 个 location 定义')

if len(location_indices) > 1:
    # 从后往前删除，避免索引变化
    for idx in reversed(location_indices[1:]):  # 跳过第一个
        # 向前查找注释
        block_start = idx
        for i in range(max(0, idx-3), idx):
            if '# WebSocket' in lines[i] or ('#' in lines[i] and 'WebSocket' in lines[i]):
                block_start = i
                break
        
        # 向后查找结束的 }
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
    
    print('重复的 location 块已删除')
else:
    print('未发现重复配置')
'''
    
    # 上传并执行修复脚本
    sftp = ssh.open_sftp()
    temp_script = "/tmp/fix_nginx_auto.py"
    with sftp.file(temp_script, 'w') as f:
        f.write(fix_script)
    sftp.close()
    
    stdin, stdout, stderr = ssh.exec_command(f"sudo python3 {temp_script} 2>&1")
    output = stdout.read().decode('utf-8', errors='ignore')
    error = stderr.read().decode('utf-8', errors='ignore')
    log(output)
    if error:
        log(f"错误: {error}")
    
    # 清理临时文件
    ssh.exec_command(f"rm {temp_script} 2>&1")
    
    # 验证
    log("\n>>> 5. 验证修复结果...")
    stdin, stdout, stderr = ssh.exec_command(
        "sudo grep -c 'location /api/v1/notifications/ws' /etc/nginx/sites-available/aikz.usdt2026.cc 2>&1"
    )
    new_count = stdout.read().decode('utf-8', errors='ignore').strip()
    log(f"剩余 location 块数量: {new_count}")
    
    if new_count == "1":
        log("[OK] 重复配置已删除\n")
        
        # 测试配置
        log(">>> 6. 测试 Nginx 配置...")
        stdin, stdout, stderr = ssh.exec_command("sudo nginx -t 2>&1")
        test_output = stdout.read().decode('utf-8', errors='ignore')
        log(test_output)
        
        if "syntax is ok" in test_output:
            log("\n[OK] Nginx 配置语法正确")
            
            # 重载 Nginx
            log("\n>>> 7. 重载 Nginx...")
            stdin, stdout, stderr = ssh.exec_command("sudo systemctl reload nginx 2>&1")
            reload_output = stdout.read().decode('utf-8', errors='ignore')
            log(reload_output if reload_output.strip() else "Nginx 重载完成")
            
            # 检查服务状态
            stdin, stdout, stderr = ssh.exec_command("sudo systemctl is-active nginx 2>&1")
            nginx_status = stdout.read().decode('utf-8', errors='ignore').strip()
            log(f"Nginx 状态: {nginx_status}")
            
            # 显示最终配置
            log("\n>>> 8. 最终配置：")
            stdin, stdout, stderr = ssh.exec_command(
                "sudo grep -A 15 'location /api/v1/notifications/ws' /etc/nginx/sites-available/aikz.usdt2026.cc 2>&1"
            )
            final_config = stdout.read().decode('utf-8', errors='ignore')
            log(final_config)
            
            log("\n" + "=" * 60)
            log("[OK] 修复完成！")
            log("=" * 60)
        else:
            log("\n[错误] Nginx 配置测试失败")
    else:
        log(f"\n[错误] 仍有 {new_count} 个 location 块")
    
    ssh.close()
    
except Exception as e:
    log(f"\n[错误] 发生异常: {e}")
    import traceback
    traceback.print_exc()

# 保存日志
try:
    with open('deploy/修复日志.txt', 'w', encoding='utf-8') as f:
        f.write('\n'.join(log_messages))
except:
    pass

log("\n修复完成！")

