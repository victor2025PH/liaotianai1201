#!/usr/bin/env python3
"""
全自动测试 SSH 连接和输出
"""

import subprocess
import sys
from datetime import datetime

def run_ssh_test(cmd, description):
    """执行 SSH 命令测试并返回结果"""
    print(f"\n{'='*60}")
    print(f"{description}")
    print(f"{'='*60}")
    print(f"执行命令: ssh ubuntu@165.154.233.55 \"{cmd}\"")
    print()
    
    full_cmd = f'ssh ubuntu@165.154.233.55 "{cmd}"'
    
    try:
        result = subprocess.run(
            full_cmd,
            shell=True,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='ignore',
            timeout=30
        )
        
        print(f"退出码: {result.returncode}")
        print()
        
        if result.stdout:
            print("标准输出 (stdout):")
            print("-" * 60)
            print(result.stdout)
            print("-" * 60)
        else:
            print("标准输出 (stdout): (空)")
        
        if result.stderr:
            print()
            print("错误输出 (stderr):")
            print("-" * 60)
            print(result.stderr)
            print("-" * 60)
        else:
            print()
            print("错误输出 (stderr): (空)")
        
        return result.returncode == 0, result.stdout, result.stderr
        
    except subprocess.TimeoutExpired:
        print("❌ 命令执行超时（超过 30 秒）")
        return False, "", "Timeout"
    except Exception as e:
        print(f"❌ 执行失败: {e}")
        return False, "", str(e)

def main():
    print("="*60)
    print("全自动测试 SSH 连接和输出")
    print("="*60)
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    results = []
    
    # 测试 1: 基本连接测试
    success, stdout, stderr = run_ssh_test(
        "echo 'Hello from server - SSH 连接测试成功'",
        "测试 1: 基本连接测试"
    )
    results.append(("基本连接", success, bool(stdout), bool(stderr)))
    
    # 测试 2: 中文输出测试
    success, stdout, stderr = run_ssh_test(
        "echo '测试中文输出：你好世界'",
        "测试 2: 中文输出测试"
    )
    results.append(("中文输出", success, bool(stdout), bool(stderr)))
    
    # 测试 3: 系统信息
    success, stdout, stderr = run_ssh_test(
        "whoami && hostname && pwd",
        "测试 3: 系统信息"
    )
    results.append(("系统信息", success, bool(stdout), bool(stderr)))
    
    # 测试 4: Nginx 配置测试
    success, stdout, stderr = run_ssh_test(
        "sudo nginx -t",
        "测试 4: Nginx 配置语法检查"
    )
    results.append(("Nginx 配置", success, bool(stdout), bool(stderr)))
    
    # 测试 5: 检查 WebSocket 配置
    success, stdout, stderr = run_ssh_test(
        "sudo grep -A 15 'location /api/v1/notifications/ws' /etc/nginx/sites-available/aikz.usdt2026.cc",
        "测试 5: 检查 WebSocket 配置"
    )
    results.append(("WebSocket 配置", success, bool(stdout), bool(stderr)))
    
    # 测试 6: 检查服务状态
    success, stdout, stderr = run_ssh_test(
        "sudo systemctl is-active nginx && sudo systemctl is-active liaotian-backend",
        "测试 6: 检查服务状态"
    )
    results.append(("服务状态", success, bool(stdout), bool(stderr)))
    
    # 测试 7: 检查后端日志（WebSocket 相关）
    success, stdout, stderr = run_ssh_test(
        "sudo journalctl -u liaotian-backend -n 20 --no-pager | grep -i websocket || echo '未找到 WebSocket 相关日志'",
        "测试 7: 检查后端 WebSocket 日志"
    )
    results.append(("后端日志", success, bool(stdout), bool(stderr)))
    
    # 测试 8: 检查 Nginx 错误日志
    success, stdout, stderr = run_ssh_test(
        "sudo tail -20 /var/log/nginx/error.log | grep -i websocket || echo '未找到 WebSocket 相关错误'",
        "测试 8: 检查 Nginx 错误日志"
    )
    results.append(("Nginx 错误日志", success, bool(stdout), bool(stderr)))
    
    # 测试 9: 测试后端 WebSocket 端点（直接连接）
    success, stdout, stderr = run_ssh_test(
        "curl -i -N -H 'Connection: Upgrade' -H 'Upgrade: websocket' -H 'Sec-WebSocket-Version: 13' -H 'Sec-WebSocket-Key: test' http://127.0.0.1:8000/api/v1/notifications/ws/test@example.com 2>&1 | head -15",
        "测试 9: 测试后端 WebSocket 端点（直接连接）"
    )
    results.append(("后端 WebSocket", success, bool(stdout), bool(stderr)))
    
    # 测试 10: 检查端口监听
    success, stdout, stderr = run_ssh_test(
        "sudo netstat -tlnp 2>/dev/null | grep :8000 || sudo ss -tlnp 2>/dev/null | grep :8000 || echo '未找到端口 8000 监听'",
        "测试 10: 检查后端端口监听"
    )
    results.append(("端口监听", success, bool(stdout), bool(stderr)))
    
    # 总结
    print("\n" + "="*60)
    print("测试总结")
    print("="*60)
    print(f"{'测试项':<20} {'成功':<8} {'有输出':<8} {'有错误':<8}")
    print("-" * 60)
    
    all_success = True
    for name, success, has_stdout, has_stderr in results:
        status = "✓" if success else "✗"
        stdout_status = "✓" if has_stdout else "✗"
        stderr_status = "✓" if has_stderr else "✗"
        print(f"{name:<20} {status:<8} {stdout_status:<8} {stderr_status:<8}")
        if not success:
            all_success = False
    
    print("-" * 60)
    
    if all_success:
        print("\n✅ 所有测试通过！SSH 连接正常。")
    else:
        print("\n⚠️  部分测试失败，请检查上述输出。")
    
    print()
    print("="*60)
    print("测试完成")
    print("="*60)
    
    return 0 if all_success else 1

if __name__ == "__main__":
    sys.exit(main())

