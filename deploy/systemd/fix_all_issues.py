#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复所有问题：安装依赖、确保服务监听端口
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

def install_pyrogram(ssh, deploy_dir):
    """在虚拟环境中安装 pyrogram"""
    print("\n[1/4] 安装 pyrogram...")
    
    backend_dir = f"{deploy_dir}/admin-backend"
    install_cmd = f"cd {backend_dir} && source .venv/bin/activate && pip install pyrogram"
    
    stdin, stdout, stderr = ssh.exec_command(install_cmd, timeout=300)
    
    # 实时输出
    while True:
        line = stdout.readline()
        if not line:
            break
        print(f"  {line.rstrip()}")
    
    # 验证安装
    verify_cmd = f"cd {backend_dir} && source .venv/bin/activate && python -c 'import pyrogram; print(pyrogram.__version__)'"
    stdin, stdout, stderr = ssh.exec_command(verify_cmd)
    version = stdout.read().decode('utf-8').strip()
    
    if version:
        print(f"[OK] pyrogram 已安装: {version}")
        return True
    else:
        print("[ERROR] pyrogram 安装失败")
        return False

def check_frontend_build(ssh, deploy_dir):
    """检查前端构建"""
    print("\n[2/4] 检查前端构建...")
    
    frontend_dir = f"{deploy_dir}/saas-demo"
    
    # 检查 BUILD_ID
    stdin, stdout, stderr = ssh.exec_command(f"test -f {frontend_dir}/.next/BUILD_ID && echo 'exists' || echo 'not_exists'")
    build_id_exists = stdout.read().decode('utf-8').strip()
    
    if build_id_exists == 'not_exists':
        print("重新构建前端...")
        build_cmd = f'''cd {frontend_dir} && \
export NVM_DIR="$HOME/.nvm" && \
[ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh" && \
nvm use 20 && \
npm run build
'''
        
        stdin, stdout, stderr = ssh.exec_command(build_cmd, timeout=600)
        
        while True:
            line = stdout.readline()
            if not line:
                break
            if 'error' in line.lower() or 'Error' in line:
                print(f"  {line.rstrip()}")
        
        stdin, stdout, stderr = ssh.exec_command(f"test -f {frontend_dir}/.next/BUILD_ID && echo 'success' || echo 'failed'")
        result = stdout.read().decode('utf-8').strip()
        
        if result == 'success':
            print("[OK] 前端构建成功")
        else:
            print("[ERROR] 前端构建失败")
            return False
    else:
        print("[OK] 前端构建已存在")
    
    return True

def restart_services(ssh, deploy_dir, username):
    """重启服务"""
    print("\n[3/4] 重启服务...")
    
    # 停止服务
    ssh.exec_command("sudo systemctl stop smart-tg-backend smart-tg-frontend")
    time.sleep(2)
    
    # 启动后端
    print("启动后端服务...")
    ssh.exec_command("sudo systemctl start smart-tg-backend")
    ssh.exec_command("sudo systemctl enable smart-tg-backend")
    
    time.sleep(5)
    
    # 检查后端状态
    stdin, stdout, stderr = ssh.exec_command("sudo systemctl is-active smart-tg-backend")
    backend_status = stdout.read().decode('utf-8').strip()
    print(f"后端服务状态: {backend_status}")
    
    if backend_status != 'active':
        print("后端服务日志:")
        stdin, stdout, stderr = ssh.exec_command("sudo journalctl -u smart-tg-backend -n 30 --no-pager")
        print(stdout.read().decode('utf-8'))
    else:
        print("[OK] 后端服务已启动")
    
    # 启动前端
    print("启动前端服务...")
    ssh.exec_command("sudo systemctl start smart-tg-frontend")
    ssh.exec_command("sudo systemctl enable smart-tg-frontend")
    
    time.sleep(3)
    
    # 检查前端状态
    stdin, stdout, stderr = ssh.exec_command("sudo systemctl is-active smart-tg-frontend")
    frontend_status = stdout.read().decode('utf-8').strip()
    print(f"前端服务状态: {frontend_status}")
    
    if frontend_status != 'active':
        print("前端服务日志:")
        stdin, stdout, stderr = ssh.exec_command("sudo journalctl -u smart-tg-frontend -n 30 --no-pager")
        print(stdout.read().decode('utf-8'))
    else:
        print("[OK] 前端服务已启动")
    
    return backend_status == 'active' and frontend_status == 'active'

def verify_ports(ssh, server_ip):
    """验证端口监听"""
    print("\n[4/4] 验证端口监听...")
    
    time.sleep(3)
    
    # 检查端口
    print("检查端口监听...")
    stdin, stdout, stderr = ssh.exec_command("sudo netstat -tlnp 2>/dev/null | grep -E ':8000|:3000' || ss -tlnp | grep -E ':8000|:3000' || echo '端口未被占用'")
    ports = stdout.read().decode('utf-8').strip()
    print(f"端口状态:\n{ports}")
    
    # 健康检查
    print("\n健康检查:")
    stdin, stdout, stderr = ssh.exec_command("curl -s http://localhost:8000/health 2>/dev/null || echo '后端不可访问'")
    backend_health = stdout.read().decode('utf-8').strip()
    print(f"后端本地: {backend_health}")
    
    stdin, stdout, stderr = ssh.exec_command("curl -s -o /dev/null -w '%{http_code}' http://localhost:3000 2>/dev/null || echo '000'")
    frontend_code = stdout.read().decode('utf-8').strip()
    print(f"前端本地: HTTP {frontend_code}")
    
    # 检查进程
    print("\n检查进程:")
    stdin, stdout, stderr = ssh.exec_command("ps aux | grep -E 'gunicorn|next-server' | grep -v grep || echo '进程未找到'")
    processes = stdout.read().decode('utf-8').strip()
    print(processes)

def main():
    config = load_config()
    ssh = connect_server(config['host'], config['user'], config['password'])
    
    try:
        # 1. 安装 pyrogram
        install_pyrogram(ssh, config['deploy_dir'])
        
        # 2. 检查前端构建
        check_frontend_build(ssh, config['deploy_dir'])
        
        # 3. 重启服务
        restart_services(ssh, config['deploy_dir'], config['user'])
        
        # 4. 验证端口
        verify_ports(ssh, config['host'])
        
        print("\n" + "=" * 50)
        print("修复完成！")
        print("=" * 50)
        print(f"\n访问地址:")
        print(f"  后端: http://{config['host']}:8000")
        print(f"  前端: http://{config['host']}:3000")
        print(f"  API 文档: http://{config['host']}:8000/docs")
        print(f"\n如果仍然无法访问，请检查云服务器安全组是否开放 8000 和 3000 端口")
        
    finally:
        ssh.close()

if __name__ == "__main__":
    main()

