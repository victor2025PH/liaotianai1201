# -*- coding: utf-8 -*-
"""
部署 Workers API 到服务器
"""

import paramiko
import sys
import os
from pathlib import Path

# 设置输出编码
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

SERVER = "165.154.233.55"
USERNAME = "ubuntu"
# 使用 SSH 密钥认证，不需要密码

log_messages = []

def log(msg):
    print(msg)
    log_messages.append(msg)
    sys.stdout.flush()

log("=" * 60)
log("部署 Workers API 到服务器")
log("=" * 60)
log("")

try:
    # SSH 连接（使用密钥认证）
    log(">>> 1. 连接服务器...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    # 使用 SSH 密钥
    ssh_key_path = os.path.expanduser("~/.ssh/id_rsa")
    if os.path.exists(ssh_key_path):
        ssh.connect(SERVER, username=USERNAME, key_filename=ssh_key_path, timeout=30)
        log("[OK] SSH 连接成功（使用密钥认证）\n")
    else:
        log("[错误] 未找到 SSH 密钥，请先配置 SSH 密钥认证")
        sys.exit(1)
    
    # SFTP 连接
    log(">>> 2. 建立 SFTP 连接...")
    sftp = ssh.open_sftp()
    log("[OK] SFTP 连接成功\n")
    
    # 获取项目根目录
    project_root = Path(__file__).parent.parent
    workers_file = project_root / "admin-backend" / "app" / "api" / "workers.py"
    api_init_file = project_root / "admin-backend" / "app" / "api" / "__init__.py"
    
    if not workers_file.exists():
        log(f"[错误] 文件不存在: {workers_file}")
        sys.exit(1)
    
    # 上传 workers.py
    log(">>> 3. 上传 workers.py...")
    remote_path = "/home/ubuntu/liaotian/admin-backend/app/api/workers.py"
    
    try:
        sftp.put(str(workers_file), remote_path)
        log(f"[OK] 已上传: {remote_path}\n")
    except Exception as e:
        log(f"[错误] 上传失败: {e}")
        sys.exit(1)
    
    # 上传 __init__.py（如果已修改）
    if api_init_file.exists():
        log(">>> 4. 上传 __init__.py...")
        remote_init_path = "/home/ubuntu/liaotian/admin-backend/app/api/__init__.py"
        try:
            sftp.put(str(api_init_file), remote_init_path)
            log(f"[OK] 已上传: {remote_init_path}\n")
        except Exception as e:
            log(f"[警告] 上传 __init__.py 失败: {e}")
    
    # 关闭 SFTP
    sftp.close()
    
    # 检查后端服务状态
    log(">>> 5. 检查后端服务状态...")
    stdin, stdout, stderr = ssh.exec_command("sudo systemctl status liaotian-backend --no-pager | head -5")
    status_output = stdout.read().decode('utf-8', errors='ignore')
    log(status_output)
    
    # 重启后端服务
    log("\n>>> 6. 重启后端服务...")
    stdin, stdout, stderr = ssh.exec_command("sudo systemctl restart liaotian-backend")
    exit_status = stdout.channel.recv_exit_status()
    
    if exit_status == 0:
        log("[OK] 后端服务重启成功\n")
    else:
        error_output = stderr.read().decode('utf-8', errors='ignore')
        log(f"[错误] 重启失败: {error_output}")
        sys.exit(1)
    
    # 等待服务启动
    log(">>> 7. 等待服务启动（5秒）...")
    import time
    time.sleep(5)
    
    # 检查服务状态
    log("\n>>> 8. 检查服务状态...")
    stdin, stdout, stderr = ssh.exec_command("sudo systemctl status liaotian-backend --no-pager | head -10")
    status_output = stdout.read().decode('utf-8', errors='ignore')
    log(status_output)
    
    # 检查 Workers API 端点
    log("\n>>> 9. 测试 Workers API 端点...")
    stdin, stdout, stderr = ssh.exec_command("curl -s http://127.0.0.1:8000/api/v1/workers/ | head -20")
    api_output = stdout.read().decode('utf-8', errors='ignore')
    if api_output:
        log(api_output)
    else:
        log("[警告] API 端点无响应，可能需要等待服务完全启动")
    
    # 检查后端日志
    log("\n>>> 10. 检查后端启动日志...")
    stdin, stdout, stderr = ssh.exec_command("sudo journalctl -u liaotian-backend -n 20 --no-pager | grep -i 'worker\|error\|started'")
    log_output = stdout.read().decode('utf-8', errors='ignore')
    if log_output:
        log(log_output)
    else:
        log("（无相关日志）")
    
    log("\n" + "=" * 60)
    log("部署完成！")
    log("=" * 60)
    log("\n下一步：")
    log("1. 在 computer_001 和 computer_002 上运行 worker_client_example.py")
    log("2. 在前端页面查看节点管理，应该能看到节点状态")
    log("3. 测试发送命令和广播命令功能")
    
    ssh.close()
    
except paramiko.AuthenticationException:
    log("[错误] SSH 认证失败，请检查 SSH 密钥配置")
    sys.exit(1)
except Exception as e:
    log(f"[错误] 部署失败: {e}")
    import traceback
    log(traceback.format_exc())
    sys.exit(1)

