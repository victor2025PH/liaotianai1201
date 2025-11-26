#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检测并修复前端无法访问的问题
"""

import json
import paramiko
import sys
import time
from pathlib import Path

# 设置 Windows 控制台编码
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

def load_config():
    """加载服务器配置"""
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent
    config_path = project_root / "data" / "master_config.json"
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    servers = config.get('servers', {})
    server_name = list(servers.keys())[0]
    server_config = servers[server_name]
    
    return {
        'host': server_config['host'],
        'user': server_config.get('user', 'ubuntu'),
        'password': server_config.get('password', ''),
        'deploy_dir': server_config.get('deploy_dir', '/opt/smart-tg')
    }

def connect_server(host, user, password):
    """连接服务器"""
    print(f"连接服务器: {host}...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(host, username=user, password=password, timeout=10)
    print("[OK] 连接成功")
    return ssh

def diagnose(ssh, server_ip):
    """诊断问题"""
    print("\n" + "=" * 50)
    print("诊断前端访问问题")
    print("=" * 50)
    
    # 1. 检查服务状态
    print("\n[1] 检查服务状态...")
    stdin, stdout, stderr = ssh.exec_command("systemctl is-active smart-tg-frontend")
    status = stdout.read().decode('utf-8').strip()
    print(f"前端服务状态: {status}")
    
    # 2. 检查端口监听
    print("\n[2] 检查端口监听...")
    stdin, stdout, stderr = ssh.exec_command("sudo ss -tlnp | grep :3000")
    ports = stdout.read().decode('utf-8').strip()
    if ports:
        print(f"端口监听:\n{ports}")
        # 检查是否绑定到 0.0.0.0
        if '0.0.0.0:3000' in ports or '*:3000' in ports:
            print("[OK] 端口已绑定到所有接口")
        else:
            print("[WARNING] 端口可能只绑定到 localhost")
    else:
        print("[ERROR] 端口 3000 未被监听")
    
    # 3. 检查进程
    print("\n[3] 检查进程...")
    stdin, stdout, stderr = ssh.exec_command("ps aux | grep -E 'next-server|node.*start' | grep -v grep")
    processes = stdout.read().decode('utf-8').strip()
    if processes:
        print("相关进程:")
        print(processes)
    else:
        print("[WARNING] 未找到前端进程")
    
    # 4. 检查防火墙
    print("\n[4] 检查防火墙...")
    stdin, stdout, stderr = ssh.exec_command("sudo ufw status 2>/dev/null || echo 'ufw未安装'")
    ufw_status = stdout.read().decode('utf-8').strip()
    print(f"UFW 状态: {ufw_status}")
    
    stdin, stdout, stderr = ssh.exec_command("sudo iptables -L -n | grep -E '3000|8000' || echo 'iptables规则中未找到端口'")
    iptables = stdout.read().decode('utf-8').strip()
    if iptables and '未找到' not in iptables:
        print(f"iptables 规则:\n{iptables}")
    
    # 5. 本地访问测试
    print("\n[5] 本地访问测试...")
    stdin, stdout, stderr = ssh.exec_command("curl -s -o /dev/null -w '%{http_code}' http://localhost:3000 2>/dev/null || echo '000'")
    local_code = stdout.read().decode('utf-8').strip()
    print(f"本地访问: HTTP {local_code}")
    
    # 6. 外部访问测试（从服务器内部测试外部IP）
    print(f"\n[6] 外部访问测试...")
    stdin, stdout, stderr = ssh.exec_command(f"curl -s -o /dev/null -w '%{{http_code}}' --connect-timeout 5 http://{server_ip}:3000 2>/dev/null || echo 'TIMEOUT'")
    external_code = stdout.read().decode('utf-8').strip()
    print(f"外部访问 ({server_ip}:3000): {external_code}")
    
    # 7. 检查服务日志
    print("\n[7] 检查服务日志（最近20行）...")
    stdin, stdout, stderr = ssh.exec_command("sudo journalctl -u smart-tg-frontend -n 20 --no-pager")
    logs = stdout.read().decode('utf-8')
    print(logs)

def fix_issues(ssh, deploy_dir, username, server_ip):
    """修复问题"""
    print("\n" + "=" * 50)
    print("修复前端访问问题")
    print("=" * 50)
    
    frontend_dir = f"{deploy_dir}/saas-demo"
    
    # 1. 确保防火墙开放端口
    print("\n[1] 配置防火墙...")
    ssh.exec_command("sudo ufw allow 3000/tcp 2>/dev/null || true")
    ssh.exec_command("sudo ufw allow 8000/tcp 2>/dev/null || true")
    print("[OK] 防火墙规则已配置")
    
    # 2. 检查 Next.js 配置，确保绑定到 0.0.0.0
    print("\n[2] 检查 Next.js 配置...")
    
    # 检查 package.json 中的 start 脚本
    stdin, stdout, stderr = ssh.exec_command(f"cat {frontend_dir}/package.json | grep -A 5 '\"scripts\"'")
    scripts = stdout.read().decode('utf-8')
    print("package.json scripts:")
    print(scripts)
    
    # 3. 修改启动脚本，确保绑定到 0.0.0.0
    print("\n[3] 修复启动脚本...")
    start_script = f"""#!/bin/bash
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"
cd {frontend_dir}
# 确保 Next.js 绑定到所有接口
HOSTNAME=0.0.0.0 PORT=3000 npm start
"""
    
    stdin, stdout, stderr = ssh.exec_command(f"cat > /tmp/start-frontend.sh << 'EOFFRONTEND'\n{start_script}EOFFRONTEND")
    stdout.read()
    ssh.exec_command("chmod +x /tmp/start-frontend.sh")
    print("[OK] 启动脚本已更新（绑定到 0.0.0.0）")
    
    # 4. 更新服务文件
    print("\n[4] 更新服务文件...")
    frontend_service = f"""[Unit]
Description=Smart TG Frontend Service (Next.js)
After=network.target smart-tg-backend.service

[Service]
Type=simple
User={username}
Group={username}
WorkingDirectory={frontend_dir}
Environment="PATH=/usr/local/bin:/usr/bin:/bin"
Environment="NVM_DIR=$HOME/.nvm"
Environment="HOSTNAME=0.0.0.0"
Environment="PORT=3000"
EnvironmentFile={frontend_dir}/.env.local
ExecStart=/bin/bash /tmp/start-frontend.sh
Restart=on-failure
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
"""
    
    stdin, stdout, stderr = ssh.exec_command(f"cat > /tmp/smart-tg-frontend.service << 'EOFFRONTEND'\n{frontend_service}EOFFRONTEND")
    stdout.read()
    ssh.exec_command("sudo cp /tmp/smart-tg-frontend.service /etc/systemd/system/smart-tg-frontend.service")
    ssh.exec_command("sudo chmod 644 /etc/systemd/system/smart-tg-frontend.service")
    ssh.exec_command("sudo systemctl daemon-reload")
    print("[OK] 服务文件已更新")
    
    # 5. 重启前端服务
    print("\n[5] 重启前端服务...")
    ssh.exec_command("sudo systemctl stop smart-tg-frontend")
    time.sleep(2)
    ssh.exec_command("sudo systemctl start smart-tg-frontend")
    ssh.exec_command("sudo systemctl enable smart-tg-frontend")
    
    print("等待服务启动...")
    time.sleep(5)
    
    # 6. 验证
    print("\n[6] 验证修复结果...")
    stdin, stdout, stderr = ssh.exec_command("sudo systemctl is-active smart-tg-frontend")
    status = stdout.read().decode('utf-8').strip()
    print(f"服务状态: {status}")
    
    stdin, stdout, stderr = ssh.exec_command("sudo ss -tlnp | grep :3000")
    ports = stdout.read().decode('utf-8').strip()
    if ports:
        print(f"端口监听:\n{ports}")
        if '0.0.0.0:3000' in ports:
            print("[OK] 端口已正确绑定到 0.0.0.0:3000")
        else:
            print("[WARNING] 端口绑定可能不正确")
    else:
        print("[ERROR] 端口未被监听")
    
    time.sleep(2)
    stdin, stdout, stderr = ssh.exec_command("curl -s -o /dev/null -w '%{http_code}' http://localhost:3000 2>/dev/null || echo '000'")
    local_code = stdout.read().decode('utf-8').strip()
    print(f"本地访问: HTTP {local_code}")
    
    # 检查服务日志
    print("\n服务日志（最近10行）...")
    stdin, stdout, stderr = ssh.exec_command("sudo journalctl -u smart-tg-frontend -n 10 --no-pager")
    logs = stdout.read().decode('utf-8')
    print(logs)

def main():
    config = load_config()
    ssh = connect_server(config['host'], config['user'], config['password'])
    
    try:
        # 诊断
        diagnose(ssh, config['host'])
        
        # 修复
        fix_issues(ssh, config['deploy_dir'], config['user'], config['host'])
        
        print("\n" + "=" * 50)
        print("修复完成！")
        print("=" * 50)
        print(f"\n访问地址:")
        print(f"  后端: http://{config['host']}:8000")
        print(f"  前端: http://{config['host']}:3000")
        print(f"  API 文档: http://{config['host']}:8000/docs")
        print(f"\n如果仍然无法访问，请检查:")
        print(f"  1. 云服务器安全组是否开放 3000 端口（TCP）")
        print(f"  2. 等待 10-20 秒让服务完全启动")
        print(f"  3. 清除浏览器缓存后重试")
        
    finally:
        ssh.close()

if __name__ == "__main__":
    main()

