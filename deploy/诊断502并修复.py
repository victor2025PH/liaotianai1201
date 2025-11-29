# -*- coding: utf-8 -*-
"""
诊断502错误并修复
"""

import paramiko
import os
import time

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
    print("诊断502错误并修复")
    print("=" * 60)
    print()
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy)
    ssh_key = os.path.expanduser("~/.ssh/id_rsa")
    ssh.connect(SERVER, username=USERNAME, key_filename=ssh_key, timeout=30)
    print("[OK] 已连接\n")
    
    # 1. 检查BUILD_ID
    print("[1] 检查BUILD_ID...")
    success, output, _ = run_ssh(ssh, "cd /home/ubuntu/liaotian/saas-demo && test -f .next/BUILD_ID && cat .next/BUILD_ID || echo '不存在'")
    print(f"BUILD_ID: {output.strip()}\n")
    
    # 2. 检查服务状态
    print("[2] 检查服务状态...")
    success, output, _ = run_ssh(ssh, "sudo systemctl status liaotian-frontend --no-pager | head -15")
    print(output)
    
    # 3. 检查端口
    print("[3] 检查端口3000...")
    success, output, _ = run_ssh(ssh, "ss -tlnp | grep ':3000' || echo '端口未监听'")
    print(output)
    
    # 4. 检查最新日志
    print("[4] 检查最新日志...")
    success, output, _ = run_ssh(ssh, "sudo journalctl -u liaotian-frontend -n 20 --no-pager | tail -20")
    print(output)
    
    # 5. 停止服务
    print("[5] 停止服务...")
    run_ssh(ssh, "sudo systemctl stop liaotian-frontend")
    time.sleep(2)
    print("[OK] 服务已停止\n")
    
    # 6. 检查NVM
    print("[6] 检查NVM和Node...")
    success, output, _ = run_ssh(ssh, """cd /home/ubuntu/liaotian/saas-demo && \
export NVM_DIR="\$HOME/.nvm" && \
[ -s "\$NVM_DIR/nvm.sh" ] && . "\$NVM_DIR/nvm.sh" && \
nvm use 20 && \
echo "Node: $(node --version)" && \
echo "NPM: $(npm --version)" """)
    print(output)
    
    # 7. 启动服务
    print("[7] 启动服务...")
    run_ssh(ssh, "sudo systemctl start liaotian-frontend")
    time.sleep(5)
    print("[OK] 服务已启动\n")
    
    # 8. 再次检查状态
    print("[8] 检查服务状态...")
    success, output, _ = run_ssh(ssh, "sudo systemctl status liaotian-frontend --no-pager | head -20")
    print(output)
    
    # 9. 再次检查端口
    print("[9] 检查端口3000...")
    success, output, _ = run_ssh(ssh, "ss -tlnp | grep ':3000' || echo '端口未监听'")
    print(output)
    
    if ":3000" in output:
        print("\n[成功] 服务应该正常运行了！")
    else:
        print("\n[警告] 端口仍未监听，查看最新日志:")
        success, output, _ = run_ssh(ssh, "sudo journalctl -u liaotian-frontend -n 10 --no-pager")
        print(output)
    
    ssh.close()
    print("\n" + "=" * 60)
    print("完成")
    print("=" * 60)
    
except Exception as e:
    print(f"\n[错误] {e}")
    import traceback
    traceback.print_exc()

