#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全自动部署脚本 - Python 版本
自动检查部署状态并完成部署
"""

import json
import paramiko
import os
import sys
from pathlib import Path
from datetime import datetime

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
    
    if not config_path.exists():
        print("错误: 找不到配置文件")
        print(f"路径: {config_path}")
        return None
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    servers = config.get('servers', {})
    if not servers:
        print("错误: 配置文件中没有服务器信息")
        return None
    
    # 选择第一个服务器
    server_name = list(servers.keys())[0]
    server_config = servers[server_name]
    
    return {
        'name': server_name,
        'host': server_config['host'],
        'user': server_config.get('user', 'ubuntu'),
        'password': server_config.get('password', ''),
        'deploy_dir': server_config.get('deploy_dir', '/opt/smart-tg')
    }

def connect_server(host, user, password):
    """连接服务器"""
    print(f"\n连接服务器: {host}...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        ssh.connect(host, username=user, password=password, timeout=10)
        print("[OK] 连接成功")
        return ssh
    except Exception as e:
        print(f"[ERROR] 连接失败: {e}")
        return None

def check_deployment_status(ssh, project_path):
    """检查部署状态"""
    print("\n[1/3] 检查当前部署状态...")
    
    check_script = f'''#!/bin/bash
echo "=== 服务状态检查 ==="
if systemctl is-active --quiet smart-tg-backend 2>/dev/null; then
    echo "BACKEND_RUNNING"
    systemctl status smart-tg-backend --no-pager -l | head -n 3
else
    echo "BACKEND_STOPPED"
fi

if systemctl is-active --quiet smart-tg-frontend 2>/dev/null; then
    echo "FRONTEND_RUNNING"
    systemctl status smart-tg-frontend --no-pager -l | head -n 3
else
    echo "FRONTEND_STOPPED"
fi

echo ""
echo "=== 端口检查 ==="
sudo netstat -tlnp 2>/dev/null | grep -E ':8000|:3000' || echo "端口未被占用"

echo ""
echo "=== 健康检查 ==="
curl -s http://localhost:8000/health 2>/dev/null || echo "后端健康检查失败"
curl -s http://localhost:3000 >/dev/null 2>&1 && echo "前端可访问" || echo "前端不可访问"

echo ""
echo "=== 目录检查 ==="
[ -d "{project_path}/admin-backend" ] && echo "BACKEND_DIR_EXISTS" || echo "BACKEND_DIR_MISSING"
[ -d "{project_path}/saas-demo" ] && echo "FRONTEND_DIR_EXISTS" || echo "FRONTEND_DIR_MISSING"
'''
    
    stdin, stdout, stderr = ssh.exec_command(f"bash -c {repr(check_script)}")
    output = stdout.read().decode('utf-8')
    error = stderr.read().decode('utf-8')
    
    print(output)
    if error:
        print(f"错误: {error}")
    
    backend_running = "BACKEND_RUNNING" in output
    frontend_running = "FRONTEND_RUNNING" in output
    backend_dir_exists = "BACKEND_DIR_EXISTS" in output
    frontend_dir_exists = "FRONTEND_DIR_EXISTS" in output
    
    return {
        'backend_running': backend_running,
        'frontend_running': frontend_running,
        'backend_dir_exists': backend_dir_exists,
        'frontend_dir_exists': frontend_dir_exists
    }

def deploy_services(ssh, project_path):
    """执行部署"""
    print("\n[2/3] 执行自动化部署...")
    
    script_dir = Path(__file__).parent
    temp_dir = f"/tmp/smart-tg-deploy-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    
    # 创建临时目录
    ssh.exec_command(f"mkdir -p {temp_dir}")
    
    # 上传文件
    sftp = ssh.open_sftp()
    files_to_upload = ["auto_deploy.sh", "smart-tg-backend.service", "smart-tg-frontend.service"]
    
    for filename in files_to_upload:
        local_path = script_dir / filename
        if local_path.exists():
            try:
                remote_path = f"{temp_dir}/{filename}"
                sftp.put(str(local_path), remote_path)
                print(f"  [OK] 已上传: {filename}")
            except Exception as e:
                print(f"  [ERROR] 上传失败: {filename} - {e}")
    
    sftp.close()
    
    # 配置并执行部署脚本
    deploy_cmd = f'''cd {temp_dir} && \
sed -i 's|/opt/smart-tg|{project_path}|g' auto_deploy.sh && \
sed -i 's|/opt/smart-tg|{project_path}|g' smart-tg-backend.service && \
sed -i 's|/opt/smart-tg|{project_path}|g' smart-tg-frontend.service && \
chmod +x auto_deploy.sh && \
sudo bash auto_deploy.sh
'''
    
    print("执行部署脚本...")
    stdin, stdout, stderr = ssh.exec_command(deploy_cmd, timeout=600)
    
    # 实时输出
    while True:
        line = stdout.readline()
        if not line:
            break
        print(line.rstrip())
    
    error_output = stderr.read().decode('utf-8')
    if error_output:
        print(f"错误输出: {error_output}")

def verify_deployment(ssh):
    """验证部署结果"""
    print("\n[3/3] 验证部署结果...")
    
    verify_script = '''#!/bin/bash
echo "=== 服务状态 ==="
systemctl is-active smart-tg-backend 2>/dev/null && echo "[OK] 后端服务运行中" || echo "[FAIL] 后端服务未运行"
systemctl is-active smart-tg-frontend 2>/dev/null && echo "[OK] 前端服务运行中" || echo "[FAIL] 前端服务未运行"

echo ""
echo "=== 健康检查 ==="
HEALTH=$(curl -s http://localhost:8000/health 2>/dev/null)
if [ -n "$HEALTH" ]; then
    echo "[OK] 后端健康检查: $HEALTH"
else
    echo "[FAIL] 后端健康检查失败"
fi

FRONTEND=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3000 2>/dev/null)
if [ "$FRONTEND" = "200" ]; then
    echo "[OK] 前端服务可访问"
else
    echo "[FAIL] 前端服务不可访问 (HTTP $FRONTEND)"
fi
'''
    
    stdin, stdout, stderr = ssh.exec_command(f"bash -c {repr(verify_script)}")
    output = stdout.read().decode('utf-8')
    print(output)

def main():
    print("=" * 50)
    print("Smart TG 全自动部署系统")
    print("=" * 50)
    
    # 加载配置
    config = load_config()
    if not config:
        sys.exit(1)
    
    print(f"\n服务器信息:")
    print(f"  名称: {config['name']}")
    print(f"  IP: {config['host']}")
    print(f"  用户: {config['user']}")
    print(f"  项目路径: {config['deploy_dir']}")
    
    # 连接服务器
    ssh = connect_server(config['host'], config['user'], config['password'])
    if not ssh:
        sys.exit(1)
    
    try:
        # 检查部署状态
        status = check_deployment_status(ssh, config['deploy_dir'])
        
        # 执行部署
        deploy_services(ssh, config['deploy_dir'])
        
        # 验证部署
        verify_deployment(ssh)
        
        print("\n" + "=" * 50)
        print("部署完成！")
        print("=" * 50)
        print(f"\n访问地址:")
        print(f"  后端: http://{config['host']}:8000")
        print(f"  前端: http://{config['host']}:3000")
        print(f"  API 文档: http://{config['host']}:8000/docs")
        
    finally:
        ssh.close()

if __name__ == "__main__":
    main()

