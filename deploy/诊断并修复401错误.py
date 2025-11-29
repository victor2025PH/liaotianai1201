# -*- coding: utf-8 -*-
"""
诊断并修复 401 错误
"""

import paramiko
import sys
import os

# 设置输出编码
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

SERVER = "165.154.233.55"
USERNAME = "ubuntu"

def run_ssh_command(ssh, command, description):
    """执行 SSH 命令并返回输出"""
    print(f"\n{'='*60}")
    print(f"{description}")
    print(f"{'='*60}")
    print(f"命令: {command}")
    print("-" * 60)
    
    stdin, stdout, stderr = ssh.exec_command(command)
    exit_status = stdout.channel.recv_exit_status()
    
    output = stdout.read().decode('utf-8', errors='ignore')
    error = stderr.read().decode('utf-8', errors='ignore')
    
    print(output)
    if error:
        print(f"错误: {error}")
    print(f"退出码: {exit_status}")
    
    return exit_status == 0, output, error

try:
    print("=" * 60)
    print("诊断并修复 401 错误")
    print("=" * 60)
    
    # SSH 连接
    print("\n>>> 连接服务器...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy)
    
    ssh_key_path = os.path.expanduser("~/.ssh/id_rsa")
    if os.path.exists(ssh_key_path):
        ssh.connect(SERVER, username=USERNAME, key_filename=ssh_key_path, timeout=30)
        print("[OK] SSH 连接成功")
    else:
        print("[错误] 未找到 SSH 密钥")
        sys.exit(1)
    
    # 1. 检查 deps.py 是否已部署
    success, output, error = run_ssh_command(
        ssh,
        "grep -n 'auto_error' /home/ubuntu/liaotian/admin-backend/app/api/deps.py | head -3",
        "1. 检查 deps.py 中的 auto_error 配置"
    )
    
    if "auto_error=False" not in output:
        print("\n[警告] deps.py 可能未正确部署，需要上传修复后的文件")
    
    # 2. 检查 DISABLE_AUTH 配置
    success, output, error = run_ssh_command(
        ssh,
        "cd /home/ubuntu/liaotian/admin-backend && python3 -c \"from app.core.config import get_settings; s = get_settings(); print(f'DISABLE_AUTH: {s.disable_auth}')\" 2>&1",
        "2. 检查 DISABLE_AUTH 配置"
    )
    
    # 3. 测试 Workers API（无 token）
    success, output, error = run_ssh_command(
        ssh,
        "curl -s http://127.0.0.1:8000/api/v1/workers/ 2>&1",
        "3. 测试 Workers API（无 token）"
    )
    
    # 4. 检查后端日志
    success, output, error = run_ssh_command(
        ssh,
        "sudo journalctl -u liaotian-backend -n 30 --no-pager | grep -i 'worker\|401\|auth' | tail -10",
        "4. 检查后端日志中的认证相关错误"
    )
    
    # 5. 检查后端服务状态
    success, output, error = run_ssh_command(
        ssh,
        "sudo systemctl status liaotian-backend --no-pager | head -10",
        "5. 检查后端服务状态"
    )
    
    # 6. 如果 deps.py 未正确部署，上传修复后的文件
    if "auto_error=False" not in output:
        print("\n" + "=" * 60)
        print("需要上传修复后的 deps.py")
        print("=" * 60)
        print("请运行: scp admin-backend/app/api/deps.py ubuntu@165.154.233.55:/home/ubuntu/liaotian/admin-backend/app/api/deps.py")
        print("然后重启后端: ssh ubuntu@165.154.233.55 'sudo systemctl restart liaotian-backend'")
    
    # 7. 建议：如果认证是启用的，确保前端正确发送 token
    if "DISABLE_AUTH: False" in output or "DISABLE_AUTH: true" not in output.lower():
        print("\n" + "=" * 60)
        print("建议")
        print("=" * 60)
        print("1. 认证是启用的，前端必须正确发送 token")
        print("2. 确保用户已登录，token 已存储在 localStorage")
        print("3. 检查浏览器控制台，确认 Authorization header 已发送")
        print("4. 如果仍然失败，可能需要重新登录获取新的 token")
    
    ssh.close()
    
except Exception as e:
    print(f"\n[错误] 诊断失败: {e}")
    import traceback
    print(traceback.format_exc())
    sys.exit(1)

