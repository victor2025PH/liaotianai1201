#!/bin/bash
# 修复 CPU 和 DNS 高占用问题
# 解决 systemd-resolved 占用过高 CPU 的问题

set -e

echo "=========================================="
echo "修复 CPU 和 DNS 高占用问题"
echo "=========================================="
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查是否为 root 用户
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}错误: 请使用 sudo 运行此脚本${NC}"
    exit 1
fi

# ============ 步骤 1: 修复 DNS 高占用 ============
echo "[1/4] 修复 DNS 高占用（systemd-resolved）"
echo "----------------------------------------"

# 检查 systemd-resolved 是否运行
if systemctl is-active --quiet systemd-resolved; then
    echo "检测到 systemd-resolved 正在运行"
    
    # 先尝试重启服务
    echo "尝试重启 systemd-resolved 服务..."
    systemctl restart systemd-resolved || echo "⚠️  重启失败，继续下一步"
    
    # 等待 3 秒检查状态
    sleep 3
    
    # 检查 CPU 占用（通过 top 命令）
    echo "检查 systemd-resolved 的 CPU 占用..."
    RESOLVED_CPU=$(top -b -n 1 | grep systemd-resolved | awk '{print $9}' | head -n 1 || echo "0")
    
    if [ -n "$RESOLVED_CPU" ] && [ "$(echo "$RESOLVED_CPU > 50" | bc 2>/dev/null || echo 0)" = "1" ]; then
        echo -e "${YELLOW}警告: systemd-resolved CPU 占用仍然很高 (${RESOLVED_CPU}%)${NC}"
        echo "尝试修改 DNSStubListener 配置..."
        
        # 备份配置文件
        if [ -f /etc/systemd/resolved.conf ]; then
            cp /etc/systemd/resolved.conf /etc/systemd/resolved.conf.backup.$(date +%Y%m%d_%H%M%S)
            echo "✅ 已备份配置文件"
        fi
        
        # 修改 DNSStubListener
        if grep -q "^DNSStubListener=yes" /etc/systemd/resolved.conf 2>/dev/null; then
            sed -i 's/^DNSStubListener=yes/DNSStubListener=no/' /etc/systemd/resolved.conf
            echo "✅ 已将 DNSStubListener 设置为 no"
            
            # 重启服务使配置生效
            systemctl restart systemd-resolved || echo "⚠️  重启失败"
            sleep 2
        elif grep -q "^#DNSStubListener=yes" /etc/systemd/resolved.conf 2>/dev/null; then
            # 如果被注释了，取消注释并设置为 no
            sed -i 's/^#DNSStubListener=yes/DNSStubListener=no/' /etc/systemd/resolved.conf
            echo "✅ 已取消注释并将 DNSStubListener 设置为 no"
            systemctl restart systemd-resolved || echo "⚠️  重启失败"
            sleep 2
        else
            # 如果配置不存在，添加它
            if ! grep -q "DNSStubListener" /etc/systemd/resolved.conf 2>/dev/null; then
                echo "" >> /etc/systemd/resolved.conf
                echo "[Resolve]" >> /etc/systemd/resolved.conf
                echo "DNSStubListener=no" >> /etc/systemd/resolved.conf
                echo "✅ 已添加 DNSStubListener=no 配置"
                systemctl restart systemd-resolved || echo "⚠️  重启失败"
                sleep 2
            fi
        fi
        
        # 再次检查 CPU 占用
        sleep 3
        RESOLVED_CPU_AFTER=$(top -b -n 1 | grep systemd-resolved | awk '{print $9}' | head -n 1 || echo "0")
        
        if [ -n "$RESOLVED_CPU_AFTER" ] && [ "$(echo "$RESOLVED_CPU_AFTER > 50" | bc 2>/dev/null || echo 0)" = "1" ]; then
            echo -e "${YELLOW}警告: 修改配置后 CPU 占用仍然很高 (${RESOLVED_CPU_AFTER}%)${NC}"
            echo "尝试暂时停止 systemd-resolved 服务..."
            echo -e "${YELLOW}注意: 停止此服务可能会影响域名解析${NC}"
            
            read -p "是否继续停止 systemd-resolved? (y/N): " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                systemctl stop systemd-resolved
                systemctl disable systemd-resolved
                echo "✅ systemd-resolved 已停止并禁用"
            else
                echo "跳过停止 systemd-resolved"
            fi
        else
            echo -e "${GREEN}✅ DNS 问题已解决，CPU 占用已降低${NC}"
        fi
    else
        echo -e "${GREEN}✅ systemd-resolved CPU 占用正常${NC}"
    fi
else
    echo "systemd-resolved 未运行，跳过"
fi

echo ""

# ============ 步骤 2: 优化防火墙日志 ============
echo "[2/4] 优化防火墙日志（关闭 UFW 日志记录）"
echo "----------------------------------------"

if command -v ufw >/dev/null 2>&1; then
    CURRENT_LOGGING=$(ufw status verbose 2>/dev/null | grep "Logging:" | awk '{print $2}' || echo "unknown")
    
    if [ "$CURRENT_LOGGING" != "off" ]; then
        echo "当前防火墙日志状态: $CURRENT_LOGGING"
        echo "关闭防火墙日志记录..."
        ufw logging off && echo -e "${GREEN}✅ 防火墙日志已关闭${NC}" || echo -e "${RED}❌ 关闭防火墙日志失败${NC}"
    else
        echo -e "${GREEN}✅ 防火墙日志已关闭${NC}"
    fi
else
    echo "⚠️  UFW 未安装，跳过"
fi

echo ""

# ============ 步骤 3: 重启业务服务 ============
echo "[3/4] 重启业务服务"
echo "----------------------------------------"

# 重启 luckyred-api
if systemctl list-unit-files | grep -q "luckyred-api.service"; then
    echo "重启 luckyred-api 服务..."
    systemctl restart luckyred-api && echo -e "${GREEN}✅ luckyred-api 已重启${NC}" || echo -e "${RED}❌ luckyred-api 重启失败${NC}"
    sleep 2
    systemctl status luckyred-api --no-pager -l | head -n 5 || true
else
    echo "⚠️  luckyred-api 服务不存在，跳过"
fi

echo ""

# 重启 liaotian-frontend
if systemctl list-unit-files | grep -q "liaotian-frontend.service"; then
    echo "重启 liaotian-frontend 服务..."
    systemctl restart liaotian-frontend && echo -e "${GREEN}✅ liaotian-frontend 已重启${NC}" || echo -e "${RED}❌ liaotian-frontend 重启失败${NC}"
    sleep 2
    systemctl status liaotian-frontend --no-pager -l | head -n 5 || true
else
    echo "⚠️  liaotian-frontend 服务不存在，跳过"
fi

echo ""

# ============ 步骤 4: 最后检查 ============
echo "[4/4] 检查当前 CPU 占用情况"
echo "----------------------------------------"
echo ""

echo "Top 20 进程 CPU 占用情况:"
echo "----------------------------------------"
top -b -n 1 | head -n 20

echo ""
echo "=========================================="
echo -e "${GREEN}修复完成！${NC}"
echo "=========================================="
echo ""
echo "建议后续操作："
echo "1. 持续监控 CPU 占用: watch -n 2 'top -b -n 1 | head -n 20'"
echo "2. 如果 systemd-resolved 问题持续，考虑："
echo "   - 检查 DNS 服务器配置"
echo "   - 检查是否有 DNS 查询风暴"
echo "   - 考虑使用其他 DNS 解析方案"
echo "3. 检查防火墙规则，避免过多的日志记录"
echo ""

