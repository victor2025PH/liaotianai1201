#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用 SFTP 上传 Nginx 配置文件并应用修复
"""
import paramiko
import sys
import os

# 强制使用 UTF-8
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

SERVER = "165.154.233.55"
USERNAME = "ubuntu"
PASSWORD = "Along2025!!!"

print("=" * 60)
print("WebSocket 连接修复 - SFTP 部署")
print("=" * 60)
sys.stdout.flush()

try:
    # 读取本地配置文件
    config_file = os.path.join(os.path.dirname(__file__), "nginx_websocket_config.conf")
    if not os.path.exists(config_file):
        print(f"[ERROR] 配置文件不存在: {config_file}")
        sys.exit(1)
    
    with open(config_file, 'r', encoding='utf-8') as f:
        nginx_config = f.read()
    
    print(f"[OK] 已读取配置文件: {config_file}")
    sys.stdout.flush()
    
    # SSH 连接
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(SERVER, username=USERNAME, password=PASSWORD, timeout=30)
    print("[OK] SSH 连接成功")
    sys.stdout.flush()
    
    # 备份现有配置
    print("\n>>> 备份现有配置...")
    sys.stdout.flush()
    stdin, stdout, stderr = ssh.exec_command(
        "sudo cp /etc/nginx/sites-available/aikz.usdt2026.cc /etc/nginx/sites-available/aikz.usdt2026.cc.bak.$(date +%Y%m%d_%H%M%S)"
    )
    stdout.channel.recv_exit_status()
    print("[OK] 配置已备份")
    sys.stdout.flush()
    
    # 使用 SFTP 上传配置
    print("\n>>> 上传新配置...")
    sys.stdout.flush()
    sftp = ssh.open_sftp()
    
    # 写入临时文件
    temp_file = "/tmp/nginx_config_new.conf"
    with sftp.file(temp_file, 'w') as f:
        f.write(nginx_config)
    
    sftp.close()
    print("[OK] 配置已上传到临时文件")
    sys.stdout.flush()
    
    # 移动到目标位置
    print("\n>>> 应用新配置...")
    sys.stdout.flush()
    stdin, stdout, stderr = ssh.exec_command(
        f"sudo mv {temp_file} /etc/nginx/sites-available/aikz.usdt2026.cc && sudo chown root:root /etc/nginx/sites-available/aikz.usdt2026.cc"
    )
    exit_status = stdout.channel.recv_exit_status()
    
    if exit_status == 0:
        print("[OK] 配置已应用")
        sys.stdout.flush()
        
        # 测试配置
        print("\n>>> 测试 Nginx 配置...")
        sys.stdout.flush()
        stdin, stdout, stderr = ssh.exec_command("sudo nginx -t")
        test_output = stdout.read().decode('utf-8', errors='ignore')
        error_output = stderr.read().decode('utf-8', errors='ignore')
        print(test_output)
        if error_output:
            print(f"错误: {error_output}")
        sys.stdout.flush()
        
        if "syntax is ok" in test_output:
            # 重载 Nginx
            print("\n>>> 重载 Nginx...")
            sys.stdout.flush()
            stdin, stdout, stderr = ssh.exec_command("sudo systemctl reload nginx")
            exit_status = stdout.channel.recv_exit_status()
            
            if exit_status == 0:
                print("[OK] Nginx 已重载")
                sys.stdout.flush()
                
                # 验证配置
                print("\n>>> 验证 WebSocket 配置...")
                sys.stdout.flush()
                stdin, stdout, stderr = ssh.exec_command(
                    "sudo cat /etc/nginx/sites-available/aikz.usdt2026.cc | grep -A 12 'notifications/ws'"
                )
                verification = stdout.read().decode('utf-8', errors='ignore')
                print(verification)
                sys.stdout.flush()
                
                # 检查后端服务
                print("\n>>> 检查后端服务状态...")
                sys.stdout.flush()
                stdin, stdout, stderr = ssh.exec_command("sudo systemctl status liaotian-backend --no-pager | head -10")
                backend_status = stdout.read().decode('utf-8', errors='ignore')
                print(backend_status)
                sys.stdout.flush()
                
                print("\n" + "=" * 60)
                print("[OK] WebSocket 配置修复完成！")
                print("=" * 60)
                print("\n修复内容：")
                print("1. 添加了专用的 WebSocket location (/api/v1/notifications/ws)")
                print("2. 配置了正确的 Upgrade 和 Connection 头")
                print("3. 设置了长连接超时（86400 秒）")
                print("4. 禁用了代理缓冲（proxy_buffering off）")
                print("\nWebSocket 路径：")
                print("  ws://aikz.usdt2026.cc/api/v1/notifications/ws/{user_email}")
                print("\n请在前端测试 WebSocket 连接。")
                sys.stdout.flush()
            else:
                print(f"[ERROR] 重载 Nginx 失败，退出码: {exit_status}")
                sys.stdout.flush()
        else:
            print("\n[ERROR] Nginx 配置测试失败，请检查上面的错误信息")
            print("可以使用以下命令恢复备份：")
            print("  sudo cp /etc/nginx/sites-available/aikz.usdt2026.cc.bak.* /etc/nginx/sites-available/aikz.usdt2026.cc")
            sys.stdout.flush()
    else:
        print(f"[ERROR] 应用配置失败，退出码: {exit_status}")
        sys.stdout.flush()
    
    ssh.close()
    
except Exception as e:
    print(f"[ERROR] 发生错误: {e}")
    import traceback
    traceback.print_exc()
    sys.stdout.flush()
    sys.exit(1)

