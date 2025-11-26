#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
重新构建前端并重启服务
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
    
    servers = config.get('servers', {})
    server_name = list(servers.keys())[0]
    server_config = servers[server_name]
    
    return {
        'host': server_config['host'],
        'user': server_config.get('user', 'ubuntu'),
        'password': server_config.get('password', ''),
        'deploy_dir': server_config.get('deploy_dir', '/opt/smart-tg')
    }

def connect_server(host, user, password):
    """连接服务器"""
    print(f"连接服务器: {host}...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(host, username=user, password=password, timeout=10)
    print("[OK] 连接成功")
    return ssh

def main():
    config = load_config()
    ssh = connect_server(config['host'], config['user'], config['password'])
    
    try:
        deploy_dir = config['deploy_dir']
        frontend_dir = f"{deploy_dir}/saas-demo"
        
        print("\n" + "=" * 50)
        print("重新构建前端")
        print("=" * 50)
        
        # 1. 停止前端服务
        print("\n[1] 停止前端服务...")
        ssh.exec_command("sudo systemctl stop smart-tg-frontend")
        time.sleep(2)
        print("[OK] 服务已停止")
        
        # 2. 上传修复后的代码
        print("\n[2] 准备上传修复后的代码...")
        print("  需要手动上传 saas-demo/src/components/layout-wrapper.tsx")
        print("  或者使用以下命令在服务器上直接修复:")
        
        # 创建修复脚本
        fix_script = """#!/bin/bash
cd /home/ubuntu/saas-demo
# 备份原文件
cp src/components/layout-wrapper.tsx src/components/layout-wrapper.tsx.bak

# 修复认证检查逻辑
cat > /tmp/fix_layout.patch << 'ENDPATCH'
--- a/src/components/layout-wrapper.tsx
+++ b/src/components/layout-wrapper.tsx
@@ -18,6 +18,7 @@ export function LayoutWrapper({ children }: { children: React.ReactNode }) {
       const authenticated = isAuthenticated();
       
       if (!isLoginPage && !authenticated) {
+        setChecking(false); // 先停止檢查狀態，避免卡住
         // 未登錄且不在登入頁，強制重定向到登入頁
         if (window.location.pathname !== "/login") {
           window.location.href = "/login";
@@ -28,7 +29,7 @@ export function LayoutWrapper({ children }: { children: React.ReactNode }) {
         setAuthState(authenticated);
       }
       
-      if (isLoginPage || authenticated) {
-        setChecking(false);
-      }
+      // 無論是否認證，都應該停止檢查狀態
+      setChecking(false);
       
       return authenticated;
     };
@@ -75,7 +76,7 @@ export function LayoutWrapper({ children }: { children: React.ReactNode }) {
       window.removeEventListener("tokenCleared", handleTokenCleared);
     };
-  }, [pathname, router, isLoginPage]);
+  }, [pathname, router, isLoginPage, authState]);
ENDPATCH

# 应用修复（使用 sed 直接修改）
sed -i 's/if (isLoginPage || authenticated) {/\/\/ 無論是否認證，都應該停止檢查狀態\n      setChecking(false);\n      \/\/ 原代码: if (isLoginPage || authenticated) {/' src/components/layout-wrapper.tsx
sed -i '/if (!isLoginPage && !authenticated) {/a\        setChecking(false); // 先停止檢查狀態，避免卡住' src/components/layout-wrapper.tsx
sed -i 's/}, \[pathname, router, isLoginPage\]);/}, [pathname, router, isLoginPage, authState]);/' src/components/layout-wrapper.tsx

echo "[OK] 代码修复完成"
"""
        
        # 在服务器上执行修复
        print("\n[3] 在服务器上修复代码...")
        stdin, stdout, stderr = ssh.exec_command(fix_script)
        stdout.channel.recv_exit_status()
        output = stdout.read().decode('utf-8')
        error = stderr.read().decode('utf-8')
        if output:
            print(output)
        if error:
            print(f"[ERROR] {error}")
        
        # 3. 重新构建前端
        print("\n[4] 重新构建前端...")
        stdin, stdout, stderr = ssh.exec_command(f"cd {frontend_dir} && npm run build 2>&1")
        print("  构建中，请稍候...")
        
        # 实时输出构建日志
        while True:
            if stdout.channel.exit_status_ready():
                break
            line = stdout.readline()
            if line:
                print(f"  {line.strip()}")
            time.sleep(0.1)
        
        exit_status = stdout.channel.recv_exit_status()
        remaining = stdout.read().decode('utf-8')
        if remaining:
            print(remaining)
        
        error_output = stderr.read().decode('utf-8')
        if error_output:
            print(f"[ERROR] {error_output}")
        
        if exit_status != 0:
            print(f"\n[ERROR] 构建失败 (退出码: {exit_status})")
            return
        
        print("[OK] 构建完成")
        
        # 4. 重启前端服务
        print("\n[5] 重启前端服务...")
        ssh.exec_command("sudo systemctl restart smart-tg-frontend")
        time.sleep(3)
        
        # 检查服务状态
        stdin, stdout, stderr = ssh.exec_command("systemctl is-active smart-tg-frontend")
        status = stdout.read().decode('utf-8').strip()
        if status == "active":
            print("[OK] 前端服务已启动")
        else:
            print(f"[WARNING] 前端服务状态: {status}")
            print("查看日志:")
            stdin, stdout, stderr = ssh.exec_command("sudo journalctl -u smart-tg-frontend -n 10 --no-pager")
            logs = stdout.read().decode('utf-8')
            print(logs)
        
        print("\n" + "=" * 50)
        print("修复完成！")
        print("=" * 50)
        print(f"\n请清除浏览器缓存后访问: http://{config['host']}:3000")
        
    finally:
        ssh.close()

if __name__ == "__main__":
    main()

