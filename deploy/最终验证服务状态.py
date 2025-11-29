# -*- coding: utf-8 -*-
"""
最终验证服务状态
"""

import paramiko
import os

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
    print("最终验证服务状态")
    print("=" * 60)
    print()
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy)
    ssh_key = os.path.expanduser("~/.ssh/id_rsa")
    ssh.connect(SERVER, username=USERNAME, key_filename=ssh_key, timeout=30)
    print("[OK] 已连接\n")
    
    # 1. 检查服务状态
    print("[1] 检查服务状态...")
    success, output, _ = run_ssh(ssh, "sudo systemctl status liaotian-frontend --no-pager | head -25")
    print(output)
    print()
    
    # 2. 检查端口
    print("[2] 检查端口3000...")
    success, output, _ = run_ssh(ssh, "ss -tlnp | grep ':3000' || echo '端口未监听'")
    print(output)
    print()
    
    # 3. 检查最新日志
    print("[3] 检查最新日志...")
    success, output, _ = run_ssh(ssh, "sudo journalctl -u liaotian-frontend -n 20 --no-pager | tail -20")
    print(output)
    print()
    
    # 4. 检查服务配置
    print("[4] 检查服务配置...")
    success, output, _ = run_ssh(ssh, "cat /etc/systemd/system/liaotian-frontend.service | grep -E 'ExecStart|WorkingDirectory'")
    print(output)
    print()
    
    # 5. 如果服务未运行，尝试启动
    print("[5] 检查服务是否激活...")
    success, output, _ = run_ssh(ssh, "sudo systemctl is-active liaotian-frontend")
    is_active = "active" in output.lower()
    print(f"服务状态: {output.strip()}\n")
    
    if not is_active:
        print("服务未运行，尝试启动...")
        run_ssh(ssh, "sudo systemctl start liaotian-frontend")
        import time
        time.sleep(5)
        success, output, _ = run_ssh(ssh, "sudo systemctl status liaotian-frontend --no-pager | head -15")
        print(output)
        print()
    
    # 6. 再次检查端口
    print("[6] 再次检查端口...")
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

