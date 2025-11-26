#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从 GitHub 自动部署到马尼拉服务器
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
    
    # 等待命令完成
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
    print("从 GitHub 自动部署到马尼拉服务器")
    print("=" * 70)
    print(f"\n服务器信息:")
    print(f"  主机: {config['host']}")
    print(f"  用户: {config['user']}")
    print(f"  部署目录: {config['deploy_dir']}")
    
    # 连接服务器
    ssh = connect_server(config['host'], config['user'], config['password'])
    if not ssh:
        print("\n无法连接到服务器")
        return
    
    try:
        deploy_dir = config['deploy_dir']
        project_dir = f"{deploy_dir}/聊天AI群聊程序"
        
        # 步骤1: 检查并安装必要工具
        print("\n" + "=" * 70)
        print("步骤 1: 检查环境")
        print("=" * 70)
        
        # 检查 git
        success, output, _ = execute_command(ssh, "which git", "检查 Git", check_output=False)
        if not success:
            print("  安装 Git...")
            execute_command(ssh, "sudo apt-get update && sudo apt-get install -y git", "安装 Git")
        
        # 检查 Node.js 和 nvm
        success, output, _ = execute_command(ssh, "source ~/.nvm/nvm.sh 2>/dev/null && nvm --version || echo 'not found'", "检查 nvm", check_output=True)
        if 'not found' in output or not success:
            print("  安装 nvm...")
            install_nvm = """
            curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
            export NVM_DIR="$HOME/.nvm"
            [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
            """
            execute_command(ssh, install_nvm, "安装 nvm")
        
        # 检查 Python 和 pip
        success, output, _ = execute_command(ssh, "python3 --version", "检查 Python3", check_output=True)
        if not success:
            execute_command(ssh, "sudo apt-get install -y python3 python3-pip python3-venv", "安装 Python3")
        
        # 步骤2: 从 GitHub 克隆或更新代码
        print("\n" + "=" * 70)
        print("步骤 2: 从 GitHub 获取代码")
        print("=" * 70)
        
        # 检查项目目录是否存在
        success, output, _ = execute_command(ssh, f"test -d {project_dir} && echo 'exists' || echo 'not exists'", "检查项目目录")
        
        if 'not exists' in output or not success:
            print("  项目目录不存在，需要从 GitHub 克隆")
            print("  请提供 GitHub 仓库 URL，或使用本地代码部署")
            print("\n  使用本地代码部署...")
            
            # 如果无法从 GitHub 克隆，使用本地代码
            # 这里我们假设用户会手动上传代码，或者我们可以使用 SCP
            print("  请确保代码已上传到服务器，或使用以下命令克隆:")
            print(f"    cd {deploy_dir}")
            print(f"    git clone <YOUR_GITHUB_REPO_URL> 聊天AI群聊程序")
        else:
            print("  项目目录存在，更新代码...")
            update_cmd = f"""
            cd {project_dir}
            git fetch origin
            git reset --hard origin/main || git reset --hard origin/master
            git pull
            """
            success, output, error = execute_command(ssh, update_cmd, "更新代码", check_output=True)
            if not success:
                print("  [WARNING] Git 更新失败，继续使用现有代码")
        
        # 步骤3: 部署后端
        print("\n" + "=" * 70)
        print("步骤 3: 部署后端")
        print("=" * 70)
        
        backend_dir = f"{project_dir}/admin-backend"
        
        # 检查后端目录
        success, output, _ = execute_command(ssh, f"test -d {backend_dir} && echo 'exists' || echo 'not exists'", "检查后端目录")
        
        if 'exists' in output:
            # 停止后端服务
            execute_command(ssh, "sudo systemctl stop smart-tg-backend 2>/dev/null || echo 'service not running'", "停止后端服务")
            time.sleep(2)
            
            # 创建虚拟环境
            venv_cmd = f"""
            cd {backend_dir}
            python3 -m venv .venv || true
            source .venv/bin/activate
            pip install --upgrade pip
            pip install -r requirements.txt || pip install fastapi uvicorn gunicorn sqlalchemy
            """
            execute_command(ssh, venv_cmd, "安装后端依赖", check_output=True)
            
            # 配置 .env 文件（如果不存在）
            env_check = f"test -f {backend_dir}/.env && echo 'exists' || echo 'not exists'"
            success, output, _ = execute_command(ssh, env_check, "检查 .env 文件")
            if 'not exists' in output:
                print("  创建基本 .env 文件...")
                basic_env = f"""
                cat > {backend_dir}/.env << 'EOF'
                # 数据库配置
                DATABASE_URL=sqlite:///./data/app.db
                # 安全配置
                SECRET_KEY=$(openssl rand -hex 32)
                # CORS 配置
                CORS_ORIGINS=["http://localhost:3000","http://{config['host']}:3000"]
                EOF
                """
                execute_command(ssh, basic_env, "创建 .env 文件")
            
            # 重启后端服务
            execute_command(ssh, "sudo systemctl restart smart-tg-backend", "重启后端服务")
            time.sleep(3)
            
            # 检查后端服务状态
            success, output, _ = execute_command(ssh, "systemctl is-active smart-tg-backend", "检查后端服务状态", check_output=True)
            if success and 'active' in output:
                print("  [OK] 后端服务已启动")
            else:
                print("  [WARNING] 后端服务可能未正常启动")
        else:
            print("  [WARNING] 后端目录不存在，跳过后端部署")
        
        # 步骤4: 部署前端
        print("\n" + "=" * 70)
        print("步骤 4: 部署前端")
        print("=" * 70)
        
        frontend_dir = f"{project_dir}/saas-demo"
        
        # 检查前端目录
        success, output, _ = execute_command(ssh, f"test -d {frontend_dir} && echo 'exists' || echo 'not exists'", "检查前端目录")
        
        if 'exists' in output:
            # 停止前端服务
            execute_command(ssh, "sudo systemctl stop smart-tg-frontend 2>/dev/null || echo 'service not running'", "停止前端服务")
            time.sleep(2)
            
            # 确保使用 Node.js 20
            node_cmd = f"""
            source ~/.nvm/nvm.sh
            nvm install 20 || true
            nvm use 20
            nvm alias default 20
            node --version
            """
            success, output, _ = execute_command(ssh, node_cmd, "设置 Node.js 20", check_output=True)
            
            # 安装依赖
            install_cmd = f"""
            cd {frontend_dir}
            source ~/.nvm/nvm.sh
            nvm use 20
            npm install
            """
            execute_command(ssh, install_cmd, "安装前端依赖", check_output=True)
            
            # 配置 .env.local
            env_local_check = f"test -f {frontend_dir}/.env.local && echo 'exists' || echo 'not exists'"
            success, output, _ = execute_command(ssh, env_local_check, "检查 .env.local 文件")
            if 'not exists' in output:
                print("  创建 .env.local 文件...")
                env_local = f"""
                cat > {frontend_dir}/.env.local << 'EOF'
                # API 配置
                NEXT_PUBLIC_API_BASE_URL=http://{config['host']}:8000/api/v1
                EOF
                """
                execute_command(ssh, env_local, "创建 .env.local 文件")
            
            # 重新构建前端
            build_cmd = f"""
            cd {frontend_dir}
            source ~/.nvm/nvm.sh
            nvm use 20
            npm run build
            """
            print("\n  开始构建前端（这可能需要几分钟）...")
            success, output, error = execute_command(ssh, build_cmd, "构建前端", check_output=True)
            
            if success:
                print("  [OK] 前端构建成功")
            else:
                print("  [ERROR] 前端构建失败")
                print("  错误信息:")
                if error:
                    for line in error.split('\n')[-20:]:  # 只显示最后20行
                        if line.strip():
                            print(f"    {line}")
            
            # 重启前端服务
            execute_command(ssh, "sudo systemctl restart smart-tg-frontend", "重启前端服务")
            time.sleep(5)
            
            # 检查前端服务状态
            success, output, _ = execute_command(ssh, "systemctl is-active smart-tg-frontend", "检查前端服务状态", check_output=True)
            if success and 'active' in output:
                print("  [OK] 前端服务已启动")
            else:
                print("  [WARNING] 前端服务可能未正常启动")
                print("  查看日志:")
                execute_command(ssh, "sudo journalctl -u smart-tg-frontend -n 20 --no-pager", "查看前端服务日志", check_output=True)
        else:
            print("  [WARNING] 前端目录不存在，跳过前端部署")
        
        # 步骤5: 验证部署
        print("\n" + "=" * 70)
        print("步骤 5: 验证部署")
        print("=" * 70)
        
        # 检查服务状态
        print("\n检查服务状态...")
        execute_command(ssh, "systemctl status smart-tg-backend smart-tg-frontend --no-pager -l", "服务状态", check_output=True)
        
        # 检查端口
        print("\n检查端口监听...")
        execute_command(ssh, "sudo ss -tlnp | grep -E ':8000|:3000'", "端口监听", check_output=True)
        
        # 健康检查
        print("\n健康检查...")
        execute_command(ssh, "curl -s http://localhost:8000/health || echo 'backend health check failed'", "后端健康检查", check_output=True)
        execute_command(ssh, "curl -s -o /dev/null -w '%{http_code}' http://localhost:3000 || echo '000'", "前端健康检查", check_output=True)
        
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
        ssh.close()

if __name__ == "__main__":
    main()

