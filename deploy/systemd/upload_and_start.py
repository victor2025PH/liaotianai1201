#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
上传后端代码、重新构建前端并启动服务
"""

import json
import paramiko
import sys
import os
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

def upload_backend_code(ssh, deploy_dir, project_root):
    """上传后端代码"""
    print("\n[1/4] 上传后端代码...")
    
    backend_dir = project_root / "admin-backend"
    group_ai_dir = project_root / "group_ai_service"
    
    if not backend_dir.exists():
        print("[ERROR] 本地后端目录不存在")
        return False
    
    if not group_ai_dir.exists():
        print("[ERROR] 本地 group_ai_service 目录不存在")
        return False
    
    # 使用 tar 打包并上传
    print("打包后端代码（包括 group_ai_service）...")
    temp_tar = f"/tmp/backend-{datetime.now().strftime('%Y%m%d-%H%M%S')}.tar.gz"
    
    # 在本地创建 tar 包
    import tarfile
    import tempfile
    
    local_temp = tempfile.NamedTemporaryFile(delete=False, suffix='.tar.gz')
    local_temp.close()
    
    try:
        with tarfile.open(local_temp.name, 'w:gz') as tar:
            # 排除不需要的文件
            exclude_patterns = [
                '.git', '__pycache__', '*.pyc', '.venv', 'venv',
                '.env', '.env.local', '*.log', '.pytest_cache',
                'node_modules', '.next', 'dist', 'build', '.pytest_cache'
            ]
            
            # 添加 admin-backend 目录
            for root, dirs, files in os.walk(backend_dir):
                # 过滤目录
                dirs[:] = [d for d in dirs if not any(d.startswith(p) for p in exclude_patterns)]
                
                for file in files:
                    if any(file.endswith(p.replace('*', '')) for p in exclude_patterns):
                        continue
                    
                    file_path = Path(root) / file
                    arcname = Path("admin-backend") / file_path.relative_to(backend_dir)
                    tar.add(file_path, arcname=arcname)
            
            # 添加 group_ai_service 目录
            for root, dirs, files in os.walk(group_ai_dir):
                # 过滤目录
                dirs[:] = [d for d in dirs if not any(d.startswith(p) for p in exclude_patterns)]
                
                for file in files:
                    if any(file.endswith(p.replace('*', '')) for p in exclude_patterns):
                        continue
                    
                    file_path = Path(root) / file
                    arcname = Path("group_ai_service") / file_path.relative_to(group_ai_dir)
                    tar.add(file_path, arcname=arcname)
        
        print(f"[OK] 已打包: {os.path.getsize(local_temp.name) / 1024 / 1024:.2f} MB")
        
        # 上传 tar 包
        print("上传到服务器...")
        sftp = ssh.open_sftp()
        sftp.put(local_temp.name, temp_tar)
        sftp.close()
        print("[OK] 上传完成")
        
        # 解压到目标目录
        print("解压到目标目录...")
        ssh.exec_command(f"mkdir -p {deploy_dir}")
        ssh.exec_command(f"tar -xzf {temp_tar} -C {deploy_dir}")
        
        # 等待解压完成
        import time
        time.sleep(2)
        
        # 验证上传
        stdin, stdout, stderr = ssh.exec_command(f"test -d {deploy_dir}/admin-backend/app && echo 'exists' || echo 'not_exists'")
        app_exists = stdout.read().decode('utf-8').strip()
        
        if app_exists == 'exists':
            print("[OK] 后端代码上传成功")
            
            # 列出 app 目录内容
            stdin, stdout, stderr = ssh.exec_command(f"ls -la {deploy_dir}/admin-backend/app/ | head -10")
            print("app 目录内容:")
            print(stdout.read().decode('utf-8'))
            
            # 清理临时文件
            ssh.exec_command(f"rm -f {temp_tar}")
            os.unlink(local_temp.name)
            return True
        else:
            print("[ERROR] app 目录不存在，上传可能失败")
            return False
            
    except Exception as e:
        print(f"[ERROR] 上传失败: {e}")
        if os.path.exists(local_temp.name):
            os.unlink(local_temp.name)
        return False

def rebuild_frontend(ssh, deploy_dir):
    """重新构建前端"""
    print("\n[2/4] 重新构建前端...")
    
    frontend_dir = f"{deploy_dir}/saas-demo"
    
    # 清理旧的构建
    print("清理旧的构建...")
    ssh.exec_command(f"rm -rf {frontend_dir}/.next")
    
    # 使用 nvm 重新构建
    build_cmd = f'''cd {frontend_dir} && \
export NVM_DIR="$HOME/.nvm" && \
[ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh" && \
nvm use 20 && \
npm run build
'''
    
    print("执行构建...")
    stdin, stdout, stderr = ssh.exec_command(build_cmd, timeout=600)
    
    # 实时输出
    error_lines = []
    while True:
        line = stdout.readline()
        if not line:
            break
        print(f"  {line.rstrip()}")
        if 'error' in line.lower() or 'Error' in line:
            error_lines.append(line)
    
    # 检查构建结果
    stdin, stdout, stderr = ssh.exec_command(f"test -f {frontend_dir}/.next/BUILD_ID && echo 'success' || echo 'failed'")
    result = stdout.read().decode('utf-8').strip()
    
    if result == 'success':
        print("[OK] 前端构建成功")
        return True
    else:
        print("[ERROR] 前端构建失败")
        if error_lines:
            print("错误信息:")
            for line in error_lines[-10:]:
                print(f"  {line.rstrip()}")
        return False

def start_services(ssh):
    """启动服务"""
    print("\n[3/4] 启动服务...")
    
    # 停止现有服务
    print("停止现有服务...")
    ssh.exec_command("sudo systemctl stop smart-tg-backend smart-tg-frontend")
    
    # 启动后端服务
    print("启动后端服务...")
    ssh.exec_command("sudo systemctl start smart-tg-backend")
    ssh.exec_command("sudo systemctl enable smart-tg-backend")
    
    import time
    time.sleep(3)
    
    stdin, stdout, stderr = ssh.exec_command("sudo systemctl is-active smart-tg-backend")
    backend_status = stdout.read().decode('utf-8').strip()
    print(f"后端服务状态: {backend_status}")
    
    if backend_status != 'active':
        print("后端服务日志:")
        stdin, stdout, stderr = ssh.exec_command("sudo journalctl -u smart-tg-backend -n 20 --no-pager")
        print(stdout.read().decode('utf-8'))
    else:
        print("[OK] 后端服务已启动")
    
    # 启动前端服务
    print("启动前端服务...")
    ssh.exec_command("sudo systemctl start smart-tg-frontend")
    ssh.exec_command("sudo systemctl enable smart-tg-frontend")
    
    time.sleep(3)
    
    stdin, stdout, stderr = ssh.exec_command("sudo systemctl is-active smart-tg-frontend")
    frontend_status = stdout.read().decode('utf-8').strip()
    print(f"前端服务状态: {frontend_status}")
    
    if frontend_status != 'active':
        print("前端服务日志:")
        stdin, stdout, stderr = ssh.exec_command("sudo journalctl -u smart-tg-frontend -n 20 --no-pager")
        print(stdout.read().decode('utf-8'))
    else:
        print("[OK] 前端服务已启动")
    
    return backend_status == 'active' and frontend_status == 'active'

def verify_deployment(ssh, server_ip):
    """验证部署"""
    print("\n[4/4] 验证部署...")
    
    import time
    time.sleep(2)
    
    # 检查服务状态
    print("服务状态:")
    stdin, stdout, stderr = ssh.exec_command("systemctl is-active smart-tg-backend smart-tg-frontend")
    status = stdout.read().decode('utf-8').strip()
    print(status)
    
    # 健康检查
    print("\n健康检查:")
    stdin, stdout, stderr = ssh.exec_command("curl -s http://localhost:8000/health 2>/dev/null || echo '后端不可访问'")
    backend_health = stdout.read().decode('utf-8').strip()
    print(f"后端: {backend_health}")
    
    stdin, stdout, stderr = ssh.exec_command("curl -s -o /dev/null -w '%{http_code}' http://localhost:3000 2>/dev/null || echo '000'")
    frontend_code = stdout.read().decode('utf-8').strip()
    print(f"前端: HTTP {frontend_code}")
    
    # 端口检查
    print("\n端口检查:")
    stdin, stdout, stderr = ssh.exec_command("sudo netstat -tlnp 2>/dev/null | grep -E ':8000|:3000' || echo '端口未被占用'")
    ports = stdout.read().decode('utf-8').strip()
    print(ports)

def main():
    print("=" * 50)
    print("上传代码、构建并启动服务")
    print("=" * 50)
    
    # 加载配置
    config = load_config()
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent
    
    print(f"\n服务器信息:")
    print(f"  IP: {config['host']}")
    print(f"  用户: {config['user']}")
    print(f"  项目路径: {config['deploy_dir']}")
    print(f"  本地项目路径: {project_root}")
    
    # 连接服务器
    ssh = connect_server(config['host'], config['user'], config['password'])
    if not ssh:
        sys.exit(1)
    
    try:
        # 1. 上传后端代码
        if not upload_backend_code(ssh, config['deploy_dir'], project_root):
            print("\n[警告] 后端代码上传失败，但继续执行其他步骤...")
        
        # 2. 重新构建前端
        if not rebuild_frontend(ssh, config['deploy_dir']):
            print("\n[警告] 前端构建失败，但继续启动服务...")
        
        # 3. 启动服务
        start_services(ssh)
        
        # 4. 验证部署
        verify_deployment(ssh, config['host'])
        
        print("\n" + "=" * 50)
        print("部署完成！")
        print("=" * 50)
        print(f"\n访问地址:")
        print(f"  后端: http://{config['host']}:8000")
        print(f"  前端: http://{config['host']}:3000")
        print(f"  API 文档: http://{config['host']}:8000/docs")
        print(f"\n[重要] 请检查并配置后端 .env 文件中的数据库连接和密钥！")
        
    finally:
        ssh.close()

if __name__ == "__main__":
    main()

