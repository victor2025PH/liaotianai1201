#!/bin/bash
# ============================================================
# 检查服务自动启动配置
# ============================================================

echo "=========================================="
echo "检查服务自动启动配置"
echo "=========================================="
echo ""

# 定义服务列表
SERVICES=(
    "luckyred-api"
    "liaotian-frontend"
    "telegram-bot"
)

echo "检查服务状态和自动启动配置..."
echo ""

for service in "${SERVICES[@]}"; do
    echo "----------------------------------------"
    echo "服务: $service"
    echo "----------------------------------------"
    
    # 检查服务是否存在
    if systemctl list-unit-files | grep -q "^${service}.service"; then
        # 检查是否启用自动启动
        if systemctl is-enabled "$service" >/dev/null 2>&1; then
            ENABLED_STATUS=$(systemctl is-enabled "$service")
            echo "  自动启动: $ENABLED_STATUS"
        else
            echo "  自动启动: disabled (未启用)"
        fi
        
        # 检查当前状态
        if systemctl is-active "$service" >/dev/null 2>&1; then
            ACTIVE_STATUS=$(systemctl is-active "$service")
            echo "  当前状态: $ACTIVE_STATUS"
        else
            echo "  当前状态: inactive (未运行)"
        fi
        
        # 检查服务文件中的 Install 部分
        SERVICE_FILE="/etc/systemd/system/${service}.service"
        if [ -f "$SERVICE_FILE" ]; then
            if grep -q "WantedBy=multi-user.target" "$SERVICE_FILE"; then
                echo "  配置文件: ✅ 已配置自动启动"
            else
                echo "  配置文件: ⚠️  未配置自动启动"
            fi
        else
            echo "  配置文件: ❌ 服务文件不存在"
        fi
    else
        echo "  ❌ 服务未安装"
    fi
    echo ""
done

echo "=========================================="
echo "总结"
echo "=========================================="
echo ""
echo "如果服务显示 'enabled'，表示会在系统启动时自动启动"
echo "如果服务显示 'disabled'，需要运行以下命令启用："
echo ""
for service in "${SERVICES[@]}"; do
    if systemctl list-unit-files | grep -q "^${service}.service"; then
        if ! systemctl is-enabled "$service" >/dev/null 2>&1; then
            echo "  sudo systemctl enable $service"
        fi
    fi
done
echo ""

