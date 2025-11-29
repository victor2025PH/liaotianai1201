# -*- coding: utf-8 -*-
"""
获取构建错误详情
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
    
    if output:
        print(output)
    if error:
        print(f"错误输出: {error}")
    print(f"退出码: {exit_status}")
    
    return exit_status == 0, output, error

try:
    print("=" * 60)
    print("获取构建错误详情")
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
    
    # 1. 尝试构建并获取完整输出
    print("\n>>> 1. 执行构建并获取完整输出...")
    build_cmd = """
cd /home/ubuntu/liaotian/saas-demo && \
source $HOME/.nvm/nvm.sh && \
nvm use 20 && \
npm run build 2>&1
"""
    
    success, output, error = run_ssh_command(ssh, build_cmd, "执行构建")
    
    # 2. 提取错误信息
    if not success or "error" in output.lower() or "failed" in output.lower():
        print("\n>>> 2. 提取错误信息...")
        error_lines = []
        for line in output.split('\n'):
            if any(keyword in line.lower() for keyword in ['error', 'failed', 'fail', 'exception', 'syntax']):
                error_lines.append(line)
        
        if error_lines:
            print("\n发现的错误行:")
            for i, line in enumerate(error_lines[:50], 1):  # 最多显示50行
                print(f"{i:3d}: {line}")
        else:
            print("未找到明显的错误关键词，显示最后50行输出:")
            print("\n".join(output.split('\n')[-50:]))
    
    # 3. 检查TypeScript编译错误
    print("\n>>> 3. 检查TypeScript编译错误...")
    if "typescript" in output.lower() or ".tsx" in output.lower() or ".ts" in output.lower():
        ts_errors = [line for line in output.split('\n') if any(keyword in line.lower() for keyword in ['.tsx', '.ts', 'typescript', 'type error'])]
        if ts_errors:
            print("TypeScript相关错误:")
            for line in ts_errors[:20]:
                print(line)
    
    # 4. 检查文件是否存在
    print("\n>>> 4. 检查关键文件...")
    files_to_check = [
        "/home/ubuntu/liaotian/saas-demo/src/app/group-ai/accounts/page.tsx",
        "/home/ubuntu/liaotian/saas-demo/src/lib/api/group-ai.ts",
        "/home/ubuntu/liaotian/saas-demo/package.json",
    ]
    
    for file_path in files_to_check:
        success, output, error = run_ssh_command(ssh, f"test -f {file_path} && echo '存在' || echo '不存在'", f"检查 {os.path.basename(file_path)}")
    
    # 5. 检查Node.js版本
    print("\n>>> 5. 检查Node.js和npm版本...")
    run_ssh_command(ssh, "source $HOME/.nvm/nvm.sh && nvm use 20 && node --version && npm --version", "检查版本")
    
    ssh.close()
    
    print("\n" + "=" * 60)
    print("分析完成！")
    print("=" * 60)
    print("\n请根据上述错误信息修复问题。")
    print("常见问题：")
    print("1. TypeScript语法错误 - 检查代码语法")
    print("2. 缺少依赖 - 运行 npm install")
    print("3. 文件路径错误 - 检查文件是否存在")
    
except Exception as e:
    print(f"\n[错误] 获取失败: {e}")
    import traceback
    print(traceback.format_exc())
    sys.exit(1)

