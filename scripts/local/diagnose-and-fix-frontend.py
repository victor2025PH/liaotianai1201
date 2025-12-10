#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
诊断并修复前端 404 问题
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
        'host': '165.154.233.55',
        'user': manila_config.get('user', 'ubuntu'),
        'password': manila_config.get('password', 'Along2025!!!'),
        'project_dir': '/home/ubuntu/telegram-ai-system',
    }

def connect_server(host, user, password, retries=3):
    """连接服务器"""
    for i in range(retries):
        try:
            print(f"正在连接服务器 {host}... (尝试 {i+1}/{retries})")
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(host, username=user, password=password, timeout=30)
            print("✅ SSH 连接成功!")
            return client
        except Exception as e:
            if i < retries - 1:
                print(f"⚠️  连接失败: {e}, 3秒后重试...")
                time.sleep(3)
            else:
                print(f"❌ 连接失败: {e}")
                raise
    return None

def run_command(client, command, description="", check_output=True):
    """执行远程命令"""
    if description:
        print(f"\n{'='*60}")
        print(f"📋 {description}")
        print(f"{'='*60}")
    
    try:
        stdin, stdout, stderr = client.exec_command(command, get_pty=True)
        
        output_lines = []
        error_lines = []
        
        for line in iter(stdout.readline, ""):
            if line:
                line = line.rstrip()
                print(line)
                output_lines.append(line)
        
        for line in iter(stderr.readline, ""):
            if line:
                line = line.rstrip()
                if line and not line.startswith('Warning:'):
                    print(f"⚠️  {line}", file=sys.stderr)
                error_lines.append(line)
        
        exit_status = stdout.channel.recv_exit_status()
        
        if exit_status != 0 and check_output:
            error_msg = '\n'.join(error_lines) if error_lines else "命令执行失败"
            raise Exception(f"命令执行失败 (退出码: {exit_status}): {error_msg}")
        
        return '\n'.join(output_lines), '\n'.join(error_lines), exit_status
    
    except Exception as e:
        print(f"❌ 执行命令失败: {e}")
        raise

def main():
    """主函数"""
    print("="*60)
    print("🔍 诊断并修复前端 404 问题")
    print("="*60)
    print()
    
    config = load_config()
    host = config['host']
    user = config['user']
    password = config['password']
    project_dir = config['project_dir']
    frontend_dir = f"{project_dir}/saas-demo"
    
    client = None
    try:
        client = connect_server(host, user, password)
        
        # 1. 检查前端服务
        print(f"\n{'='*60}")
        print("📋 步骤 1: 检查前端服务状态")
        print(f"{'='*60}")
        
        stdout, stderr, exit_code = run_command(
            client,
            f"systemctl list-units --type=service --all | grep -E 'frontend|next' || echo '未找到前端服务'",
            "",
            check_output=False
        )
        
        # 2. 检查端口
        stdout, stderr, exit_code = run_command(
            client,
            f"ss -tlnp | grep :3000 || echo '端口 3000 未监听'",
            "",
            check_output=False
        )
        
        if ':3000' not in stdout:
            print("⚠️  端口 3000 未监听，需要启动前端服务")
            # 启动前端服务
            run_command(
                client,
                f"cd {frontend_dir} && nohup npm start > /tmp/frontend.log 2>&1 &",
                "启动前端服务",
                check_output=False
            )
            time.sleep(5)
        
        # 3. 检查静态文件是否存在
        print(f"\n{'='*60}")
        print("📋 步骤 2: 检查静态文件")
        print(f"{'='*60}")
        
        stdout, stderr, exit_code = run_command(
            client,
            f"ls -la {frontend_dir}/.next/static/chunks 2>/dev/null | head -5 || echo '静态文件目录不存在'",
            "",
            check_output=False
        )
        
        if '静态文件目录不存在' in stdout or not stdout.strip():
            print("⚠️  静态文件不存在，需要重新构建")
            # 重新构建
            run_command(
                client,
                f"cd {frontend_dir} && export NODE_OPTIONS='--max-old-space-size=1536' && npm run build",
                "重新构建前端",
                check_output=False
            )
        
        # 4. 测试本地访问
        print(f"\n{'='*60}")
        print("📋 步骤 3: 测试本地访问")
        print(f"{'='*60}")
        
        stdout, stderr, exit_code = run_command(
            client,
            f"curl -s -o /dev/null -w 'HTTP %{{http_code}}' http://localhost:3000 2>/dev/null || echo '无法访问'",
            "",
            check_output=False
        )
        print(f"本地访问结果: {stdout}")
        
        # 5. 测试静态资源访问
        stdout, stderr, exit_code = run_command(
            client,
            f"curl -s -o /dev/null -w 'HTTP %{{http_code}}' http://localhost:3000/_next/static/chunks/ 2>/dev/null || echo '无法访问静态资源'",
            "",
            check_output=False
        )
        print(f"静态资源访问结果: {stdout}")
        
        # 6. 检查 Nginx 配置
        print(f"\n{'='*60}")
        print("📋 步骤 4: 检查并修复 Nginx 配置")
        print(f"{'='*60}")
        
        # 检查当前 Nginx 配置
        stdout, stderr, exit_code = run_command(
            client,
            f"sudo nginx -T 2>/dev/null | grep -A 10 'server_name.*aikz' || sudo cat /etc/nginx/sites-enabled/* 2>/dev/null | grep -A 10 'server_name.*aikz' || echo '未找到 Nginx 配置'",
            "检查 Nginx 配置",
            check_output=False
        )
        
        # 7. 确保 Nginx 配置正确
        nginx_config = f'''server {{
    listen 80;
    server_name aikz.usdt2026.cc;

    # 前端应用（所有请求，包括静态资源）
    location / {{
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        proxy_read_timeout 86400;
    }}

    # Next.js 静态资源（明确配置）
    location /_next/static/ {{
        proxy_pass http://127.0.0.1:3000/_next/static/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        add_header Cache-Control "public, max-age=31536000, immutable";
    }}

    # 后端 API
    location /api/ {{
        proxy_pass http://127.0.0.1:8000/api/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        proxy_read_timeout 300;
    }}

    # 后端健康检查
    location /health {{
        proxy_pass http://127.0.0.1:8000/health;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
    }}

    # 后端 API 文档
    location /docs {{
        proxy_pass http://127.0.0.1:8000/docs;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
    }}

    location /redoc {{
        proxy_pass http://127.0.0.1:8000/redoc;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
    }}
}}'''
        
        # 写入 Nginx 配置
        print("\n更新 Nginx 配置...")
        run_command(
            client,
            f"echo '{nginx_config}' | sudo tee /etc/nginx/sites-available/aikz.conf",
            "写入 Nginx 配置",
            check_output=False
        )
        
        # 创建符号链接
        run_command(
            client,
            f"sudo ln -sf /etc/nginx/sites-available/aikz.conf /etc/nginx/sites-enabled/aikz.conf",
            "启用 Nginx 配置",
            check_output=False
        )
        
        # 测试配置
        run_command(
            client,
            f"sudo nginx -t",
            "测试 Nginx 配置"
        )
        
        # 重载 Nginx
        run_command(
            client,
            f"sudo systemctl reload nginx",
            "重载 Nginx"
        )
        
        # 8. 最终检查
        print(f"\n{'='*60}")
        print("📋 步骤 5: 最终验证")
        print(f"{'='*60}")
        
        time.sleep(3)
        
        # 检查端口
        run_command(
            client,
            f"ss -tlnp | grep :3000 || echo '⚠️  端口 3000 未监听'",
            "检查端口 3000"
        )
        
        # 检查 Nginx 状态
        run_command(
            client,
            f"sudo systemctl status nginx --no-pager -l | head -10",
            "检查 Nginx 状态",
            check_output=False
        )
        
        print(f"\n{'='*60}")
        print("✅ 修复完成！")
        print(f"{'='*60}")
        print()
        print("📝 下一步:")
        print("   1. 等待 10-20 秒让服务完全启动")
        print("   2. 刷新浏览器页面: https://aikz.usdt2026.cc")
        print("   3. 清除浏览器缓存 (Ctrl+Shift+Delete)")
        print("   4. 如果还有问题，检查:")
        print(f"      - 前端日志: tail -50 /tmp/frontend.log")
        print(f"      - Nginx 日志: sudo tail -50 /var/log/nginx/error.log")
        print()
        
    except Exception as e:
        print(f"\n❌ 执行失败: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    finally:
        if client:
            client.close()
            print("🔌 SSH 连接已关闭")
    
    return 0

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断操作")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

