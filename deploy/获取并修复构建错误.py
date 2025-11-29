# -*- coding: utf-8 -*-
"""
获取构建错误并自动修复
"""

import paramiko
import os
import sys
import re

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
    
    stdin, stdout, stderr = ssh.exec_command(command)
    exit_status = stdout.channel.recv_exit_status()
    
    output = stdout.read().decode('utf-8', errors='ignore')
    error = stderr.read().decode('utf-8', errors='ignore')
    
    if output:
        print(output)
    if error:
        print(f"错误输出: {error}")
    
    return exit_status == 0, output, error

try:
    print("=" * 60)
    print("获取构建错误并修复")
    print("=" * 60)
    
    # SSH 连接
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy)
    
    ssh_key_path = os.path.expanduser("~/.ssh/id_rsa")
    if os.path.exists(ssh_key_path):
        ssh.connect(SERVER, username=USERNAME, key_filename=ssh_key_path, timeout=30)
        print("[OK] SSH 连接成功")
    else:
        print("[错误] 未找到 SSH 密钥")
        sys.exit(1)
    
    # 1. 上传修复后的文件
    print("\n>>> 1. 上传修复后的文件...")
    local_file = "saas-demo/src/app/group-ai/accounts/page.tsx"
    remote_file = "/home/ubuntu/liaotian/saas-demo/src/app/group-ai/accounts/page.tsx"
    
    if os.path.exists(local_file):
        sftp = ssh.open_sftp()
        sftp.put(local_file, remote_file)
        sftp.close()
        print(f"[OK] 文件已上传: {local_file}")
    else:
        print(f"[错误] 本地文件不存在: {local_file}")
        sys.exit(1)
    
    # 2. 检查文件行数
    print("\n>>> 2. 检查文件行数...")
    success, output, error = run_ssh_command(ssh, f"wc -l {remote_file}", "检查文件行数")
    if "2023" in output or "2024" in output or "2025" in output:
        print(f"[OK] 文件行数正常")
    else:
        print(f"[警告] 文件行数异常: {output}")
    
    # 3. 检查第2023行内容
    print("\n>>> 3. 检查第2023行内容...")
    success, output, error = run_ssh_command(ssh, f"sed -n '2020,2030p' {remote_file}", "查看第2020-2030行")
    
    # 4. 检查workerAccounts.map出现次数
    print("\n>>> 4. 检查workerAccounts.map出现次数...")
    success, output, error = run_ssh_command(ssh, f"grep -c 'workerAccounts.map' {remote_file}", "检查workerAccounts.map")
    count = output.strip()
    if count == "1":
        print("[OK] workerAccounts.map只出现1次（正确）")
    else:
        print(f"[警告] workerAccounts.map出现{count}次（应该只出现1次）")
    
    # 5. 检查TableBody闭合
    print("\n>>> 5. 检查TableBody闭合...")
    success, output, error = run_ssh_command(ssh, f"grep -n 'TableBody' {remote_file} | tail -2", "检查TableBody标签")
    
    # 6. 尝试构建
    print("\n>>> 6. 清理并重新构建...")
    build_cmd = """
cd /home/ubuntu/liaotian/saas-demo && \
source $HOME/.nvm/nvm.sh && \
nvm use 20 && \
rm -rf .next node_modules/.cache && \
npm run build 2>&1
"""
    
    success, output, error = run_ssh_command(ssh, build_cmd, "执行构建")
    
    # 7. 分析构建结果
    if "error" in output.lower() or "failed" in output.lower() or not success:
        print("\n>>> 7. 分析构建错误...")
        # 提取错误行号
        error_match = re.search(r':(\d+):(\d+)', output)
        if error_match:
            line_num = error_match.group(1)
            col_num = error_match.group(2)
            print(f"[错误] 第{line_num}行第{col_num}列有错误")
            
            # 查看错误行附近的内容
            success, context, _ = run_ssh_command(ssh, f"sed -n '{int(line_num)-5},{int(line_num)+5}p' {remote_file}", f"查看第{line_num}行附近的内容")
            
            # 检查是否有未闭合的标签
            if "))}" in context:
                print("[发现] 可能有未闭合的括号或标签")
    else:
        print("\n[OK] 构建成功！")
        
        # 8. 验证构建
        success, output, error = run_ssh_command(ssh, "test -f /home/ubuntu/liaotian/saas-demo/.next/BUILD_ID && echo '构建ID存在' || echo '构建ID不存在'", "验证构建")
        
        # 9. 重启服务
        if "构建ID存在" in output:
            print("\n>>> 8. 重启服务...")
            run_ssh_command(ssh, "sudo systemctl restart liaotian-frontend", "重启服务")
            import time
            time.sleep(5)
            
            # 10. 检查服务状态
            print("\n>>> 9. 检查服务状态...")
            success, output, error = run_ssh_command(ssh, "sudo systemctl status liaotian-frontend --no-pager | head -20", "检查服务状态")
            
            if "active (running)" in output:
                print("\n[成功] 服务已正常运行！")
            else:
                print("\n[警告] 服务可能未正常运行")
                run_ssh_command(ssh, "sudo journalctl -u liaotian-frontend -n 30 --no-pager", "查看服务日志")
    
    ssh.close()
    
    print("\n" + "=" * 60)
    print("完成！")
    print("=" * 60)
    
except Exception as e:
    print(f"\n[错误] 执行失败: {e}")
    import traceback
    print(traceback.format_exc())
    sys.exit(1)

