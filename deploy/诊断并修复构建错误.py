# -*- coding: utf-8 -*-
"""
诊断并修复构建错误
"""

import paramiko
import os
import sys

SERVER = "165.154.233.55"
USERNAME = "ubuntu"

def run_ssh(ssh, cmd):
    """执行SSH命令并返回输出"""
    stdin, stdout, stderr = ssh.exec_command(cmd)
    exit_status = stdout.channel.recv_exit_status()
    output = stdout.read().decode('utf-8', errors='ignore')
    error = stderr.read().decode('utf-8', errors='ignore')
    return exit_status == 0, output, error, exit_status

try:
    print("=" * 60)
    print("诊断并修复构建错误")
    print("=" * 60)
    
    # 连接
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy)
    ssh_key = os.path.expanduser("~/.ssh/id_rsa")
    ssh.connect(SERVER, username=USERNAME, key_filename=ssh_key, timeout=30)
    print("[OK] SSH连接成功\n")
    
    # 1. 上传文件
    print("[1/6] 上传修复后的文件...")
    local_file = "saas-demo/src/app/group-ai/accounts/page.tsx"
    remote_file = "/home/ubuntu/liaotian/saas-demo/src/app/group-ai/accounts/page.tsx"
    
    if os.path.exists(local_file):
        sftp = ssh.open_sftp()
        sftp.put(local_file, remote_file)
        sftp.close()
        print(f"[OK] 文件已上传\n")
    else:
        print(f"[错误] 本地文件不存在\n")
        sys.exit(1)
    
    # 2. 检查文件
    print("[2/6] 检查文件...")
    success, output, error, code = run_ssh(ssh, f"wc -l {remote_file}")
    print(f"文件行数: {output.strip()}")
    
    success, output, error, code = run_ssh(ssh, f"grep -c 'workerAccounts.map' {remote_file}")
    count = output.strip()
    print(f"workerAccounts.map出现次数: {count}")
    if count != "1":
        print(f"[警告] 应该只出现1次\n")
    else:
        print("[OK] 无重复代码\n")
    
    # 3. 查看第2023行附近
    print("[3/6] 查看第2023行附近的内容...")
    success, output, error, code = run_ssh(ssh, f"sed -n '2018,2028p' {remote_file}")
    print(output)
    print()
    
    # 4. 停止服务
    print("[4/6] 停止服务...")
    run_ssh(ssh, "sudo systemctl stop liaotian-frontend")
    print("[OK] 服务已停止\n")
    
    # 5. 清理并构建
    print("[5/6] 清理并重新构建...")
    print("这可能需要几分钟，请耐心等待...\n")
    
    build_cmd = """cd /home/ubuntu/liaotian/saas-demo && \
source $HOME/.nvm/nvm.sh && \
nvm use 20 && \
rm -rf .next node_modules/.cache && \
npm run build 2>&1"""
    
    success, output, error, code = run_ssh(ssh, build_cmd)
    
    # 显示构建输出
    if "error" in output.lower() or "failed" in output.lower() or not success:
        print("[错误] 构建失败\n")
        print("构建输出（最后100行）：")
        print("\n".join(output.split("\n")[-100:]))
        print()
        
        # 提取错误信息
        if "2023" in output:
            print("[发现] 第2023行有错误")
            print("查看第2023行附近的内容：")
            success, context, _, _ = run_ssh(ssh, f"sed -n '2015,2035p' {remote_file}")
            print(context)
            print()
    else:
        print("[OK] 构建成功\n")
        print("构建输出（最后30行）：")
        print("\n".join(output.split("\n")[-30:]))
        print()
    
    # 6. 验证构建并重启服务
    print("[6/6] 验证构建并重启服务...")
    success, output, error, code = run_ssh(ssh, "test -f /home/ubuntu/liaotian/saas-demo/.next/BUILD_ID && echo '构建成功' || echo '构建失败'")
    print(output.strip())
    
    if "构建成功" in output:
        print("\n重启服务...")
        run_ssh(ssh, "sudo systemctl restart liaotian-frontend")
        import time
        time.sleep(5)
        
        print("\n检查服务状态...")
        success, output, error, code = run_ssh(ssh, "sudo systemctl status liaotian-frontend --no-pager | head -20")
        print(output)
        
        if "active (running)" in output:
            print("\n[成功] 服务已正常运行！")
        else:
            print("\n[警告] 服务可能未正常运行")
            success, logs, _, _ = run_ssh(ssh, "sudo journalctl -u liaotian-frontend -n 20 --no-pager")
            print("服务日志：")
            print(logs)
    else:
        print("\n[错误] 构建失败，无法启动服务")
    
    ssh.close()
    
    print("\n" + "=" * 60)
    print("完成！")
    print("=" * 60)
    
except Exception as e:
    print(f"\n[错误] 执行失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

