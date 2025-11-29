#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化版 WebSocket 修复部署脚本
"""
import paramiko
import sys

SERVER = "165.154.233.55"
USERNAME = "ubuntu"
PASSWORD = "Along2025!!!"

print("=" * 60)
print("WebSocket 连接修复部署")
print("=" * 60)

try:
    # SSH 连接
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(SERVER, username=USERNAME, password=PASSWORD, timeout=30)
    print("[OK] SSH 连接成功")
    
    # 读取本地配置文件
    with open("deploy/nginx_websocket_config.conf", "r", encoding="utf-8") as f:
        nginx_config = f.read()
    
    print("[OK] 已读取配置文件")
    
    # 备份现有配置
    print("\n>>> 备份现有配置...")
    stdin, stdout, stderr = ssh.exec_command(
        "sudo cp /etc/nginx/sites-available/aikz.usdt2026.cc /etc/nginx/sites-available/aikz.usdt2026.cc.bak.$(date +%Y%m%d_%H%M%S) && echo '备份完成'"
    )
    output = stdout.read().decode('utf-8', errors='ignore')
    print(output if output else "备份命令执行完成")
    
    # 使用 SFTP 上传配置
    print("\n>>> 上传新配置...")
    sftp = ssh.open_sftp()
    temp_file = "/tmp/nginx_ws_config.conf"
    
    with sftp.file(temp_file, 'w') as f:
        f.write(nginx_config)
    
    sftp.close()
    print("[OK] 配置已上传")
    
    # 移动到目标位置
    print("\n>>> 应用新配置...")
    stdin, stdout, stderr = ssh.exec_command(
        f"sudo mv {temp_file} /etc/nginx/sites-available/aikz.usdt2026.cc && sudo chown root:root /etc/nginx/sites-available/aikz.usdt2026.cc && echo '配置已应用'"
    )
    output = stdout.read().decode('utf-8', errors='ignore')
    print(output if output else "配置应用完成")
    
    # 测试配置
    print("\n>>> 测试 Nginx 配置...")
    stdin, stdout, stderr = ssh.exec_command("sudo nginx -t")
    test_output = stdout.read().decode('utf-8', errors='ignore')
    error_output = stderr.read().decode('utf-8', errors='ignore')
    print(test_output)
    if error_output:
        print(f"错误: {error_output}")
    
    if "syntax is ok" in test_output:
        # 重载 Nginx
        print("\n>>> 重载 Nginx...")
        stdin, stdout, stderr = ssh.exec_command("sudo systemctl reload nginx && echo 'Nginx 已重载'")
        output = stdout.read().decode('utf-8', errors='ignore')
        print(output if output else "Nginx 重载完成")
        
        # 验证配置
        print("\n>>> 验证 WebSocket 配置...")
        stdin, stdout, stderr = ssh.exec_command(
            "sudo grep -A 12 'notifications/ws' /etc/nginx/sites-available/aikz.usdt2026.cc"
        )
        verification = stdout.read().decode('utf-8', errors='ignore')
        if verification:
            print(verification)
        else:
            print("未找到 WebSocket 配置（可能有问题）")
        
        # 检查后端服务
        print("\n>>> 检查后端服务...")
        stdin, stdout, stderr = ssh.exec_command("sudo systemctl is-active liaotian-backend && echo '后端服务运行中' || echo '后端服务未运行'")
        backend_status = stdout.read().decode('utf-8', errors='ignore')
        print(backend_status)
        
        print("\n" + "=" * 60)
        print("[OK] WebSocket 配置修复完成！")
        print("=" * 60)
        print("\n修复内容：")
        print("1. 添加了专用的 WebSocket location (/api/v1/notifications/ws)")
        print("2. 配置了正确的 Upgrade 和 Connection 头")
        print("3. 设置了长连接超时（86400 秒）")
        print("4. 禁用了代理缓冲")
        print("\nWebSocket 路径：")
        print("  ws://aikz.usdt2026.cc/api/v1/notifications/ws/{user_email}")
        print("\n请在前端测试 WebSocket 连接。")
    else:
        print("\n[ERROR] Nginx 配置测试失败")
        print("可以使用以下命令恢复备份：")
        print("  sudo cp /etc/nginx/sites-available/aikz.usdt2026.cc.bak.* /etc/nginx/sites-available/aikz.usdt2026.cc")
    
    ssh.close()
    
except Exception as e:
    print(f"[ERROR] 发生错误: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

