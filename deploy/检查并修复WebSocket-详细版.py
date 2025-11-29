#!/usr/bin/env python3
"""
详细检查并修复 WebSocket 连接
"""

import subprocess
import sys
import os

def run_command(cmd, description, capture_output=True):
    """执行命令并返回结果"""
    print(f"\n{'='*60}")
    print(f"{description}")
    print(f"{'='*60}")
    print(f"执行: {cmd}")
    
    try:
        if capture_output:
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='ignore'
            )
            output = result.stdout + result.stderr
            print(output)
            return result.returncode == 0, output
        else:
            result = subprocess.run(cmd, shell=True)
            return result.returncode == 0, ""
    except Exception as e:
        print(f"错误: {e}")
        return False, str(e)

def main():
    print("="*60)
    print("全自动修复 WebSocket 连接 - 详细版")
    print("="*60)
    
    server = "ubuntu@165.154.233.55"
    script_path = "deploy/修复WebSocket-服务器直接执行.sh"
    remote_script = "/tmp/修复WS.sh"
    
    # 步骤 1: 上传脚本
    print("\n[步骤 1] 上传修复脚本...")
    success, output = run_command(
        f'scp {script_path} {server}:{remote_script}',
        "上传修复脚本"
    )
    if not success:
        print("[错误] 上传失败")
        return 1
    
    # 步骤 2: 执行修复
    print("\n[步骤 2] 执行修复...")
    success, output = run_command(
        f'ssh {server} "chmod +x {remote_script} && sudo bash {remote_script}"',
        "执行修复脚本"
    )
    
    # 步骤 3: 检查 WebSocket 配置
    print("\n[步骤 3] 检查 WebSocket 配置...")
    success, output = run_command(
        f'ssh {server} "sudo grep -A 15 \'location /api/v1/notifications/ws\' /etc/nginx/sites-available/aikz.usdt2026.cc"',
        "WebSocket Location 配置"
    )
    
    if not output or 'location /api/v1/notifications/ws' not in output:
        print("[警告] 未找到 WebSocket location，需要添加")
        # 使用 Python 脚本添加
        print("\n[步骤 3.1] 使用 Python 脚本添加 WebSocket 配置...")
        python_script = '''
import re
config_path = "/etc/nginx/sites-available/aikz.usdt2026.cc"
with open(config_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()
api_idx = None
for i, line in enumerate(lines):
    if 'location /api/' in line:
        api_idx = i
        break
if api_idx is None:
    print("错误: 未找到 location /api/")
    exit(1)
has_ws = any('location /api/v1/notifications/ws' in line for line in lines[:api_idx])
if not has_ws:
    ws_block = ['    # WebSocket 支持\\n', '    location /api/v1/notifications/ws {\\n', '        proxy_pass http://127.0.0.1:8000;\\n', '        proxy_http_version 1.1;\\n', '        proxy_set_header Upgrade $http_upgrade;\\n', '        proxy_set_header Connection "upgrade";\\n', '        proxy_set_header Host $host;\\n', '        proxy_set_header X-Real-IP $remote_addr;\\n', '        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;\\n', '        proxy_set_header X-Forwarded-Proto $scheme;\\n', '        proxy_read_timeout 86400;\\n', '        proxy_send_timeout 86400;\\n', '        proxy_buffering off;\\n', '    }\\n', '\\n']
    lines[api_idx:api_idx] = ws_block
    print("已添加 WebSocket location")
    with open(config_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)
    print("配置已更新")
else:
    print("WebSocket location 已存在")
'''
        success, output = run_command(
            f'ssh {server} "python3 << \'PYEOF\'{python_script}PYEOF"',
            "添加 WebSocket 配置"
        )
    else:
        print("[OK] WebSocket location 配置已存在")
        # 检查配置是否正确
        if 'Upgrade' in output and 'upgrade' in output:
            print("[OK] WebSocket 配置正确")
        else:
            print("[警告] WebSocket 配置不完整")
    
    # 步骤 4: 测试 Nginx 配置
    print("\n[步骤 4] 测试 Nginx 配置...")
    success, output = run_command(
        f'ssh {server} "sudo nginx -t"',
        "Nginx 配置测试"
    )
    
    if success and 'syntax is ok' in output:
        print("[OK] Nginx 配置语法正确")
        # 重新加载
        print("\n[步骤 4.1] 重新加载 Nginx...")
        success, output = run_command(
            f'ssh {server} "sudo systemctl reload nginx"',
            "重新加载 Nginx"
        )
    else:
        print("[错误] Nginx 配置语法错误")
        return 1
    
    # 步骤 5: 检查服务状态
    print("\n[步骤 5] 检查服务状态...")
    run_command(
        f'ssh {server} "sudo systemctl status nginx --no-pager | head -5"',
        "Nginx 服务状态"
    )
    run_command(
        f'ssh {server} "sudo systemctl status liaotian-backend --no-pager | head -5"',
        "后端服务状态"
    )
    
    # 步骤 6: 最终验证
    print("\n[步骤 6] 最终验证 WebSocket 配置...")
    success, output = run_command(
        f'ssh {server} "sudo grep -A 15 \'location /api/v1/notifications/ws\' /etc/nginx/sites-available/aikz.usdt2026.cc"',
        "最终 WebSocket 配置"
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

