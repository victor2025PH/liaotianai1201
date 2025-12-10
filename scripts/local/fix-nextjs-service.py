#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
服务器前端运维：排查并修复 Next.js 服务端问题
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

def run_command(client, command, description="", show_output=True):
    """执行远程命令"""
    if description:
        print(f"\n{'='*70}")
        print(f"📋 {description}")
        print(f"{'='*70}")
    
    try:
        stdin, stdout, stderr = client.exec_command(command, get_pty=True)
        
        output_lines = []
        error_lines = []
        
        for line in iter(stdout.readline, ""):
            if line:
                line = line.rstrip()
                if show_output:
                    print(line)
                output_lines.append(line)
        
        for line in iter(stderr.readline, ""):
            if line:
                line = line.rstrip()
                if line and not line.startswith('Warning:'):
                    if show_output:
                        print(f"⚠️  {line}", file=sys.stderr)
                    error_lines.append(line)
        
        exit_status = stdout.channel.recv_exit_status()
        
        return '\n'.join(output_lines), '\n'.join(error_lines), exit_status
    
    except Exception as e:
        print(f"❌ 执行命令失败: {e}")
        raise

def main():
    """主函数"""
    print("="*70)
    print("🔧 服务器前端运维：排查并修复 Next.js 服务端问题")
    print("="*70)
    print()
    
    config = load_config()
    host = config['host']
    user = config['user']
    password = config['password']
    
    client = None
    try:
        client = connect_server(host, user, password)
        
        # ============================================================
        # 第一步：确认前端服务运行目录
        # ============================================================
        print("\n" + "="*70)
        print("第一步：确认前端服务运行目录")
        print("="*70)
        
        # 1.1 查看服务状态
        stdout, stderr, exit_code = run_command(
            client,
            "sudo systemctl status liaotian-frontend.service --no-pager -l | head -30",
            "查看服务状态",
            show_output=True
        )
        
        # 1.2 查看服务配置
        stdout, stderr, exit_code = run_command(
            client,
            "sudo systemctl cat liaotian-frontend.service",
            "查看服务配置",
            show_output=True
        )
        
        # 提取 WorkingDirectory 和 ExecStart
        working_dir = None
        exec_start = None
        
        for line in stdout.split('\n'):
            if 'WorkingDirectory=' in line:
                working_dir = line.split('=')[1].strip()
            elif 'ExecStart=' in line:
                exec_start = line.split('=', 1)[1].strip()
        
        print(f"\n✅ WorkingDirectory: {working_dir}")
        print(f"✅ ExecStart: {exec_start}")
        
        if not working_dir:
            # 尝试从 ExecStart 中提取路径
            if exec_start and 'cd' in exec_start:
                # 简单提取，实际可能需要更复杂的解析
                print("⚠️  未找到 WorkingDirectory，尝试从 ExecStart 提取...")
            else:
                # 尝试常见路径
                possible_dirs = [
                    "/home/ubuntu/telegram-ai-system/saas-demo",
                    "/home/ubuntu/liaotian/saas-demo",
                    "/var/www/liaotian/saas-demo",
                ]
                for test_dir in possible_dirs:
                    stdout, stderr, exit_code = run_command(
                        client,
                        f"test -f {test_dir}/package.json && echo 'OK'",
                        "",
                        show_output=False
                    )
                    if "OK" in stdout:
                        working_dir = test_dir
                        break
        
        if not working_dir:
            working_dir = "/home/ubuntu/telegram-ai-system/saas-demo"
            print(f"⚠️  使用默认路径: {working_dir}")
        
        # 1.3 进入项目目录并检查
        print(f"\n📋 进入项目目录: {working_dir}")
        stdout, stderr, exit_code = run_command(
            client,
            f"cd {working_dir} && pwd && ls -la | head -20",
            "检查项目目录",
            show_output=True
        )
        
        # ============================================================
        # 第二步：检查 .next 目录和构建结果
        # ============================================================
        print("\n" + "="*70)
        print("第二步：检查 .next 目录和构建结果")
        print("="*70)
        
        # 2.1 检查 .next 目录
        stdout, stderr, exit_code = run_command(
            client,
            f"cd {working_dir} && ls -a | grep -E '^\\.next$|^\\.next/'",
            "检查 .next 目录",
            show_output=True
        )
        
        # 2.2 检查 static/chunks
        stdout, stderr, exit_code = run_command(
            client,
            f"cd {working_dir} && ls .next/static/chunks 2>/dev/null | head -10 || echo '.next/static/chunks 不存在或为空'",
            "检查 chunks 文件",
            show_output=True
        )
        
        chunks_exist = ".next/static/chunks 不存在或为空" not in stdout
        
        if not chunks_exist:
            print("\n⚠️  chunks 文件不存在，需要重新构建...")
            
            # 2.3 检查 package.json
            stdout, stderr, exit_code = run_command(
                client,
                f"cd {working_dir} && cat package.json | grep -A 10 '\"scripts\"'",
                "查看 package.json scripts",
                show_output=True
            )
            
            # 2.4 重新构建
            print("\n📋 开始重新构建...")
            build_cmd = f"""
cd {working_dir}
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"
nvm use 20 || true
npm install --production=false
npm run build
"""
            stdout, stderr, exit_code = run_command(
                client,
                build_cmd,
                "重新构建前端",
                show_output=True
            )
            
            # 再次检查
            stdout, stderr, exit_code = run_command(
                client,
                f"cd {working_dir} && ls .next/static/chunks 2>/dev/null | head -10 || echo '.next/static/chunks 仍然不存在'",
                "再次检查 chunks 文件",
                show_output=True
            )
            chunks_exist = ".next/static/chunks 仍然不存在" not in stdout
        
        # 获取一个测试文件名
        stdout, stderr, exit_code = run_command(
            client,
            f"cd {working_dir} && ls .next/static/chunks/*.js 2>/dev/null | head -1 | xargs -n1 basename",
            "",
            show_output=False
        )
        test_chunk = stdout.strip() if stdout.strip() else "00d08e8cd5345827.js"
        print(f"\n✅ 使用测试文件: {test_chunk}")
        
        # ============================================================
        # 第三步：确认启动命令和端口
        # ============================================================
        print("\n" + "="*70)
        print("第三步：确认启动命令和端口")
        print("="*70)
        
        # 3.1 查看 package.json scripts
        stdout, stderr, exit_code = run_command(
            client,
            f"cd {working_dir} && cat package.json | grep -A 20 '\"scripts\"'",
            "查看 package.json scripts",
            show_output=True
        )
        
        # 3.2 检查当前服务配置是否正确
        needs_fix = False
        
        if working_dir not in exec_start if exec_start else True:
            print("\n⚠️  服务配置可能不正确，需要修复...")
            needs_fix = True
        
        # 3.3 修复服务配置
        if needs_fix or not exec_start or 'next start' not in exec_start:
            print("\n📋 修复服务配置...")
            
            # 检查 Node.js 路径
            stdout, stderr, exit_code = run_command(
                client,
                "which node || which nodejs || echo '/usr/bin/node'",
                "",
                show_output=False
            )
            node_path = stdout.strip() or "/usr/bin/node"
            
            # 检查 npm 路径
            stdout, stderr, exit_code = run_command(
                client,
                "which npm || echo '/usr/bin/npm'",
                "",
                show_output=False
            )
            npm_path = stdout.strip() or "/usr/bin/npm"
            
            # 创建新的服务配置
            service_config = f"""[Unit]
Description=Liaotian Frontend Service
After=network.target

[Service]
Type=simple
User=ubuntu
Group=ubuntu
WorkingDirectory={working_dir}
Environment="NODE_ENV=production"
Environment="PATH=/home/ubuntu/.nvm/versions/node/v20.0.0/bin:/usr/local/bin:/usr/bin:/bin"
Environment="NVM_DIR=/home/ubuntu/.nvm"
ExecStart=/bin/bash -c 'source /home/ubuntu/.nvm/nvm.sh && cd {working_dir} && nvm use 20 && npm run start'
Restart=always
RestartSec=10

StandardOutput=journal
StandardError=journal
SyslogIdentifier=liaotian-frontend

[Install]
WantedBy=multi-user.target
"""
            
            # 写入服务文件
            sftp = client.open_sftp()
            temp_file = '/tmp/liaotian-frontend.service'
            with sftp.open(temp_file, 'w') as f:
                f.write(service_config)
            sftp.close()
            
            run_command(
                client,
                f"sudo mv {temp_file} /etc/systemd/system/liaotian-frontend.service && sudo chmod 644 /etc/systemd/system/liaotian-frontend.service",
                "安装服务文件",
                show_output=True
            )
            
            # 重新加载并重启
            run_command(
                client,
                "sudo systemctl daemon-reload",
                "重新加载 systemd",
                show_output=True
            )
            
            run_command(
                client,
                "sudo systemctl restart liaotian-frontend.service",
                "重启服务",
                show_output=True
            )
            
            time.sleep(5)
            
            run_command(
                client,
                "sudo systemctl status liaotian-frontend.service --no-pager -l | head -20",
                "检查服务状态",
                show_output=True
            )
        
        # ============================================================
        # 第四步：验证 3000 端口是否正常返回静态资源
        # ============================================================
        print("\n" + "="*70)
        print("第四步：验证 3000 端口是否正常返回静态资源")
        print("="*70)
        
        time.sleep(3)
        
        # 4.1 测试根路径
        stdout, stderr, exit_code = run_command(
            client,
            "curl -I http://127.0.0.1:3000/ 2>&1 | head -15",
            "测试 http://127.0.0.1:3000/",
            show_output=True
        )
        
        # 4.2 测试 chunks 文件（本地）
        stdout, stderr, exit_code = run_command(
            client,
            f"curl -I http://127.0.0.1:3000/_next/static/chunks/{test_chunk} 2>&1 | head -15",
            f"测试 http://127.0.0.1:3000/_next/static/chunks/{test_chunk}",
            show_output=True
        )
        
        local_ok = "200" in stdout or "301" in stdout or "302" in stdout
        
        # 4.3 测试 chunks 文件（域名）
        stdout, stderr, exit_code = run_command(
            client,
            f"curl -I http://aikz.usdt2026.cc/_next/static/chunks/{test_chunk} 2>&1 | head -15",
            f"测试 http://aikz.usdt2026.cc/_next/static/chunks/{test_chunk}",
            show_output=True
        )
        
        domain_ok = "200" in stdout or "301" in stdout or "302" in stdout
        
        # ============================================================
        # 第五步：检查 basePath 或 assetPrefix
        # ============================================================
        print("\n" + "="*70)
        print("第五步：检查 basePath 或 assetPrefix")
        print("="*70)
        
        stdout, stderr, exit_code = run_command(
            client,
            f"cd {working_dir} && cat next.config.* 2>/dev/null || echo '未找到 next.config 文件'",
            "检查 next.config 配置",
            show_output=True
        )
        
        has_basepath = "basePath" in stdout or "assetPrefix" in stdout
        
        if has_basepath and not local_ok:
            print("\n⚠️  发现 basePath 或 assetPrefix 配置，可能需要调整...")
        
        # ============================================================
        # 总结
        # ============================================================
        print("\n" + "="*70)
        print("📊 修复结果总结")
        print("="*70)
        
        print(f"\n项目根目录: {working_dir}")
        print(f"测试文件: {test_chunk}")
        print(f"本地 3000 端口: {'✅ 正常' if local_ok else '❌ 失败'}")
        print(f"域名访问: {'✅ 正常' if domain_ok else '❌ 失败'}")
        
        if local_ok and domain_ok:
            print("\n✅ 修复成功！/_next/static/chunks/ 现在应该返回 200")
            print("\n📝 下一步:")
            print("   1. 清除浏览器缓存 (Ctrl+Shift+Delete)")
            print("   2. 刷新页面: http://aikz.usdt2026.cc")
            print("   3. 检查浏览器控制台，应该不再有 404 错误")
        elif local_ok and not domain_ok:
            print("\n⚠️  本地 3000 端口正常，但域名访问失败，可能是 Nginx 配置问题")
        else:
            print("\n❌ 本地 3000 端口也失败，需要进一步排查 Next.js 服务")
            print("\n可能的原因:")
            print("   1. Next.js 服务未正确启动")
            print("   2. 构建文件路径问题")
            print("   3. basePath 配置问题")
        
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

