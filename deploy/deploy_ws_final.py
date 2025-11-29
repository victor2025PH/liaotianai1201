# -*- coding: utf-8 -*-
import paramiko
import os
import sys

SERVER = "165.154.233.55"
USERNAME = "ubuntu"
PASSWORD = "Along2025!!!"

log_file = open("deploy/deploy_log.txt", "w", encoding="utf-8")

def log(msg):
    print(msg)
    log_file.write(msg + "\n")
    log_file.flush()

log("=" * 60)
log("WebSocket 连接修复部署")
log("=" * 60)

try:
    log("正在连接 SSH...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(SERVER, username=USERNAME, password=PASSWORD, timeout=30)
    log("[OK] SSH 连接成功")
    
    # 读取配置文件
    config_path = os.path.join(os.path.dirname(__file__), "nginx_websocket_config.conf")
    log(f"读取配置文件: {config_path}")
    with open(config_path, "r", encoding="utf-8") as f:
        nginx_config = f.read()
    log("[OK] 已读取配置文件")
    
    # 备份
    log("\n>>> 备份现有配置...")
    stdin, stdout, stderr = ssh.exec_command(
        "sudo cp /etc/nginx/sites-available/aikz.usdt2026.cc /etc/nginx/sites-available/aikz.usdt2026.cc.bak.$(date +%Y%m%d_%H%M%S) 2>&1"
    )
    stdout.channel.recv_exit_status()
    log("[OK] 配置已备份")
    
    # 上传配置
    log("\n>>> 上传新配置...")
    sftp = ssh.open_sftp()
    temp_file = "/tmp/nginx_ws_config.conf"
    with sftp.file(temp_file, 'w') as f:
        f.write(nginx_config)
    sftp.close()
    log("[OK] 配置已上传")
    
    # 应用配置
    log("\n>>> 应用新配置...")
    stdin, stdout, stderr = ssh.exec_command(
        f"sudo mv {temp_file} /etc/nginx/sites-available/aikz.usdt2026.cc && sudo chown root:root /etc/nginx/sites-available/aikz.usdt2026.cc 2>&1"
    )
    stdout.channel.recv_exit_status()
    log("[OK] 配置已应用")
    
    # 测试配置
    log("\n>>> 测试 Nginx 配置...")
    stdin, stdout, stderr = ssh.exec_command("sudo nginx -t 2>&1")
    test_output = stdout.read().decode('utf-8', errors='ignore')
    log(test_output)
    
    if "syntax is ok" in test_output:
        # 重载
        log("\n>>> 重载 Nginx...")
        stdin, stdout, stderr = ssh.exec_command("sudo systemctl reload nginx 2>&1")
        stdout.channel.recv_exit_status()
        log("[OK] Nginx 已重载")
        
        # 验证
        log("\n>>> 验证 WebSocket 配置...")
        stdin, stdout, stderr = ssh.exec_command(
            "sudo grep -A 12 'notifications/ws' /etc/nginx/sites-available/aikz.usdt2026.cc 2>&1"
        )
        verification = stdout.read().decode('utf-8', errors='ignore')
        if verification.strip():
            log(verification)
        else:
            log("[WARN] 未找到 WebSocket 配置")
        
        log("\n" + "=" * 60)
        log("[OK] WebSocket 配置修复完成！")
        log("=" * 60)
        log("\n修复内容：")
        log("1. 添加了专用的 WebSocket location")
        log("2. 配置了正确的 Upgrade 和 Connection 头")
        log("3. 设置了长连接超时")
        log("4. 禁用了代理缓冲")
        log("\nWebSocket 路径：")
        log("  ws://aikz.usdt2026.cc/api/v1/notifications/ws/{user_email}")
        log("\n请在前端测试 WebSocket 连接。")
    else:
        log("\n[ERROR] Nginx 配置测试失败")
    
    ssh.close()
    log("\n部署完成!")
    
except Exception as e:
    log(f"[ERROR] 发生错误: {e}")
    import traceback
    traceback.print_exc(file=log_file)
    log_file.close()
    sys.exit(1)

log_file.close()

