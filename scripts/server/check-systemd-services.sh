#!/bin/bash
# ============================================================
# 检查 systemd 服务文件是否有问题
# ============================================================

set +e

echo "=========================================="
echo "🔍 检查 Systemd 服务文件"
echo "=========================================="
echo ""

# 检查的服务文件
SERVICE_FILES=(
    "/etc/systemd/system/liaotian-backend.service"
    "/etc/systemd/system/luckyred-api.service"
    "/etc/systemd/system/telegram-bot.service"
    "/lib/systemd/system/liaotian-backend.service"
    "/lib/systemd/system/luckyred-api.service"
    "/lib/systemd/system/telegram-bot.service"
    "/usr/lib/systemd/system/liaotian-backend.service"
    "/usr/lib/systemd/system/luckyred-api.service"
    "/usr/lib/systemd/system/telegram-bot.service"
)

echo "[1/4] 检查服务文件是否存在..."
echo ""
FOUND_SERVICES=0
for service_file in "${SERVICE_FILES[@]}"; do
    if [ -f "$service_file" ]; then
        FOUND_SERVICES=$((FOUND_SERVICES+1))
        echo "  ✅ 找到: $service_file"
    fi
done

if [ "$FOUND_SERVICES" -eq 0 ]; then
    echo "  ⚠️  未找到任何服务文件"
    echo ""
    echo "  检查所有 systemd 服务:"
    systemctl list-unit-files --type=service | grep -E "liaotian|luckyred|telegram" | sed 's/^/    /'
fi
echo ""

echo "[2/4] 分析服务文件内容..."
echo ""
for service_file in "${SERVICE_FILES[@]}"; do
    if [ -f "$service_file" ]; then
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "📄 $service_file"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        
        # 显示完整内容
        cat "$service_file" | sed 's/^/  /'
        
        echo ""
        echo "  分析:"
        
        # 检查可疑内容
        SUSPICIOUS_FOUND=false
        
        # 检查是否有可疑 URL 或 IP
        if grep -E "80.64.16.241|unk.sh|curl.*http|wget.*http" "$service_file" >/dev/null 2>&1; then
            echo "    ❌ 发现可疑 URL/IP"
            SUSPICIOUS_FOUND=true
        fi
        
        # 检查是否有 /data/ 目录相关操作
        if grep -E "/data/" "$service_file" >/dev/null 2>&1; then
            echo "    ⚠️  涉及 /data/ 目录"
            grep -E "/data/" "$service_file" | sed 's/^/      /'
        fi
        
        # 检查 ExecStart 路径
        EXECSTART=$(grep "^ExecStart=" "$service_file" | head -1)
        if [ -n "$EXECSTART" ]; then
            echo "    ExecStart: $EXECSTART"
            
            # 检查路径是否存在
            EXEC_PATH=$(echo "$EXECSTART" | sed 's/ExecStart=//' | awk '{print $1}')
            if [ -f "$EXEC_PATH" ] || [ -x "$EXEC_PATH" ]; then
                echo "      ✅ 可执行文件存在"
                ls -lh "$EXEC_PATH" 2>/dev/null | awk '{print "        大小: " $5 ", 权限: " $1}'
            else
                echo "      ⚠️  可执行文件不存在或不可执行"
            fi
        fi
        
        # 检查 WorkingDirectory
        WORK_DIR=$(grep "^WorkingDirectory=" "$service_file" | head -1 | sed 's/WorkingDirectory=//')
        if [ -n "$WORK_DIR" ]; then
            echo "    WorkingDirectory: $WORK_DIR"
            if [ -d "$WORK_DIR" ]; then
                echo "      ✅ 工作目录存在"
            else
                echo "      ⚠️  工作目录不存在"
            fi
        fi
        
        # 检查是否有可疑的环境变量
        ENV_VARS=$(grep "^Environment=" "$service_file" || true)
        if [ -n "$ENV_VARS" ]; then
            echo "    环境变量:"
            echo "$ENV_VARS" | sed 's/^/      /'
        fi
        
        if [ "$SUSPICIOUS_FOUND" = false ]; then
            echo "    ✅ 未发现明显可疑内容"
        fi
        
        echo ""
    fi
done

echo "[3/4] 检查服务状态..."
echo ""
SERVICE_NAMES=("liaotian-backend.service" "luckyred-api.service" "telegram-bot.service")
for service_name in "${SERVICE_NAMES[@]}"; do
    if systemctl list-unit-files | grep -q "$service_name"; then
        echo "  服务: $service_name"
        systemctl status "$service_name" --no-pager -l | head -15 | sed 's/^/    /'
        echo ""
    fi
done

echo "[4/4] 检查服务关联的进程..."
echo ""
for service_name in "${SERVICE_NAMES[@]}"; do
    if systemctl is-active --quiet "$service_name" 2>/dev/null; then
        echo "  服务 $service_name 正在运行，相关进程:"
        MAIN_PID=$(systemctl show "$service_name" --property=MainPID --value 2>/dev/null)
        if [ -n "$MAIN_PID" ] && [ "$MAIN_PID" != "0" ]; then
            ps aux | grep "^[^ ]* *$MAIN_PID " | grep -v grep | sed 's/^/    /'
            # 检查子进程
            ps --ppid "$MAIN_PID" -o pid,cmd 2>/dev/null | sed 's/^/    /' || true
        fi
        echo ""
    fi
done

echo "=========================================="
echo "📊 检查总结"
echo "=========================================="
echo ""
echo "如果服务文件看起来正常，但系统仍有问题:"
echo "  1. 检查服务实际运行的命令和参数"
echo "  2. 检查服务启动时加载的环境变量"
echo "  3. 检查服务的工作目录中的脚本"
echo "  4. 检查服务的依赖关系"
echo ""
echo "建议:"
echo "  1. 如果服务文件正常，问题可能在其他地方（定时任务、启动脚本等）"
echo "  2. 运行: bash scripts/server/trace-file-origin.sh"
echo "  3. 监控系统，看文件何时被创建"
echo ""

