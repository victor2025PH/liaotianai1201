# -*- coding: utf-8 -*-
"""
诊断前端服务启动失败问题
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
    print("诊断前端服务启动失败问题")
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
    
    # 1. 检查构建目录
    print("\n>>> 1. 检查构建目录...")
    success, output, error = run_ssh_command(ssh, "test -d /home/ubuntu/liaotian/saas-demo/.next && echo '存在' || echo '不存在'", "检查构建目录")
    if "不存在" in output:
        print("[错误] 构建目录不存在，需要重新构建")
    else:
        print("[OK] 构建目录存在")
        # 检查构建时间
        run_ssh_command(ssh, "stat -c '%y' /home/ubuntu/liaotian/saas-demo/.next 2>/dev/null || echo '无法获取时间'", "检查构建时间")
    
    # 2. 检查服务配置
    print("\n>>> 2. 检查服务配置...")
    run_ssh_command(ssh, "cat /etc/systemd/system/liaotian-frontend.service", "查看服务配置文件")
    
    # 3. 查看详细的服务日志
    print("\n>>> 3. 查看详细的服务日志（最后50行）...")
    run_ssh_command(ssh, "sudo journalctl -u liaotian-frontend -n 50 --no-pager", "查看服务日志")
    
    # 4. 尝试手动启动并查看错误
    print("\n>>> 4. 尝试手动启动并查看错误...")
    run_ssh_command(ssh, "cd /home/ubuntu/liaotian/saas-demo && export NVM_DIR=\"$HOME/.nvm\" && [ -s \"$NVM_DIR/nvm.sh\" ] && . \"$NVM_DIR/nvm.sh\" && nvm use 20 && npm start 2>&1 | head -30", "手动启动查看错误")
    
    # 5. 检查package.json中的start脚本
    print("\n>>> 5. 检查package.json中的start脚本...")
    run_ssh_command(ssh, "cd /home/ubuntu/liaotian/saas-demo && cat package.json | grep -A 5 '\"scripts\"'", "查看package.json脚本")
    
    # 6. 检查Node.js和npm版本
    print("\n>>> 6. 检查Node.js和npm版本...")
    run_ssh_command(ssh, "cd /home/ubuntu/liaotian/saas-demo && export NVM_DIR=\"$HOME/.nvm\" && [ -s \"$NVM_DIR/nvm.sh\" ] && . \"$NVM_DIR/nvm.sh\" && nvm use 20 && node --version && npm --version", "检查Node.js和npm版本")
    
    # 7. 检查是否有构建错误
    print("\n>>> 7. 检查构建错误...")
    run_ssh_command(ssh, "cd /home/ubuntu/liaotian/saas-demo && test -f .next/BUILD_ID && echo '构建ID存在' || echo '构建ID不存在'", "检查构建ID")
    
    # 8. 检查端口是否被占用
    print("\n>>> 8. 检查端口是否被占用...")
    run_ssh_command(ssh, "sudo lsof -i :3000 || sudo netstat -tlnp | grep ':3000' || echo '端口3000未被占用'", "检查端口3000")
    
    ssh.close()
    
    print("\n" + "=" * 60)
    print("诊断完成！")
    print("=" * 60)
    print("\n请根据上述输出信息查找问题原因。")
    print("常见问题：")
    print("1. 构建失败 - 需要重新构建")
    print("2. 服务配置错误 - 需要修改systemd服务文件")
    print("3. 端口被占用 - 需要停止占用端口的进程")
    print("4. Node.js版本不匹配 - 需要检查版本")
    
except Exception as e:
    print(f"\n[错误] 诊断失败: {e}")
    import traceback
    print(traceback.format_exc())
    sys.exit(1)

