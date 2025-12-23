#!/bin/bash
# 启动并检查 Nginx 服务

set -e

echo "🔧 检查并启动 Nginx 服务..."

# 检查 Nginx 是否安装
if ! command -v nginx &> /dev/null; then
    echo "❌ Nginx 未安装"
    echo "安装命令: sudo apt update && sudo apt install -y nginx"
    exit 1
fi

# 检查 Nginx 状态
if sudo systemctl is-active --quiet nginx; then
    echo "✅ Nginx 服务正在运行"
    sudo systemctl status nginx --no-pager | head -5
else
    echo "⚠️  Nginx 服务未运行，正在启动..."
    
    # 测试配置
    echo "🧪 测试 Nginx 配置..."
    if sudo nginx -t; then
        echo "✅ Nginx 配置测试通过"
        
        # 启动服务
        echo "🚀 启动 Nginx 服务..."
        sudo systemctl start nginx
        
        # 设置开机自启
        sudo systemctl enable nginx
        
        # 检查状态
        sleep 2
        if sudo systemctl is-active --quiet nginx; then
            echo "✅ Nginx 服务已启动"
            sudo systemctl status nginx --no-pager | head -5
        else
            echo "❌ Nginx 启动失败"
            echo "查看错误日志:"
            sudo journalctl -u nginx -n 20 --no-pager
            exit 1
        fi
    else
        echo "❌ Nginx 配置测试失败"
        echo "请修复配置错误后重试"
        exit 1
    fi
fi

# 检查端口监听
echo ""
echo "🔌 检查端口监听状态:"
if sudo netstat -tlnp | grep -E ":80 |:443 " > /dev/null 2>&1; then
    echo "✅ Nginx 正在监听端口:"
    sudo netstat -tlnp | grep -E ":80 |:443 " | head -5
else
    echo "⚠️  未检测到 Nginx 监听 80/443 端口"
    echo "检查所有监听端口:"
    sudo netstat -tlnp | grep nginx | head -5 || echo "未找到 Nginx 进程"
fi

echo ""
echo "📋 Nginx 服务状态:"
sudo systemctl status nginx --no-pager | head -10

