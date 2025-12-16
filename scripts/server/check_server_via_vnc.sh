#!/bin/bash
# ============================================================
# 通过 VNC 控制台检查服务器状态脚本
# ============================================================
# 
# 功能：
# 当 SSH 无法连接时，可以通过 VNC 控制台登录后运行此脚本
# 检查服务器状态、服务状态、网络连接等
#
# 使用方法：
# 1. 通过 UCloud 控制台的 VNC 登录服务器
# 2. 运行: bash scripts/server/check_server_via_vnc.sh
# ============================================================

echo "============================================================"
echo "服务器状态检查脚本（VNC 控制台版本）"
echo "============================================================"
echo "开始时间: $(date)"
echo ""

# ============================================================
# [1/7] 检查系统基本信息
# ============================================================
echo "[1/7] 检查系统基本信息"
echo "------------------------------------------------------------"
echo "□ 系统负载:"
uptime
echo ""

echo "□ 系统运行时间:"
uptime -p 2>/dev/null || echo "无法获取运行时间"
echo ""

echo "□ 内存使用:"
free -h
echo ""

echo "□ 磁盘使用:"
df -h | head -5
echo ""

# ============================================================
# [2/7] 检查网络连接
# ============================================================
echo "[2/7] 检查网络连接"
echo "------------------------------------------------------------"

echo "□ 网络接口:"
ip addr show | grep -E "inet |state " || ifconfig | grep -E "inet |flags"
echo ""

echo "□ 测试外网连接:"
if ping -c 3 8.8.8.8 > /dev/null 2>&1; then
    echo "✅ 外网连接正常"
else
    echo "❌ 外网连接失败"
fi
echo ""

echo "□ 测试 DNS 解析:"
if ping -c 3 google.com > /dev/null 2>&1; then
    echo "✅ DNS 解析正常"
else
    echo "❌ DNS 解析失败"
fi
echo ""

# ============================================================
# [3/7] 检查 SSH 服务
# ============================================================
echo "[3/7] 检查 SSH 服务"
echo "------------------------------------------------------------"

if systemctl is-active --quiet ssh 2>/dev/null || systemctl is-active --quiet sshd 2>/dev/null; then
    echo "✅ SSH 服务运行中"
    systemctl status ssh --no-pager | head -5 || systemctl status sshd --no-pager | head -5
else
    echo "❌ SSH 服务未运行"
    echo "   尝试启动 SSH 服务..."
    sudo systemctl start ssh 2>/dev/null || sudo systemctl start sshd 2>/dev/null || echo "启动失败"
fi
echo ""

echo "□ SSH 端口监听:"
if ss -tlnp 2>/dev/null | grep -q ":22 "; then
    echo "✅ 端口 22 正在监听"
    ss -tlnp 2>/dev/null | grep ":22 "
else
    echo "❌ 端口 22 未监听"
fi
echo ""

# ============================================================
# [4/7] 检查应用服务
# ============================================================
echo "[4/7] 检查应用服务"
echo "------------------------------------------------------------"

# 检查 Nginx
echo "□ Nginx 服务:"
if systemctl is-active --quiet nginx 2>/dev/null; then
    echo "✅ Nginx 运行中"
    systemctl status nginx --no-pager | head -5
else
    echo "❌ Nginx 未运行"
    echo "   尝试启动 Nginx..."
    sudo systemctl start nginx 2>/dev/null && echo "✅ Nginx 已启动" || echo "❌ Nginx 启动失败"
fi
echo ""

# 检查前端服务
echo "□ 前端服务:"
if systemctl is-active --quiet liaotian-frontend 2>/dev/null; then
    echo "✅ 前端服务运行中"
    systemctl status liaotian-frontend --no-pager | head -5
else
    echo "❌ 前端服务未运行"
    echo "   尝试启动前端服务..."
    sudo systemctl start liaotian-frontend 2>/dev/null && echo "✅ 前端服务已启动" || echo "❌ 前端服务启动失败"
fi
echo ""

# 检查后端服务
echo "□ 后端服务:"
if systemctl is-active --quiet luckyred-api 2>/dev/null; then
    echo "✅ 后端服务运行中"
    systemctl status luckyred-api --no-pager | head -5
else
    echo "❌ 后端服务未运行"
    echo "   尝试启动后端服务..."
    sudo systemctl start luckyred-api 2>/dev/null && echo "✅ 后端服务已启动" || echo "❌ 后端服务启动失败"
fi
echo ""

# ============================================================
# [5/7] 检查端口监听
# ============================================================
echo "[5/7] 检查端口监听"
echo "------------------------------------------------------------"

PORTS=(22 80 443 3000 8000)
for port in "${PORTS[@]}"; do
    if ss -tlnp 2>/dev/null | grep -q ":$port "; then
        echo "✅ 端口 $port 正在监听"
        ss -tlnp 2>/dev/null | grep ":$port "
    else
        echo "❌ 端口 $port 未监听"
    fi
done
echo ""

# ============================================================
# [6/7] 检查防火墙
# ============================================================
echo "[6/7] 检查防火墙"
echo "------------------------------------------------------------"

# 检查 UFW
if command -v ufw > /dev/null 2>&1; then
    echo "□ UFW 状态:"
    sudo ufw status | head -10
else
    echo "□ UFW 未安装"
fi
echo ""

# 检查 iptables
if command -v iptables > /dev/null 2>&1; then
    echo "□ iptables 规则（端口 22, 80, 443）:"
    sudo iptables -L -n 2>/dev/null | grep -E "22|80|443" || echo "未找到相关规则"
fi
echo ""

# ============================================================
# [7/7] 检查服务日志（最近错误）
# ============================================================
echo "[7/7] 检查服务日志（最近错误）"
echo "------------------------------------------------------------"

echo "□ Nginx 错误日志（最后 10 行）:"
sudo tail -10 /var/log/nginx/error.log 2>/dev/null || echo "无法读取 Nginx 错误日志"
echo ""

echo "□ 后端服务错误日志（最后 10 行）:"
sudo journalctl -u luckyred-api -n 20 --no-pager 2>/dev/null | grep -i "error\|exception" | tail -5 || echo "未找到错误日志"
echo ""

echo "□ 前端服务错误日志（最后 10 行）:"
sudo journalctl -u liaotian-frontend -n 20 --no-pager 2>/dev/null | grep -i "error\|exception" | tail -5 || echo "未找到错误日志"
echo ""

# ============================================================
# 总结和建议
# ============================================================
echo "============================================================"
echo "检查总结"
echo "============================================================"

echo ""
echo "如果服务未运行，可以执行以下命令重启："
echo "  sudo systemctl restart nginx"
echo "  sudo systemctl restart liaotian-frontend"
echo "  sudo systemctl restart luckyred-api"
echo "  sudo systemctl restart ssh"
echo ""

echo "如果所有服务都正常但仍无法从外部访问，请检查："
echo "1. 云服务商安全组/防火墙规则"
echo "2. 服务器公网 IP 地址是否正确"
echo "3. DNS 解析是否正确"
echo ""

echo "============================================================"
echo "检查完成"
echo "结束时间: $(date)"
echo "============================================================"

