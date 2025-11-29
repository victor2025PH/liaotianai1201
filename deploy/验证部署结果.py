# -*- coding: utf-8 -*-
"""
验证账号管理功能增强部署结果
"""

import paramiko
import os
import sys

# 设置输出编码
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

SERVER = "165.154.233.55"
USERNAME = "ubuntu"

def run_ssh_command(ssh, command, description):
    """执行 SSH 命令并返回输出"""
    print(f"\n{description}")
    print("-" * 60)
    
    stdin, stdout, stderr = ssh.exec_command(command)
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
    print("验证部署结果")
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
    
    # 1. 检查文件是否存在
    print("\n>>> 检查上传的文件...")
    files_to_check = [
        "/home/ubuntu/liaotian/saas-demo/src/lib/api/group-ai.ts",
        "/home/ubuntu/liaotian/saas-demo/src/app/group-ai/accounts/page.tsx",
    ]
    
    for file_path in files_to_check:
        success, output, error = run_ssh_command(ssh, f"test -f {file_path} && echo '文件存在' || echo '文件不存在'", f"检查 {file_path}")
        if "文件存在" in output:
            print(f"[OK] {os.path.basename(file_path)} 已上传")
        else:
            print(f"[错误] {os.path.basename(file_path)} 不存在")
    
    # 2. 检查文件内容（验证关键函数）
    print("\n>>> 验证文件内容...")
    success, output, error = run_ssh_command(ssh, "grep -n 'getWorkers' /home/ubuntu/liaotian/saas-demo/src/lib/api/group-ai.ts | head -3", "检查 getWorkers 函数")
    if "getWorkers" in output:
        print("[OK] getWorkers 函数已添加")
    else:
        print("[警告] getWorkers 函数可能未正确添加")
    
    success, output, error = run_ssh_command(ssh, "grep -n 'fetchWorkerAccounts' /home/ubuntu/liaotian/saas-demo/src/app/group-ai/accounts/page.tsx | head -3", "检查 fetchWorkerAccounts 函数")
    if "fetchWorkerAccounts" in output:
        print("[OK] fetchWorkerAccounts 函数已添加")
    else:
        print("[警告] fetchWorkerAccounts 函数可能未正确添加")
    
    # 3. 检查前端构建
    print("\n>>> 检查前端构建...")
    success, output, error = run_ssh_command(ssh, "test -d /home/ubuntu/liaotian/saas-demo/.next && echo '构建目录存在' || echo '构建目录不存在'", "检查构建目录")
    if "构建目录存在" in output:
        print("[OK] 前端已构建")
    else:
        print("[警告] 前端可能未构建，需要重新构建")
    
    # 4. 检查服务状态
    print("\n>>> 检查服务状态...")
    success, output, error = run_ssh_command(ssh, "sudo systemctl is-active liaotian-frontend", "检查前端服务状态")
    if "active" in output:
        print("[OK] 前端服务运行中")
    else:
        print("[错误] 前端服务未运行")
    
    success, output, error = run_ssh_command(ssh, "sudo systemctl is-active liaotian-backend", "检查后端服务状态")
    if "active" in output:
        print("[OK] 后端服务运行中")
    else:
        print("[错误] 后端服务未运行")
    
    # 5. 检查端口监听
    print("\n>>> 检查端口监听...")
    success, output, error = run_ssh_command(ssh, "sudo netstat -tlnp | grep ':3000' || sudo ss -tlnp | grep ':3000'", "检查前端端口 3000")
    if ":3000" in output:
        print("[OK] 前端端口 3000 正在监听")
    else:
        print("[警告] 前端端口 3000 可能未监听")
    
    success, output, error = run_ssh_command(ssh, "sudo netstat -tlnp | grep ':8000' || sudo ss -tlnp | grep ':8000'", "检查后端端口 8000")
    if ":8000" in output:
        print("[OK] 后端端口 8000 正在监听")
    else:
        print("[警告] 后端端口 8000 可能未监听")
    
    ssh.close()
    
    print("\n" + "=" * 60)
    print("验证完成！")
    print("=" * 60)
    print("\n如果所有检查都通过，部署成功！")
    print("请清除浏览器缓存并刷新页面测试新功能。")
    
except Exception as e:
    print(f"\n[错误] 验证失败: {e}")
    import traceback
    print(traceback.format_exc())
    sys.exit(1)

