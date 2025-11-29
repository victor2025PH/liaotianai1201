# -*- coding: utf-8 -*-
"""
全自动修复重复的 WebSocket location 配置
"""
import paramiko
import sys
import re

SERVER = "165.154.233.55"
USERNAME = "ubuntu"
PASSWORD = "Along2025!!!"

print("=" * 60)
print("全自动修复 WebSocket location 重复配置")
print("=" * 60)
print()

try:
    # SSH 连接
    print(">>> 1. 连接服务器...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(SERVER, username=USERNAME, password=PASSWORD, timeout=30)
    print("[OK] SSH 连接成功\n")
    
    # 检查当前配置
    print(">>> 2. 检查当前配置...")
    stdin, stdout, stderr = ssh.exec_command(
        "sudo grep -n 'location /api/v1/notifications/ws' /etc/nginx/sites-available/aikz.usdt2026.cc"
    )
    locations_output = stdout.read().decode('utf-8', errors='ignore')
    print(locations_output)
    
    stdin, stdout, stderr = ssh.exec_command(
        "sudo grep -c 'location /api/v1/notifications/ws' /etc/nginx/sites-available/aikz.usdt2026.cc"
    )
    count = stdout.read().decode('utf-8', errors='ignore').strip()
    print(f"当前 location 块数量: {count}\n")
    
    if count == "1":
        print("[OK] 配置正常，只有一个 location 块")
        print(">>> 测试配置...")
        stdin, stdout, stderr = ssh.exec_command("sudo nginx -t 2>&1")
        test_output = stdout.read().decode('utf-8', errors='ignore')
        print(test_output)
        
        if "syntax is ok" in test_output:
            print("\n[OK] 配置正确，无需修复")
        else:
            print("\n[警告] 配置有语法错误，但只有一个 location 块")
        ssh.close()
        sys.exit(0)
    
    # 备份配置
    print(">>> 3. 备份配置...")
    stdin, stdout, stderr = ssh.exec_command(
        "sudo cp /etc/nginx/sites-available/aikz.usdt2026.cc /etc/nginx/sites-available/aikz.usdt2026.cc.bak.auto.$(date +%Y%m%d_%H%M%S) 2>&1"
    )
    stdout.channel.recv_exit_status()
    print("[OK] 配置已备份\n")
    
    # 读取配置文件
    print(">>> 4. 读取配置文件...")
    stdin, stdout, stderr = ssh.exec_command(
        "sudo cat /etc/nginx/sites-available/aikz.usdt2026.cc"
    )
    config_content = stdout.read().decode('utf-8', errors='ignore')
    lines = config_content.split('\n')
    print(f"[OK] 已读取 {len(lines)} 行配置\n")
    
    # 找到所有 location 块
    print(">>> 5. 查找所有 location 块...")
    location_indices = []
    for i, line in enumerate(lines):
        if 'location /api/v1/notifications/ws' in line:
            location_indices.append(i)
    
    print(f"找到 {len(location_indices)} 个 location 定义（行号：{[i+1 for i in location_indices]}）\n")
    
    if len(location_indices) <= 1:
        print("[OK] 只有一个 location 块，无需修复")
        ssh.close()
        sys.exit(0)
    
    # 删除第二个及之后的 location 块
    print(">>> 6. 删除重复的 location 块...")
    
    # 从后往前删除，避免索引变化
    blocks_to_delete = []
    for idx in reversed(location_indices[1:]):  # 跳过第一个，删除其余的
        # 向前查找注释（最多向前 3 行）
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
            line = lines[i]
            if '{' in line:
                brace_count += line.count('{')
                found_open = True
            if '}' in line:
                brace_count -= line.count('}')
                if found_open and brace_count == 0:
                    block_end = i
                    break
        
        blocks_to_delete.append((block_start, block_end))
        print(f"  标记删除：行 {block_start+1} 到 {block_end+1}")
    
    # 删除标记的块（从后往前删除）
    for block_start, block_end in blocks_to_delete:
        print(f"  删除行 {block_start+1} 到 {block_end+1}")
        lines = lines[:block_start] + lines[block_end+1:]
    
    # 写入新配置
    print("\n>>> 7. 写入修复后的配置...")
    new_config = '\n'.join(lines)
    
    # 使用 SFTP 上传
    sftp = ssh.open_sftp()
    temp_file = "/tmp/nginx_fixed.conf"
    with sftp.file(temp_file, 'w') as f:
        f.write(new_config)
    sftp.close()
    
    # 移动到目标位置
    stdin, stdout, stderr = ssh.exec_command(
        f"sudo mv {temp_file} /etc/nginx/sites-available/aikz.usdt2026.cc && sudo chown root:root /etc/nginx/sites-available/aikz.usdt2026.cc 2>&1"
    )
    stdout.channel.recv_exit_status()
    print("[OK] 配置已更新\n")
    
    # 验证
    print(">>> 8. 验证修复结果...")
    stdin, stdout, stderr = ssh.exec_command(
        "sudo grep -c 'location /api/v1/notifications/ws' /etc/nginx/sites-available/aikz.usdt2026.cc"
    )
    new_count = stdout.read().decode('utf-8', errors='ignore').strip()
    print(f"剩余 location 块数量: {new_count}")
    
    if new_count == "1":
        print("[OK] 重复配置已删除\n")
        
        # 测试配置
        print(">>> 9. 测试 Nginx 配置...")
        stdin, stdout, stderr = ssh.exec_command("sudo nginx -t 2>&1")
        test_output = stdout.read().decode('utf-8', errors='ignore')
        print(test_output)
        
        if "syntax is ok" in test_output:
            print("\n[OK] Nginx 配置语法正确")
            
            # 重载 Nginx
            print("\n>>> 10. 重载 Nginx...")
            stdin, stdout, stderr = ssh.exec_command("sudo systemctl reload nginx 2>&1")
            reload_output = stdout.read().decode('utf-8', errors='ignore')
            error_output = stderr.read().decode('utf-8', errors='ignore')
            
            if reload_output:
                print(reload_output)
            if error_output and "error" in error_output.lower():
                print(f"警告: {error_output}")
            
            # 检查服务状态
            stdin, stdout, stderr = ssh.exec_command("sudo systemctl is-active nginx 2>&1")
            nginx_status = stdout.read().decode('utf-8', errors='ignore').strip()
            
            if nginx_status == "active":
                print("[OK] Nginx 已成功重载")
            else:
                print(f"[警告] Nginx 状态: {nginx_status}")
            
            # 显示最终配置
            print("\n>>> 11. 最终配置：")
            stdin, stdout, stderr = ssh.exec_command(
                "sudo grep -A 15 'location /api/v1/notifications/ws' /etc/nginx/sites-available/aikz.usdt2026.cc"
            )
            final_config = stdout.read().decode('utf-8', errors='ignore')
            print(final_config)
            
            print("\n" + "=" * 60)
            print("[OK] 修复完成！")
            print("=" * 60)
            print("\n修复内容：")
            print(f"1. 删除了 {len(location_indices)-1} 个重复的 location 块")
            print("2. 保留了第一个 location 块")
            print("3. Nginx 配置已测试通过")
            print("4. Nginx 已重载")
            print("\n下一步：")
            print("1. 在前端浏览器中刷新页面")
            print("2. 打开开发者工具（F12）→ Network 标签")
            print("3. 筛选 WS (WebSocket) 连接")
            print("4. 检查连接状态，应该看到状态码 101")
        else:
            print("\n[错误] Nginx 配置测试失败")
            print("可以使用备份文件恢复：")
            print("  sudo cp /etc/nginx/sites-available/aikz.usdt2026.cc.bak.auto.* /etc/nginx/sites-available/aikz.usdt2026.cc")
    else:
        print(f"\n[错误] 仍有 {new_count} 个 location 块")
        print("可能需要手动检查配置文件")
    
    ssh.close()
    
except Exception as e:
    print(f"\n[错误] 发生异常: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n修复完成！")

