import paramiko

HOST = '165.154.233.55'
USER = 'ubuntu'

FIX_SCRIPT = r"""
#!/bin/bash
set -e

echo "🔧 开始修复 Nginx..."

# 1. 检查并安装 Nginx
if ! command -v nginx &> /dev/null; then
    echo "Installing Nginx..."
    sudo apt-get update
    sudo apt-get install -y nginx
fi

# 2. 写入 Nginx 配置
echo "Writing Nginx config..."
sudo bash -c "cat > /etc/nginx/sites-available/aikz.conf <<EOF
server {
    listen 80;
    server_name aikz.usdt2026.cc;

    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF"

# 3. 启用配置
echo "Enabling config..."
sudo ln -sf /etc/nginx/sites-available/aikz.conf /etc/nginx/sites-enabled/aikz.conf
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl restart nginx

# 4. 验证服务状态
echo ""
echo "=== 服务状态检查 ==="
echo "Frontned Service:"
sudo systemctl status liaotian-frontend.service --no-pager
echo ""
echo "Nginx Service:"
sudo systemctl status nginx --no-pager

echo ""
echo "🎉 修复完成！请访问 http://aikz.usdt2026.cc"
"""

try:
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER)
    
    print("正在执行修复脚本...")
    cmd = f"cat > /tmp/fix_nginx.sh << 'END_SCRIPT'\n{FIX_SCRIPT}\nEND_SCRIPT\n"
    cmd += "chmod +x /tmp/fix_nginx.sh && bash /tmp/fix_nginx.sh"
    
    stdin, stdout, stderr = client.exec_command(cmd, get_pty=True)
    for line in iter(stdout.readline, ""):
        print(line, end="")
        
    client.close()
except Exception as e:
    print(f"❌ 错误: {e}")