#!/bin/bash
# 服务器急救脚本 - 解决内存溢出 (OOM) 问题
# 创建 Swap、修复 DNS、释放缓存、安全重启服务

set -e

echo "=========================================="
echo "服务器急救脚本 - 解决内存溢出问题"
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

# ============ 步骤 1: 创建 4GB Swap 文件 ============
echo "[1/4] 创建 4GB 虚拟内存 (Swap)"
echo "----------------------------------------"

# 检查是否已有 Swap
EXISTING_SWAP=$(swapon --show | grep -v "NAME" | wc -l || echo "0")
SWAPFILE_SIZE="4G"

if [ "$EXISTING_SWAP" -gt 0 ]; then
    echo "检测到已存在的 Swap:"
    swapon --show
    echo ""
    read -p "是否继续创建新的 Swap 文件? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "跳过 Swap 创建"
    else
        # 检查 /swapfile 是否已存在
        if [ -f /swapfile ]; then
            echo "检测到 /swapfile 已存在"
            read -p "是否删除并重新创建? (y/N): " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                swapoff /swapfile 2>/dev/null || true
                rm -f /swapfile
                echo "✅ 已删除旧的 Swap 文件"
            else
                echo "跳过 Swap 创建"
                SKIP_SWAP=true
            fi
        fi
        
        if [ "$SKIP_SWAP" != "true" ]; then
            echo "创建 ${SWAPFILE_SIZE} Swap 文件..."
            fallocate -l ${SWAPFILE_SIZE} /swapfile || dd if=/dev/zero of=/swapfile bs=1M count=4096
            chmod 600 /swapfile
            mkswap /swapfile
            swapon /swapfile
            echo -e "${GREEN}✅ Swap 文件已创建并启用${NC}"
            
            # 写入 /etc/fstab 确保重启有效
            if ! grep -q "/swapfile" /etc/fstab; then
                echo "/swapfile none swap sw 0 0" >> /etc/fstab
                echo -e "${GREEN}✅ 已写入 /etc/fstab${NC}"
            else
                echo "⚠️  /etc/fstab 中已存在 /swapfile 配置"
            fi
        fi
    fi
else
    # 没有 Swap，直接创建
    echo "未检测到 Swap，开始创建..."
    
    # 检查 /swapfile 是否已存在但未启用
    if [ -f /swapfile ]; then
        echo "检测到 /swapfile 文件存在但未启用，尝试启用..."
        chmod 600 /swapfile
        mkswap /swapfile
        swapon /swapfile
        echo -e "${GREEN}✅ 已启用现有 Swap 文件${NC}"
    else
        echo "创建 ${SWAPFILE_SIZE} Swap 文件..."
        
        # 检查可用磁盘空间
        AVAILABLE_SPACE=$(df -BG / | tail -1 | awk '{print $4}' | sed 's/G//')
        if [ "$AVAILABLE_SPACE" -lt 5 ]; then
            echo -e "${YELLOW}警告: 可用磁盘空间不足 5GB，可能无法创建 4GB Swap${NC}"
            read -p "是否继续? (y/N): " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                echo "跳过 Swap 创建"
                SKIP_SWAP=true
            fi
        fi
        
        if [ "$SKIP_SWAP" != "true" ]; then
            # 使用 fallocate（更快）或 dd（兼容性更好）
            if command -v fallocate >/dev/null 2>&1; then
                fallocate -l ${SWAPFILE_SIZE} /swapfile && echo "✅ 使用 fallocate 创建 Swap 文件" || {
                    echo "fallocate 失败，使用 dd 创建..."
                    dd if=/dev/zero of=/swapfile bs=1M count=4096 status=progress
                }
            else
                echo "使用 dd 创建 Swap 文件（这可能需要几分钟）..."
                dd if=/dev/zero of=/swapfile bs=1M count=4096 status=progress
            fi
            
            chmod 600 /swapfile
            mkswap /swapfile
            swapon /swapfile
            echo -e "${GREEN}✅ Swap 文件已创建并启用${NC}"
            
            # 写入 /etc/fstab 确保重启有效
            if ! grep -q "/swapfile" /etc/fstab; then
                echo "/swapfile none swap sw 0 0" >> /etc/fstab
                echo -e "${GREEN}✅ 已写入 /etc/fstab${NC}"
            fi
        fi
    fi
fi

# 显示当前 Swap 状态
echo ""
echo "当前 Swap 状态:"
swapon --show
free -h | grep -i swap
echo ""

# ============ 步骤 2: 限制并重启 DNS 服务 ============
echo "[2/4] 限制并重启 DNS 服务 (systemd-resolved)"
echo "----------------------------------------"

# 备份配置文件
if [ -f /etc/systemd/resolved.conf ]; then
    cp /etc/systemd/resolved.conf /etc/systemd/resolved.conf.backup.$(date +%Y%m%d_%H%M%S)
    echo "✅ 已备份配置文件"
fi

# 修改 DNSStubListener 配置
if [ -f /etc/systemd/resolved.conf ]; then
    # 检查 [Resolve] 部分是否存在
    if ! grep -q "^\[Resolve\]" /etc/systemd/resolved.conf; then
        echo "" >> /etc/systemd/resolved.conf
        echo "[Resolve]" >> /etc/systemd/resolved.conf
    fi
    
    # 取消注释并设置 DNSStubListener=no
    if grep -q "^DNSStubListener=" /etc/systemd/resolved.conf; then
        sed -i 's/^DNSStubListener=.*/DNSStubListener=no/' /etc/systemd/resolved.conf
        echo "✅ 已设置 DNSStubListener=no"
    elif grep -q "^#DNSStubListener=" /etc/systemd/resolved.conf; then
        sed -i 's/^#DNSStubListener=.*/DNSStubListener=no/' /etc/systemd/resolved.conf
        echo "✅ 已取消注释并设置 DNSStubListener=no"
    else
        # 在 [Resolve] 部分后添加
        sed -i '/^\[Resolve\]/a DNSStubListener=no' /etc/systemd/resolved.conf
        echo "✅ 已添加 DNSStubListener=no"
    fi
else
    echo "⚠️  /etc/systemd/resolved.conf 不存在，创建新文件..."
    cat > /etc/systemd/resolved.conf <<EOF
[Resolve]
DNSStubListener=no
EOF
    echo "✅ 已创建配置文件"
fi

# 重启 systemd-resolved
echo "重启 systemd-resolved 服务..."
systemctl restart systemd-resolved && echo -e "${GREEN}✅ systemd-resolved 已重启${NC}" || echo -e "${YELLOW}⚠️  systemd-resolved 重启失败（可能已停止）${NC}"

sleep 2

# 检查服务状态
if systemctl is-active --quiet systemd-resolved; then
    echo -e "${GREEN}✅ systemd-resolved 运行正常${NC}"
else
    echo -e "${YELLOW}⚠️  systemd-resolved 未运行${NC}"
fi

echo ""

# ============ 步骤 3: 释放缓存 ============
echo "[3/4] 释放系统缓存"
echo "----------------------------------------"

echo "同步文件系统..."
sync

echo "释放页面缓存、目录项和 inode..."
echo 3 > /proc/sys/vm/drop_caches && echo -e "${GREEN}✅ 缓存已释放${NC}" || echo -e "${YELLOW}⚠️  释放缓存失败${NC}"

echo ""
echo "当前内存使用情况:"
free -h
echo ""

# ============ 步骤 4: 安全重启业务服务 ============
echo "[4/4] 安全重启业务服务"
echo "----------------------------------------"

# 停止所有服务
echo "停止所有服务..."

# 停止 PM2（如果存在）
if command -v pm2 >/dev/null 2>&1; then
    echo "停止 PM2 进程..."
    pm2 kill 2>/dev/null && echo -e "${GREEN}✅ PM2 已停止${NC}" || echo "⚠️  PM2 未运行或停止失败"
fi

# 停止前端服务
if systemctl list-unit-files | grep -q "liaotian-frontend.service"; then
    echo "停止 liaotian-frontend 服务..."
    systemctl stop liaotian-frontend && echo -e "${GREEN}✅ liaotian-frontend 已停止${NC}" || echo -e "${YELLOW}⚠️  liaotian-frontend 停止失败${NC}"
fi

# 停止后端服务
if systemctl list-unit-files | grep -q "luckyred-api.service"; then
    echo "停止 luckyred-api 服务..."
    systemctl stop luckyred-api && echo -e "${GREEN}✅ luckyred-api 已停止${NC}" || echo -e "${YELLOW}⚠️  luckyred-api 停止失败${NC}"
fi

echo ""
echo "等待 5 秒确保服务完全停止..."
sleep 5

# 检查进程是否还在运行
REMAINING_PROCESSES=$(ps aux | grep -E "(node|uvicorn|python.*main.py)" | grep -v grep | wc -l || echo "0")
if [ "$REMAINING_PROCESSES" -gt 0 ]; then
    echo -e "${YELLOW}警告: 仍有 $REMAINING_PROCESSES 个相关进程在运行${NC}"
    echo "尝试强制终止..."
    pkill -9 -f "node.*next" 2>/dev/null || true
    pkill -9 -f "uvicorn" 2>/dev/null || true
    pkill -9 -f "python.*main.py" 2>/dev/null || true
    sleep 2
fi

echo ""
echo "依次启动服务..."

# 先启动后端
if systemctl list-unit-files | grep -q "luckyred-api.service"; then
    echo "启动 luckyred-api 服务..."
    systemctl start luckyred-api && echo -e "${GREEN}✅ luckyred-api 已启动${NC}" || echo -e "${RED}❌ luckyred-api 启动失败${NC}"
    
    echo "等待 10 秒让后端服务完全启动..."
    sleep 10
    
    # 检查后端状态
    if systemctl is-active --quiet luckyred-api; then
        echo -e "${GREEN}✅ luckyred-api 运行正常${NC}"
    else
        echo -e "${RED}❌ luckyred-api 启动失败，请检查日志${NC}"
        systemctl status luckyred-api --no-pager -l | head -n 10 || true
    fi
else
    echo "⚠️  luckyred-api 服务不存在，跳过"
fi

echo ""

# 再启动前端
if systemctl list-unit-files | grep -q "liaotian-frontend.service"; then
    echo "启动 liaotian-frontend 服务..."
    systemctl start liaotian-frontend && echo -e "${GREEN}✅ liaotian-frontend 已启动${NC}" || echo -e "${RED}❌ liaotian-frontend 启动失败${NC}"
    
    echo "等待 5 秒让前端服务启动..."
    sleep 5
    
    # 检查前端状态
    if systemctl is-active --quiet liaotian-frontend; then
        echo -e "${GREEN}✅ liaotian-frontend 运行正常${NC}"
    else
        echo -e "${RED}❌ liaotian-frontend 启动失败，请检查日志${NC}"
        systemctl status liaotian-frontend --no-pager -l | head -n 10 || true
    fi
else
    echo "⚠️  liaotian-frontend 服务不存在，跳过"
fi

echo ""

# ============ 最终检查 ============
echo "=========================================="
echo "最终检查"
echo "=========================================="
echo ""

echo "内存和 Swap 使用情况:"
free -h
echo ""

echo "Swap 状态:"
swapon --show
echo ""

echo "服务状态:"
systemctl is-active luckyred-api >/dev/null 2>&1 && echo -e "luckyred-api: ${GREEN}运行中${NC}" || echo -e "luckyred-api: ${RED}未运行${NC}"
systemctl is-active liaotian-frontend >/dev/null 2>&1 && echo -e "liaotian-frontend: ${GREEN}运行中${NC}" || echo -e "liaotian-frontend: ${RED}未运行${NC}"
echo ""

echo "Top 10 进程 CPU 和内存占用:"
echo "----------------------------------------"
top -b -n 1 | head -n 17
echo ""

echo "=========================================="
echo -e "${GREEN}急救脚本执行完成！${NC}"
echo "=========================================="
echo ""
echo "后续建议："
echo "1. 持续监控内存使用: watch -n 2 'free -h'"
echo "2. 如果内存仍然不足，考虑："
echo "   - 增加 Swap 大小（当前 4GB）"
echo "   - 优化应用内存使用"
echo "   - 升级服务器内存"
echo "3. 检查服务日志确认启动正常："
echo "   - sudo journalctl -u luckyred-api -n 50"
echo "   - sudo journalctl -u liaotian-frontend -n 50"
echo "4. 监控 systemd-resolved CPU 占用"
echo ""

