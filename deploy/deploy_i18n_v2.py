#!/usr/bin/env python3
"""
部署多语言系统更新（三语言版本）
"""
import paramiko
import os

SERVER = "165.154.233.55"
USERNAME = "ubuntu"
PASSWORD = "Along2025!!!"
PROJECT_DIR = "/home/ubuntu/liaotian"

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(SERVER, username=USERNAME, password=PASSWORD, timeout=30)
print("✓ SSH 连接成功!")

sftp = client.open_sftp()

# 本地前端目录
local_base = r"E:\002-工作文件\重要程序\聊天AI群聊程序\saas-demo"
remote_base = f"{PROJECT_DIR}/saas-demo"

# 需要上传的文件
files_to_upload = [
    # i18n 文件
    ("src/lib/i18n/translations.ts", "src/lib/i18n/translations.ts"),
    ("src/lib/i18n/context.tsx", "src/lib/i18n/context.tsx"),
    ("src/lib/i18n/index.ts", "src/lib/i18n/index.ts"),
    
    # 组件文件
    ("src/components/language-toggle.tsx", "src/components/language-toggle.tsx"),
    ("src/components/sidebar.tsx", "src/components/sidebar.tsx"),
    ("src/components/header.tsx", "src/components/header.tsx"),
    
    # 首页
    ("src/app/page.tsx", "src/app/page.tsx"),
]

print("\n>>> 创建目录结构")
dirs_to_create = [
    f"{remote_base}/src/lib/i18n",
]

for dir_path in dirs_to_create:
    stdin, stdout, stderr = client.exec_command(f"mkdir -p {dir_path}")
    stdout.channel.recv_exit_status()
    print(f"  ✓ {dir_path}")

print("\n>>> 上传文件")
for local_file, remote_file in files_to_upload:
    local_path = os.path.join(local_base, local_file)
    remote_path = f"{remote_base}/{remote_file}"
    
    if os.path.exists(local_path):
        print(f"  上传: {local_file}")
        sftp.put(local_path, remote_path)
    else:
        print(f"  ⚠ 跳过（本地不存在）: {local_file}")

# 重新构建
print("\n>>> 重新构建前端...")
stdin, stdout, stderr = client.exec_command(f"""
cd {remote_base}
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"
nvm use 20 || true

# 清理旧的构建
rm -rf .next

# 重新构建
npm run build 2>&1 | tail -30
""", timeout=600)

exit_code = stdout.channel.recv_exit_status()
output = stdout.read().decode()
print(output)

if exit_code != 0:
    print(f"❌ 构建失败，退出码: {exit_code}")
    error_output = stderr.read().decode()
    if error_output:
        print(f"错误: {error_output[:1000]}")
else:
    print("✓ 构建成功!")

# 重启服务
print("\n>>> 重启前端服务")
stdin, stdout, stderr = client.exec_command("sudo systemctl restart liaotian-frontend && sleep 5 && sudo systemctl status liaotian-frontend --no-pager | head -15")
print(stdout.read().decode())

print("\n✅ 部署完成！")
print("\n新增/更新功能：")
print("  1. 三语言支持：简体中文、繁体中文、英文")
print("  2. 点击顶部 🌐 地球图标切换语言")
print("  3. 首页已完成 i18n 国际化")

sftp.close()
client.close()

