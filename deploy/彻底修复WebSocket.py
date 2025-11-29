# -*- coding: utf-8 -*-
"""彻底修复 WebSocket 配置 - 包括重启服务"""
import paramiko
import sys
import io
import time

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

SERVER = "165.154.233.55"
USERNAME = "ubuntu"
PASSWORD = "Along2025!!!"

def exec_cmd(ssh, cmd, wait=True):
    stdin, stdout, stderr = ssh.exec_command(cmd)
    if wait:
        stdout.channel.recv_exit_status()
    output = stdout.read().decode('utf-8', errors='ignore')
    error = stderr.read().decode('utf-8', errors='ignore')
    return output, error

print("=" * 60)
print("彻底修复 WebSocket 配置")
print("=" * 60)
print()

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(SERVER, username=USERNAME, password=PASSWORD, timeout=30)
    print("[OK] 已连接服务器\n")
    
    # 1. 备份并修复配置
    print(">>> [1/8] 检查并修复配置...")
    output, _ = exec_cmd(ssh, "sudo grep -c 'location /api/v1/notifications/ws' /etc/nginx/sites-available/aikz.usdt2026.cc")
    count = int(output.strip() or "0")
    print(f"当前 location 块数量: {count}")
    
    if count > 1:
        print("发现重复配置，执行修复...")
        exec_cmd(ssh, "sudo cp /etc/nginx/sites-available/aikz.usdt2026.cc /etc/nginx/sites-available/aikz.usdt2026.cc.bak.deep")
        
        fix_code = '''import re
f=open('/etc/nginx/sites-available/aikz.usdt2026.cc','r',encoding='utf-8')
lines=f.readlines()
f.close()
idx=[i for i,l in enumerate(lines) if 'location /api/v1/notifications/ws' in l]
if len(idx)>1:
    for i in reversed(idx[1:]):
        s=i
        for j in range(max(0,i-3),i):
            if '# WebSocket' in lines[j] or ('#' in lines[j] and 'WebSocket' in lines[j]):
                s=j
                break
        b=0
        e=i
        f=False
        for j in range(i,len(lines)):
            if '{' in lines[j]:
                b+=lines[j].count('{')
                f=True
            if '}' in lines[j]:
                b-=lines[j].count('}')
                if f and b==0:
                    e=j
                    break
        lines=lines[:s]+lines[e+1:]
    with open('/etc/nginx/sites-available/aikz.usdt2026.cc','w',encoding='utf-8') as f:
        f.writelines(lines)
    print('已删除',len(idx)-1,'个重复块')
else:
    print('无需修复')
'''
        
        sftp = ssh.open_sftp()
        f = sftp.file('/tmp/fix_deep.py', 'w')
        f.write(fix_code)
        f.close()
        sftp.close()
        
        output, _ = exec_cmd(ssh, "sudo python3 /tmp/fix_deep.py")
        print(output)
        exec_cmd(ssh, "rm /tmp/fix_deep.py")
        
        output, _ = exec_cmd(ssh, "sudo grep -c 'location /api/v1/notifications/ws' /etc/nginx/sites-available/aikz.usdt2026.cc")
        count = int(output.strip() or "0")
        print(f"修复后 location 数量: {count}\n")
    
    if count != 1:
        print(f"[错误] 仍有 {count} 个 location 块")
        ssh.close()
        sys.exit(1)
    
    # 2. 验证配置语法
    print(">>> [2/8] 测试 Nginx 配置语法...")
    output, error = exec_cmd(ssh, "sudo nginx -t")
    print(output)
    if "syntax is ok" not in output:
        print("[错误] 配置语法错误")
        ssh.close()
        sys.exit(1)
    print("[OK] 配置语法正确\n")
    
    # 3. 显示 WebSocket 配置
    print(">>> [3/8] 当前 WebSocket 配置：")
    output, _ = exec_cmd(ssh, "sudo grep -A 15 'location /api/v1/notifications/ws' /etc/nginx/sites-available/aikz.usdt2026.cc")
    print(output)
    print()
    
    # 4. 重启 Nginx（而不是 reload，确保配置完全生效）
    print(">>> [4/8] 重启 Nginx 服务...")
    exec_cmd(ssh, "sudo systemctl restart nginx")
    time.sleep(2)
    output, _ = exec_cmd(ssh, "sudo systemctl is-active nginx")
    print(f"Nginx 状态: {output.strip()}\n")
    
    # 5. 检查后端服务
    print(">>> [5/8] 检查后端服务...")
    output, _ = exec_cmd(ssh, "sudo systemctl is-active liaotian-backend")
    backend_status = output.strip()
    print(f"后端服务状态: {backend_status}")
    
    if backend_status != "active":
        print("重启后端服务...")
        exec_cmd(ssh, "sudo systemctl restart liaotian-backend")
        time.sleep(3)
        output, _ = exec_cmd(ssh, "sudo systemctl is-active liaotian-backend")
        print(f"重启后状态: {output.strip()}\n")
    else:
        print("[OK] 后端服务正常运行\n")
    
    # 6. 检查端口监听
    print(">>> [6/8] 检查端口监听...")
    output, _ = exec_cmd(ssh, "sudo ss -tlnp | grep -E ':80|:8000'")
    print(output if output.strip() else "未检测到端口")
    print()
    
    # 7. 测试 WebSocket 端点（HTTP 方式，应该返回 400 或类似错误，说明路由存在）
    print(">>> [7/8] 测试 WebSocket 路由...")
    output, _ = exec_cmd(ssh, "curl -s -o /dev/null -w '%{http_code}' http://localhost:8000/api/v1/notifications/ws/test@example.com || echo '无法连接'")
    print(f"后端 WebSocket 端点响应: {output.strip()}")
    print()
    
    # 8. 检查 Nginx 错误日志
    print(">>> [8/8] 检查最近的 Nginx 错误日志...")
    output, _ = exec_cmd(ssh, "sudo tail -5 /var/log/nginx/error.log 2>&1 | grep -i websocket || echo '无 WebSocket 相关错误'")
    print(output if output.strip() else "无相关错误")
    
    print("\n" + "=" * 60)
    print("[完成] 修复和验证完成！")
    print("=" * 60)
    print("\n重要提示：")
    print("1. Nginx 已重启，配置已生效")
    print("2. 请在前端浏览器中：")
    print("   - 完全关闭浏览器标签页")
    print("   - 重新打开 http://aikz.usdt2026.cc")
    print("   - 或使用无痕模式（Ctrl+Shift+N）")
    print("3. 打开开发者工具（F12）→ Network → 筛选 WS")
    print("4. 检查 WebSocket 连接状态")
    print("\n如果仍有错误，请检查：")
    print("- 浏览器控制台的详细错误信息")
    print("- 后端日志：sudo journalctl -u liaotian-backend -n 100")
    print("- Nginx 日志：sudo tail -f /var/log/nginx/error.log")
    
    ssh.close()
    
except Exception as e:
    print(f"\n[错误] {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n修复完成！")

