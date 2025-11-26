#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
完成马尼拉服务器部署
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
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(host, username=user, password=password, timeout=15)
    return ssh

def execute_command(ssh, command, description, show_output=True):
    """执行命令"""
    if show_output:
        print(f"\n{description}...")
    stdin, stdout, stderr = ssh.exec_command(command)
    exit_status = stdout.channel.recv_exit_status()
    
    output = stdout.read().decode('utf-8', errors='replace').strip()
    error = stderr.read().decode('utf-8', errors='replace').strip()
    
    if show_output:
        if output:
            for line in output.split('\n')[:40]:
                if line.strip():
                    print(f"  {line}")
        if error and exit_status != 0:
            for line in error.split('\n')[:20]:
                if line.strip():
                    print(f"  [ERROR] {line}")
    
    return exit_status == 0, output, error

def main():
    config = load_config()
    
    print("=" * 70)
    print("完成马尼拉服务器部署")
    print("=" * 70)
    
    ssh = connect_server(config['host'], config['user'], config['password'])
    
    try:
        code_dir = "/home/ubuntu/liaotian20251126"
        deploy_dir = config['deploy_dir']
        
        # 步骤1: 部署后端
        print("\n" + "=" * 70)
        print("步骤 1: 部署后端")
        print("=" * 70)
        
        # 使用 full-backend-deploy（更完整）
        backend_source = f"{code_dir}/full-backend-deploy"
        backend_target = f"{deploy_dir}/admin-backend"
        
        print(f"\n后端源目录: {backend_source}")
        print(f"后端目标目录: {backend_target}")
        
        # 停止服务
        execute_command(ssh, "sudo systemctl stop admin-backend 2>/dev/null || sudo systemctl stop smart-tg-backend 2>/dev/null || echo 'stopped'", "停止后端服务")
        time.sleep(2)
        
        # 备份旧目录
        execute_command(ssh, f"test -d {backend_target} && mv {backend_target} {backend_target}.backup.$(date +%Y%m%d_%H%M%S) || echo 'no backup needed'", "备份旧后端")
        
        # 复制新代码
        execute_command(ssh, f"cp -r {backend_source} {backend_target}", "复制后端代码")
        
        # 创建虚拟环境
        venv_cmd = f"""
        cd {backend_target}
        python3 -m venv .venv || python3 -m venv venv
        source .venv/bin/activate || source venv/bin/activate
        pip install --upgrade pip -q
        pip install -r requirements.txt 2>&1 | tail -30
        """
        execute_command(ssh, venv_cmd, "安装后端依赖")
        
        # 配置 .env
        env_file = f"{backend_target}/.env"
        env_content = f"""DATABASE_URL=sqlite:///./data/app.db
SECRET_KEY=$(openssl rand -hex 32)
CORS_ORIGINS=["http://localhost:3000","http://{config['host']}:3000","http://{config['host']}:8000"]
"""
        execute_command(ssh, f"cat > {env_file} << 'ENVEOF'\n{env_content}ENVEOF", "配置 .env")
        
        # 启动服务
        execute_command(ssh, "sudo systemctl restart admin-backend || sudo systemctl start admin-backend", "启动后端服务")
        time.sleep(5)
        
        success, output, _ = execute_command(ssh, "systemctl is-active admin-backend", "检查后端服务", show_output=False)
        if 'active' in output:
            print("  [OK] 后端服务已启动")
        else:
            print("  [WARNING] 后端服务可能未启动")
            execute_command(ssh, "sudo journalctl -u admin-backend -n 20 --no-pager", "查看后端日志")
        
        # 步骤2: 部署前端
        print("\n" + "=" * 70)
        print("步骤 2: 部署前端")
        print("=" * 70)
        
        frontend_zip = f"{code_dir}/frontend.zip"
        frontend_target = f"{deploy_dir}/saas-demo"
        
        print(f"\n前端压缩包: {frontend_zip}")
        print(f"前端目标目录: {frontend_target}")
        
        # 停止服务
        execute_command(ssh, "sudo systemctl stop smart-tg-frontend 2>/dev/null || echo 'stopped'", "停止前端服务")
        time.sleep(2)
        
        # 备份旧目录
        execute_command(ssh, f"test -d {frontend_target} && mv {frontend_target} {frontend_target}.backup.$(date +%Y%m%d_%H%M%S) || echo 'no backup needed'", "备份旧前端")
        
        # 解压前端
        execute_command(ssh, f"cd {deploy_dir} && unzip -q {frontend_zip} -d . && mv saas-demo* saas-demo 2>/dev/null || unzip -q {frontend_zip} -d {deploy_dir}", "解压前端代码")
        
        # 确保使用 Node.js 20
        node_cmd = """
        source ~/.nvm/nvm.sh
        nvm use 20 || nvm install 20 && nvm use 20
        node --version
        """
        execute_command(ssh, node_cmd, "确保使用 Node.js 20")
        
        # 安装依赖
        install_cmd = f"""
        source ~/.nvm/nvm.sh
        nvm use 20
        cd {frontend_target}
        npm install 2>&1 | tail -30
        """
        execute_command(ssh, install_cmd, "安装前端依赖")
        
        # 配置 .env.local
        env_local = f"{frontend_target}/.env.local"
        env_local_content = f"NEXT_PUBLIC_API_BASE_URL=http://{config['host']}:8000/api/v1"
        execute_command(ssh, f"echo '{env_local_content}' > {env_local}", "配置 .env.local")
        
        # 构建前端
        build_cmd = f"""
        source ~/.nvm/nvm.sh
        nvm use 20
        cd {frontend_target}
        npm run build 2>&1 | tail -50
        """
        print("\n  开始构建前端（这可能需要几分钟）...")
        success, output, error = execute_command(ssh, build_cmd, "构建前端")
        
        if success:
            print("  [OK] 前端构建成功")
        else:
            print("  [WARNING] 前端构建可能有问题")
        
        # 启动服务
        execute_command(ssh, "sudo systemctl restart smart-tg-frontend || sudo systemctl start smart-tg-frontend", "启动前端服务")
        time.sleep(5)
        
        success, output, _ = execute_command(ssh, "systemctl is-active smart-tg-frontend", "检查前端服务", show_output=False)
        if 'active' in output:
            print("  [OK] 前端服务已启动")
        else:
            print("  [WARNING] 前端服务可能未启动")
            execute_command(ssh, "sudo journalctl -u smart-tg-frontend -n 20 --no-pager", "查看前端日志")
        
        # 步骤3: 验证部署
        print("\n" + "=" * 70)
        print("步骤 3: 验证部署")
        print("=" * 70)
        
        execute_command(ssh, "systemctl status admin-backend smart-tg-frontend --no-pager -l | head -40", "服务状态")
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
        ssh.close()

if __name__ == "__main__":
    main()

