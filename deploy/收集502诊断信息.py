#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
收集502错误的诊断信息
"""
import subprocess
import os
from pathlib import Path

def run_ssh_command(command, description):
    """执行SSH命令并返回输出"""
    print(f"\n{'='*50}")
    print(f"[{description}]")
    print(f"{'='*50}")
    
    ssh_cmd = f'ssh ubuntu@165.154.233.55 "{command}"'
    try:
        result = subprocess.run(
            ssh_cmd,
            shell=True,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='ignore'
        )
        output = result.stdout + result.stderr
        print(output)
        return output
    except Exception as e:
        error_msg = f"执行失败: {e}"
        print(error_msg)
        return error_msg

def main():
    """主函数"""
    print("="*50)
    print("收集502错误诊断信息")
    print("="*50)
    
    # 创建输出目录
    output_dir = Path("deploy/诊断结果")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. 检查服务状态
    output1 = run_ssh_command(
        "sudo systemctl status liaotian-frontend --no-pager | head -20",
        "检查服务状态"
    )
    (output_dir / "服务状态.txt").write_text(output1, encoding='utf-8')
    
    # 2. 查看服务日志
    output2 = run_ssh_command(
        "sudo journalctl -u liaotian-frontend -n 50 --no-pager",
        "查看服务日志"
    )
    (output_dir / "服务日志.txt").write_text(output2, encoding='utf-8')
    
    # 3. 检查端口监听
    output3 = run_ssh_command(
        "ss -tlnp | grep ':3000' || echo '端口3000未监听'",
        "检查端口监听"
    )
    (output_dir / "端口监听.txt").write_text(output3, encoding='utf-8')
    
    # 4. 检查standalone目录
    output4 = run_ssh_command(
        "cd /home/ubuntu/liaotian/saas-demo && STANDALONE_DIR=$(find .next/standalone -name 'server.js' -type f 2>/dev/null | head -1 | xargs dirname) && echo \"Standalone目录: $STANDALONE_DIR\" && ls -la \"$STANDALONE_DIR/server.js\" 2>&1 && ls -la \"$STANDALONE_DIR/.next/static/chunks/adc3be135379192a.js\" 2>&1",
        "检查standalone目录和静态文件"
    )
    (output_dir / "standalone目录.txt").write_text(output4, encoding='utf-8')
    
    # 5. 检查systemd服务配置
    output5 = run_ssh_command(
        "cat /etc/systemd/system/liaotian-frontend.service",
        "检查systemd服务配置"
    )
    (output_dir / "服务配置.txt").write_text(output5, encoding='utf-8')
    
    # 6. 检查Node.js路径
    output6 = run_ssh_command(
        "which node && /home/ubuntu/.nvm/versions/node/v20.19.6/bin/node --version",
        "检查Node.js路径"
    )
    (output_dir / "Node路径.txt").write_text(output6, encoding='utf-8')
    
    print("\n" + "="*50)
    print("诊断信息已保存到 deploy/诊断结果/ 目录")
    print("="*50)

if __name__ == "__main__":
    main()

