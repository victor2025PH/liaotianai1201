# -*- coding: utf-8 -*-
"""检查当前 Nginx 配置，找到所有 location 块"""
import paramiko
import sys

SERVER = "165.154.233.55"
USERNAME = "ubuntu"
PASSWORD = "Along2025!!!"

print("=" * 60)
print("检查当前 Nginx 配置中的 WebSocket location")
print("=" * 60)

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(SERVER, username=USERNAME, password=PASSWORD, timeout=30)
    print("[OK] SSH 连接成功\n")
    
    # 1. 查看所有 location 的行号
    print(">>> 1. 所有 location 块的行号：")
    stdin, stdout, stderr = ssh.exec_command(
        "sudo grep -n 'location /api/v1/notifications/ws' /etc/nginx/sites-available/aikz.usdt2026.cc"
    )
    locations = stdout.read().decode('utf-8', errors='ignore')
    print(locations)
    
    # 2. 统计数量
    print(">>> 2. location 块数量：")
    stdin, stdout, stderr = ssh.exec_command(
        "sudo grep -c 'location /api/v1/notifications/ws' /etc/nginx/sites-available/aikz.usdt2026.cc"
    )
    count = stdout.read().decode('utf-8', errors='ignore').strip()
    print(f"找到 {count} 个 location 块\n")
    
    # 3. 显示所有 location 块及其上下文
    print(">>> 3. 所有 location 块的内容（前后各 2 行）：")
    stdin, stdout, stderr = ssh.exec_command(
        "sudo grep -B 2 -A 20 'location /api/v1/notifications/ws' /etc/nginx/sites-available/aikz.usdt2026.cc"
    )
    all_blocks = stdout.read().decode('utf-8', errors='ignore')
    print(all_blocks)
    
    # 4. 如果还有 2 个，显示每个的详细位置
    if count == "2":
        print("\n>>> 4. 详细分析每个 location 块：")
        
        # 获取所有行号
        stdin, stdout, stderr = ssh.exec_command(
            "sudo grep -n 'location /api/v1/notifications/ws' /etc/nginx/sites-available/aikz.usdt2026.cc | awk -F: '{print $1}'"
        )
        line_numbers = stdout.read().decode('utf-8', errors='ignore').strip().split('\n')
        
        for i, line_num in enumerate(line_numbers, 1):
            if line_num:
                line_num = int(line_num)
                print(f"\n--- 第 {i} 个 location 块（从第 {line_num} 行开始）---")
                # 显示这个 location 块的内容
                stdin, stdout, stderr = ssh.exec_command(
                    f"sudo sed -n '{max(1, line_num-2)},{line_num+20}p' /etc/nginx/sites-available/aikz.usdt2026.cc"
                )
                block_content = stdout.read().decode('utf-8', errors='ignore')
                print(block_content)
        
        print("\n" + "=" * 60)
        print("建议：")
        print("=" * 60)
        print("保留：第一个 location 块")
        print("删除：第二个 location 块（包括前面的注释）")
        print("\n可以使用以下命令查看第二个 location 块的确切位置：")
        if len(line_numbers) >= 2:
            second_line = line_numbers[1]
            print(f"sudo sed -n '{int(second_line)-1},{int(second_line)+15}p' /etc/nginx/sites-available/aikz.usdt2026.cc")
    
    ssh.close()
    
except Exception as e:
    print(f"\n[错误] 发生异常: {e}")
    import traceback
    traceback.print_exc()

print("\n检查完成！")

