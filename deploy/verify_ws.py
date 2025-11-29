# -*- coding: utf-8 -*-
import paramiko
import sys

SERVER = "165.154.233.55"
USERNAME = "ubuntu"
PASSWORD = "Along2025!!!"

output_file = open("deploy/verify_result.txt", "w", encoding="utf-8")

def log(msg):
    print(msg)
    output_file.write(msg + "\n")
    output_file.flush()

log("=" * 60)
log("WebSocket 配置部署验证")
log("=" * 60)
log("")

try:
    log(">>> 连接服务器...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(SERVER, username=USERNAME, password=PASSWORD, timeout=30)
    log("[OK] SSH 连接成功\n")
    
    # 1. 检查 WebSocket 配置
    log(">>> 1. 检查 WebSocket 配置...")
    stdin, stdout, stderr = ssh.exec_command(
        "sudo grep -A 15 'notifications/ws' /etc/nginx/sites-available/aikz.usdt2026.cc 2>&1"
    )
    ws_config = stdout.read().decode('utf-8', errors='ignore')
    
    if "notifications/ws" in ws_config:
        log("[OK] WebSocket location 配置已找到")
        log("\n配置内容：")
        log("-" * 60)
        log(ws_config)
        log("-" * 60)
        
        checks = {
            "proxy_pass": "proxy_pass" in ws_config,
            "Upgrade 头": "Upgrade" in ws_config and "$http_upgrade" in ws_config,
            "Connection 头": "Connection" in ws_config and "upgrade" in ws_config,
            "超时设置": "proxy_read_timeout" in ws_config or "proxy_send_timeout" in ws_config,
        }
        
        log("\n配置项检查：")
        for item, status in checks.items():
            log(f"  {'[OK]' if status else '[缺失]'} {item}")
    else:
        log("[错误] WebSocket 配置未找到！")
    
    # 2. 检查 Nginx 配置语法
    log("\n>>> 2. 检查 Nginx 配置语法...")
    stdin, stdout, stderr = ssh.exec_command("sudo nginx -t 2>&1")
    nginx_test = stdout.read().decode('utf-8', errors='ignore')
    log(nginx_test)
    
    if "syntax is ok" in nginx_test:
        log("[OK] Nginx 配置语法正确")
    else:
        log("[错误] Nginx 配置语法有误！")
    
    # 3. 检查服务状态
    log("\n>>> 3. 检查服务状态...")
    stdin, stdout, stderr = ssh.exec_command("sudo systemctl is-active nginx 2>&1")
    nginx_status = stdout.read().decode('utf-8', errors='ignore').strip()
    log(f"Nginx 状态: {nginx_status}")
    
    stdin, stdout, stderr = ssh.exec_command("sudo systemctl is-active liaotian-backend 2>&1")
    backend_status = stdout.read().decode('utf-8', errors='ignore').strip()
    log(f"后端服务状态: {backend_status}")
    
    # 总结
    log("\n" + "=" * 60)
    log("验证总结")
    log("=" * 60)
    
    if "notifications/ws" in ws_config and "syntax is ok" in nginx_test:
        log("[OK] WebSocket 配置部署成功！")
        log("\n下一步：在前端浏览器测试 WebSocket 连接")
    else:
        log("[警告] 部分检查未通过")
    
    ssh.close()
    
except Exception as e:
    log(f"\n[错误] 验证过程发生异常: {e}")
    import traceback
    traceback.print_exc(file=output_file)

output_file.close()
print("\n验证完成！结果已保存到 deploy/verify_result.txt")

