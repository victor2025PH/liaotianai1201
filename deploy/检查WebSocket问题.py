#!/usr/bin/env python3
"""
检查 WebSocket 问题
"""

import subprocess
import sys

def run_ssh(cmd, description):
    """执行 SSH 命令并显示输出"""
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
    print("检查 WebSocket 问题")
    print("="*60)
    
    # 1. 检查 Nginx WebSocket 配置
    print("\n[检查 1] Nginx WebSocket 配置...")
    success, output = run_ssh(
        "sudo grep -A 20 'location /api/v1/notifications/ws' /etc/nginx/sites-available/aikz.usdt2026.cc",
        "WebSocket Location 配置"
    )
    
    # 2. 检查 Nginx 配置语法
    print("\n[检查 2] Nginx 配置语法...")
    success, output = run_ssh(
        "sudo nginx -t",
        "Nginx 配置测试"
    )
    
    # 3. 检查后端服务状态
    print("\n[检查 3] 后端服务状态...")
    success, output = run_ssh(
        "sudo systemctl status liaotian-backend --no-pager | head -15",
        "后端服务状态"
    )
    
    # 4. 检查后端日志
    print("\n[检查 4] 后端日志（最近 30 条）...")
    success, output = run_ssh(
        "sudo journalctl -u liaotian-backend -n 30 --no-pager | tail -20",
        "后端服务日志"
    )
    
    # 5. 检查 Nginx 错误日志
    print("\n[检查 5] Nginx 错误日志（最近 20 条）...")
    success, output = run_ssh(
        "sudo tail -20 /var/log/nginx/error.log",
        "Nginx 错误日志"
    )
    
    # 6. 测试后端 WebSocket 端点（直接连接）
    print("\n[检查 6] 测试后端 WebSocket 端点（直接连接）...")
    success, output = run_ssh(
        "curl -i -N -H 'Connection: Upgrade' -H 'Upgrade: websocket' -H 'Sec-WebSocket-Version: 13' -H 'Sec-WebSocket-Key: test' http://127.0.0.1:8000/api/v1/notifications/ws/test@example.com 2>&1 | head -15",
        "测试后端 WebSocket 端点"
    )
    
    # 7. 检查后端端口是否监听
    print("\n[检查 7] 检查后端端口监听...")
    success, output = run_ssh(
        "sudo netstat -tlnp | grep :8000 || sudo ss -tlnp | grep :8000",
        "后端端口监听状态"
    )
    
    print("\n" + "="*60)
    print("检查完成")
    print("="*60)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

