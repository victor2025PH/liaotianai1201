# -*- coding: utf-8 -*-
"""
验证修复后的部署结果
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
    print("验证修复后的部署结果")
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
    print("\n>>> 检查修复后的文件...")
    success, output, error = run_ssh_command(ssh, "test -f /home/ubuntu/liaotian/saas-demo/src/app/group-ai/accounts/page.tsx && echo '文件存在' || echo '文件不存在'", "检查 page.tsx")
    
    # 2. 检查语法错误（查找重复的代码）
    print("\n>>> 检查语法错误...")
    success, output, error = run_ssh_command(ssh, "grep -n 'workerAccounts.map' /home/ubuntu/liaotian/saas-demo/src/app/group-ai/accounts/page.tsx | wc -l", "检查 workerAccounts.map 出现次数")
    if "1" in output.strip():
        print("[OK] workerAccounts.map 只出现一次（正确）")
    else:
        print(f"[警告] workerAccounts.map 出现 {output.strip()} 次（可能有问题）")
    
    # 3. 检查构建目录
    print("\n>>> 检查构建结果...")
    success, output, error = run_ssh_command(ssh, "test -d /home/ubuntu/liaotian/saas-demo/.next && echo '构建目录存在' || echo '构建目录不存在'", "检查构建目录")
    if "构建目录存在" in output:
        print("[OK] 前端已构建")
    else:
        print("[错误] 前端未构建，需要重新构建")
        print("\n>>> 重新构建前端...")
        build_cmd = """
cd /home/ubuntu/liaotian/saas-demo && \
export NVM_DIR="$HOME/.nvm" && \
[ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh" && \
nvm use 20 && \
rm -rf .next && \
npm run build 2>&1 | tail -30
"""
        success, output, error = run_ssh_command(ssh, build_cmd, "构建前端")
        if "error" in output.lower() or "failed" in output.lower():
            print("[错误] 构建失败")
            print("最后30行输出:")
            print(output)
        else:
            print("[OK] 构建成功")
    
    # 4. 检查服务状态
    print("\n>>> 检查服务状态...")
    success, output, error = run_ssh_command(ssh, "sudo systemctl is-active liaotian-frontend", "检查前端服务状态")
    if "active" in output:
        print("[OK] 前端服务运行中")
    else:
        print("[错误] 前端服务未运行，尝试重启...")
        success, output, error = run_ssh_command(ssh, "sudo systemctl restart liaotian-frontend && sleep 3 && sudo systemctl is-active liaotian-frontend", "重启前端服务")
        if "active" in output:
            print("[OK] 前端服务已重启并运行")
        else:
            print("[错误] 前端服务重启失败")
            run_ssh_command(ssh, "sudo journalctl -u liaotian-frontend -n 20 --no-pager", "查看前端服务日志")
    
    # 5. 检查端口监听
    print("\n>>> 检查端口监听...")
    success, output, error = run_ssh_command(ssh, "sudo netstat -tlnp 2>/dev/null | grep ':3000' || sudo ss -tlnp 2>/dev/null | grep ':3000'", "检查前端端口 3000")
    if ":3000" in output:
        print("[OK] 前端端口 3000 正在监听")
    else:
        print("[警告] 前端端口 3000 可能未监听")
    
    ssh.close()
    
    print("\n" + "=" * 60)
    print("验证完成！")
    print("=" * 60)
    print("\n如果所有检查都通过，修复成功！")
    print("请清除浏览器缓存并刷新页面测试。")
    
except Exception as e:
    print(f"\n[错误] 验证失败: {e}")
    import traceback
    print(traceback.format_exc())
    sys.exit(1)
