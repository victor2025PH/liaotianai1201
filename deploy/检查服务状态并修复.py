# -*- coding: utf-8 -*-
"""
检查服务状态并修复
"""

import paramiko
import os
import time

SERVER = "165.154.233.55"
USERNAME = "ubuntu"

def run_ssh(ssh, cmd):
    stdin, stdout, stderr = ssh.exec_command(cmd)
    exit_status = stdout.channel.recv_exit_status()
    output = stdout.read().decode('utf-8', errors='ignore')
    error = stderr.read().decode('utf-8', errors='ignore')
    return exit_status == 0, output, error

try:
    print("=" * 60)
    print("检查服务状态并修复")
    print("=" * 60)
    print()
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy)
    ssh_key = os.path.expanduser("~/.ssh/id_rsa")
    ssh.connect(SERVER, username=USERNAME, key_filename=ssh_key, timeout=30)
    print("[OK] 已连接\n")
    
    # 1. 检查服务配置
    print("[1] 检查服务配置...")
    success, output, _ = run_ssh(ssh, "cat /etc/systemd/system/liaotian-frontend.service")
    print(output)
    print()
    
    # 2. 检查服务状态
    print("[2] 检查服务状态...")
    success, output, _ = run_ssh(ssh, "sudo systemctl status liaotian-frontend --no-pager | head -25")
    print(output)
    print()
    
    # 3. 检查端口
    print("[3] 检查端口3000...")
    success, output, _ = run_ssh(ssh, "ss -tlnp | grep ':3000' || echo '端口未监听'")
    print(output)
    print()
    
    # 4. 检查最新日志
    print("[4] 检查最新日志...")
    success, output, _ = run_ssh(ssh, "sudo journalctl -u liaotian-frontend -n 30 --no-pager | tail -30")
    print(output)
    print()
    
    # 5. 检查server.js是否存在
    print("[5] 检查server.js...")
    success, output, _ = run_ssh(ssh, "ls -la /home/ubuntu/liaotian/saas-demo/.next/standalone/liaotian/saas-demo/server.js 2>&1")
    print(output)
    print()
    
    # 6. 检查Node路径
    print("[6] 检查Node路径...")
    success, output, _ = run_ssh(ssh, """export NVM_DIR="\$HOME/.nvm" && \
[ -s "\$NVM_DIR/nvm.sh" ] && . "\$NVM_DIR/nvm.sh" && \
nvm use 20 && \
which node""")
    print(f"Node路径: {output.strip()}\n")
    
    # 7. 如果服务未运行，尝试手动启动
    print("[7] 检查服务是否运行...")
    success, output, _ = run_ssh(ssh, "sudo systemctl is-active liaotian-frontend")
    if "active" not in output:
        print("服务未运行，尝试启动...\n")
        run_ssh(ssh, "sudo systemctl start liaotian-frontend")
        time.sleep(5)
        success, output, _ = run_ssh(ssh, "sudo systemctl status liaotian-frontend --no-pager | head -20")
        print(output)
        print()
    
    # 8. 再次检查端口
    print("[8] 再次检查端口...")
    success, output, _ = run_ssh(ssh, "ss -tlnp | grep ':3000' || echo '端口仍未监听'")
    print(output)
    print()
    
    ssh.close()
    print("=" * 60)
    print("完成")
    print("=" * 60)
    
except Exception as e:
    print(f"\n[错误] {e}")
    import traceback
    traceback.print_exc()

