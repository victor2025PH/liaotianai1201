#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
服务器运维：排查并修复 Nginx 配置问题
"""

import json
import paramiko
import sys
import time
import re
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
    print("🔧 服务器运维：排查并修复 Nginx 配置问题")
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
        # 第一步：确认 3000 端口是否正常提供 _next 资源
        # ============================================================
        print("\n" + "="*70)
        print("第一步：确认 3000 端口是否正常提供 _next 资源")
        print("="*70)
        
        # 1.1 找到前端目录
        print("\n📋 查找前端目录（包含 package.json 和 .next 的目录）...")
        stdout, stderr, exit_code = run_command(
            client,
            "find /home /var/www /opt -name 'package.json' -path '*/saas-demo/package.json' 2>/dev/null | head -3",
            "",
            show_output=True
        )
        
        package_json_paths = [line.strip() for line in stdout.split('\n') if line.strip()]
        
        # 尝试多个可能的路径
        possible_dirs = [
            "/home/ubuntu/telegram-ai-system/saas-demo",
            "/home/ubuntu/liaotian/saas-demo",
            "/var/www/liaotian/saas-demo",
        ]
        
        if package_json_paths:
            possible_dirs = [str(Path(p).parent) for p in package_json_paths] + possible_dirs
        
        frontend_dir = None
        for test_dir in possible_dirs:
            stdout, stderr, exit_code = run_command(
                client,
                f"test -f {test_dir}/package.json && test -d {test_dir}/.next && echo 'OK'",
                "",
                show_output=False
            )
            if "OK" in stdout:
                frontend_dir = test_dir
                break
        
        if not frontend_dir:
            frontend_dir = possible_dirs[0]
            print(f"⚠️  使用默认路径: {frontend_dir}")
        else:
            print(f"\n✅ 使用前端目录: {frontend_dir}")
        
        # 1.2 列出 chunks 文件
        print("\n📋 列出 Next.js chunks 文件...")
        stdout, stderr, exit_code = run_command(
            client,
            f"cd {frontend_dir} && ls .next/static/chunks/*.js 2>/dev/null | head -5",
            "",
            show_output=True
        )
        
        chunk_files = [line.strip() for line in stdout.split('\n') if line.strip()]
        
        if not chunk_files:
            print("❌ 未找到 chunks 文件，检查 .next 目录...")
            run_command(
                client,
                f"ls -la {frontend_dir}/.next/static/ 2>/dev/null || echo '目录不存在'",
                "",
                show_output=True
            )
            print("\n⚠️  可能需要重新构建前端")
            return 1
        
        # 从完整路径中提取文件名
        import os
        test_chunk = os.path.basename(chunk_files[0])
        print(f"\n✅ 使用测试文件: {test_chunk}")
        
        # 1.3 检查 3000 端口是否监听
        print("\n📋 检查 3000 端口是否监听...")
        stdout, stderr, exit_code = run_command(
            client,
            "ss -tlnp | grep :3000 || echo '端口 3000 未监听'",
            "",
            show_output=True
        )
        
        port_listening = ":3000" in stdout
        
        # 1.4 检查前端服务状态
        print("\n📋 检查前端服务状态...")
        stdout, stderr, exit_code = run_command(
            client,
            "systemctl list-units --type=service --all | grep -E 'frontend|next' || echo '未找到前端服务'",
            "",
            show_output=True
        )
        
        # 1.5 如果端口未监听，尝试启动前端服务
        if not port_listening:
            print("\n⚠️  端口 3000 未监听，尝试启动前端服务...")
            
            # 检查是否有 systemd 服务
            stdout, stderr, exit_code = run_command(
                client,
                "systemctl list-units --type=service | grep -E 'liaotian-frontend|telegram-frontend' | head -1 | awk '{print $1}'",
                "",
                show_output=False
            )
            
            service_name = stdout.strip()
            if service_name:
                print(f"找到服务: {service_name}，尝试启动...")
                run_command(
                    client,
                    f"sudo systemctl start {service_name}",
                    "",
                    show_output=True
                )
                time.sleep(3)
            else:
                # 手动启动 Next.js
                print("未找到 systemd 服务，手动启动 Next.js...")
                run_command(
                    client,
                    f"cd {frontend_dir} && export NVM_DIR=\"$HOME/.nvm\" && [ -s \"$NVM_DIR/nvm.sh\" ] && . \"$NVM_DIR/nvm.sh\" && nvm use 20 && nohup npm start > /tmp/frontend.log 2>&1 &",
                    "",
                    show_output=True
                )
                time.sleep(5)
        
        # 1.6 再次检查端口
        print("\n📋 再次检查 3000 端口...")
        stdout, stderr, exit_code = run_command(
            client,
            "ss -tlnp | grep :3000 || echo '端口 3000 仍未监听'",
            "",
            show_output=True
        )
        
        port_listening = ":3000" in stdout
        
        if not port_listening:
            print("❌ 无法启动前端服务，请检查日志")
            run_command(
                client,
                "tail -50 /tmp/frontend.log 2>/dev/null || journalctl -u liaotian-frontend -n 50 --no-pager 2>/dev/null || echo '无日志'",
                "查看前端日志",
                show_output=True
            )
            return 1
        
        # 1.7 测试 3000 端口响应
        print("\n📋 测试 3000 端口响应...")
        
        # 测试根路径
        stdout, stderr, exit_code = run_command(
            client,
            "curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:3000/ 2>&1",
            "测试 http://127.0.0.1:3000/",
            show_output=True
        )
        
        root_status = stdout.strip()
        
        # 测试 chunks 文件
        stdout, stderr, exit_code = run_command(
            client,
            f"curl -s -o /dev/null -w '%{{http_code}}' http://127.0.0.1:3000/_next/static/chunks/{test_chunk} 2>&1",
            f"测试 http://127.0.0.1:3000/_next/static/chunks/{test_chunk}",
            show_output=True
        )
        
        chunk_status = stdout.strip()
        
        port_3000_ok = chunk_status == "200" or chunk_status == "301" or chunk_status == "302"
        
        # 1.8 测试域名
        print("\n📋 测试域名响应...")
        stdout, stderr, exit_code = run_command(
            client,
            f"curl -s -o /dev/null -w '%{{http_code}}' http://aikz.usdt2026.cc/_next/static/chunks/{test_chunk} 2>&1",
            f"测试 http://aikz.usdt2026.cc/_next/static/chunks/{test_chunk}",
            show_output=True
        )
        
        domain_status = stdout.strip()
        domain_ok = domain_status == "200" or domain_status == "301" or domain_status == "302"
        
        # 判断问题
        print("\n" + "="*70)
        print("📊 诊断结果")
        print("="*70)
        if port_3000_ok and not domain_ok:
            print("✅ 3000 端口正常，但域名返回 404 → Nginx 配置有问题")
            problem_type = "nginx"
        elif not port_3000_ok:
            print("❌ 3000 端口也返回 404 → Next.js 服务/构建有问题")
            problem_type = "nextjs"
        else:
            print("✅ 两边都正常，可能已修复")
            problem_type = "ok"
        
        if problem_type == "nextjs":
            print("\n需要检查 Next.js 服务状态和日志")
            run_command(
                client,
                "ps aux | grep -E 'node.*next|npm.*start' | grep -v grep || echo '未找到前端进程'",
                "检查前端进程",
                show_output=True
            )
            # 检查 Next.js 工作目录
            print("\n检查 Next.js 工作目录...")
            run_command(
                client,
                "ps aux | grep 'next-server' | grep -v grep | awk '{print $NF}' | head -1",
                "",
                show_output=True
            )
            # 继续执行，即使 Next.js 有问题，也要修复 Nginx 配置
            print("\n⚠️  继续执行 Nginx 配置修复...")
        
        # ============================================================
        # 第二步：检查真正生效的 Nginx 配置
        # ============================================================
        print("\n" + "="*70)
        print("第二步：检查真正生效的 Nginx 配置")
        print("="*70)
        
        # 2.1 查找包含域名的配置
        print("\n📋 查找包含 aikz.usdt2026.cc 的配置...")
        stdout, stderr, exit_code = run_command(
            client,
            "sudo nginx -T 2>/dev/null | grep -n 'aikz.usdt2026.cc' | head -10",
            "",
            show_output=True
        )
        
        # 2.2 查找配置文件路径
        print("\n📋 查找配置文件路径...")
        stdout, stderr, exit_code = run_command(
            client,
            "sudo nginx -T 2>/dev/null | grep -B 5 'server_name.*aikz.usdt2026.cc' | grep '# configuration file' | head -3",
            "",
            show_output=True
        )
        
        # 2.3 获取完整的 server 块
        print("\n📋 获取完整的 server 配置块...")
        stdout, stderr, exit_code = run_command(
            client,
            "sudo nginx -T 2>/dev/null | sed -n '/server_name.*aikz.usdt2026.cc/,/^[[:space:]]*}/p'",
            "",
            show_output=True
        )
        
        # 查找实际配置文件
        print("\n📋 查找实际配置文件...")
        stdout, stderr, exit_code = run_command(
            client,
            "ls -la /etc/nginx/sites-enabled/ | grep aikz",
            "",
            show_output=True
        )
        
        # 获取配置文件路径
        config_file = None
        if stdout:
            for line in stdout.split('\n'):
                if '->' in line:
                    # 符号链接，提取目标
                    parts = line.split('->')
                    if len(parts) > 1:
                        config_file = parts[1].strip()
                        break
        
        if not config_file:
            # 尝试直接查找
            stdout, stderr, exit_code = run_command(
                client,
                "sudo find /etc/nginx -name '*aikz*' -o -name '*liaotian*' 2>/dev/null | head -3",
                "",
                show_output=True
            )
            if stdout.strip():
                config_file = stdout.strip().split('\n')[0]
        
        if not config_file:
            config_file = "/etc/nginx/sites-available/aikz.conf"
        
        print(f"\n✅ 使用配置文件: {config_file}")
        
        # 2.4 读取配置文件内容
        print("\n📋 读取配置文件内容...")
        stdout, stderr, exit_code = run_command(
            client,
            f"sudo cat {config_file}",
            "",
            show_output=True
        )
        
        # ============================================================
        # 第三步：强制改成最简单的反向代理
        # ============================================================
        print("\n" + "="*70)
        print("第三步：强制改成最简单的反向代理")
        print("="*70)
        
        # 3.1 备份原配置
        print("\n📋 备份原配置...")
        run_command(
            client,
            f"sudo cp {config_file} {config_file}.backup.$(date +%Y%m%d_%H%M%S)",
            "",
            show_output=True
        )
        
        # 3.2 创建新的简化配置
        simple_config = '''server {
    listen 80;
    server_name aikz.usdt2026.cc;

    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;

        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_cache_bypass $http_upgrade;
    }
}'''
        
        # 3.3 写入新配置
        print("\n📋 写入新的简化配置...")
        sftp = client.open_sftp()
        temp_file = '/tmp/aikz_nginx_simple.conf'
        with sftp.open(temp_file, 'w') as f:
            f.write(simple_config)
        sftp.close()
        
        run_command(
            client,
            f"sudo mv {temp_file} {config_file} && sudo chmod 644 {config_file}",
            "",
            show_output=True
        )
        
        # 3.4 检查是否有其他冲突配置
        print("\n📋 检查是否有其他冲突配置...")
        stdout, stderr, exit_code = run_command(
            client,
            "sudo nginx -T 2>/dev/null | grep -c 'server_name.*aikz.usdt2026.cc'",
            "",
            show_output=True
        )
        
        count = int(stdout.strip()) if stdout.strip().isdigit() else 0
        if count > 1:
            print(f"⚠️  发现 {count} 个包含该域名的配置，需要禁用其他配置")
            run_command(
                client,
                "ls -la /etc/nginx/sites-enabled/ | grep -v 'aikz.conf' | grep -E 'aikz|liaotian' | awk '{print $NF}' | xargs -I {} sudo rm -f /etc/nginx/sites-enabled/{} 2>/dev/null || true",
                "禁用冲突配置",
                show_output=True
            )
        
        # 3.5 测试配置
        print("\n📋 测试 Nginx 配置...")
        stdout, stderr, exit_code = run_command(
            client,
            "sudo nginx -t",
            "",
            show_output=True
        )
        
        if exit_code != 0:
            print("❌ Nginx 配置测试失败")
            return 1
        
        # 3.6 重载 Nginx
        print("\n📋 重载 Nginx...")
        run_command(
            client,
            "sudo systemctl reload nginx",
            "",
            show_output=True
        )
        
        # ============================================================
        # 第四步：再次验证
        # ============================================================
        print("\n" + "="*70)
        print("第四步：再次验证")
        print("="*70)
        
        time.sleep(2)
        
        # 4.1 测试根路径
        print("\n📋 测试根路径...")
        stdout, stderr, exit_code = run_command(
            client,
            "curl -I http://aikz.usdt2026.cc/ 2>&1 | head -10",
            "",
            show_output=True
        )
        
        # 4.2 测试 chunks 文件
        print(f"\n📋 测试 chunks 文件: {test_chunk}...")
        stdout, stderr, exit_code = run_command(
            client,
            f"curl -I http://aikz.usdt2026.cc/_next/static/chunks/{test_chunk} 2>&1 | head -10",
            "",
            show_output=True
        )
        
        final_ok = "200" in stdout or "301" in stdout or "302" in stdout
        
        # 4.3 显示最终配置
        print("\n" + "="*70)
        print("📋 最终 Nginx 配置")
        print("="*70)
        run_command(
            client,
            f"sudo cat {config_file}",
            "",
            show_output=True
        )
        
        # 4.4 总结
        print("\n" + "="*70)
        print("📊 修复结果")
        print("="*70)
        if final_ok:
            print("✅ 修复成功！/_next/static/chunks/ 现在应该返回 200")
            print("\n📝 下一步:")
            print("   1. 清除浏览器缓存 (Ctrl+Shift+Delete)")
            print("   2. 刷新页面: http://aikz.usdt2026.cc")
            print("   3. 检查浏览器控制台，应该不再有 404 错误")
        else:
            print("❌ 修复后仍然返回 404，需要进一步排查")
            print("\n可能的原因:")
            print("   1. Next.js 服务未正常运行")
            print("   2. 前端构建文件缺失")
            print("   3. 端口 3000 未监听")
        
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

