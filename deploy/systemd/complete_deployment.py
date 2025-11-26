#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
完成部署脚本 - 升级 Node.js、配置环境变量、构建并启动服务
"""

import json
import paramiko
import sys
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
        'name': server_name,
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

def upgrade_nodejs(ssh):
    """升级 Node.js 到 20.x"""
    print("\n[1/5] 升级 Node.js 到 20.x...")
    
    # 检查当前 Node.js 版本
    stdin, stdout, stderr = ssh.exec_command("node --version 2>/dev/null || echo 'not_installed'")
    current_version = stdout.read().decode('utf-8').strip()
    print(f"当前 Node.js 版本: {current_version}")
    
    if current_version.startswith('v20'):
        print("[OK] Node.js 版本已经是 20.x，跳过升级")
        return True
    
    # 安装 nvm（如果未安装）
    print("检查 nvm...")
    stdin, stdout, stderr = ssh.exec_command("command -v nvm || echo 'not_installed'")
    nvm_installed = stdout.read().decode('utf-8').strip()
    
    if nvm_installed == 'not_installed':
        print("安装 nvm...")
        install_nvm_cmd = '''curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash'''
        stdin, stdout, stderr = ssh.exec_command(install_nvm_cmd)
        stdout.read()  # 等待完成
        
        # 加载 nvm
        load_nvm_cmd = '''export NVM_DIR="$HOME/.nvm" && [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"'''
        ssh.exec_command(load_nvm_cmd)
    
    # 安装 Node.js 20
    print("安装 Node.js 20...")
    install_node_cmd = '''export NVM_DIR="$HOME/.nvm" && [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh" && nvm install 20 && nvm use 20 && nvm alias default 20'''
    stdin, stdout, stderr = ssh.exec_command(install_node_cmd, timeout=300)
    
    # 实时输出
    while True:
        line = stdout.readline()
        if not line:
            break
        print(f"  {line.rstrip()}")
    
    # 验证安装
    verify_cmd = '''export NVM_DIR="$HOME/.nvm" && [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh" && node --version'''
    stdin, stdout, stderr = ssh.exec_command(verify_cmd)
    new_version = stdout.read().decode('utf-8').strip()
    
    if new_version.startswith('v20'):
        print(f"[OK] Node.js 已升级到: {new_version}")
        return True
    else:
        print(f"[ERROR] Node.js 升级失败，当前版本: {new_version}")
        return False

def configure_backend_env(ssh, deploy_dir):
    """配置后端 .env 文件"""
    print("\n[2/5] 配置后端 .env 文件...")
    
    backend_dir = f"{deploy_dir}/admin-backend"
    env_file = f"{backend_dir}/.env"
    
    # 检查 .env 文件是否存在
    stdin, stdout, stderr = ssh.exec_command(f"test -f {env_file} && echo 'exists' || echo 'not_exists'")
    exists = stdout.read().decode('utf-8').strip()
    
    if exists == 'exists':
        print("[INFO] .env 文件已存在，跳过创建")
        return True
    
    # 检查 .env.example 是否存在
    stdin, stdout, stderr = ssh.exec_command(f"test -f {backend_dir}/.env.example && echo 'exists' || echo 'not_exists'")
    example_exists = stdout.read().decode('utf-8').strip()
    
    if example_exists == 'exists':
        # 复制 .env.example 到 .env
        print("从 .env.example 创建 .env...")
        ssh.exec_command(f"cp {backend_dir}/.env.example {env_file}")
        print("[OK] .env 文件已创建（从 .env.example）")
        print("[WARNING] 请手动编辑 .env 文件配置数据库连接和密钥")
    else:
        # 创建基本的 .env 文件
        print("创建基本 .env 文件...")
        basic_env = """# 数据库配置
DATABASE_URL=postgresql://user:password@localhost:5432/smart_tg

# 安全密钥（请修改）
SECRET_KEY=your-secret-key-here-change-this-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Redis 配置（可选）
REDIS_URL=redis://localhost:6379/0

# CORS 配置
CORS_ORIGINS=["http://localhost:3000","http://localhost:8000"]

# 环境
ENVIRONMENT=production
"""
        stdin, stdout, stderr = ssh.exec_command(f"cat > {env_file} << 'EOF'\n{basic_env}EOF")
        stdout.read()
        print("[OK] .env 文件已创建（基本配置）")
        print("[WARNING] 请手动编辑 .env 文件配置数据库连接和密钥")
    
    return True

def configure_frontend_env(ssh, deploy_dir, server_ip):
    """配置前端 .env.local 文件"""
    print("\n[3/5] 配置前端 .env.local 文件...")
    
    frontend_dir = f"{deploy_dir}/saas-demo"
    env_file = f"{frontend_dir}/.env.local"
    
    # 检查 .env.local 文件是否存在
    stdin, stdout, stderr = ssh.exec_command(f"test -f {env_file} && echo 'exists' || echo 'not_exists'")
    exists = stdout.read().decode('utf-8').strip()
    
    if exists == 'exists':
        print("[INFO] .env.local 文件已存在")
        # 检查是否包含 API 地址
        stdin, stdout, stderr = ssh.exec_command(f"grep -q 'NEXT_PUBLIC_API_BASE_URL' {env_file} && echo 'has_api' || echo 'no_api'")
        has_api = stdout.read().decode('utf-8').strip()
        
        if has_api == 'no_api':
            print("添加 API 地址配置...")
            api_url = f"http://{server_ip}:8000/api/v1"
            ssh.exec_command(f"echo 'NEXT_PUBLIC_API_BASE_URL={api_url}' >> {env_file}")
            print(f"[OK] 已添加 API 地址: {api_url}")
        else:
            print("[OK] API 地址已配置")
        return True
    
    # 创建 .env.local 文件
    api_url = f"http://{server_ip}:8000/api/v1"
    env_content = f"""# API 配置
NEXT_PUBLIC_API_BASE_URL={api_url}
"""
    
    stdin, stdout, stderr = ssh.exec_command(f"cat > {env_file} << 'EOF'\n{env_content}EOF")
    stdout.read()
    print(f"[OK] .env.local 文件已创建")
    print(f"[OK] API 地址: {api_url}")
    
    return True

def rebuild_frontend(ssh, deploy_dir):
    """重新构建前端"""
    print("\n[4/5] 重新构建前端...")
    
    frontend_dir = f"{deploy_dir}/saas-demo"
    
    # 使用 nvm 加载 Node.js 20 并构建
    build_cmd = f'''cd {frontend_dir} && \
export NVM_DIR="$HOME/.nvm" && \
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh" && \
nvm use 20 && \
npm run build
'''
    
    print("执行构建命令...")
    stdin, stdout, stderr = ssh.exec_command(build_cmd, timeout=600)
    
    # 实时输出
    error_lines = []
    while True:
        line = stdout.readline()
        if not line:
            break
        print(f"  {line.rstrip()}")
    
    # 检查构建结果
    stdin, stdout, stderr = ssh.exec_command(f"test -d {frontend_dir}/.next && echo 'success' || echo 'failed'")
    result = stdout.read().decode('utf-8').strip()
    
    if result == 'success':
        print("[OK] 前端构建成功")
        return True
    else:
        error_output = stderr.read().decode('utf-8')
        if error_output:
            print(f"[ERROR] 构建错误: {error_output}")
        print("[ERROR] 前端构建失败")
        return False

def start_services(ssh):
    """启动服务"""
    print("\n[5/5] 启动服务...")
    
    # 启动后端服务
    print("启动后端服务...")
    stdin, stdout, stderr = ssh.exec_command("sudo systemctl start smart-tg-backend")
    stdout.read()
    
    stdin, stdout, stderr = ssh.exec_command("sudo systemctl enable smart-tg-backend")
    stdout.read()
    
    # 检查后端服务状态
    stdin, stdout, stderr = ssh.exec_command("sudo systemctl is-active smart-tg-backend")
    backend_status = stdout.read().decode('utf-8').strip()
    
    if backend_status == 'active':
        print("[OK] 后端服务已启动")
    else:
        print(f"[WARNING] 后端服务状态: {backend_status}")
        # 查看日志
        stdin, stdout, stderr = ssh.exec_command("sudo journalctl -u smart-tg-backend -n 10 --no-pager")
        logs = stdout.read().decode('utf-8')
        if logs:
            print("后端服务日志:")
            print(logs)
    
    # 启动前端服务
    print("启动前端服务...")
    stdin, stdout, stderr = ssh.exec_command("sudo systemctl start smart-tg-frontend")
    stdout.read()
    
    stdin, stdout, stderr = ssh.exec_command("sudo systemctl enable smart-tg-frontend")
    stdout.read()
    
    # 检查前端服务状态
    stdin, stdout, stderr = ssh.exec_command("sudo systemctl is-active smart-tg-frontend")
    frontend_status = stdout.read().decode('utf-8').strip()
    
    if frontend_status == 'active':
        print("[OK] 前端服务已启动")
    else:
        print(f"[WARNING] 前端服务状态: {frontend_status}")
        # 查看日志
        stdin, stdout, stderr = ssh.exec_command("sudo journalctl -u smart-tg-frontend -n 10 --no-pager")
        logs = stdout.read().decode('utf-8')
        if logs:
            print("前端服务日志:")
            print(logs)
    
    return True

def verify_services(ssh, server_ip):
    """验证服务"""
    print("\n验证服务状态...")
    
    # 检查服务状态
    stdin, stdout, stderr = ssh.exec_command("systemctl is-active smart-tg-backend smart-tg-frontend")
    status = stdout.read().decode('utf-8').strip()
    print(f"服务状态:\n{status}")
    
    # 健康检查
    print("\n健康检查:")
    stdin, stdout, stderr = ssh.exec_command("curl -s http://localhost:8000/health || echo '后端健康检查失败'")
    health = stdout.read().decode('utf-8').strip()
    print(f"后端: {health}")
    
    stdin, stdout, stderr = ssh.exec_command("curl -s -o /dev/null -w '%{http_code}' http://localhost:3000 || echo '前端不可访问'")
    frontend_code = stdout.read().decode('utf-8').strip()
    print(f"前端: HTTP {frontend_code}")

def main():
    print("=" * 50)
    print("完成部署 - 升级 Node.js、配置环境、启动服务")
    print("=" * 50)
    
    # 加载配置
    config = load_config()
    
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
        # 1. 升级 Node.js
        if not upgrade_nodejs(ssh):
            print("[ERROR] Node.js 升级失败，但继续执行其他步骤...")
        
        # 2. 配置后端 .env
        configure_backend_env(ssh, config['deploy_dir'])
        
        # 3. 配置前端 .env.local
        configure_frontend_env(ssh, config['deploy_dir'], config['host'])
        
        # 4. 重新构建前端
        if not rebuild_frontend(ssh, config['deploy_dir']):
            print("[ERROR] 前端构建失败，但继续启动服务...")
        
        # 5. 启动服务
        start_services(ssh)
        
        # 验证服务
        verify_services(ssh, config['host'])
        
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

