# -*- coding: utf-8 -*-
"""
完整修复路由 - 确保账号管理页面可以正常访问
"""

import paramiko
import os
import sys
import time

SERVER = "165.154.233.55"
USERNAME = "ubuntu"

def run_ssh(ssh, cmd, show=True):
    stdin, stdout, stderr = ssh.exec_command(cmd)
    exit_status = stdout.channel.recv_exit_status()
    output = stdout.read().decode('utf-8', errors='ignore')
    error = stderr.read().decode('utf-8', errors='ignore')
    if show:
        if output:
            print(output, end='')
        if error:
            print(f"错误: {error}", end='')
    return exit_status == 0, output, error

try:
    print("=" * 60)
    print("完整修复路由")
    print("=" * 60)
    print()
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy)
    ssh_key = os.path.expanduser("~/.ssh/id_rsa")
    ssh.connect(SERVER, username=USERNAME, key_filename=ssh_key, timeout=30)
    print("[OK] 已连接\n")
    
    # 1. 检查文件
    print("[1] 检查文件...")
    file_path = "/home/ubuntu/liaotian/saas-demo/src/app/group-ai/accounts/page.tsx"
    success, output, _ = run_ssh(ssh, f"test -f {file_path} && echo '存在' || echo '不存在'")
    print(f"文件状态: {output.strip()}")
    
    if "不存在" in output:
        print("\n[错误] 文件不存在！")
        print("上传文件...")
        local = "saas-demo/src/app/group-ai/accounts/page.tsx"
        if os.path.exists(local):
            sftp = ssh.open_sftp()
            sftp.put(local, file_path)
            sftp.close()
            print("[OK] 文件已上传\n")
        else:
            print(f"[错误] 本地文件不存在: {local}\n")
            sys.exit(1)
    else:
        # 检查文件行数
        success, output, _ = run_ssh(ssh, f"wc -l {file_path}")
        print(f"文件行数: {output.strip()}")
    
    # 2. 停止服务
    print("\n[2] 停止服务...")
    run_ssh(ssh, "sudo systemctl stop liaotian-frontend", False)
    time.sleep(2)
    print("[OK] 服务已停止\n")
    
    # 3. 清理
    print("[3] 清理构建缓存...")
    run_ssh(ssh, "cd /home/ubuntu/liaotian/saas-demo && rm -rf .next node_modules/.cache", False)
    print("[OK] 已清理\n")
    
    # 4. 构建
    print("[4] 构建（这可能需要几分钟）...")
    print("正在构建，请稍候...\n")
    
    build_cmd = """cd /home/ubuntu/liaotian/saas-demo && \
export NVM_DIR="$HOME/.nvm" && \
[ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh" && \
nvm use 20 && \
npm run build 2>&1 | tee /tmp/build.log"""
    
    stdin, stdout, stderr = ssh.exec_command(build_cmd)
    
    # 等待构建完成
    output_lines = []
    route_found = False
    error_found = False
    
    while True:
        if stdout.channel.recv_ready():
            data = stdout.channel.recv(4096).decode('utf-8', errors='ignore')
            if data:
                output_lines.append(data)
                if 'group-ai/accounts' in data.lower():
                    route_found = True
                if 'error' in data.lower() or 'failed' in data.lower():
                    error_found = True
                # 只显示关键信息
                if any(keyword in data.lower() for keyword in ['route', 'compiled', 'error', 'failed', 'group-ai']):
                    print(data, end='')
        if stdout.channel.exit_status_ready():
            break
        time.sleep(0.1)
    
    exit_status = stdout.channel.recv_exit_status()
    full_output = ''.join(output_lines)
    
    print(f"\n退出码: {exit_status}\n")
    
    # 5. 检查构建结果
    if exit_status == 0:
        print("[OK] 构建成功\n")
        
        # 检查路由文件
        print("[5] 检查路由文件...")
        success, output, _ = run_ssh(ssh, "find /home/ubuntu/liaotian/saas-demo/.next -path '*group-ai/accounts*' -type f 2>/dev/null | head -5")
        if output.strip():
            print("找到的路由文件:")
            print(output)
        else:
            print("[警告] 未找到路由文件\n")
        
        # 验证构建
        success, output, _ = run_ssh(ssh, "test -f /home/ubuntu/liaotian/saas-demo/.next/BUILD_ID && echo 'OK' || echo 'FAIL'", False)
        if "OK" in output:
            print("[OK] BUILD_ID存在\n")
            
            # 6. 重启服务
            print("[6] 重启服务...")
            run_ssh(ssh, "sudo systemctl restart liaotian-frontend", False)
            time.sleep(5)
            print("[OK] 服务已重启\n")
            
            # 7. 检查状态
            print("[7] 检查服务状态...")
            success, output, _ = run_ssh(ssh, "sudo systemctl status liaotian-frontend --no-pager | head -20")
            print(output)
            
            if "active (running)" in output:
                print("\n[成功] 服务正常运行！")
                print("\n请访问: http://aikz.usdt2026.cc/group-ai/accounts")
            else:
                print("\n[警告] 服务可能未正常运行")
        else:
            print("[错误] BUILD_ID不存在\n")
    else:
        print("[错误] 构建失败\n")
        # 显示错误信息
        error_lines = [line for line in full_output.split('\n') if 'error' in line.lower() or 'failed' in line.lower()]
        print("错误信息:")
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

