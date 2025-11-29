# -*- coding: utf-8 -*-
"""
全面诊断部署状态
"""

import paramiko
import os
import sys
import json

# 设置输出编码
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

SERVER = "165.154.233.55"
USERNAME = "ubuntu"

def run_ssh_command(ssh, command, description):
    """执行 SSH 命令并返回输出"""
    print(f"\n{'='*60}")
    print(f"{description}")
    print(f"{'='*60}")
    print(f"命令: {command}")
    print("-" * 60)
    
    stdin, stdout, stderr = ssh.exec_command(command)
    exit_status = stdout.channel.recv_exit_status()
    
    output = stdout.read().decode('utf-8', errors='ignore')
    error = stderr.read().decode('utf-8', errors='ignore')
    
    if output:
        print(output)
    if error:
        print(f"错误输出: {error}")
    print(f"退出码: {exit_status}")
    
    return exit_status == 0, output, error

try:
    print("=" * 60)
    print("全面诊断部署状态")
    print("=" * 60)
    
    # SSH 连接
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy)
    
    ssh_key_path = os.path.expanduser("~/.ssh/id_rsa")
    if os.path.exists(ssh_key_path):
        ssh.connect(SERVER, username=USERNAME, key_filename=ssh_key_path, timeout=30)
        print("[OK] SSH 连接成功")
    else:
        print("[错误] 未找到 SSH 密钥")
        sys.exit(1)
    
    results = {
        "文件检查": {},
        "构建检查": {},
        "服务检查": {},
        "端口检查": {},
        "Nginx检查": {},
        "问题汇总": []
    }
    
    # 1. 文件检查
    print("\n" + "="*60)
    print("1. 文件检查")
    print("="*60)
    
    files_to_check = [
        ("/home/ubuntu/liaotian/saas-demo/src/lib/api/group-ai.ts", "API客户端"),
        ("/home/ubuntu/liaotian/saas-demo/src/app/group-ai/accounts/page.tsx", "账号管理页面"),
    ]
    
    for file_path, desc in files_to_check:
        success, output, error = run_ssh_command(ssh, f"test -f {file_path} && ls -lh {file_path} || echo '文件不存在'", f"检查 {desc}")
        if "文件不存在" in output:
            results["问题汇总"].append(f"{desc} 文件不存在")
            results["文件检查"][desc] = "不存在"
        else:
            results["文件检查"][desc] = "存在"
    
    # 检查语法错误
    success, output, error = run_ssh_command(ssh, "grep -c 'workerAccounts.map' /home/ubuntu/liaotian/saas-demo/src/app/group-ai/accounts/page.tsx", "检查 workerAccounts.map 出现次数")
    count = output.strip()
    if count == "1":
        print("[OK] workerAccounts.map 只出现一次（正确）")
        results["文件检查"]["语法检查"] = "通过"
    else:
        print(f"[警告] workerAccounts.map 出现 {count} 次（可能有问题）")
        results["问题汇总"].append(f"语法错误：workerAccounts.map 出现 {count} 次")
        results["文件检查"]["语法检查"] = f"异常（{count}次）"
    
    # 2. 构建检查
    print("\n" + "="*60)
    print("2. 构建检查")
    print("="*60)
    
    success, output, error = run_ssh_command(ssh, "test -d /home/ubuntu/liaotian/saas-demo/.next && echo '存在' || echo '不存在'", "检查构建目录")
    if "存在" in output:
        results["构建检查"]["构建目录"] = "存在"
        # 检查构建时间
        success, output, error = run_ssh_command(ssh, "stat -c '%y' /home/ubuntu/liaotian/saas-demo/.next 2>/dev/null || echo '无法获取时间'", "检查构建时间")
        print(f"构建时间: {output.strip()}")
    else:
        results["问题汇总"].append("构建目录不存在，需要重新构建")
        results["构建检查"]["构建目录"] = "不存在"
    
    # 检查最近的构建日志
    success, output, error = run_ssh_command(ssh, "cd /home/ubuntu/liaotian/saas-demo && tail -50 .next/trace 2>/dev/null | grep -i error | tail -5 || echo '无错误日志'", "检查构建错误日志")
    if "error" in output.lower() and "无错误日志" not in output:
        results["问题汇总"].append("构建日志中发现错误")
        results["构建检查"]["构建错误"] = "发现错误"
    else:
        results["构建检查"]["构建错误"] = "无错误"
    
    # 3. 服务检查
    print("\n" + "="*60)
    print("3. 服务检查")
    print("="*60)
    
    # 前端服务
    success, output, error = run_ssh_command(ssh, "sudo systemctl is-active liaotian-frontend", "检查前端服务状态")
    if "active" in output:
        results["服务检查"]["前端服务"] = "运行中"
    else:
        results["问题汇总"].append("前端服务未运行")
        results["服务检查"]["前端服务"] = "未运行"
        # 查看服务日志
        run_ssh_command(ssh, "sudo journalctl -u liaotian-frontend -n 30 --no-pager", "查看前端服务日志")
    
    # 后端服务
    success, output, error = run_ssh_command(ssh, "sudo systemctl is-active liaotian-backend", "检查后端服务状态")
    if "active" in output:
        results["服务检查"]["后端服务"] = "运行中"
    else:
        results["问题汇总"].append("后端服务未运行")
        results["服务检查"]["后端服务"] = "未运行"
        # 查看服务日志
        run_ssh_command(ssh, "sudo journalctl -u liaotian-backend -n 30 --no-pager", "查看后端服务日志")
    
    # 4. 端口检查
    print("\n" + "="*60)
    print("4. 端口检查")
    print("="*60)
    
    success, output, error = run_ssh_command(ssh, "sudo netstat -tlnp 2>/dev/null | grep ':3000' || sudo ss -tlnp 2>/dev/null | grep ':3000'", "检查前端端口 3000")
    if ":3000" in output:
        results["端口检查"]["前端端口3000"] = "监听中"
    else:
        results["问题汇总"].append("前端端口3000未监听")
        results["端口检查"]["前端端口3000"] = "未监听"
    
    success, output, error = run_ssh_command(ssh, "sudo netstat -tlnp 2>/dev/null | grep ':8000' || sudo ss -tlnp 2>/dev/null | grep ':8000'", "检查后端端口 8000")
    if ":8000" in output:
        results["端口检查"]["后端端口8000"] = "监听中"
    else:
        results["问题汇总"].append("后端端口8000未监听")
        results["端口检查"]["后端端口8000"] = "未监听"
    
    # 5. Nginx检查
    print("\n" + "="*60)
    print("5. Nginx检查")
    print("="*60)
    
    success, output, error = run_ssh_command(ssh, "sudo systemctl is-active nginx", "检查Nginx服务状态")
    if "active" in output:
        results["Nginx检查"]["服务状态"] = "运行中"
    else:
        results["问题汇总"].append("Nginx服务未运行")
        results["Nginx检查"]["服务状态"] = "未运行"
    
    success, output, error = run_ssh_command(ssh, "sudo nginx -t", "检查Nginx配置")
    if "syntax is ok" in output.lower() and "test is successful" in output.lower():
        results["Nginx检查"]["配置检查"] = "通过"
    else:
        results["问题汇总"].append("Nginx配置有错误")
        results["Nginx检查"]["配置检查"] = "失败"
    
    # 6. 尝试构建
    print("\n" + "="*60)
    print("6. 尝试重新构建（如果需要）")
    print("="*60)
    
    if results["构建检查"].get("构建目录") == "不存在" or results["构建检查"].get("构建错误") == "发现错误":
        print("检测到构建问题，尝试重新构建...")
        build_cmd = """
cd /home/ubuntu/liaotian/saas-demo && \
export NVM_DIR="$HOME/.nvm" && \
[ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh" && \
nvm use 20 && \
rm -rf .next && \
npm run build 2>&1 | tail -50
"""
        success, output, error = run_ssh_command(ssh, build_cmd, "重新构建前端")
        if "error" in output.lower() or "failed" in output.lower():
            results["问题汇总"].append("重新构建失败")
            print("[错误] 构建失败，请检查错误信息")
        else:
            print("[OK] 构建成功")
            # 重启服务
            run_ssh_command(ssh, "sudo systemctl restart liaotian-frontend", "重启前端服务")
    
    ssh.close()
    
    # 7. 汇总报告
    print("\n" + "="*60)
    print("诊断报告汇总")
    print("="*60)
    print(json.dumps(results, indent=2, ensure_ascii=False))
    
    print("\n" + "="*60)
    print("问题汇总")
    print("="*60)
    if results["问题汇总"]:
        for i, problem in enumerate(results["问题汇总"], 1):
            print(f"{i}. {problem}")
    else:
        print("未发现问题！")
    
    print("\n" + "="*60)
    print("建议操作")
    print("="*60)
    if results["问题汇总"]:
        print("1. 根据上述问题逐一解决")
        print("2. 如果构建失败，检查代码语法")
        print("3. 如果服务未运行，检查服务日志")
        print("4. 如果端口未监听，检查服务配置")
    else:
        print("所有检查通过！服务应该正常运行。")
        print("如果浏览器仍显示502，请清除缓存并刷新。")
    
except Exception as e:
    print(f"\n[错误] 诊断失败: {e}")
    import traceback
    print(traceback.format_exc())
    sys.exit(1)

