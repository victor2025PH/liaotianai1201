# -*- coding: utf-8 -*-
"""
检查服务并修复
"""

import paramiko
import os
import sys
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
    print("检查服务并修复")
    print("=" * 60)
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy)
    ssh_key = os.path.expanduser("~/.ssh/id_rsa")
    ssh.connect(SERVER, username=USERNAME, key_filename=ssh_key, timeout=30)
    print("[OK] 已连接\n")
    
    # 1. 检查文件是否存在
    print("[1] 检查文件...")
    file_path = "/home/ubuntu/liaotian/saas-demo/src/app/group-ai/accounts/page.tsx"
    success, output, _ = run_ssh(ssh, f"test -f {file_path} && echo '存在' || echo '不存在'")
    print(f"文件状态: {output.strip()}")
    
    if "不存在" in output:
        print("\n[2] 上传文件...")
        local = "saas-demo/src/app/group-ai/accounts/page.tsx"
        if os.path.exists(local):
            sftp = ssh.open_sftp()
            sftp.put(local, file_path)
            sftp.close()
            print("[OK] 文件已上传\n")
        else:
            print(f"[错误] 本地文件不存在\n")
            sys.exit(1)
    
    # 2. 验证文件
    success, output, _ = run_ssh(ssh, f"wc -l {file_path}")
    print(f"文件行数: {output.strip()}")
    
    success, output, _ = run_ssh(ssh, f"sed -n '2023p' {file_path}")
    print(f"第2023行: {output.strip()}\n")
    
    # 3. 检查构建
    print("[3] 检查构建...")
    success, output, _ = run_ssh(ssh, "test -f /home/ubuntu/liaotian/saas-demo/.next/BUILD_ID && echo '构建成功' || echo '构建失败'")
    print(f"构建状态: {output.strip()}\n")
    
    # 4. 如果构建失败或文件已更新，重新构建
    if "构建失败" in output or "不存在" in output:
        print("[4] 重新构建...")
        run_ssh(ssh, "cd /home/ubuntu/liaotian/saas-demo && rm -rf .next node_modules/.cache", False)
        
        build_cmd = """cd /home/ubuntu/liaotian/saas-demo && \
source $HOME/.nvm/nvm.sh && \
nvm use 20 && \
npm run build 2>&1"""
        
        chan = ssh.get_transport().open_session()
        chan.exec_command(build_cmd)
        
        output_lines = []
        while True:
            if chan.recv_ready():
                data = chan.recv(4096).decode('utf-8', errors='ignore')
                if data:
                    print(data, end='')
                    output_lines.append(data)
            if chan.exit_status_ready():
                break
            time.sleep(0.1)
        
        exit_status = chan.recv_exit_status()
        print(f"\n退出码: {exit_status}\n")
        
        if exit_status == 0:
            print("[OK] 构建成功\n")
        else:
            print("[错误] 构建失败\n")
            sys.exit(1)
    
    # 5. 检查服务状态
    print("[5] 检查服务状态...")
    success, output, _ = run_ssh(ssh, "sudo systemctl is-active liaotian-frontend")
    print(f"服务状态: {output.strip()}\n")
    
    # 6. 重启服务
    print("[6] 重启服务...")
    run_ssh(ssh, "sudo systemctl restart liaotian-frontend", False)
    time.sleep(5)
    print("[OK] 服务已重启\n")
    
    # 7. 检查服务状态
    print("[7] 检查服务状态...")
    success, output, _ = run_ssh(ssh, "sudo systemctl status liaotian-frontend --no-pager | head -25")
    print(output)
    
    if "active (running)" in output:
        print("\n[成功] 服务正常运行！")
    else:
        print("\n[警告] 服务可能未正常运行")
        success, logs, _ = run_ssh(ssh, "sudo journalctl -u liaotian-frontend -n 30 --no-pager")
        print("服务日志:")
        print(logs)
    
    # 8. 检查端口
    print("\n[8] 检查端口...")
    success, output, _ = run_ssh(ssh, "sudo netstat -tlnp 2>/dev/null | grep ':3000' || sudo ss -tlnp 2>/dev/null | grep ':3000' || echo '未监听'")
    print(f"端口3000: {output.strip()}")
    
    ssh.close()
    print("\n" + "=" * 60)
    print("完成")
    print("=" * 60)
    
except Exception as e:
    print(f"\n[错误] {e}")
    import traceback
    traceback.print_exc()

