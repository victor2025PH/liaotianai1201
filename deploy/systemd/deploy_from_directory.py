#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从指定目录部署到马尼拉服务器
"""

import json
import paramiko
import sys
import time
import os
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
    
    manila_config = config.get('servers', {}).get('manila', {})
    
    return {
        'host': manila_config.get('host', '165.154.233.55'),
        'user': manila_config.get('user', 'ubuntu'),
        'password': manila_config.get('password', 'Along2025!!!'),
        'deploy_dir': manila_config.get('deploy_dir', '/home/ubuntu'),
    }

def connect_server(host, user, password):
    """连接服务器"""
    print(f"连接服务器: {host}...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(host, username=user, password=password, timeout=15)
        print("[OK] 连接成功")
        return ssh
    except Exception as e:
        print(f"[ERROR] 连接失败: {e}")
        return None

def execute_command(ssh, command, description, check_output=False):
    """执行命令并显示输出"""
    print(f"\n{description}...")
    stdin, stdout, stderr = ssh.exec_command(command)
    exit_status = stdout.channel.recv_exit_status()
    
    output = stdout.read().decode('utf-8', errors='replace').strip()
    error = stderr.read().decode('utf-8', errors='replace').strip()
    
    if check_output or exit_status != 0:
        if output:
            for line in output.split('\n'):
                if line.strip():
                    print(f"  {line}")
        if error:
            for line in error.split('\n'):
                if line.strip():
                    print(f"  [ERROR] {line}")
    
    return exit_status == 0, output, error

def main():
    config = load_config()
    
    print("=" * 70)
    print("从本地目录部署到马尼拉服务器")
    print("=" * 70)
    
    # 询问代码目录路径
    print("\n请提供代码目录的完整路径")
    print("例如: E:\\002-工作文件\\重要程序\\liaotian20251126")
    print("或者: /path/to/liaotian20251126")
    
    code_dir = input("\n请输入代码目录路径（直接回车使用默认路径）: ").strip()
    
    if not code_dir:
        # 尝试常见路径
        possible_paths = [
            r"E:\002-工作文件\重要程序\liaotian20251126",
            r"C:\liaotian20251126",
            "liaotian20251126",
        ]
        for path in possible_paths:
            if os.path.exists(path):
                code_dir = path
                print(f"使用找到的路径: {code_dir}")
                break
        else:
            print("[ERROR] 未找到代码目录，请手动输入路径")
            return
    
    code_path = Path(code_dir)
    if not code_path.exists():
        print(f"[ERROR] 目录不存在: {code_dir}")
        return
    
    print(f"\n代码目录: {code_path}")
    
    # 检查关键目录
    admin_backend = code_path / "admin-backend"
    saas_demo = code_path / "saas-demo"
    
    if not admin_backend.exists():
        # 检查是否有压缩包
        admin_backend_zip = code_path / "admin-backend.zip"
        full_backend_zip = code_path / "full-backend.zip"
        if admin_backend_zip.exists() or full_backend_zip.exists():
            print(f"[INFO] 发现后端压缩包，需要先解压")
        else:
            print(f"[WARNING] 未找到 admin-backend 目录")
    
    if not saas_demo.exists():
        frontend_zip = code_path / "frontend.zip"
        if frontend_zip.exists():
            print(f"[INFO] 发现前端压缩包，需要先解压")
        else:
            print(f"[WARNING] 未找到 saas-demo 目录")
    
    # 连接服务器
    ssh = connect_server(config['host'], config['user'], config['password'])
    if not ssh:
        return
    
    sftp = ssh.open_sftp()
    
    try:
        deploy_dir = config['deploy_dir']
        remote_project_dir = f"{deploy_dir}/smart-tg"
        
        print("\n" + "=" * 70)
        print("步骤 1: 准备服务器环境")
        print("=" * 70)
        
        # 检查并创建目录
        execute_command(ssh, f"mkdir -p {remote_project_dir}", "创建项目目录")
        
        # 检查 Node.js
        success, output, _ = execute_command(ssh, "source ~/.nvm/nvm.sh 2>/dev/null && nvm use 20 2>&1 && node --version || echo 'not found'", "检查 Node.js", check_output=True)
        if 'not found' in output or 'v20' not in output:
            print("  安装 Node.js 20...")
            install_nvm = """
            curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
            export NVM_DIR="$HOME/.nvm"
            [ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"
            nvm install 20
            nvm use 20
            nvm alias default 20
            """
            execute_command(ssh, install_nvm, "安装 Node.js 20")
        
        print("\n" + "=" * 70)
        print("步骤 2: 上传代码")
        print("=" * 70)
        
        # 这里需要用户确认上传方式
        print("\n请选择上传方式:")
        print("1. 使用 SCP 上传整个目录（推荐，但需要时间）")
        print("2. 使用 tar 压缩后上传")
        print("3. 手动上传（提供命令）")
        
        choice = input("\n请选择 (1/2/3，默认1): ").strip() or "1"
        
        if choice == "1":
            print("\n使用 SCP 上传...")
            print("这可能需要一些时间，请耐心等待...")
            # 这里应该使用 subprocess 调用 scp，但为了简化，我们提供命令
            print(f"\n请在另一个终端执行以下命令:")
            print(f"scp -r \"{code_path}\"/* {config['user']}@{config['host']}:{remote_project_dir}/")
            input("\n上传完成后按 Enter 继续...")
        
        elif choice == "2":
            print("\n创建压缩包并上传...")
            # 创建临时压缩包
            import tempfile
            import tarfile
            with tempfile.NamedTemporaryFile(suffix='.tar.gz', delete=False) as tmp:
                tar_path = tmp.name
            
            print(f"  创建压缩包: {tar_path}")
            with tarfile.open(tar_path, 'w:gz') as tar:
                tar.add(code_path, arcname=os.path.basename(code_path))
            
            print(f"  上传压缩包...")
            remote_tar = f"{remote_project_dir}/code.tar.gz"
            sftp.put(tar_path, remote_tar)
            
            print(f"  解压...")
            execute_command(ssh, f"cd {deploy_dir} && tar -xzf {remote_tar} && mv {os.path.basename(code_path)}/* {remote_project_dir}/ || true", "解压代码")
            
            os.unlink(tar_path)
        
        else:
            print("\n请手动上传代码到服务器")
            print(f"  目标目录: {remote_project_dir}")
            input("\n上传完成后按 Enter 继续...")
        
        # 步骤3: 部署后端
        print("\n" + "=" * 70)
        print("步骤 3: 部署后端")
        print("=" * 70)
        
        remote_backend = f"{remote_project_dir}/admin-backend"
        success, output, _ = execute_command(ssh, f"test -d {remote_backend} && echo 'exists' || echo 'not exists'", "检查后端目录")
        
        if 'exists' in output:
            execute_command(ssh, "sudo systemctl stop smart-tg-backend 2>/dev/null || echo 'stopped'", "停止后端服务")
            
            # 安装依赖
            venv_cmd = f"""
            cd {remote_backend}
            python3 -m venv .venv || true
            source .venv/bin/activate
            pip install --upgrade pip
            pip install -r requirements.txt 2>&1 || pip install fastapi uvicorn gunicorn sqlalchemy pydantic
            """
            execute_command(ssh, venv_cmd, "安装后端依赖", check_output=True)
            
            # 配置 .env
            env_file = f"{remote_backend}/.env"
            env_content = f"""
DATABASE_URL=sqlite:///./data/app.db
SECRET_KEY=$(openssl rand -hex 32)
CORS_ORIGINS=["http://localhost:3000","http://{config['host']}:3000"]
"""
            execute_command(ssh, f"cat > {env_file} << 'ENVEOF'\n{env_content}ENVEOF", "配置 .env 文件")
            
            # 重启服务
            execute_command(ssh, "sudo systemctl restart smart-tg-backend || sudo systemctl start smart-tg-backend", "启动后端服务")
            time.sleep(3)
        
        # 步骤4: 部署前端
        print("\n" + "=" * 70)
        print("步骤 4: 部署前端")
        print("=" * 70)
        
        remote_frontend = f"{remote_project_dir}/saas-demo"
        success, output, _ = execute_command(ssh, f"test -d {remote_frontend} && echo 'exists' || echo 'not exists'", "检查前端目录")
        
        if 'exists' in output:
            execute_command(ssh, "sudo systemctl stop smart-tg-frontend 2>/dev/null || echo 'stopped'", "停止前端服务")
            
            # 确保使用 Node.js 20
            node_cmd = f"""
            source ~/.nvm/nvm.sh
            nvm use 20
            cd {remote_frontend}
            npm install
            """
            execute_command(ssh, node_cmd, "安装前端依赖", check_output=True)
            
            # 配置 .env.local
            env_local = f"{remote_frontend}/.env.local"
            env_local_content = f"NEXT_PUBLIC_API_BASE_URL=http://{config['host']}:8000/api/v1\n"
            execute_command(ssh, f"echo '{env_local_content}' > {env_local}", "配置 .env.local")
            
            # 构建前端
            build_cmd = f"""
            source ~/.nvm/nvm.sh
            nvm use 20
            cd {remote_frontend}
            npm run build
            """
            print("\n  开始构建前端（这可能需要几分钟）...")
            success, output, error = execute_command(ssh, build_cmd, "构建前端", check_output=True)
            
            if success:
                print("  [OK] 前端构建成功")
            else:
                print("  [WARNING] 前端构建可能有问题")
            
            # 重启服务
            execute_command(ssh, "sudo systemctl restart smart-tg-frontend || sudo systemctl start smart-tg-frontend", "启动前端服务")
            time.sleep(5)
        
        # 步骤5: 验证
        print("\n" + "=" * 70)
        print("步骤 5: 验证部署")
        print("=" * 70)
        
        execute_command(ssh, "systemctl status smart-tg-backend smart-tg-frontend --no-pager -l | head -20", "服务状态", check_output=True)
        execute_command(ssh, "sudo ss -tlnp | grep -E ':8000|:3000'", "端口监听", check_output=True)
        execute_command(ssh, "curl -s http://localhost:8000/health || echo 'backend check failed'", "后端健康检查", check_output=True)
        execute_command(ssh, "curl -s -o /dev/null -w '%{http_code}' http://localhost:3000 || echo '000'", "前端健康检查", check_output=True)
        
        print("\n" + "=" * 70)
        print("部署完成！")
        print("=" * 70)
        print(f"\n访问地址:")
        print(f"  前端: http://{config['host']}:3000")
        print(f"  后端: http://{config['host']}:8000")
        
    finally:
        sftp.close()
        ssh.close()

if __name__ == "__main__":
    main()

