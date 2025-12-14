#!/bin/bash
# ============================================================
# 分析可疑文件（验证是否为恶意软件）
# ============================================================

set +e

echo "=========================================="
echo "🔍 分析可疑文件"
echo "=========================================="
echo ""

# 检测到的可疑文件
SUSPICIOUS_FILES=("/data/4pVffo7" "/data/T1ID" "/data/ZaAxbGP")

echo "[1/6] 检查文件基本信息..."
echo ""
for file in "${SUSPICIOUS_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "📄 文件: $file"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        
        # 基本信息
        echo "基本信息:"
        ls -lh "$file" | awk '{print "  大小: " $5 "\n  权限: " $1 "\n  所有者: " $3 ":" $4 "\n  修改时间: " $6 " " $7 " " $8}'
        
        # 文件类型
        echo ""
        echo "文件类型:"
        file_type=$(file "$file" 2>/dev/null || echo "无法确定")
        echo "  $file_type"
        
        # 前几个字节（十六进制）
        echo ""
        echo "文件头部（前32字节，十六进制）:"
        hexdump -C "$file" | head -2 | sed 's/^/  /'
        
        # 字符串内容（前20行）
        echo ""
        echo "可打印字符串（前20行）:"
        strings "$file" 2>/dev/null | head -20 | sed 's/^/  /' || echo "  无法提取字符串"
        
        echo ""
    fi
done

echo ""
echo "[2/6] 检查是否有进程在使用这些文件..."
echo ""
PROCESSES_FOUND=false
for file in "${SUSPICIOUS_FILES[@]}"; do
    if [ -f "$file" ]; then
        FILE_NAME=$(basename "$file")
        
        # 使用 lsof 检查
        LSOF_OUTPUT=$(sudo lsof "$file" 2>/dev/null || true)
        if [ -n "$LSOF_OUTPUT" ]; then
            PROCESSES_FOUND=true
            echo "  ❌ 发现进程正在使用: $file"
            echo "$LSOF_OUTPUT" | sed 's/^/    /'
        fi
        
        # 检查进程名
        PS_OUTPUT=$(ps aux | grep -E "$FILE_NAME" | grep -v grep || true)
        if [ -n "$PS_OUTPUT" ]; then
            PROCESSES_FOUND=true
            echo "  ❌ 发现相关进程:"
            echo "$PS_OUTPUT" | awk '{printf "    PID:%-8s CPU:%-6s MEM:%-6s CMD: %s\n", $2, $3"%", $4"%", $11}' | sed 's/^/    /'
        fi
    fi
done

if [ "$PROCESSES_FOUND" = false ]; then
    echo "  ✅ 未发现进程使用这些文件"
fi
echo ""

echo "[3/6] 检查文件是否在运行（通过进程列表）..."
echo ""
RUNNING_FILES=0
for file in "${SUSPICIOUS_FILES[@]}"; do
    if [ -f "$file" ]; then
        FILE_NAME=$(basename "$file")
        # 检查是否有同名进程在运行
        if pgrep -f "$FILE_NAME" >/dev/null 2>&1; then
            RUNNING_FILES=$((RUNNING_FILES+1))
            echo "  ❌ $FILE_NAME 正在运行！"
            ps aux | grep -E "$FILE_NAME" | grep -v grep | awk '{printf "    PID:%-8s CPU:%-6s MEM:%-6s CMD: %s\n", $2, $3"%", $4"%", $11}'
        else
            echo "  ✅ $FILE_NAME 未在运行"
        fi
    fi
done
echo ""

echo "[4/6] 检查文件网络连接..."
echo ""
for file in "${SUSPICIOUS_FILES[@]}"; do
    if [ -f "$file" ]; then
        FILE_NAME=$(basename "$file")
        # 查找使用该文件的进程的网络连接
        PIDS=$(pgrep -f "$FILE_NAME" 2>/dev/null || true)
        if [ -n "$PIDS" ]; then
            for pid in $PIDS; do
                NET_CONN=$(sudo ss -tunp 2>/dev/null | grep "pid=$pid" || true)
                if [ -n "$NET_CONN" ]; then
                    echo "  ❌ $FILE_NAME (PID: $pid) 的网络连接:"
                    echo "$NET_CONN" | sed 's/^/    /'
                fi
            done
        fi
    fi
done
echo ""

echo "[5/6] 检查文件创建来源（通过系统日志）..."
echo ""
for file in "${SUSPICIOUS_FILES[@]}"; do
    if [ -f "$file" ]; then
        FILE_NAME=$(basename "$file")
        # 检查最近的系统日志
        echo "  检查 $FILE_NAME 相关日志:"
        sudo journalctl -u cron --since "1 hour ago" 2>/dev/null | grep -i "$FILE_NAME" | tail -5 | sed 's/^/    /' || echo "    未找到相关日志"
        
        # 检查 auth.log
        if [ -f /var/log/auth.log ]; then
            sudo grep -i "$FILE_NAME" /var/log/auth.log 2>/dev/null | tail -3 | sed 's/^/    /' || true
        fi
    fi
done
echo ""

echo "[6/6] 检查文件哈希值（用于威胁情报查询）..."
echo ""
for file in "${SUSPICIOUS_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "  $file:"
        if command -v md5sum >/dev/null 2>&1; then
            MD5=$(md5sum "$file" 2>/dev/null | awk '{print $1}')
            echo "    MD5:    $MD5"
        fi
        if command -v sha256sum >/dev/null 2>&1; then
            SHA256=$(sha256sum "$file" 2>/dev/null | awk '{print $1}')
            echo "    SHA256: $SHA256"
        fi
        echo ""
    fi
done

echo "=========================================="
echo "📊 分析总结"
echo "=========================================="
echo ""

# 判断是否为恶意软件的特征
MALICIOUS_INDICATORS=0

for file in "${SUSPICIOUS_FILES[@]}"; do
    if [ -f "$file" ]; then
        FILE_NAME=$(basename "$file")
        
        # 特征 1: 随机文件名
        if [[ ! "$FILE_NAME" =~ ^[a-zA-Z0-9._-]+$ ]] || [ ${#FILE_NAME} -lt 3 ] || [ ${#FILE_NAME} -gt 20 ]; then
            MALICIOUS_INDICATORS=$((MALICIOUS_INDICATORS+1))
        fi
        
        # 特征 2: 可执行权限
        if [ -x "$file" ]; then
            MALICIOUS_INDICATORS=$((MALICIOUS_INDICATORS+1))
        fi
        
        # 特征 3: 文件大小在几MB范围（常见恶意软件大小）
        FILE_SIZE=$(stat -c%s "$file" 2>/dev/null || echo "0")
        if [ "$FILE_SIZE" -gt 1000000 ] && [ "$FILE_SIZE" -lt 10000000 ]; then
            MALICIOUS_INDICATORS=$((MALICIOUS_INDICATORS+1))
        fi
        
        # 特征 4: 有进程在使用
        if pgrep -f "$FILE_NAME" >/dev/null 2>&1; then
            MALICIOUS_INDICATORS=$((MALICIOUS_INDICATORS+1))
        fi
    fi
done

echo "恶意软件特征匹配数: $MALICIOUS_INDICATORS"
echo ""

if [ "$MALICIOUS_INDICATORS" -ge 3 ]; then
    echo "⚠️  高度可疑！这些文件很可能是恶意软件。"
    echo ""
    echo "建议立即操作:"
    echo "  1. 终止所有相关进程"
    echo "  2. 删除这些文件"
    echo "  3. 检查定时任务和启动项"
    echo "  4. 更改所有密码"
    echo ""
    echo "运行删除脚本:"
    echo "  bash scripts/server/delete-new-malware-files.sh"
elif [ "$MALICIOUS_INDICATORS" -ge 2 ]; then
    echo "⚠️  可疑文件，建议进一步检查。"
else
    echo "✅ 未发现明显的恶意软件特征，但建议保持警惕。"
fi

echo ""

