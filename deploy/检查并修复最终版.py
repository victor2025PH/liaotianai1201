# -*- coding: utf-8 -*-
"""
检查并修复最终版
"""

import paramiko
import os
import sys
import time

SERVER = "165.154.233.55"
USERNAME = "ubuntu"

def run_ssh(ssh, cmd):
    """执行SSH命令"""
    print(f"\n执行: {cmd}")
    print("-" * 60)
    stdin, stdout, stderr = ssh.exec_command(cmd)
    exit_status = stdout.channel.recv_exit_status()
    output = stdout.read().decode('utf-8', errors='ignore')
    error = stderr.read().decode('utf-8', errors='ignore')
    if output:
        print(output)
    if error:
        print(f"错误: {error}")
    print(f"退出码: {exit_status}")
    return exit_status == 0, output, error

try:
    print("=" * 60)
    print("检查并修复最终版")
    print("=" * 60)
    
    # 连接
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy)
    ssh_key = os.path.expanduser("~/.ssh/id_rsa")
    ssh.connect(SERVER, username=USERNAME, key_filename=ssh_key, timeout=30)
    print("[OK] 已连接\n")
    
    # 1. 上传文件
    print("[1] 上传文件...")
    local = "saas-demo/src/app/group-ai/accounts/page.tsx"
    remote = "/home/ubuntu/liaotian/saas-demo/src/app/group-ai/accounts/page.tsx"
    
    if os.path.exists(local):
        sftp = ssh.open_sftp()
        sftp.put(local, remote)
        sftp.close()
        print("[OK] 文件已上传\n")
    else:
        print(f"[错误] 文件不存在: {local}\n")
        sys.exit(1)
    
    # 2. 检查文件
    print("[2] 检查文件...")
    success, output, _ = run_ssh(ssh, f"wc -l {remote}")
    success, output, _ = run_ssh(ssh, f"sed -n '2023p' {remote}")
    print(f"第2023行: {output.strip()}")
    
    success, output, _ = run_ssh(ssh, f"grep -c 'workerAccounts.map' {remote}")
    print(f"workerAccounts.map出现次数: {output.strip()}\n")
    
    # 3. 停止服务
    print("[3] 停止服务...")
    run_ssh(ssh, "sudo systemctl stop liaotian-frontend", False)
    time.sleep(2)
    print("[OK] 服务已停止\n")
    
    # 4. 清理
    print("[4] 清理...")
    run_ssh(ssh, "cd /home/ubuntu/liaotian/saas-demo && rm -rf .next node_modules/.cache", False)
    print("[OK] 已清理\n")
    
    # 5. 构建
    print("[5] 构建（这可能需要几分钟）...")
    build_cmd = """cd /home/ubuntu/liaotian/saas-demo && \
source $HOME/.nvm/nvm.sh && \
nvm use 20 && \
npm run build 2>&1"""
    
    # 使用交互式shell
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
    full_output = ''.join(output_lines)
    
    print(f"\n退出码: {exit_status}\n")
    
    # 6. 检查构建结果
    if exit_status == 0 and "error" not in full_output.lower():
        print("[OK] 构建成功\n")
        
        # 验证
        success, output, _ = run_ssh(ssh, "test -f /home/ubuntu/liaotian/saas-demo/.next/BUILD_ID && echo 'OK' || echo 'FAIL'", False)
        if "OK" in output:
            print("[OK] BUILD_ID存在\n")
            
            # 7. 重启服务
            print("[6] 重启服务...")
            run_ssh(ssh, "sudo systemctl restart liaotian-frontend", False)
            time.sleep(5)
            print("[OK] 服务已重启\n")
            
            # 8. 检查状态
            print("[7] 检查服务状态...")
            success, output, _ = run_ssh(ssh, "sudo systemctl status liaotian-frontend --no-pager | head -25")
            
            if "active (running)" in output:
                print("\n[成功] 服务正常运行！")
                
                # 检查端口
                print("\n[8] 检查端口...")
                success, output, _ = run_ssh(ssh, "sudo netstat -tlnp 2>/dev/null | grep ':3000' || sudo ss -tlnp 2>/dev/null | grep ':3000' || echo '未监听'")
            else:
                print("\n[警告] 服务可能未正常运行")
                run_ssh(ssh, "sudo journalctl -u liaotian-frontend -n 30 --no-pager")
        else:
            print("[错误] BUILD_ID不存在\n")
    else:
        print("[错误] 构建失败\n")
        print("错误信息（最后50行）：")
        error_lines = [line for line in full_output.split('\n') if 'error' in line.lower() or 'failed' in line.lower() or '2023' in line]
        for line in error_lines[-50:]:
            print(line)
    
    ssh.close()
    print("\n" + "=" * 60)
    print("完成")
    print("=" * 60)
    
except Exception as e:
    print(f"\n[错误] {e}")
    import traceback
    traceback.print_exc()

