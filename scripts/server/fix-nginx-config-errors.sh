#!/bin/bash
# ============================================================
# 修复 Nginx 配置文件中的错误（移除误添加的命令）
# ============================================================

set +e

echo "=========================================="
echo "🔧 修复 Nginx 配置文件错误"
echo "=========================================="
echo ""

if [ "$EUID" -ne 0 ]; then
    echo "请使用 sudo 运行: sudo bash $0"
    exit 1
fi

# 查找所有配置文件
CONFIG_FILES="/etc/nginx/sites-available/default /etc/nginx/sites-available/aikz.conf /etc/nginx/sites-enabled/default"

for CONFIG_FILE in $CONFIG_FILES; do
    if [ ! -f "$CONFIG_FILE" ]; then
        continue
    fi
    
    echo "检查配置文件: $CONFIG_FILE"
    
    # 检查是否有错误（如 sudo, nano 等命令）
    ERRORS=$(grep -nE "^(sudo|nano|#.*sudo|#.*nano)" "$CONFIG_FILE" 2>/dev/null || true)
    
    if [ -n "$ERRORS" ]; then
        echo "⚠️  发现错误行:"
        echo "$ERRORS"
        echo ""
        
        # 备份
        BACKUP="${CONFIG_FILE}.backup.$(date +%Y%m%d_%H%M%S)"
        cp "$CONFIG_FILE" "$BACKUP"
        echo "✅ 已备份到: $BACKUP"
        
        # 移除错误行
        sed -i '/^sudo/d; /^nano/d; /^#.*sudo/d; /^#.*nano/d' "$CONFIG_FILE"
        echo "✅ 已移除错误行"
        
        # 测试配置
        if nginx -t 2>&1 | grep -q "successful"; then
            echo "✅ 配置语法已修复"
        else
            echo "❌ 配置仍有错误，恢复备份"
            cp "$BACKUP" "$CONFIG_FILE"
            nginx -t 2>&1 | tail -5
        fi
    else
        echo "✅ 未发现错误"
    fi
    echo ""
done

echo "=========================================="
echo "✅ 检查完成"
echo "=========================================="
echo ""

