#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
获取 SSH 输出的可靠方案
使用多种方法确保能够获取输出
"""

import subprocess
import sys
import os
import tempfile
from pathlib import Path

# 设置输出编码
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except:
        pass

os.environ['PYTHONUNBUFFERED'] = '1'

def run_ssh_reliable(cmd, description):
    """使用多种方法执行 SSH 命令并获取输出"""
    print(f"\n{'='*60}")
    print(f"{description}")
    print(f"{'='*60}")
    print(f"命令: {cmd}")
    print("-" * 60)
    
    full_cmd = f'ssh ubuntu@165.154.233.55 "{cmd}"'
    
    # 方法1: 使用临时文件
    try:
        with tempfile.NamedTemporaryFile(mode='w+', delete=False, encoding='utf-8', suffix='.txt') as tmp_file:
            tmp_path = tmp_file.name
        
        # 执行命令并重定向到文件
        result = subprocess.run(
            f'{full_cmd} > "{tmp_path}" 2>&1',
            shell=True,
            timeout=30
        )
        
        # 读取文件内容
        try:
            with open(tmp_path, 'r', encoding='utf-8', errors='replace') as f:
                output = f.read()
        except Exception as e:
            output = f"读取文件失败: {e}"
        
        # 清理临时文件
        try:
            os.unlink(tmp_path)
        except:
            pass
        
        print(f"退出码: {result.returncode}")
        print("输出:")
        if output:
            print(output)
        else:
            print("(空)")
        
        return result.returncode == 0, output, ""
        
    except subprocess.TimeoutExpired:
        print("❌ 命令执行超时")
        return False, "", "Timeout"
    except Exception as e:
        print(f"❌ 执行失败: {e}")
        import traceback
        traceback.print_exc()
        return False, "", str(e)

def main():
    print("="*60)
    print("SSH 输出获取测试 - 可靠方案")
    print("="*60)
    print(f"Python 版本: {sys.version}")
    print(f"编码: {sys.stdout.encoding}")
    print()
    
    # 保存所有输出到文件
    output_file = Path("deploy/SSH测试结果_完整.txt")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("="*60 + "\n")
        f.write("SSH 测试结果 - 完整输出\n")
        f.write("="*60 + "\n\n")
        
        tests = [
            ("echo 'SSH 连接测试成功 - TEST123'", "测试 1: 基本连接"),
            ("whoami", "测试 2: 当前用户"),
            ("hostname", "测试 3: 主机名"),
            ("sudo nginx -t 2>&1", "测试 4: Nginx 配置语法"),
            ("sudo grep -A 15 'location /api/v1/notifications/ws' /etc/nginx/sites-available/aikz.usdt2026.cc 2>&1", "测试 5: WebSocket 配置"),
            ("sudo systemctl is-active nginx 2>&1", "测试 6: Nginx 服务状态"),
            ("sudo systemctl is-active liaotian-backend 2>&1", "测试 7: 后端服务状态"),
            ("sudo netstat -tlnp 2>/dev/null | grep :8000 || sudo ss -tlnp 2>/dev/null | grep :8000 || echo '未找到端口 8000' 2>&1", "测试 8: 后端端口监听"),
        ]
        
        results = []
        for cmd, desc in tests:
            success, output, error = run_ssh_reliable(cmd, desc)
            results.append((desc, success, output))
            
            # 写入文件
            f.write(f"\n{'='*60}\n")
            f.write(f"{desc}\n")
            f.write(f"{'='*60}\n")
            f.write(f"命令: {cmd}\n")
            f.write(f"成功: {success}\n")
            f.write(f"输出:\n{output}\n")
            f.write("\n")
            f.flush()
        
        # 总结
        f.write("\n" + "="*60 + "\n")
        f.write("测试总结\n")
        f.write("="*60 + "\n")
        for desc, success, output in results:
            status = "✓" if success else "✗"
            has_output = "✓" if output.strip() else "✗"
            f.write(f"{desc}: {status} (有输出: {has_output})\n")
        f.flush()
    
    print(f"\n结果已保存到: {output_file}")
    print("\n" + "="*60)
    print("测试总结")
    print("="*60)
    for desc, success, output in results:
        status = "✓" if success else "✗"
        has_output = "✓" if output.strip() else "✗"
        print(f"{desc}: {status} (有输出: {has_output})")
    
    # 读取并显示文件内容
    print(f"\n完整结果请查看: {output_file}")
    print("\n前500字符预览:")
    try:
        with open(output_file, 'r', encoding='utf-8') as f:
            content = f.read()
            print(content[:500])
            if len(content) > 500:
                print("\n... (更多内容请查看文件)")
    except Exception as e:
        print(f"读取文件失败: {e}")

if __name__ == "__main__":
    main()

