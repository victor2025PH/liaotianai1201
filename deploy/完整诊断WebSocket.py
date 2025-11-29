#!/usr/bin/env python3
"""
完整诊断 WebSocket 连接问题
"""

import subprocess
import sys
import json

def run_ssh(cmd, description):
    """执行 SSH 命令"""
    print(f"\n{'='*60}")
    print(f"{description}")
    print(f"{'='*60}")
    
    full_cmd = f'ssh ubuntu@165.154.233.55 "{cmd}"'
    print(f"执行: {full_cmd}\n")
    
    try:
        result = subprocess.run(
            full_cmd,
            shell=True,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='ignore'
        )
        
        output = result.stdout + result.stderr
        if output.strip():
            print(output)
        else:
            print("(无输出)")
        
        return result.returncode == 0, output
    except Exception as e:
        print(f"错误: {e}")
        return False, str(e)

def main():
    print("="*60)
    print("完整诊断 WebSocket 连接问题")
    print("="*60)
    
    # 1. 检查 Nginx WebSocket 配置
    print("\n[诊断 1] 检查 Nginx WebSocket 配置...")
    success, output = run_ssh(
        "sudo grep -A 20 'location /api/v1/notifications/ws' /etc/nginx/sites-available/aikz.usdt2026.cc",
        "WebSocket Location 配置"
    )
    
    if not output or 'location /api/v1/notifications/ws' not in output:
        print("\n[问题] WebSocket location 不存在，需要添加")
        print("\n[修复] 执行修复脚本...")
        run_ssh(
            "chmod +x /tmp/修复WS.sh && sudo bash /tmp/修复WS.sh",
            "执行修复"
        )
    else:
        print("\n[OK] WebSocket location 已存在")
        # 检查配置完整性
        if 'Upgrade' in output and 'upgrade' in output and 'proxy_pass' in output:
            print("[OK] WebSocket 配置完整")
        else:
            print("[警告] WebSocket 配置可能不完整")
    
    # 2. 检查 Nginx 配置语法
    print("\n[诊断 2] 检查 Nginx 配置语法...")
    success, output = run_ssh(
        "sudo nginx -t",
        "Nginx 配置测试"
    )
    
    if success and 'syntax is ok' in output:
        print("[OK] Nginx 配置语法正确")
    else:
        print("[错误] Nginx 配置语法错误")
        return 1
    
    # 3. 检查服务状态
    print("\n[诊断 3] 检查服务状态...")
    success, output = run_ssh(
        "sudo systemctl is-active nginx && echo 'Nginx: active' || echo 'Nginx: inactive'",
        "Nginx 服务状态"
    )
    
    success, output = run_ssh(
        "sudo systemctl is-active liaotian-backend && echo 'Backend: active' || echo 'Backend: inactive'",
        "后端服务状态"
    )
    
    # 4. 检查后端日志
    print("\n[诊断 4] 检查后端日志（最近 30 条）...")
    success, output = run_ssh(
        "sudo journalctl -u liaotian-backend -n 30 --no-pager | tail -20",
        "后端服务日志"
    )
    
    # 5. 检查 WebSocket 端点是否可访问
    print("\n[诊断 5] 检查后端 WebSocket 端点...")
    success, output = run_ssh(
        "curl -i -N -H 'Connection: Upgrade' -H 'Upgrade: websocket' -H 'Sec-WebSocket-Version: 13' -H 'Sec-WebSocket-Key: test' http://127.0.0.1:8000/api/v1/notifications/ws/test@example.com 2>&1 | head -10",
        "测试后端 WebSocket 端点"
    )
    
    # 6. 检查 Nginx 错误日志
    print("\n[诊断 6] 检查 Nginx 错误日志（最近 20 条）...")
    success, output = run_ssh(
        "sudo tail -20 /var/log/nginx/error.log",
        "Nginx 错误日志"
    )
    
    # 7. 检查 Nginx 访问日志中的 WebSocket 请求
    print("\n[诊断 7] 检查 Nginx 访问日志中的 WebSocket 请求...")
    success, output = run_ssh(
        "sudo tail -50 /var/log/nginx/access.log | grep -i 'notifications/ws' || echo '未找到 WebSocket 请求'",
        "WebSocket 访问日志"
    )
    
    print("\n" + "="*60)
    print("诊断完成")
    print("="*60)
    print("\n建议：")
    print("1. 如果 WebSocket location 不存在，已自动执行修复")
    print("2. 检查浏览器 Console（F12）查看前端错误")
    print("3. 确保用户已登录（WebSocket 需要用户邮箱）")
    print("4. 刷新浏览器页面（F5）")
    print()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

