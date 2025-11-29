# -*- coding: utf-8 -*-
"""
部署账号管理功能增强 - 详细版
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
    print(f"\n{'='*60}")
    print(f"{description}")
    print(f"{'='*60}")
    print(f"命令: {command}")
    print("-" * 60)
    
    stdin, stdout, stderr = ssh.exec_command(command)
    exit_status = stdout.channel.recv_exit_status()
    
    output = stdout.read().decode('utf-8', errors='ignore')
    error = stderr.read().decode('utf-8', errors='ignore')
    
    print(output)
    if error:
        print(f"错误输出: {error}")
    print(f"退出码: {exit_status}")
    
    return exit_status == 0, output, error

def upload_file(ssh, local_path, remote_path, description):
    """上传文件到服务器"""
    print(f"\n{'='*60}")
    print(f"{description}")
    print(f"{'='*60}")
    print(f"本地: {local_path}")
    print(f"远程: {remote_path}")
    print("-" * 60)
    
    if not os.path.exists(local_path):
        print(f"[错误] 本地文件不存在: {local_path}")
        return False
    
    try:
        sftp = ssh.open_sftp()
        sftp.put(local_path, remote_path)
        sftp.close()
        print(f"[OK] 文件上传成功")
        return True
    except Exception as e:
        print(f"[错误] 文件上传失败: {e}")
        return False

try:
    print("=" * 60)
    print("部署账号管理功能增强")
    print("=" * 60)
    
    # SSH 连接
    print("\n>>> 连接服务器...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy)
    
    ssh_key_path = os.path.expanduser("~/.ssh/id_rsa")
    if os.path.exists(ssh_key_path):
        ssh.connect(SERVER, username=USERNAME, key_filename=ssh_key_path, timeout=30)
        print("[OK] SSH 连接成功")
    else:
        print("[错误] 未找到 SSH 密钥")
        sys.exit(1)
    
    # 1. 上传文件
    print("\n>>> 步骤 1: 上传修改的文件...")
    
    files_to_upload = [
        ("saas-demo/src/lib/api/group-ai.ts", "/home/ubuntu/liaotian/saas-demo/src/lib/api/group-ai.ts", "API 客户端文件"),
        ("saas-demo/src/app/group-ai/accounts/page.tsx", "/home/ubuntu/liaotian/saas-demo/src/app/group-ai/accounts/page.tsx", "账号管理页面"),
    ]
    
    for local_path, remote_path, desc in files_to_upload:
        if not upload_file(ssh, local_path, remote_path, f"上传 {desc}"):
            print(f"[错误] 上传失败: {local_path}")
            sys.exit(1)
    
    # 2. 重新构建前端
    print("\n>>> 步骤 2: 重新构建前端...")
    build_cmd = """
cd /home/ubuntu/liaotian/saas-demo && \
export NVM_DIR="$HOME/.nvm" && \
[ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh" && \
nvm use 20 && \
rm -rf .next && \
npm run build
"""
    
    success, output, error = run_ssh_command(ssh, build_cmd, "构建前端")
    
    if not success:
        print("[警告] 构建可能有问题，但继续执行...")
        # 检查是否有构建错误
        if "error" in output.lower() or "failed" in output.lower():
            print("[错误] 构建失败，请检查错误信息")
            print("最后50行输出:")
            print("\n".join(output.split("\n")[-50:]))
    
    # 3. 重启前端服务
    print("\n>>> 步骤 3: 重启前端服务...")
    success, output, error = run_ssh_command(ssh, "sudo systemctl restart liaotian-frontend", "重启前端服务")
    
    if success:
        print("[OK] 前端服务已重启")
    else:
        print("[错误] 重启前端服务失败")
    
    # 4. 检查服务状态
    print("\n>>> 步骤 4: 检查服务状态...")
    success, output, error = run_ssh_command(ssh, "sudo systemctl status liaotian-frontend --no-pager | head -20", "检查前端服务状态")
    
    # 5. 检查后端服务（确保Workers API可用）
    print("\n>>> 步骤 5: 检查后端服务...")
    success, output, error = run_ssh_command(ssh, "sudo systemctl status liaotian-backend --no-pager | head -15", "检查后端服务状态")
    
    ssh.close()
    
    print("\n" + "=" * 60)
    print("部署完成！")
    print("=" * 60)
    print("\n功能更新：")
    print("- 从所有Worker节点读取账号")
    print("- 合并显示数据库账号和Worker节点账号")
    print("- 角色分配功能集成到账号管理")
    print("- 选择剧本时自动加载角色列表")
    print("\n下一步：")
    print("1. 清除浏览器缓存（Ctrl+Shift+Delete）")
    print("2. 强制刷新页面（Ctrl+F5）")
    print("3. 检查账号列表是否正确显示所有账号")
    print("4. 测试角色分配功能")
    
except Exception as e:
    print(f"\n[错误] 部署失败: {e}")
    import traceback
    print(traceback.format_exc())
    sys.exit(1)

