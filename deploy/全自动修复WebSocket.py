#!/usr/bin/env python3
"""
全自动修复 WebSocket 连接问题
"""

import subprocess
import sys
import os

def run_command(cmd, check=True, capture_output=False):
    """执行命令"""
    print(f"执行: {cmd}")
    try:
        if capture_output:
            result = subprocess.run(
                cmd,
                shell=True,
                check=check,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='ignore'
            )
            return result.stdout, result.stderr, result.returncode
        else:
            result = subprocess.run(
                cmd,
                shell=True,
                check=check
            )
            return None, None, result.returncode
    except subprocess.CalledProcessError as e:
        print(f"[错误] 命令执行失败: {e}")
        return None, None, e.returncode

def main():
    print("=" * 60)
    print("全自动修复 WebSocket 连接问题")
    print("=" * 60)
    print()
    
    server = "ubuntu@165.154.233.55"
    script_path = "deploy/修复WebSocket-服务器直接执行.sh"
    remote_script = "/tmp/修复WS.sh"
    
    # 步骤 1: 检查 SSH 连接
    print("[步骤 1/5] 检查 SSH 连接...")
    stdout, stderr, code = run_command(
        f'ssh -o BatchMode=yes -o ConnectTimeout=5 {server} "echo test"',
        check=False,
        capture_output=True
    )
    
    if code != 0:
        print("[错误] SSH 密钥未配置或连接失败")
        print(f"错误信息: {stderr}")
        print()
        print("请先配置 SSH 密钥：")
        print("  1. 运行: deploy\\配置SSH密钥认证.bat")
        print("  2. 或手动配置 SSH 密钥")
        return 1
    
    print("[OK] SSH 连接正常")
    print()
    
    # 步骤 2: 上传脚本
    print("[步骤 2/5] 上传修复脚本到服务器...")
    stdout, stderr, code = run_command(
        f'scp {script_path} {server}:{remote_script}',
        check=False,
        capture_output=True
    )
    
    if code != 0:
        print("[错误] 上传失败")
        print(f"错误信息: {stderr}")
        print()
        print("可能原因：")
        print("  1. SSH 需要密码（请配置 SSH 密钥）")
        print("  2. 文件路径不正确")
        return 1
    
    print("[OK] 脚本已上传")
    print()
    
    # 步骤 3: 执行修复
    print("[步骤 3/5] 在服务器上执行修复...")
    print("（这可能需要几秒钟）")
    stdout, stderr, code = run_command(
        f'ssh {server} "chmod +x {remote_script} && sudo bash {remote_script}"',
        check=False,
        capture_output=True
    )
    
    if stdout:
        print(stdout)
    if stderr:
        print("错误输出:", stderr)
    
    if code != 0:
        print("[错误] 修复执行失败")
        return 1
    
    print("[OK] 修复执行完成")
    print()
    
    # 步骤 4: 验证配置
    print("[步骤 4/5] 验证修复结果...")
    stdout, stderr, code = run_command(
        f'ssh {server} "sudo grep -A 12 \'location /api/v1/notifications/ws\' /etc/nginx/sites-available/aikz.usdt2026.cc"',
        check=False,
        capture_output=True
    )
    
    if stdout:
        print("WebSocket 配置：")
        print(stdout)
    else:
        print("[警告] 未找到 WebSocket 配置")
    
    print()
    
    # 步骤 5: 检查服务状态
    print("[步骤 5/5] 检查 Nginx 状态...")
    stdout, stderr, code = run_command(
        f'ssh {server} "sudo systemctl status nginx --no-pager | head -5"',
        check=False,
        capture_output=True
    )
    
    if stdout:
        print(stdout)
    
    print()
    print("=" * 60)
    print("修复完成！")
    print("=" * 60)
    print()
    print("下一步：")
    print("1. 在浏览器中刷新页面（按 F5）")
    print("2. 打开开发者工具（F12）→ Console")
    print("3. 检查 WebSocket 错误是否消失")
    print()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

