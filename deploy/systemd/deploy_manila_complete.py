#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
完整部署到马尼拉服务器 - 从指定目录
"""

import json
import paramiko
import sys
import time
import tarfile
import io
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

def execute_command(ssh, command, description, show_output=True):
    """执行命令"""
    if show_output:
        print(f"\n{description}...")
    stdin, stdout, stderr = ssh.exec_command(command)
    exit_status = stdout.channel.recv_exit_status()
    
    output = stdout.read().decode('utf-8', errors='replace').strip()
    error = stderr.read().decode('utf-8', errors='replace').strip()
    
    if show_output and (output or error or exit_status != 0):
        if output:
            for line in output.split('\n')[:50]:  # 限制输出行数
                if line.strip():
                    print(f"  {line}")
        if error and exit_status != 0:
            for line in error.split('\n')[:20]:
                if line.strip():
                    print(f"  [ERROR] {line}")
    
    return exit_status == 0, output, error

def upload_directory(sftp, local_dir, remote_dir, ssh):
    """上传目录到服务器"""
    local_path = Path(local_dir)
    
    print(f"\n准备上传: {local_path} -> {remote_dir}")
    
    # 创建远程目录
    execute_command(ssh, f"mkdir -p {remote_dir}", "创建远程目录", show_output=False)
    
    # 使用 tar 压缩并上传
    print("  创建压缩包...")
    tar_buffer = io.BytesIO()
    
    with tarfile.open(fileobj=tar_buffer, mode='w:gz') as tar:
        tar.add(local_path, arcname=local_path.name, recursive=True)
    
    tar_buffer.seek(0)
    tar_size = len(tar_buffer.getvalue())
    print(f"  压缩包大小: {tar_size / 1024 / 1024:.2f} MB")
    
    # 上传压缩包
    remote_tar = f"{remote_dir}/upload.tar.gz"
    print(f"  上传到: {remote_tar}")
    
    with sftp.open(remote_tar, 'wb') as f:
        f.write(tar_buffer.getvalue())
    
    print("  [OK] 上传完成")
    
    # 解压
    print("  解压...")
    execute_command(ssh, f"cd {remote_dir} && tar -xzf {remote_tar} && rm -f {remote_tar}", "解压文件")
    
    return f"{remote_dir}/{local_path.name}"

def main():
    config = load_config()
    code_dir = Path(r"C:\Users\Administrator\Desktop\liaotian20251126")
    
    print("=" * 70)
    print("完整部署到马尼拉服务器")
    print("=" * 70)
    print(f"\n代码目录: {code_dir}")
    print(f"服务器: {config['host']}")
    
    if not code_dir.exists():
        print(f"[ERROR] 代码目录不存在: {code_dir}")
        return
    
    # 检查关键目录
    admin_backend = code_dir / "admin-backend"
    saas_demo = code_dir / "saas-demo"
    
    print(f"\n检查代码结构...")
    print(f"  后端目录: {'存在' if admin_backend.exists() else '不存在'}")
    print(f"  前端目录: {'存在' if saas_demo.exists() else '不存在'}")
    
    # 连接服务器
    ssh = connect_server(config['host'], config['user'], config['password'])
    if not ssh:
        return
    
    sftp = ssh.open_sftp()
    
    try:
        deploy_dir = config['deploy_dir']
        remote_project_dir = f"{deploy_dir}/smart-tg"
        
        # 步骤1: 准备环境
        print("\n" + "=" * 70)
        print("步骤 1: 准备服务器环境")
        print("=" * 70)
        
        # 安装必要工具
        execute_command(ssh, "which git || sudo apt-get update && sudo apt-get install -y git", "检查 Git")
        
        # 安装 Node.js 20
        node_check = "source ~/.nvm/nvm.sh 2>/dev/null && nvm use 20 2>&1 && node --version || echo 'not found'"
        success, output, _ = execute_command(ssh, node_check, "检查 Node.js", show_output=False)
        
        if 'not found' in output or 'v20' not in output:
            print("  安装 nvm 和 Node.js 20...")
            install_cmd = """
            curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
            export NVM_DIR="$HOME/.nvm"
            [ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"
            nvm install 20
            nvm use 20
            nvm alias default 20
            """
            execute_command(ssh, install_cmd, "安装 Node.js 20")
        
        # 步骤2: 上传代码
        print("\n" + "=" * 70)
        print("步骤 2: 上传代码")
        print("=" * 70)
        
        print("  这可能需要几分钟，请耐心等待...")
        remote_code_dir = upload_directory(sftp, code_dir, deploy_dir, ssh)
        print(f"  [OK] 代码已上传到: {remote_code_dir}")
        
        # 步骤3: 部署后端
        print("\n" + "=" * 70)
        print("步骤 3: 部署后端")
        print("=" * 70)
        
        remote_backend = f"{remote_code_dir}/admin-backend"
        success, output, _ = execute_command(ssh, f"test -d {remote_backend} && echo 'exists'", "检查后端目录", show_output=False)
        
        if 'exists' in output:
            # 停止服务
            execute_command(ssh, "sudo systemctl stop smart-tg-backend 2>/dev/null || echo 'stopped'", "停止后端服务")
            time.sleep(2)
            
            # 创建虚拟环境并安装依赖
            venv_cmd = f"""
            cd {remote_backend}
            python3 -m venv .venv || true
            source .venv/bin/activate
            pip install --upgrade pip -q
            pip install -r requirements.txt 2>&1 | tail -20 || pip install fastapi uvicorn[standard] gunicorn sqlalchemy pydantic
            """
            execute_command(ssh, venv_cmd, "安装后端依赖")
            
            # 配置 .env
            env_content = f"""DATABASE_URL=sqlite:///./data/app.db
SECRET_KEY=$(openssl rand -hex 32)
CORS_ORIGINS=["http://localhost:3000","http://{config['host']}:3000"]
"""
            execute_command(ssh, f"mkdir -p {remote_backend} && cat > {remote_backend}/.env << 'ENVEOF'\n{env_content}ENVEOF", "配置 .env")
            
            # 启动服务
            execute_command(ssh, "sudo systemctl restart smart-tg-backend || sudo systemctl start smart-tg-backend", "启动后端服务")
            time.sleep(3)
            
            success, output, _ = execute_command(ssh, "systemctl is-active smart-tg-backend", "检查后端服务", show_output=False)
            if 'active' in output:
                print("  [OK] 后端服务已启动")
            else:
                print("  [WARNING] 后端服务可能未启动，查看日志:")
                execute_command(ssh, "sudo journalctl -u smart-tg-backend -n 10 --no-pager", "后端日志")
        else:
            print("  [WARNING] 后端目录不存在，跳过后端部署")
        
        # 步骤4: 部署前端
        print("\n" + "=" * 70)
        print("步骤 4: 部署前端")
        print("=" * 70)
        
        remote_frontend = f"{remote_code_dir}/saas-demo"
        success, output, _ = execute_command(ssh, f"test -d {remote_frontend} && echo 'exists'", "检查前端目录", show_output=False)
        
        if 'exists' in output:
            # 停止服务
            execute_command(ssh, "sudo systemctl stop smart-tg-frontend 2>/dev/null || echo 'stopped'", "停止前端服务")
            time.sleep(2)
            
            # 安装依赖
            install_cmd = f"""
            source ~/.nvm/nvm.sh
            nvm use 20
            cd {remote_frontend}
            npm install 2>&1 | tail -30
            """
            execute_command(ssh, install_cmd, "安装前端依赖")
            
            # 配置 .env.local
            env_local_content = f"NEXT_PUBLIC_API_BASE_URL=http://{config['host']}:8000/api/v1"
            execute_command(ssh, f"echo '{env_local_content}' > {remote_frontend}/.env.local", "配置 .env.local")
            
            # 构建前端
            build_cmd = f"""
            source ~/.nvm/nvm.sh
            nvm use 20
            cd {remote_frontend}
            npm run build 2>&1 | tail -50
            """
            print("\n  开始构建前端（这可能需要几分钟）...")
            success, output, error = execute_command(ssh, build_cmd, "构建前端")
            
            if success:
                print("  [OK] 前端构建成功")
            else:
                print("  [WARNING] 前端构建可能有问题")
                if error:
                    print("  错误信息:")
                    for line in error.split('\n')[-10:]:
                        if line.strip():
                            print(f"    {line}")
            
            # 启动服务
            execute_command(ssh, "sudo systemctl restart smart-tg-frontend || sudo systemctl start smart-tg-frontend", "启动前端服务")
            time.sleep(5)
            
            success, output, _ = execute_command(ssh, "systemctl is-active smart-tg-frontend", "检查前端服务", show_output=False)
            if 'active' in output:
                print("  [OK] 前端服务已启动")
            else:
                print("  [WARNING] 前端服务可能未启动，查看日志:")
                execute_command(ssh, "sudo journalctl -u smart-tg-frontend -n 15 --no-pager", "前端日志")
        else:
            print("  [WARNING] 前端目录不存在，跳过前端部署")
        
        # 步骤5: 验证
        print("\n" + "=" * 70)
        print("步骤 5: 验证部署")
        print("=" * 70)
        
        execute_command(ssh, "systemctl status smart-tg-backend smart-tg-frontend --no-pager -l | head -30", "服务状态")
        execute_command(ssh, "sudo ss -tlnp | grep -E ':8000|:3000'", "端口监听")
        
        success, output, _ = execute_command(ssh, "curl -s http://localhost:8000/health", "后端健康检查", show_output=False)
        if 'ok' in output.lower():
            print("  [OK] 后端健康检查通过")
        else:
            print(f"  [WARNING] 后端健康检查: {output}")
        
        success, output, _ = execute_command(ssh, "curl -s -o /dev/null -w '%{http_code}' http://localhost:3000", "前端健康检查", show_output=False)
        if output == '200':
            print("  [OK] 前端健康检查通过")
        else:
            print(f"  [WARNING] 前端健康检查: HTTP {output}")
        
        print("\n" + "=" * 70)
        print("部署完成！")
        print("=" * 70)
        print(f"\n访问地址:")
        print(f"  前端: http://{config['host']}:3000")
        print(f"  后端: http://{config['host']}:8000")
        print(f"  API 文档: http://{config['host']}:8000/docs")
        print(f"\n如果前端仍然卡在认证检查，请:")
        print(f"  1. 清除浏览器缓存")
        print(f"  2. 在浏览器控制台执行: localStorage.clear()")
        print(f"  3. 刷新页面")
        
    except Exception as e:
        print(f"\n[ERROR] 部署过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        sftp.close()
        ssh.close()

if __name__ == "__main__":
    main()

