# 快速诊断 aiadmin.usdt2026.cc 跳转错误

## 方法一：直接在服务器上创建并运行脚本（最快）

在服务器上执行以下命令，直接创建并运行 Python 诊断脚本：

```bash
# 在服务器上执行
sudo python3 << 'PYTHON_EOF'
import subprocess
import sys
import re
from pathlib import Path

NGINX_CONFIG = "/etc/nginx/sites-available/aiadmin.usdt2026.cc"
NGINX_ENABLED = "/etc/nginx/sites-enabled/aiadmin.usdt2026.cc"
DOMAIN = "aiadmin.usdt2026.cc"

def run_cmd(cmd, check=False):
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=check)
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

print("=" * 60)
print("诊断 aiadmin.usdt2026.cc 跳转错误")
print("=" * 60)
print()

# 1. 检查 Nginx 配置
print("1. 检查 Nginx 配置文件")
print("-" * 60)
config_path = Path(NGINX_CONFIG)
if config_path.exists():
    print(f"✅ 配置文件存在: {NGINX_CONFIG}")
    with open(config_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检查 location / 的 proxy_pass
    match = re.search(r'location\s+/\s*\{[^}]*proxy_pass\s+([^;]+);', content, re.DOTALL)
    if match:
        proxy_pass = match.group(1).strip()
        print(f"找到 location / 的 proxy_pass: {proxy_pass}")
        port_match = re.search(r':(\d+)', proxy_pass)
        if port_match:
            port = port_match.group(1)
            print(f"检测到的代理端口: {port}")
            if port == "3007":
                print("✅ 端口正确 (应该是 3007)")
            else:
                print(f"❌ 端口错误！应该是 3007，但当前是 {port}")
else:
    print(f"❌ 配置文件不存在: {NGINX_CONFIG}")

# 2. 检查端口占用
print()
print("2. 检查端口占用情况")
print("-" * 60)
ports = [3007, 8000, 3003]
for port in ports:
    success, output, _ = run_cmd(f"sudo lsof -ti:{port}", check=False)
    if success and output.strip():
        pid = output.strip()
        _, proc_info, _ = run_cmd(f"ps -p {pid} -o comm= 2>/dev/null", check=False)
        print(f"端口 {port}: 被进程 {pid} ({proc_info.strip()}) 占用")
    else:
        print(f"端口 {port}: 未被占用")

# 3. 检查服务响应
print()
print("3. 检查服务实际响应")
print("-" * 60)
success, output, _ = run_cmd("curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:3007 2>&1", check=False)
if success:
    http_code = output.strip()
    if http_code == "200":
        print(f"✅ 端口 3007 响应正常 (HTTP {http_code})")
        _, content, _ = run_cmd("curl -s http://127.0.0.1:3007 2>&1", check=False)
        if '智控王' in content or 'aizkw' in content.lower():
            print("❌ 警告：端口 3007 返回的是 aizkw 网站内容！")
        elif '三个展示网站管理后台' in content or 'sites-admin' in content.lower():
            print("✅ 端口 3007 返回的是管理后台内容")
    else:
        print(f"❌ 端口 3007 响应异常 (HTTP {http_code})")

# 4. 检查域名响应
print()
print("4. 检查域名实际响应")
print("-" * 60)
success, output, _ = run_cmd(f"curl -s -o /dev/null -w '%{{http_code}}' http://{DOMAIN} 2>&1", check=False)
if success:
    http_code = output.strip()
    print(f"HTTP 状态码: {http_code}")
    if http_code == "200":
        _, domain_content, _ = run_cmd(f"curl -s http://{DOMAIN} 2>&1", check=False)
        if '智控王' in domain_content or 'aizkw' in domain_content.lower():
            print("❌ 发现 aizkw 网站内容！域名指向了错误的网站")
        elif '三个展示网站管理后台' in domain_content:
            print("✅ 发现管理后台内容")
        else:
            print("⚠️  无法识别内容类型")

print()
print("=" * 60)
print("诊断完成")
print("=" * 60)
PYTHON_EOF
```

## 方法二：从 GitHub 拉取脚本后运行（标准方法）

### 步骤 1：提交脚本到 GitHub

在本地执行：

```bash
cd D:\telegram-ai-system
git add scripts/diagnose_aiadmin_redirect.sh scripts/diagnose_aiadmin_redirect.py
git commit -m "添加 aiadmin 跳转错误诊断脚本"
git push origin main
```

### 步骤 2：在服务器上拉取并运行

在服务器上执行：

```bash
# 1. 进入项目目录
cd /home/ubuntu/telegram-ai-system

# 2. 拉取最新代码
git pull origin main

# 3. 运行诊断脚本（选择其中一个）
# 方法 A：使用 Bash 脚本
sudo bash scripts/diagnose_aiadmin_redirect.sh

# 方法 B：使用 Python 脚本
sudo python3 scripts/diagnose_aiadmin_redirect.py
```

## 推荐方式

**优先使用方法一**，因为：
1. 不需要提交代码到 GitHub
2. 可以直接运行，立即看到结果
3. 适合快速诊断问题

运行诊断脚本后，请将输出结果发给我，我会根据结果提供修复方案。

