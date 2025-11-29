# -*- coding: utf-8 -*-
"""
诊断服务器状态
"""

import paramiko
import os
import sys

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
    print("诊断服务器状态")
    print("=" * 60)
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy)
    ssh_key = os.path.expanduser("~/.ssh/id_rsa")
    ssh.connect(SERVER, username=USERNAME, key_filename=ssh_key, timeout=30)
    print("[OK] 已连接\n")
    
    # 1. 检查文件
    print("[1] 检查文件...")
    file_path = "/home/ubuntu/liaotian/saas-demo/src/app/group-ai/accounts/page.tsx"
    success, output, _ = run_ssh(ssh, f"test -f {file_path} && echo '存在' || echo '不存在'")
    print(f"文件: {output.strip()}")
    
    success, output, _ = run_ssh(ssh, f"wc -l {file_path}")
    print(f"行数: {output.strip()}")
    
    success, output, _ = run_ssh(ssh, f"sed -n '2020,2025p' {file_path}")
    print("第2020-2025行:")
    print(output)
    
    # 2. 检查构建
    print("[2] 检查构建...")
    success, output, _ = run_ssh(ssh, "test -f /home/ubuntu/liaotian/saas-demo/.next/BUILD_ID && echo '构建成功' || echo '构建失败'")
    print(f"构建状态: {output.strip()}")
    
    if "构建成功" in output:
        success, output, _ = run_ssh(ssh, "cat /home/ubuntu/liaotian/saas-demo/.next/BUILD_ID")
        print(f"BUILD_ID: {output.strip()}")
    
    # 3. 检查服务
    print("\n[3] 检查服务...")
    success, output, _ = run_ssh(ssh, "sudo systemctl is-active liaotian-frontend")
    print(f"服务状态: {output.strip()}")
    
    success, output, _ = run_ssh(ssh, "sudo systemctl status liaotian-frontend --no-pager | head -20")
    print("服务详情:")
    print(output)
    
    # 4. 检查端口
    print("[4] 检查端口...")
    success, output, _ = run_ssh(ssh, "sudo netstat -tlnp 2>/dev/null | grep ':3000' || sudo ss -tlnp 2>/dev/null | grep ':3000' || echo '未监听'")
    print(f"端口3000: {output.strip()}")
    
    # 5. 查看日志
    print("\n[5] 查看服务日志（最后20行）...")
    success, output, _ = run_ssh(ssh, "sudo journalctl -u liaotian-frontend -n 20 --no-pager")
    print(output)
    
    ssh.close()
    
except Exception as e:
    print(f"\n[错误] {e}")
    import traceback
    traceback.print_exc()

