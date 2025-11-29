# -*- coding: utf-8 -*-
"""
诊断并修复 502 Bad Gateway 错误
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
    print("诊断并修复 502 Bad Gateway 错误")
    print("=" * 60)
    
    # SSH 连接
    print("\n>>> 连接服务器...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    ssh_key_path = os.path.expanduser("~/.ssh/id_rsa")
    if os.path.exists(ssh_key_path):
        ssh.connect(SERVER, username=USERNAME, key_filename=ssh_key_path, timeout=30)
        print("[OK] SSH 连接成功")
    else:
        print("[错误] 未找到 SSH 密钥")
        sys.exit(1)
    
    # 1. 检查后端服务状态
    success, output, error = run_ssh_command(
        ssh, 
        "sudo systemctl status liaotian-backend --no-pager | head -20",
        "1. 检查后端服务状态"
    )
    
    # 2. 检查后端是否在运行
    success, output, error = run_ssh_command(
        ssh,
        "sudo systemctl is-active liaotian-backend",
        "2. 检查后端服务是否活跃"
    )
    
    if "active" not in output:
        print("\n[警告] 后端服务未运行，尝试启动...")
        run_ssh_command(ssh, "sudo systemctl start liaotian-backend", "启动后端服务")
        import time
        time.sleep(3)
    
    # 3. 检查后端端口监听
    success, output, error = run_ssh_command(
        ssh,
        "sudo ss -tlnp | grep :8000",
        "3. 检查后端端口 8000 是否监听"
    )
    
    # 4. 检查后端日志（最近错误）
    success, output, error = run_ssh_command(
        ssh,
        "sudo journalctl -u liaotian-backend -n 50 --no-pager | grep -i 'error\|exception\|traceback\|failed' | tail -20",
        "4. 检查后端错误日志"
    )
    
    # 5. 检查 workers.py 文件是否存在
    success, output, error = run_ssh_command(
        ssh,
        "test -f /home/ubuntu/liaotian/admin-backend/app/api/workers.py && echo '文件存在' || echo '文件不存在'",
        "5. 检查 workers.py 文件"
    )
    
    # 6. 测试后端 API
    success, output, error = run_ssh_command(
        ssh,
        "curl -s http://127.0.0.1:8000/api/v1/workers/ 2>&1 | head -20",
        "6. 测试 Workers API 端点"
    )
    
    # 7. 检查 Nginx 错误日志
    success, output, error = run_ssh_command(
        ssh,
        "sudo tail -20 /var/log/nginx/error.log | grep -i '502\|upstream'",
        "7. 检查 Nginx 502 错误日志"
    )
    
    # 8. 检查是否需要安装 websockets
    success, output, error = run_ssh_command(
        ssh,
        "cd /home/ubuntu/liaotian/admin-backend && source .venv/bin/activate && pip list | grep -i websocket",
        "8. 检查 websockets 库"
    )
    
    if "websockets" not in output.lower() and "wsproto" not in output.lower():
        print("\n[警告] 未找到 websockets 库，需要安装...")
        success, output, error = run_ssh_command(
            ssh,
            "cd /home/ubuntu/liaotian/admin-backend && source .venv/bin/activate && pip install 'uvicorn[standard]'",
            "安装 websockets 支持"
        )
        if success:
            print("[OK] websockets 库安装成功，重启服务...")
            run_ssh_command(ssh, "sudo systemctl restart liaotian-backend", "重启后端服务")
            import time
            time.sleep(5)
    
    # 9. 最终检查
    print("\n" + "=" * 60)
    print("最终检查")
    print("=" * 60)
    
    success, output, error = run_ssh_command(
        ssh,
        "sudo systemctl status liaotian-backend --no-pager | head -10",
        "9. 最终服务状态"
    )
    
    success, output, error = run_ssh_command(
        ssh,
        "curl -s http://127.0.0.1:8000/api/v1/workers/ 2>&1 | python3 -m json.tool 2>&1 | head -20",
        "10. 最终 API 测试"
    )
    
    print("\n" + "=" * 60)
    print("诊断完成")
    print("=" * 60)
    
    ssh.close()
    
except Exception as e:
    print(f"\n[错误] 诊断失败: {e}")
    import traceback
    print(traceback.format_exc())
    sys.exit(1)

