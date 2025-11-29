# -*- coding: utf-8 -*-
"""
读取并修复服务器文件
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
    print("读取并修复服务器文件")
    print("=" * 60)
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy)
    ssh_key = os.path.expanduser("~/.ssh/id_rsa")
    ssh.connect(SERVER, username=USERNAME, key_filename=ssh_key, timeout=30)
    print("[OK] 已连接\n")
    
    file_path = "/home/ubuntu/liaotian/saas-demo/src/app/group-ai/accounts/page.tsx"
    
    # 1. 读取文件内容（第1770-2030行）
    print("[1] 读取文件内容（第1770-2030行）...")
    success, output, _ = run_ssh(ssh, f"sed -n '1770,2030p' {file_path}")
    print("内容:")
    print(output)
    print()
    
    # 2. 检查文件行数
    print("[2] 检查文件行数...")
    success, output, _ = run_ssh(ssh, f"wc -l {file_path}")
    print(f"总行数: {output.strip()}")
    
    # 3. 检查所有TableBody位置
    print("\n[3] 检查所有TableBody位置...")
    success, output, _ = run_ssh(ssh, f"grep -n 'TableBody' {file_path}")
    print(output)
    
    # 4. 检查所有))}位置
    print("\n[4] 检查所有))}位置...")
    success, output, _ = run_ssh(ssh, f"grep -n '))}' {file_path} | tail -10")
    print(output)
    
    # 5. 检查workerAccounts.map位置
    print("\n[5] 检查workerAccounts.map位置...")
    success, output, _ = run_ssh(ssh, f"grep -n 'workerAccounts.map' {file_path}")
    print(output)
    
    # 6. 检查accounts.map位置
    print("\n[6] 检查accounts.map位置...")
    success, output, _ = run_ssh(ssh, f"grep -n 'accounts.map' {file_path} | grep -v 'setSelectedAccounts'")
    print(output)
    
    # 7. 上传本地文件
    print("\n[7] 上传本地文件...")
    local = "saas-demo/src/app/group-ai/accounts/page.tsx"
    if os.path.exists(local):
        sftp = ssh.open_sftp()
        sftp.put(local, file_path)
        sftp.close()
        print("[OK] 文件已上传\n")
        
        # 验证上传后的行数
        success, output, _ = run_ssh(ssh, f"wc -l {file_path}")
        print(f"上传后行数: {output.strip()}")
        
        success, output, _ = run_ssh(ssh, f"sed -n '2023p' {file_path}")
        print(f"第2023行: {output.strip()}")
    else:
        print(f"[错误] 本地文件不存在\n")
        sys.exit(1)
    
    # 8. 清理并构建
    print("\n[8] 清理并构建...")
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
        import time
        time.sleep(0.1)
    
    exit_status = chan.recv_exit_status()
    full_output = ''.join(output_lines)
    
    print(f"\n退出码: {exit_status}\n")
    
    if exit_status == 0:
        print("[OK] 构建成功\n")
        
        # 重启服务
        print("[9] 重启服务...")
        run_ssh(ssh, "sudo systemctl restart liaotian-frontend", False)
        import time
        time.sleep(5)
        
        success, output, _ = run_ssh(ssh, "sudo systemctl status liaotian-frontend --no-pager | head -20")
        print(output)
    else:
        print("[错误] 构建失败\n")
        error_lines = [line for line in full_output.split('\n') if 'error' in line.lower() or 'failed' in line.lower() or '2023' in line]
        for line in error_lines[-20:]:
            print(line)
    
    ssh.close()
    print("\n" + "=" * 60)
    print("完成")
    print("=" * 60)
    
except Exception as e:
    print(f"\n[错误] {e}")
    import traceback
    traceback.print_exc()

