# -*- coding: utf-8 -*-
"""
修复重复的 WebSocket location 配置
"""
import paramiko
import sys

SERVER = "165.154.233.55"
USERNAME = "ubuntu"
PASSWORD = "Along2025!!!"

print("=" * 60)
print("修复重复的 WebSocket location 配置")
print("=" * 60)
print()

try:
    # SSH 连接
    print(">>> 连接服务器...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(SERVER, username=USERNAME, password=PASSWORD, timeout=30)
    print("[OK] SSH 连接成功\n")
    
    # 读取当前配置
    print(">>> 读取当前配置...")
    stdin, stdout, stderr = ssh.exec_command(
        "sudo cat /etc/nginx/sites-available/aikz.usdt2026.cc"
    )
    current_config = stdout.read().decode('utf-8', errors='ignore')
    
    # 检查重复的 location
    ws_count = current_config.count('location /api/v1/notifications/ws')
    print(f"发现 {ws_count} 个 WebSocket location 配置")
    
    if ws_count > 1:
        print("[警告] 检测到重复的 WebSocket location 配置，需要修复\n")
        
        # 备份配置
        print(">>> 备份当前配置...")
        stdin, stdout, stderr = ssh.exec_command(
            "sudo cp /etc/nginx/sites-available/aikz.usdt2026.cc /etc/nginx/sites-available/aikz.usdt2026.cc.bak.duplicate_fix.$(date +%Y%m%d_%H%M%S) 2>&1"
        )
        stdout.channel.recv_exit_status()
        print("[OK] 配置已备份\n")
        
        # 读取完整配置并修复
        print(">>> 修复配置（删除重复的 location）...")
        
        # 使用 sed 删除第二个重复的 location 块
        # 找到第一个 location 块后的第二个，删除它
        stdin, stdout, stderr = ssh.exec_command("""
        sudo sed -i '/^[[:space:]]*# WebSocket 支持 - 通知服务$/,/^[[:space:]]*}[[:space:]]*$/{
            /^[[:space:]]*# WebSocket 支持 - 通知服务$/{
                :loop
                N
                /^[[:space:]]*}[[:space:]]*$/!b loop
                /location \/api\/v1\/notifications\/ws/{
                    :del
                    N
                    /^[[:space:]]*}[[:space:]]*$/!b del
                    d
                }
            }
        }' /etc/nginx/sites-available/aikz.usdt2026.cc 2>&1
        """)
        
        # 更简单的方法：使用 Python 脚本在服务器上处理
        fix_script = """
import re

with open('/etc/nginx/sites-available/aikz.usdt2026.cc', 'r', encoding='utf-8') as f:
    content = f.read()

# 找到所有 WebSocket location 块
pattern = r'(?m)^[ \t]*location /api/v1/notifications/ws \{.*?\n[ \t]*\}[ \t]*(?:\n|$)'
matches = list(re.finditer(pattern, content, re.DOTALL))

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
            # 跳过重复的
            new_content += content[last_pos:match.start()]
            last_pos = match.end()
    new_content += content[last_pos:]
    
    with open('/etc/nginx/sites-available/aikz.usdt2026.cc', 'w', encoding='utf-8') as f:
        f.write(new_content)
    print('已删除重复的 WebSocket location 配置')
else:
    print('未发现重复配置')
"""
        
        # 上传并执行修复脚本
        sftp = ssh.open_sftp()
        temp_script = "/tmp/fix_nginx.py"
        with sftp.file(temp_script, 'w') as f:
            f.write(fix_script)
        sftp.close()
        
        stdin, stdout, stderr = ssh.exec_command(f"sudo python3 {temp_script} 2>&1")
        output = stdout.read().decode('utf-8', errors='ignore')
        print(output)
        
        # 清理临时文件
        ssh.exec_command(f"rm {temp_script} 2>&1")
        
        # 验证修复
        print("\n>>> 验证修复结果...")
        stdin, stdout, stderr = ssh.exec_command(
            "sudo grep -c 'location /api/v1/notifications/ws' /etc/nginx/sites-available/aikz.usdt2026.cc 2>&1"
        )
        count = stdout.read().decode('utf-8', errors='ignore').strip()
        print(f"WebSocket location 数量: {count}")
        
        if count == "1":
            print("[OK] 重复配置已删除\n")
            
            # 测试配置
            print(">>> 测试 Nginx 配置...")
            stdin, stdout, stderr = ssh.exec_command("sudo nginx -t 2>&1")
            test_output = stdout.read().decode('utf-8', errors='ignore')
            print(test_output)
            
            if "syntax is ok" in test_output:
                print("\n[OK] Nginx 配置语法正确")
                
                # 重载 Nginx
                print("\n>>> 重载 Nginx...")
                stdin, stdout, stderr = ssh.exec_command("sudo systemctl reload nginx 2>&1")
                stdout.channel.recv_exit_status()
                print("[OK] Nginx 已重载")
                
                # 显示最终的 WebSocket 配置
                print("\n>>> 最终的 WebSocket 配置：")
                stdin, stdout, stderr = ssh.exec_command(
                    "sudo grep -A 15 'location /api/v1/notifications/ws' /etc/nginx/sites-available/aikz.usdt2026.cc 2>&1"
                )
                final_config = stdout.read().decode('utf-8', errors='ignore')
                print(final_config)
                
                print("\n" + "=" * 60)
                print("[OK] 修复完成！WebSocket 配置现在应该可以正常工作了")
                print("=" * 60)
            else:
                print("\n[错误] Nginx 配置仍有问题，请检查上面的错误信息")
        else:
            print(f"\n[警告] 仍有 {count} 个 WebSocket location，可能需要手动修复")
    else:
        print("[OK] 未发现重复配置")
        print("但 Nginx 测试失败，可能是其他问题")
        
        # 显示配置
        print("\n>>> 当前 WebSocket 配置：")
        stdin, stdout, stderr = ssh.exec_command(
            "sudo grep -A 15 'location /api/v1/notifications/ws' /etc/nginx/sites-available/aikz.usdt2026.cc 2>&1"
        )
        config = stdout.read().decode('utf-8', errors='ignore')
        print(config)
    
    ssh.close()
    
except Exception as e:
    print(f"\n[错误] 发生异常: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n修复完成！")

