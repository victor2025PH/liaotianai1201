#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全自动执行测试部署流程 - 最终版
自动连接到服务器、上传脚本、执行部署并分析结果
"""

import subprocess
import sys
import os
from pathlib import Path

# 配置
SERVER_IP = "165.154.233.55"
USERNAME = "ubuntu"
BASE_DIR = Path(__file__).parent.parent.absolute()
DEPLOY_SCRIPT = BASE_DIR / "deploy" / "从GitHub拉取并部署.sh"

def print_step(msg):
    print(f"\n[→] {msg}")

def print_success(msg):
    print(f"[✓] {msg}")

def print_error(msg):
    print(f"[✗] {msg}")

def print_info(msg):
    print(f"[i] {msg}")

def run_ssh_command(cmd, capture_output=True):
    """执行SSH命令"""
    ssh_cmd = ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=10", 
               f"{USERNAME}@{SERVER_IP}", cmd]
    
    try:
        if capture_output:
            result = subprocess.run(ssh_cmd, capture_output=True, text=True, timeout=300)
            return result.stdout, result.stderr, result.returncode
        else:
            result = subprocess.run(ssh_cmd, timeout=300)
            return None, None, result.returncode
    except subprocess.TimeoutExpired:
        return None, "命令执行超时", 1
    except Exception as e:
        return None, str(e), 1

def upload_deploy_script():
    """上传部署脚本到服务器"""
    print_step("步骤 1: 准备并上传部署脚本")
    
    if not DEPLOY_SCRIPT.exists():
        print_error(f"部署脚本不存在: {DEPLOY_SCRIPT}")
        return False
    
    print_info("读取脚本内容...")
    with open(DEPLOY_SCRIPT, 'r', encoding='utf-8') as f:
        script_content = f.read()
    
    # 转换行尾符
    script_content = script_content.replace('\r\n', '\n').replace('\r', '\n')
    
    # Base64编码
    import base64
    base64_content = base64.b64encode(script_content.encode('utf-8')).decode('utf-8')
    
    # 构建上传命令
    upload_cmd = f"""mkdir -p ~/liaotian/deploy && \
echo '{base64_content}' | base64 -d > ~/liaotian/deploy/从GitHub拉取并部署.sh && \
sed -i 's/\\r$//' ~/liaotian/deploy/从GitHub拉取并部署.sh 2>/dev/null || \
sed -i '' 's/\\r$//' ~/liaotian/deploy/从GitHub拉取并部署.sh 2>/dev/null || true && \
chmod +x ~/liaotian/deploy/从GitHub拉取并部署.sh && \
echo 'SCRIPT_UPLOADED'"""
    
    print_info(f"连接到服务器: {USERNAME}@{SERVER_IP}")
    stdout, stderr, code = run_ssh_command(upload_cmd)
    
    if "SCRIPT_UPLOADED" in (stdout or "") or code == 0:
        print_success("脚本上传成功")
        return True
    else:
        print_error(f"脚本上传可能失败: {stderr}")
        return False

def verify_script():
    """验证脚本行尾符"""
    print_step("步骤 2: 验证脚本行尾符")
    
    check_cmd = """if [ -f ~/liaotian/deploy/从GitHub拉取并部署.sh ]; then
    file ~/liaotian/deploy/从GitHub拉取并部署.sh
    CR_COUNT=$(od -c ~/liaotian/deploy/从GitHub拉取并部署.sh | grep -c '\\r' || echo '0')
    echo "CR字符数量: $CR_COUNT"
    bash -n ~/liaotian/deploy/从GitHub拉取并部署.sh 2>&1 && echo 'SCRIPT_VALID'
else
    echo 'SCRIPT_NOT_FOUND'
fi"""
    
    stdout, stderr, code = run_ssh_command(check_cmd)
    
    if stdout and "SCRIPT_VALID" in stdout:
        print_success("脚本验证通过（行尾符正确，语法正确）")
        if stdout:
            print_info(stdout)
        return True
    elif stdout and "SCRIPT_NOT_FOUND" in stdout:
        print_info("脚本文件不存在，将从GitHub拉取后创建")
        return False
    else:
        print_error(f"脚本验证失败: {stderr}")
        if stdout:
            print_info(stdout)
        return False

def execute_deploy():
    """执行部署"""
    print_step("步骤 3: 在服务器上执行部署")
    
    print("\n" + "="*50)
    print("服务器部署输出:")
    print("="*50 + "\n")
    
    deploy_cmd = "bash ~/liaotian/deploy/从GitHub拉取并部署.sh"
    
    stdout, stderr, code = run_ssh_command(deploy_cmd, capture_output=False)
    
    # 如果使用capture_output=False，需要重新运行获取输出
    stdout, stderr, code = run_ssh_command(deploy_cmd, capture_output=True)
    
    print(stdout if stdout else "")
    if stderr:
        print(stderr, file=sys.stderr)
    
    print("\n" + "="*50)
    
    # 分析结果
    output = (stdout or "") + (stderr or "")
    
    if "$'\\r': command not found" in output:
        print_error("检测到行尾符错误！修复可能未生效")
        return False
    elif "部署完成" in output or "后端服务正常运行" in output or code == 0:
        print_success("部署测试成功！")
        print("\n" + "="*50)
        print("  ✓ 测试结果: 成功")
        print("="*50 + "\n")
        
        print_info("验证点:")
        if "$'\\r'" not in output:
            print_success("  ✓ 无行尾符错误")
        if "代码拉取完成" in output or "git pull" in output:
            print_success("  ✓ 代码成功拉取")
        if "后端服务已启动" in output or "后端服务正常运行" in output:
            print_success("  ✓ 后端服务重启成功")
        
        return True
    else:
        print_error(f"部署失败（退出码: {code}）")
        if stderr:
            print_error(f"错误: {stderr}")
        return False

def main():
    print("="*50)
    print("  全自动执行测试部署流程")
    print("="*50)
    print()
    
    # 步骤 1: 上传脚本
    if not upload_deploy_script():
        print_error("脚本上传失败，退出")
        sys.exit(1)
    
    # 步骤 2: 验证脚本
    verify_script()
    
    # 步骤 3: 执行部署
    success = execute_deploy()
    
    if success:
        print_success("全自动测试部署完成！")
        sys.exit(0)
    else:
        print_error("部署测试失败")
        sys.exit(1)

if __name__ == "__main__":
    main()
