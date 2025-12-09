#!/bin/bash
# 禁用或精简 MOTD（Message of the Day）以加快 SSH 连接速度

echo "=========================================="
echo "优化 SSH 连接速度 - 禁用 MOTD"
echo "=========================================="
echo ""

# 1. 备份原始文件
echo "1. 备份原始 MOTD 文件"
echo "----------------------------------------"
if [ -f /etc/motd ]; then
    sudo cp /etc/motd /etc/motd.backup
    echo "✓ 已备份 /etc/motd"
fi

if [ -d /etc/update-motd.d ]; then
    sudo tar -czf /tmp/motd.d.backup.tar.gz /etc/update-motd.d 2>/dev/null
    echo "✓ 已备份 /etc/update-motd.d"
fi
echo ""

# 2. 禁用动态 MOTD
echo "2. 禁用动态 MOTD"
echo "----------------------------------------"
if [ -d /etc/update-motd.d ]; then
    # 重命名所有脚本，添加 .disabled 后缀
    for file in /etc/update-motd.d/*; do
        if [ -f "$file" ] && [[ ! "$file" =~ \.disabled$ ]]; then
            sudo mv "$file" "${file}.disabled" 2>/dev/null || true
        fi
    done
    echo "✓ 已禁用动态 MOTD 脚本"
else
    echo "⚠️  /etc/update-motd.d 目录不存在"
fi
echo ""

# 3. 创建简化的 MOTD
echo "3. 创建简化的 MOTD"
echo "----------------------------------------"
sudo tee /etc/motd > /dev/null << 'EOF'
Welcome to Ubuntu Server
EOF
echo "✓ 已创建简化的 MOTD"
echo ""

# 4. 禁用 SSH 横幅（如果配置了）
echo "4. 检查 SSH 配置"
echo "----------------------------------------"
if grep -q "Banner" /etc/ssh/sshd_config 2>/dev/null; then
    echo "⚠️  SSH 配置中有 Banner，可能需要手动注释"
    echo "   编辑 /etc/ssh/sshd_config 并注释 Banner 行"
else
    echo "✓ SSH 配置正常"
fi
echo ""

echo "=========================================="
echo "优化完成"
echo "=========================================="
echo ""
echo "下次 SSH 连接应该会更快。"
echo ""
echo "如果需要恢复原始 MOTD："
echo "  sudo mv /etc/motd.backup /etc/motd"
echo "  sudo tar -xzf /tmp/motd.d.backup.tar.gz -C /"
echo ""

