#!/usr/bin/env python3
"""
全自动修复 WebSocket 连接并检查配置
"""

import subprocess
import sys

def run_ssh_command(cmd, description):
    """执行 SSH 命令并返回输出"""
    print(f"\n{'='*60}")
    print(f"{description}")
    print(f"{'='*60}")
    
    full_cmd = f'ssh ubuntu@165.154.233.55 "{cmd}"'
    print(f"执行: {full_cmd}")
    
    try:
        result = subprocess.run(
            full_cmd,
            shell=True,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='ignore'
        )
        
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print("错误输出:", result.stderr)
        
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        print(f"执行失败: {e}")
        return False, "", str(e)

def main():
    print("="*60)
    print("全自动修复 WebSocket 连接")
    print("="*60)
    
    # 步骤 1: 上传修复脚本
    print("\n[步骤 1/6] 上传修复脚本到服务器...")
    try:
        result = subprocess.run(
            'scp deploy/修复WebSocket-服务器直接执行.sh ubuntu@165.154.233.55:/tmp/修复WS.sh',
            shell=True,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='ignore'
        )
        if result.returncode == 0:
            print("[OK] 脚本已上传")
        else:
            print(f"[错误] 上传失败: {result.stderr}")
            return 1
    except Exception as e:
        print(f"[错误] 上传失败: {e}")
        return 1
    
    # 步骤 2: 执行修复
    print("\n[步骤 2/6] 在服务器上执行修复...")
    success, stdout, stderr = run_ssh_command(
        "chmod +x /tmp/修复WS.sh && sudo bash /tmp/修复WS.sh",
        "执行修复脚本"
    )
    
    if not success:
        print("[错误] 修复执行失败")
        return 1
    
    # 步骤 3: 检查 WebSocket 配置
    print("\n[步骤 3/6] 检查 WebSocket 配置...")
    success, stdout, stderr = run_ssh_command(
        "sudo grep -A 15 'location /api/v1/notifications/ws' /etc/nginx/sites-available/aikz.usdt2026.cc",
        "WebSocket Location 配置"
    )
    
    if not stdout or 'location /api/v1/notifications/ws' not in stdout:
        print("[警告] 未找到 WebSocket location 配置")
    else:
        print("[OK] WebSocket location 配置已存在")
    
    # 步骤 4: 检查 Nginx 配置语法
    print("\n[步骤 4/6] 检查 Nginx 配置语法...")
    success, stdout, stderr = run_ssh_command(
        "sudo nginx -t",
        "Nginx 配置测试"
    )
    
    if success and 'syntax is ok' in stdout:
        print("[OK] Nginx 配置语法正确")
    else:
        print("[错误] Nginx 配置语法错误")
        return 1
    
    # 步骤 5: 检查 Nginx 服务状态
    print("\n[步骤 5/6] 检查 Nginx 服务状态...")
    success, stdout, stderr = run_ssh_command(
        "sudo systemctl status nginx --no-pager | head -10",
        "Nginx 服务状态"
    )
    
    # 步骤 6: 检查后端服务状态
    print("\n[步骤 6/6] 检查后端服务状态...")
    success, stdout, stderr = run_ssh_command(
        "sudo systemctl status liaotian-backend --no-pager | head -10",
        "后端服务状态"
    )
    
    print("\n" + "="*60)
    print("修复完成！")
    print("="*60)
    print("\n下一步：")
    print("1. 在浏览器中刷新页面（按 F5）")
    print("2. 打开开发者工具（F12）→ Console")
    print("3. 检查 WebSocket 错误是否消失")
    print()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

