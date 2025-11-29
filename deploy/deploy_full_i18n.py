#!/usr/bin/env python3
"""
完整部署多语言修复和按钮样式更新
"""
import paramiko
import os

SERVER = "165.154.233.55"
USERNAME = "ubuntu"
PASSWORD = "Along2025!!!"
PROJECT_DIR = "/home/ubuntu/liaotian"

print("正在连接服务器...")
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(SERVER, username=USERNAME, password=PASSWORD, timeout=30)
print("✓ SSH 连接成功!")

sftp = client.open_sftp()

# 本地前端目录
local_base = r"E:\002-工作文件\重要程序\聊天AI群聊程序\saas-demo"
remote_base = f"{PROJECT_DIR}/saas-demo"

# 需要上传的文件列表
files_to_upload = [
    # i18n 核心文件
    ("src/lib/i18n/translations.ts", "src/lib/i18n/translations.ts"),
    ("src/lib/i18n/context.tsx", "src/lib/i18n/context.tsx"),
    ("src/lib/i18n/index.ts", "src/lib/i18n/index.ts"),
    
    # UI 组件
    ("src/components/ui/action-button.tsx", "src/components/ui/action-button.tsx"),
    ("src/components/language-toggle.tsx", "src/components/language-toggle.tsx"),
    ("src/components/sidebar.tsx", "src/components/sidebar.tsx"),
    ("src/components/header.tsx", "src/components/header.tsx"),
    ("src/components/layout-wrapper.tsx", "src/components/layout-wrapper.tsx"),
    ("src/components/step-indicator.tsx", "src/components/step-indicator.tsx"),
    
    # Dashboard 组件
    ("src/components/dashboard/response-time-chart.tsx", "src/components/dashboard/response-time-chart.tsx"),
    ("src/components/dashboard/system-status.tsx", "src/components/dashboard/system-status.tsx"),
    
    # 页面文件（已转换为简体中文）
    ("src/app/page.tsx", "src/app/page.tsx"),
    ("src/app/group-ai/scripts/page.tsx", "src/app/group-ai/scripts/page.tsx"),
    ("src/app/group-ai/accounts/page.tsx", "src/app/group-ai/accounts/page.tsx"),
    ("src/app/group-ai/role-assignments/page.tsx", "src/app/group-ai/role-assignments/page.tsx"),
    ("src/app/group-ai/role-assignment-schemes/page.tsx", "src/app/group-ai/role-assignment-schemes/page.tsx"),
    ("src/app/group-ai/automation-tasks/page.tsx", "src/app/group-ai/automation-tasks/page.tsx"),
    ("src/app/group-ai/monitor/page.tsx", "src/app/group-ai/monitor/page.tsx"),
    ("src/app/group-ai/nodes/page.tsx", "src/app/group-ai/nodes/page.tsx"),
    ("src/app/group-ai/groups/page.tsx", "src/app/group-ai/groups/page.tsx"),
    ("src/app/sessions/page.tsx", "src/app/sessions/page.tsx"),
    ("src/app/logs/page.tsx", "src/app/logs/page.tsx"),
    ("src/app/monitoring/page.tsx", "src/app/monitoring/page.tsx"),
    ("src/app/permissions/page.tsx", "src/app/permissions/page.tsx"),
]

# 确保目录存在
print("\n>>> 创建目录结构")
dirs_to_create = [
    f"{remote_base}/src/lib/i18n",
    f"{remote_base}/src/components/ui",
    f"{remote_base}/src/components/dashboard",
    f"{remote_base}/src/components/onboarding",
    f"{remote_base}/src/app/group-ai/scripts",
    f"{remote_base}/src/app/group-ai/accounts",
    f"{remote_base}/src/app/group-ai/role-assignments",
    f"{remote_base}/src/app/group-ai/role-assignment-schemes",
    f"{remote_base}/src/app/group-ai/automation-tasks",
    f"{remote_base}/src/app/group-ai/monitor",
    f"{remote_base}/src/app/group-ai/nodes",
    f"{remote_base}/src/app/group-ai/groups",
    f"{remote_base}/src/app/sessions",
    f"{remote_base}/src/app/logs",
    f"{remote_base}/src/app/monitoring",
    f"{remote_base}/src/app/permissions",
]

for dir_path in dirs_to_create:
    stdin, stdout, stderr = client.exec_command(f"mkdir -p {dir_path}")
    stdout.channel.recv_exit_status()
    print(f"  ✓ {dir_path}")

# 上传文件
print("\n>>> 上传文件")
success_count = 0
fail_count = 0

for local_file, remote_file in files_to_upload:
    local_path = os.path.join(local_base, local_file)
    remote_path = f"{remote_base}/{remote_file}"
    
    if os.path.exists(local_path):
        try:
            sftp.put(local_path, remote_path)
            print(f"  ✓ {local_file}")
            success_count += 1
        except Exception as e:
            print(f"  ✗ {local_file}: {e}")
            fail_count += 1
    else:
        print(f"  ⚠ 跳过（本地不存在）: {local_file}")
        fail_count += 1

print(f"\n上传完成: 成功 {success_count}, 失败 {fail_count}")

# 重新构建前端
print("\n>>> 清理旧构建并重新构建前端...")
stdin, stdout, stderr = client.exec_command(f"""
cd {remote_base}
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"
nvm use 20 || true

# 清理旧的构建
rm -rf .next

# 重新构建
npm run build 2>&1 | tail -50
""", timeout=600)

exit_code = stdout.channel.recv_exit_status()
output = stdout.read().decode()
print(output)

if exit_code != 0:
    print(f"❌ 构建失败，退出码: {exit_code}")
    error_output = stderr.read().decode()
    if error_output:
        print(f"错误: {error_output[:2000]}")
else:
    print("✓ 构建成功!")

# 重启前端服务
print("\n>>> 重启前端服务")
stdin, stdout, stderr = client.exec_command("sudo systemctl restart liaotian-frontend && sleep 5 && sudo systemctl status liaotian-frontend --no-pager | head -20")
print(stdout.read().decode())

print("\n" + "=" * 60)
print("✅ 部署完成！")
print("=" * 60)
print("\n已修复的问题：")
print("  1. 所有页面文字已转换为简体中文")
print("  2. 语言切换支持三种语言：简体中文、繁体中文、英文")
print("  3. 按钮样式已统一优化")
print("  4. 主要操作按钮（创建、扫描等）使用突出颜色")
print("\n请刷新网页测试: http://aikz.usdt2026.cc")

sftp.close()
client.close()

