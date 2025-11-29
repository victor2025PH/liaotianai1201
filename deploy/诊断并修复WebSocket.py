# -*- coding: utf-8 -*-
"""诊断并修复 WebSocket 连接问题"""
import paramiko
import sys
import io

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

SERVER = "165.154.233.55"
USERNAME = "ubuntu"
PASSWORD = "Along2025!!!"

def exec_cmd(ssh, cmd):
    stdin, stdout, stderr = ssh.exec_command(cmd)
    output = stdout.read().decode('utf-8', errors='ignore')
    error = stderr.read().decode('utf-8', errors='ignore')
    return output.strip(), error.strip()

print("=" * 60)
print("诊断并修复 WebSocket 连接问题")
print("=" * 60)
print()

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(SERVER, username=USERNAME, password=PASSWORD, timeout=30)
    print("[OK] 已连接服务器\n")
    
    # 1. 检查 location 数量
    print(">>> [1] 检查 location 块数量...")
    output, _ = exec_cmd(ssh, "sudo grep -c 'location /api/v1/notifications/ws' /etc/nginx/sites-available/aikz.usdt2026.cc")
    count = int(output or "0")
    print(f"Location 块数量: {count}")
    
    if count > 1:
        print("\n[修复] 发现重复配置，正在修复...")
        exec_cmd(ssh, "sudo cp /etc/nginx/sites-available/aikz.usdt2026.cc /etc/nginx/sites-available/aikz.usdt2026.cc.bak.diagnose")
        
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
        f = sftp.file('/tmp/fix_diag.py', 'w')
        f.write(fix_code)
        f.close()
        sftp.close()
        
        output, _ = exec_cmd(ssh, "sudo python3 /tmp/fix_diag.py")
        print(output)
        exec_cmd(ssh, "rm /tmp/fix_diag.py")
    
    # 2. 显示 WebSocket 配置
    print("\n>>> [2] 当前 WebSocket 配置：")
    output, _ = exec_cmd(ssh, "sudo grep -A 15 'location /api/v1/notifications/ws' /etc/nginx/sites-available/aikz.usdt2026.cc")
    print(output)
    if not output:
        print("[错误] 未找到 WebSocket 配置！")
    
    # 3. 测试配置
    print("\n>>> [3] 测试 Nginx 配置...")
    output, error = exec_cmd(ssh, "sudo nginx -t")
    print(output)
    if "syntax is ok" not in output:
        print("[错误] 配置语法错误")
        ssh.close()
        sys.exit(1)
    
    # 4. 重启 Nginx
    print("\n>>> [4] 重启 Nginx...")
    exec_cmd(ssh, "sudo systemctl restart nginx")
    import time
    time.sleep(2)
    output, _ = exec_cmd(ssh, "sudo systemctl is-active nginx")
    print(f"Nginx 状态: {output}")
    
    # 5. 检查后端服务
    print("\n>>> [5] 检查后端服务...")
    output, _ = exec_cmd(ssh, "sudo systemctl is-active liaotian-backend")
    print(f"后端服务状态: {output}")
    
    if output != "active":
        print("重启后端服务...")
        exec_cmd(ssh, "sudo systemctl restart liaotian-backend")
        time.sleep(3)
        output, _ = exec_cmd(ssh, "sudo systemctl is-active liaotian-backend")
        print(f"重启后状态: {output}")
    
    # 6. 检查端口
    print("\n>>> [6] 检查端口监听...")
    output, _ = exec_cmd(ssh, "sudo ss -tlnp | grep -E ':80|:8000'")
    print(output if output else "未检测到端口")
    
    # 7. 测试后端 WebSocket 端点（直接访问，应该返回错误但说明路由存在）
    print("\n>>> [7] 测试后端 WebSocket 路由...")
    output, _ = exec_cmd(ssh, "curl -s -o /dev/null -w '%{http_code}' http://localhost:8000/api/v1/notifications/ws/test 2>&1 || echo '无法连接'")
    print(f"后端响应码: {output}")
    
    # 8. 检查 Nginx 错误日志
    print("\n>>> [8] 检查 Nginx 错误日志（最近 10 行）...")
    output, _ = exec_cmd(ssh, "sudo tail -10 /var/log/nginx/error.log 2>&1")
    if output:
        print(output)
    else:
        print("无错误日志")
    
    # 9. 检查后端日志
    print("\n>>> [9] 检查后端日志（最近 5 行，包含 websocket）...")
    output, _ = exec_cmd(ssh, "sudo journalctl -u liaotian-backend -n 50 --no-pager | grep -i websocket | tail -5 || echo '无 WebSocket 相关日志'")
    print(output if output else "无相关日志")
    
    # 10. 验证完整的 Nginx 配置
    print("\n>>> [10] 验证完整的 Nginx server 配置...")
    output, _ = exec_cmd(ssh, "sudo grep -A 5 -B 5 'notifications/ws' /etc/nginx/sites-available/aikz.usdt2026.cc")
    print(output)
    
    print("\n" + "=" * 60)
    print("诊断完成")
    print("=" * 60)
    print("\n如果 WebSocket 仍然失败，可能的原因：")
    print("1. 后端 WebSocket 路由未正确注册")
    print("2. 后端服务未正常运行")
    print("3. 防火墙阻止了连接")
    print("4. WebSocket URL 构建有问题")
    print("\n建议检查：")
    print("- 后端 API 文档：http://aikz.usdt2026.cc/docs")
    print("- 查看是否有 /api/v1/notifications/ws/{user_email} 路由")
    
    ssh.close()
    
except Exception as e:
    print(f"\n[错误] {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n诊断完成！")

