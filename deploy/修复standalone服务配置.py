# -*- coding: utf-8 -*-
"""
修复standalone模式的服务配置
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
    print("修复standalone模式的服务配置")
    print("=" * 60)
    print()
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy)
    ssh_key = os.path.expanduser("~/.ssh/id_rsa")
    ssh.connect(SERVER, username=USERNAME, key_filename=ssh_key, timeout=30)
    print("[OK] 已连接\n")
    
    # 1. 检查standalone server.js
    print("[1] 检查standalone server.js...")
    success, output, _ = run_ssh(ssh, "cd /home/ubuntu/liaotian/saas-demo && test -f .next/standalone/liaotian/saas-demo/server.js && ls -la .next/standalone/liaotian/saas-demo/server.js || echo '不存在'")
    print(output)
    if "不存在" in output:
        print("[错误] server.js不存在\n")
        ssh.close()
        exit(1)
    
    # 2. 获取Node路径
    print("[2] 获取Node路径...")
    success, output, _ = run_ssh(ssh, """cd /home/ubuntu/liaotian/saas-demo && \
export NVM_DIR="\$HOME/.nvm" && \
[ -s "\$NVM_DIR/nvm.sh" ] && . "\$NVM_DIR/nvm.sh" && \
nvm use 20 && \
which node""")
    node_path = output.strip()
    print(f"Node路径: {node_path}\n")
    
    # 3. 备份当前配置
    print("[3] 备份当前服务配置...")
    run_ssh(ssh, "sudo cp /etc/systemd/system/liaotian-frontend.service /etc/systemd/system/liaotian-frontend.service.bak")
    print("[OK] 已备份\n")
    
    # 4. 创建新配置
    print("[4] 创建新的服务配置...")
    service_config = f"""[Unit]
Description=Liaotian Frontend
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/liaotian/saas-demo
Environment=PORT=3000
Environment="NVM_DIR=$HOME/.nvm"
Environment="PATH=$HOME/.nvm/versions/node/v20.19.6/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
ExecStart={node_path} /home/ubuntu/liaotian/saas-demo/.next/standalone/liaotian/saas-demo/server.js
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
"""
    
    # 写入临时文件
    sftp = ssh.open_sftp()
    with sftp.file('/tmp/liaotian-frontend.service', 'w') as f:
        f.write(service_config)
    sftp.close()
    
    # 复制到systemd目录
    run_ssh(ssh, "sudo cp /tmp/liaotian-frontend.service /etc/systemd/system/liaotian-frontend.service")
    print("[OK] 新配置已创建\n")
    
    # 5. 重新加载systemd
    print("[5] 重新加载systemd...")
    run_ssh(ssh, "sudo systemctl daemon-reload")
    print("[OK] 已重新加载\n")
    
    # 6. 停止旧服务
    print("[6] 停止旧服务...")
    run_ssh(ssh, "sudo systemctl stop liaotian-frontend")
    time.sleep(2)
    print("[OK] 服务已停止\n")
    
    # 7. 启动新服务
    print("[7] 启动新服务...")
    run_ssh(ssh, "sudo systemctl start liaotian-frontend")
    time.sleep(5)
    print("[OK] 服务已启动\n")
    
    # 8. 检查服务状态
    print("[8] 检查服务状态...")
    success, output, _ = run_ssh(ssh, "sudo systemctl status liaotian-frontend --no-pager | head -20")
    print(output)
    
    # 9. 检查端口
    print("[9] 检查端口3000...")
    success, output, _ = run_ssh(ssh, "ss -tlnp | grep ':3000' || echo '端口未监听'")
    print(output)
    
    if ":3000" in output:
        print("\n[成功] 服务应该正常运行了！")
        print("请访问: http://aikz.usdt2026.cc/group-ai/accounts")
    else:
        print("\n[警告] 端口仍未监听，查看最新日志:")
        success, output, _ = run_ssh(ssh, "sudo journalctl -u liaotian-frontend -n 15 --no-pager")
        print(output)
    
    ssh.close()
    print("\n" + "=" * 60)
    print("完成")
    print("=" * 60)
    
except Exception as e:
    print(f"\n[错误] {e}")
    import traceback
    traceback.print_exc()

