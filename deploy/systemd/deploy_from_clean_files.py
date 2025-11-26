#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从清理后的文件部署到马尼拉服务器
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
    }

def connect_server(host, user, password):
    """连接服务器"""
    print(f"连接服务器: {host}...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(host, username=user, password=password, timeout=15)
    print("[OK] 连接成功")
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
            for line in output.split('\n')[:50]:
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
    print("从清理后的文件部署到马尼拉服务器")
    print("=" * 70)
    print(f"\n服务器: {config['host']}")
    
    ssh = connect_server(config['host'], config['user'], config['password'])
    
    try:
        deploy_dir = "/home/ubuntu"
        
        # 步骤1: 检查上传的文件
        print("\n" + "=" * 70)
        print("步骤 1: 检查上传的文件")
        print("=" * 70)
        
        execute_command(ssh, f"ls -lh {deploy_dir}/*.tar.gz {deploy_dir}/*.zip 2>/dev/null | grep -E 'admin-backend|frontend'", "检查上传的文件")
        
        # 检查文件是否存在
        success, output, _ = execute_command(ssh, f"test -f {deploy_dir}/admin-backend-deploy-clean.tar.gz && echo 'exists' || echo 'not found'", "检查后端压缩包", show_output=False)
        if 'not found' in output:
            print("[ERROR] 后端压缩包未找到: admin-backend-deploy-clean.tar.gz")
            print("请确认文件已上传")
            return
        
        success, output, _ = execute_command(ssh, f"test -f {deploy_dir}/frontend.zip && echo 'exists' || echo 'not found'", "检查前端压缩包", show_output=False)
        if 'not found' in output:
            print("[ERROR] 前端压缩包未找到: frontend.zip")
            print("请确认文件已上传")
            return
        
        print("[OK] 所有文件已找到")
        
        # 步骤2: 停止旧服务
        print("\n" + "=" * 70)
        print("步骤 2: 停止旧服务")
        print("=" * 70)
        
        execute_command(ssh, "sudo systemctl stop admin-backend smart-tg-frontend 2>/dev/null || pkill -f 'uvicorn|next-server' || echo 'services stopped'", "停止服务")
        time.sleep(3)
        
        # 步骤3: 清理旧目录
        print("\n" + "=" * 70)
        print("步骤 3: 清理旧目录")
        print("=" * 70)
        
        execute_command(ssh, "rm -rf /home/ubuntu/admin-backend /home/ubuntu/saas-demo /home/ubuntu/liaotian20251126 2>/dev/null || echo 'cleaned'", "清理旧目录")
        
        # 步骤4: 部署后端
        print("\n" + "=" * 70)
        print("步骤 4: 部署后端")
        print("=" * 70)
        
        # 解压后端
        execute_command(ssh, f"cd {deploy_dir} && tar -xzf admin-backend-deploy-clean.tar.gz", "解压后端代码")
        
        # 检查解压后的目录名
        success, output, _ = execute_command(ssh, "ls -d /home/ubuntu/admin-backend* 2>/dev/null | head -1", "查找后端目录", show_output=False)
        if output and 'admin-backend' not in output.strip():
            backend_dir = output.strip()
            execute_command(ssh, f"mv {backend_dir} /home/ubuntu/admin-backend", "重命名后端目录")
        
        backend_dir = "/home/ubuntu/admin-backend"
        
        # 创建虚拟环境
        venv_cmd = f"""
        cd {backend_dir}
        python3 -m venv .venv
        source .venv/bin/activate
        pip install --upgrade pip -q
        pip install -r requirements.txt 2>&1 | tail -30
        """
        execute_command(ssh, venv_cmd, "安装后端依赖")
        
        # 配置 .env
        env_content = f"""DATABASE_URL=sqlite:///./data/app.db
SECRET_KEY=$(openssl rand -hex 32)
CORS_ORIGINS=["http://localhost:3000","http://{config['host']}:3000","http://{config['host']}:8000"]
"""
        execute_command(ssh, f"cat > {backend_dir}/.env << 'ENVEOF'\n{env_content}ENVEOF", "配置 .env")
        
        # 配置 systemd 服务
        service_config = """
        sudo tee /etc/systemd/system/admin-backend.service > /dev/null << 'EOF'
[Unit]
Description=Smart TG Admin Backend
After=network.target

[Service]
Type=simple
User=ubuntu
Group=ubuntu
WorkingDirectory=/home/ubuntu/admin-backend
Environment="PATH=/home/ubuntu/admin-backend/.venv/bin:/usr/local/bin:/usr/bin:/bin"
EnvironmentFile=-/home/ubuntu/admin-backend/.env
ExecStart=/home/ubuntu/admin-backend/.venv/bin/python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF
        sudo systemctl daemon-reload
        """
        execute_command(ssh, service_config, "配置 systemd 服务")
        
        # 启动后端服务
        execute_command(ssh, "sudo systemctl restart admin-backend", "启动后端服务")
        time.sleep(5)
        
        success, output, _ = execute_command(ssh, "systemctl is-active admin-backend", "检查后端服务", show_output=False)
        if 'active' in output:
            print("  [OK] 后端服务已启动")
        else:
            print("  [WARNING] 后端服务可能未启动")
            execute_command(ssh, "sudo journalctl -u admin-backend -n 20 --no-pager", "查看后端日志")
        
        # 步骤5: 部署前端
        print("\n" + "=" * 70)
        print("步骤 5: 部署前端")
        print("=" * 70)
        
        # 解压前端
        execute_command(ssh, f"cd {deploy_dir} && unzip -q -o frontend.zip", "解压前端代码")
        
        # 检查解压后的目录名
        success, output, _ = execute_command(ssh, "ls -d /home/ubuntu/saas-demo* 2>/dev/null | head -1", "查找前端目录", show_output=False)
        if output and 'saas-demo' not in output.strip():
            frontend_dir = output.strip()
            execute_command(ssh, f"mv {frontend_dir} /home/ubuntu/saas-demo", "重命名前端目录")
        
        frontend_dir = "/home/ubuntu/saas-demo"
        
        # 确保使用 Node.js 20
        node_cmd = """
        source ~/.nvm/nvm.sh
        nvm use 20 || (nvm install 20 && nvm use 20)
        node --version
        """
        execute_command(ssh, node_cmd, "确保使用 Node.js 20")
        
        # 安装依赖
        install_cmd = f"""
        source ~/.nvm/nvm.sh
        nvm use 20
        cd {frontend_dir}
        npm install 2>&1 | tail -30
        """
        execute_command(ssh, install_cmd, "安装前端依赖")
        
        # 配置 .env.local
        env_local_content = f"NEXT_PUBLIC_API_BASE_URL=http://{config['host']}:8000/api/v1"
        execute_command(ssh, f"echo '{env_local_content}' > {frontend_dir}/.env.local", "配置 .env.local")
        
        # 构建前端
        build_cmd = f"""
        source ~/.nvm/nvm.sh
        nvm use 20
        cd {frontend_dir}
        npm run build 2>&1 | tail -50
        """
        print("\n  开始构建前端（这可能需要几分钟）...")
        success, output, error = execute_command(ssh, build_cmd, "构建前端")
        
        if success:
            print("  [OK] 前端构建成功")
        else:
            print("  [WARNING] 前端构建可能有问题")
        
        # 配置 systemd 服务
        frontend_service = """
        sudo tee /etc/systemd/system/smart-tg-frontend.service > /dev/null << 'EOF'
[Unit]
Description=Smart TG Frontend Service (Next.js)
After=network.target admin-backend.service

[Service]
Type=simple
User=ubuntu
Group=ubuntu
WorkingDirectory=/home/ubuntu/saas-demo
Environment="PATH=/usr/local/bin:/usr/bin:/bin"
Environment="NODE_ENV=production"
EnvironmentFile=/home/ubuntu/saas-demo/.env.local
ExecStart=/usr/bin/node .next/standalone/server.js
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF
        sudo systemctl daemon-reload
        """
        execute_command(ssh, frontend_service, "配置前端 systemd 服务")
        
        # 启动前端服务
        execute_command(ssh, "sudo systemctl restart smart-tg-frontend", "启动前端服务")
        time.sleep(5)
        
        success, output, _ = execute_command(ssh, "systemctl is-active smart-tg-frontend", "检查前端服务", show_output=False)
        if 'active' in output:
            print("  [OK] 前端服务已启动")
        else:
            print("  [WARNING] 前端服务可能未启动")
            execute_command(ssh, "sudo journalctl -u smart-tg-frontend -n 20 --no-pager", "查看前端日志")
        
        # 步骤6: 验证部署
        print("\n" + "=" * 70)
        print("步骤 6: 验证部署")
        print("=" * 70)
        
        execute_command(ssh, "systemctl status admin-backend smart-tg-frontend --no-pager -l | head -40", "服务状态")
        execute_command(ssh, "sudo ss -tlnp | grep -E ':8000|:3000'", "端口监听")
        
        success, output, _ = execute_command(ssh, "curl -s http://localhost:8000/health", "后端健康检查", show_output=False)
        if 'ok' in output.lower():
            print("  [OK] 后端健康检查通过")
        else:
            print(f"  [WARNING] 后端健康检查: {output}")
        
        success, output, _ = execute_command(ssh, "curl -s -o /dev/null -w 'HTTP %{http_code}' http://localhost:3000", "前端健康检查", show_output=False)
        if '200' in output:
            print("  [OK] 前端健康检查通过")
        else:
            print(f"  [WARNING] 前端健康检查: {output}")
        
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

