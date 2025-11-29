# -*- coding: utf-8 -*-
"""
验证 WebSocket 配置部署状态
"""
import paramiko
import sys

# 设置 UTF-8 编码
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

SERVER = "165.154.233.55"
USERNAME = "ubuntu"
PASSWORD = "Along2025!!!"

print("=" * 60)
print("WebSocket 配置部署验证")
print("=" * 60)
print()

try:
    # SSH 连接
    print(">>> 连接服务器...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(SERVER, username=USERNAME, password=PASSWORD, timeout=30)
    print("[OK] SSH 连接成功\n")
    
    # 1. 检查 WebSocket 配置是否存在
    print(">>> 1. 检查 WebSocket 配置...")
    stdin, stdout, stderr = ssh.exec_command(
        "sudo grep -A 15 'notifications/ws' /etc/nginx/sites-available/aikz.usdt2026.cc 2>&1"
    )
    ws_config = stdout.read().decode('utf-8', errors='ignore')
    
    if "notifications/ws" in ws_config:
        print("[OK] WebSocket location 配置已找到")
        print("\n配置内容：")
        print("-" * 60)
        print(ws_config)
        print("-" * 60)
        
        # 检查关键配置项
        checks = {
            "proxy_pass": "proxy_pass" in ws_config,
            "Upgrade 头": "Upgrade" in ws_config and "$http_upgrade" in ws_config,
            "Connection 头": "Connection" in ws_config and "upgrade" in ws_config,
            "超时设置": "proxy_read_timeout" in ws_config or "proxy_send_timeout" in ws_config,
            "禁用缓冲": "proxy_buffering off" in ws_config,
        }
        
        print("\n配置项检查：")
        all_ok = True
        for item, status in checks.items():
            status_str = "[OK]" if status else "[缺失]"
            print(f"  {status_str} {item}")
            if not status:
                all_ok = False
        
        if not all_ok:
            print("\n[警告] 部分配置项缺失，可能影响 WebSocket 功能")
    else:
        print("[错误] WebSocket 配置未找到！")
        print("请检查配置是否正确部署")
        if ws_config:
            print(f"\n当前输出：\n{ws_config}")
    
    # 2. 检查 Nginx 配置语法
    print("\n>>> 2. 检查 Nginx 配置语法...")
    stdin, stdout, stderr = ssh.exec_command("sudo nginx -t 2>&1")
    nginx_test = stdout.read().decode('utf-8', errors='ignore')
    error_output = stderr.read().decode('utf-8', errors='ignore')
    
    print(nginx_test)
    if error_output:
        print(f"错误输出：{error_output}")
    
    if "syntax is ok" in nginx_test:
        print("[OK] Nginx 配置语法正确")
    else:
        print("[错误] Nginx 配置语法有误！")
    
    # 3. 检查 Nginx 服务状态
    print("\n>>> 3. 检查 Nginx 服务状态...")
    stdin, stdout, stderr = ssh.exec_command("sudo systemctl is-active nginx 2>&1")
    nginx_status = stdout.read().decode('utf-8', errors='ignore').strip()
    
    if nginx_status == "active":
        print("[OK] Nginx 服务运行中")
    else:
        print(f"[警告] Nginx 服务状态: {nginx_status}")
    
    # 检查 Nginx 是否正在监听
    stdin, stdout, stderr = ssh.exec_command("sudo netstat -tlnp | grep :80 || sudo ss -tlnp | grep :80")
    nginx_listen = stdout.read().decode('utf-8', errors='ignore')
    if nginx_listen:
        print("[OK] Nginx 正在监听端口 80")
    else:
        print("[警告] 未检测到 Nginx 监听端口 80")
    
    # 4. 检查后端服务状态
    print("\n>>> 4. 检查后端服务状态...")
    stdin, stdout, stderr = ssh.exec_command("sudo systemctl is-active liaotian-backend 2>&1")
    backend_status = stdout.read().decode('utf-8', errors='ignore').strip()
    
    if backend_status == "active":
        print("[OK] 后端服务运行中")
    else:
        print(f"[警告] 后端服务状态: {backend_status}")
    
    # 检查后端端口
    stdin, stdout, stderr = ssh.exec_command("sudo netstat -tlnp | grep :8000 || sudo ss -tlnp | grep :8000")
    backend_listen = stdout.read().decode('utf-8', errors='ignore')
    if backend_listen:
        print("[OK] 后端服务正在监听端口 8000")
    else:
        print("[警告] 未检测到后端服务监听端口 8000")
    
    # 5. 检查后端 WebSocket 路由
    print("\n>>> 5. 检查后端 WebSocket 路由...")
    stdin, stdout, stderr = ssh.exec_command(
        "curl -s http://localhost:8000/docs 2>&1 | grep -i 'websocket\\|notifications' | head -5 || echo '无法检查 API 文档'"
    )
    api_docs = stdout.read().decode('utf-8', errors='ignore')
    if api_docs and api_docs.strip() != "无法检查 API 文档":
        print("[OK] 后端 API 文档可访问")
    else:
        print("[信息] 无法直接检查 API 文档（这不影响功能）")
    
    # 6. 检查 Nginx 错误日志（最近的相关错误）
    print("\n>>> 6. 检查 Nginx 错误日志（最近 10 行）...")
    stdin, stdout, stderr = ssh.exec_command(
        "sudo tail -10 /var/log/nginx/error.log 2>&1 | grep -i -E 'websocket|ws|notifications' || echo '无相关错误'"
    )
    nginx_errors = stdout.read().decode('utf-8', errors='ignore')
    if nginx_errors.strip() and "无相关错误" not in nginx_errors:
        print("[警告] 发现相关错误日志：")
        print(nginx_errors)
    else:
        print("[OK] 无相关错误日志")
    
    # 总结
    print("\n" + "=" * 60)
    print("验证总结")
    print("=" * 60)
    
    if "notifications/ws" in ws_config and "syntax is ok" in nginx_test and nginx_status == "active":
        print("[OK] WebSocket 配置部署成功！")
        print("\n下一步：")
        print("1. 在前端浏览器中打开开发者工具（F12）")
        print("2. 切换到 Network 标签，筛选 WS (WebSocket)")
        print("3. 刷新页面，检查 WebSocket 连接状态")
        print("4. 应该看到状态码 101 (Switching Protocols) 表示连接成功")
        print("\nWebSocket 连接路径：")
        print("  ws://aikz.usdt2026.cc/api/v1/notifications/ws/{user_email}")
    else:
        print("[警告] 部分检查未通过，请查看上面的详细信息")
        print("\n建议：")
        if "notifications/ws" not in ws_config:
            print("- 检查 Nginx 配置文件是否正确包含 WebSocket location")
        if "syntax is ok" not in nginx_test:
            print("- 运行 'sudo nginx -t' 查看详细错误信息")
        if nginx_status != "active":
            print("- 检查 Nginx 服务状态：sudo systemctl status nginx")
    
    ssh.close()
    
except Exception as e:
    print(f"\n[错误] 验证过程发生异常: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n验证完成！")

