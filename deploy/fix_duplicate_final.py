# -*- coding: utf-8 -*-
"""最终修复重复的 WebSocket location - 使用更可靠的方法"""
import paramiko
import sys

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
    
    # 1. 先查看当前配置，找到所有 location 块的位置
    print(">>> 1. 查找所有 WebSocket location 块...")
    stdin, stdout, stderr = ssh.exec_command(
        "sudo grep -n 'location /api/v1/notifications/ws' /etc/nginx/sites-available/aikz.usdt2026.cc"
    )
    locations = stdout.read().decode('utf-8', errors='ignore')
    print(locations)
    
    # 2. 查看完整的配置内容
    print("\n>>> 2. 查看配置内容（包含 WebSocket 的部分）...")
    stdin, stdout, stderr = ssh.exec_command(
        "sudo grep -B 2 -A 20 'location /api/v1/notifications/ws' /etc/nginx/sites-available/aikz.usdt2026.cc"
    )
    full_config = stdout.read().decode('utf-8', errors='ignore')
    print(full_config)
    
    # 3. 备份
    print("\n>>> 3. 备份配置...")
    stdin, stdout, stderr = ssh.exec_command(
        "sudo cp /etc/nginx/sites-available/aikz.usdt2026.cc /etc/nginx/sites-available/aikz.usdt2026.cc.bak.final 2>&1"
    )
    stdout.channel.recv_exit_status()
    print("[OK] 已备份\n")
    
    # 4. 使用 Python 脚本在服务器上处理
    print(">>> 4. 修复配置（删除重复的 location）...")
    
    fix_script = '''import re

# 读取文件
with open('/etc/nginx/sites-available/aikz.usdt2026.cc', 'r', encoding='utf-8') as f:
    content = f.read()

# 使用正则表达式找到所有 location 块
# 匹配从 location 开始到对应的 } 结束的整个块
pattern = r'(?m)^[ \t]*(?:#.*\n)?[ \t]*location /api/v1/notifications/ws[ \t]*\{[^\}]*\n[ \t]*\}[ \t]*(?:\n|$)'

matches = list(re.finditer(pattern, content, re.MULTILINE | re.DOTALL))

print(f'找到 {len(matches)} 个 location 块')

if len(matches) > 1:
    # 保留第一个，删除后续的
    last_pos = 0
    new_content = ''
    
    for i, match in enumerate(matches):
        if i == 0:
            # 保留第一个
            new_content += content[last_pos:match.end()]
            last_pos = match.end()
        else:
            # 跳过重复的，但需要检查前面是否有注释
            # 向前查找，看是否有注释行
            start_pos = match.start()
            # 向前查找最多 3 行，看是否有注释
            lines_before = content[max(0, start_pos-200):start_pos]
            comment_match = re.search(r'#.*WebSocket.*\\n[ \\t]*$', lines_before, re.MULTILINE)
            
            if comment_match:
                # 包含注释，从注释开始删除
                delete_start = max(0, start_pos-200) + comment_match.start()
            else:
                delete_start = start_pos
            
            new_content += content[last_pos:delete_start]
            last_pos = match.end()
    
    new_content += content[last_pos:]
    
    # 写入文件
    with open('/etc/nginx/sites-available/aikz.usdt2026.cc', 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print(f'已删除 {len(matches)-1} 个重复的 location 块')
else:
    print('未发现重复配置')
'''
    
    # 上传并执行修复脚本
    sftp = ssh.open_sftp()
    temp_script = "/tmp/fix_nginx_final.py"
    with sftp.file(temp_script, 'w') as f:
        f.write(fix_script)
    sftp.close()
    
    stdin, stdout, stderr = ssh.exec_command(f"sudo python3 {temp_script} 2>&1")
    output = stdout.read().decode('utf-8', errors='ignore')
    error = stderr.read().decode('utf-8', errors='ignore')
    print(output)
    if error:
        print(f"错误: {error}")
    
    # 5. 验证修复
    print("\n>>> 5. 验证修复结果...")
    stdin, stdout, stderr = ssh.exec_command(
        "sudo grep -c 'location /api/v1/notifications/ws' /etc/nginx/sites-available/aikz.usdt2026.cc"
    )
    count = stdout.read().decode('utf-8', errors='ignore').strip()
    print(f"WebSocket location 数量: {count}")
    
    if count == "1":
        print("[OK] 重复配置已删除\n")
        
        # 6. 测试配置
        print(">>> 6. 测试 Nginx 配置...")
        stdin, stdout, stderr = ssh.exec_command("sudo nginx -t 2>&1")
        test_output = stdout.read().decode('utf-8', errors='ignore')
        print(test_output)
        
        if "syntax is ok" in test_output:
            print("\n[OK] Nginx 配置语法正确")
            
            # 7. 重载 Nginx
            print("\n>>> 7. 重载 Nginx...")
            stdin, stdout, stderr = ssh.exec_command("sudo systemctl reload nginx 2>&1")
            reload_output = stdout.read().decode('utf-8', errors='ignore')
            error_output = stderr.read().decode('utf-8', errors='ignore')
            
            if reload_output:
                print(reload_output)
            if error_output:
                print(f"错误: {error_output}")
            
            # 检查重载是否成功
            stdin, stdout, stderr = ssh.exec_command("sudo systemctl is-active nginx 2>&1")
            nginx_status = stdout.read().decode('utf-8', errors='ignore').strip()
            if nginx_status == "active":
                print("[OK] Nginx 已成功重载")
            else:
                print(f"[警告] Nginx 状态: {nginx_status}")
            
            # 8. 显示最终配置
            print("\n>>> 8. 最终的 WebSocket 配置：")
            stdin, stdout, stderr = ssh.exec_command(
                "sudo grep -A 15 'location /api/v1/notifications/ws' /etc/nginx/sites-available/aikz.usdt2026.cc"
            )
            final_config = stdout.read().decode('utf-8', errors='ignore')
            print(final_config)
            
            print("\n" + "=" * 60)
            print("[OK] 修复完成！")
            print("=" * 60)
            print("\n下一步：")
            print("1. 在前端浏览器中刷新页面")
            print("2. 打开开发者工具（F12）→ Network 标签")
            print("3. 筛选 WS (WebSocket) 连接")
            print("4. 检查连接状态，应该看到状态码 101")
        else:
            print("\n[错误] Nginx 配置仍有问题")
            print("请检查上面的错误信息")
    else:
        print(f"\n[警告] 仍有 {count} 个 WebSocket location")
        print("可能需要手动编辑配置文件")
        
        # 显示所有 location 的位置
        print("\n所有 location 块的位置：")
        stdin, stdout, stderr = ssh.exec_command(
            "sudo grep -n 'location /api/v1/notifications/ws' /etc/nginx/sites-available/aikz.usdt2026.cc"
        )
        print(stdout.read().decode('utf-8', errors='ignore'))
    
    # 清理临时文件
    ssh.exec_command(f"rm {temp_script} 2>&1")
    
    ssh.close()
    
except Exception as e:
    print(f"\n[错误] 发生异常: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n修复完成！")

