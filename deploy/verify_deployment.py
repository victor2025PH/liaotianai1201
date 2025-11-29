# -*- coding: utf-8 -*-
"""验证 WebSocket 配置是否已部署"""
import paramiko

SERVER = "165.154.233.55"
USERNAME = "ubuntu"
PASSWORD = "Along2025!!!"

print("验证 WebSocket 配置部署状态...")
print("=" * 60)

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(SERVER, username=USERNAME, password=PASSWORD, timeout=30)
    print("[OK] SSH 连接成功\n")
    
    # 检查 WebSocket 配置
    print(">>> 检查 WebSocket 配置...")
    stdin, stdout, stderr = ssh.exec_command(
        "sudo grep -A 12 'notifications/ws' /etc/nginx/sites-available/aikz.usdt2026.cc 2>&1"
    )
    output = stdout.read().decode('utf-8', errors='ignore')
    
    if "notifications/ws" in output and "Upgrade" in output:
        print("[OK] WebSocket 配置已存在")
        print("\n配置内容：")
        print(output)
        
        # 检查 Nginx 状态
        print("\n>>> 检查 Nginx 状态...")
        stdin, stdout, stderr = ssh.exec_command("sudo systemctl is-active nginx 2>&1")
        nginx_status = stdout.read().decode('utf-8', errors='ignore').strip()
        print(f"Nginx 状态: {nginx_status}")
        
        # 检查后端服务
        print("\n>>> 检查后端服务...")
        stdin, stdout, stderr = ssh.exec_command("sudo systemctl is-active liaotian-backend 2>&1")
        backend_status = stdout.read().decode('utf-8', errors='ignore').strip()
        print(f"后端服务状态: {backend_status}")
        
        print("\n" + "=" * 60)
        print("[OK] WebSocket 配置已正确部署！")
        print("=" * 60)
    else:
        print("[WARN] WebSocket 配置未找到或配置不完整")
        print("需要执行部署脚本")
        if output:
            print(f"\n当前配置片段：\n{output}")
    
    ssh.close()
    
except Exception as e:
    print(f"[ERROR] 发生错误: {e}")
    import traceback
    traceback.print_exc()
