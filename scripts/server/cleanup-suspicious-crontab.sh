#!/bin/bash
# ============================================================
# 清理可疑 crontab 条目
# ============================================================

set -e

echo "=========================================="
echo "🔒 清理可疑 crontab 条目"
echo "时间: $(date)"
echo "=========================================="
echo ""

# 1. 备份当前 crontab
echo "[1/5] 备份当前 crontab..."
echo "----------------------------------------"
BACKUP_FILE="$HOME/crontab_backup_$(date +%Y%m%d_%H%M%S).txt"
if crontab -l > "$BACKUP_FILE" 2>/dev/null; then
  echo "✅ 已备份到: $BACKUP_FILE"
else
  echo "⚠️  当前没有 crontab 条目"
  BACKUP_FILE=""
fi
echo ""

# 2. 显示当前 crontab 内容
echo "[2/5] 当前 crontab 内容："
echo "----------------------------------------"
crontab -l 2>/dev/null || echo "（无内容）"
echo ""

# 3. 识别可疑条目
echo "[3/5] 识别可疑条目..."
echo "----------------------------------------"
SUSPICIOUS_PATTERNS=(
  "\.update startup"
  "/run/user/.*\.update"
  "/var/tmp/.*\.update"
  "/tmp/.*\.update"
)

SUSPICIOUS_FOUND=false
CURRENT_CRON=$(crontab -l 2>/dev/null || echo "")

for pattern in "${SUSPICIOUS_PATTERNS[@]}"; do
  if echo "$CURRENT_CRON" | grep -qE "$pattern"; then
    SUSPICIOUS_FOUND=true
    echo "⚠️  发现可疑条目（匹配模式: $pattern）:"
    echo "$CURRENT_CRON" | grep -E "$pattern" | sed 's/^/    /'
  fi
done

if [ "$SUSPICIOUS_FOUND" = false ]; then
  echo "✅ 未发现可疑条目"
else
  echo ""
  echo "⚠️  发现可疑条目，准备清理..."
fi
echo ""

# 4. 清理可疑条目（只保留合法条目）
echo "[4/5] 清理可疑条目..."
echo "----------------------------------------"

# 合法条目模式（我设置的）
LEGITIMATE_PATTERNS=(
  "monitor-system\.sh"
  "check-and-restore-nginx\.sh"
  "telegram-ai-system"
)

# 创建新的 crontab（只保留合法条目）
if [ -n "$CURRENT_CRON" ]; then
  NEW_CRON=""
  
  while IFS= read -r line; do
    # 跳过空行和注释
    if [[ -z "$line" ]] || [[ "$line" =~ ^[[:space:]]*# ]]; then
      NEW_CRON+="$line"$'\n'
      continue
    fi
    
    # 检查是否是可疑条目
    IS_SUSPICIOUS=false
    for pattern in "${SUSPICIOUS_PATTERNS[@]}"; do
      if echo "$line" | grep -qE "$pattern"; then
        IS_SUSPICIOUS=true
        break
      fi
    done
    
    # 检查是否是合法条目
    IS_LEGITIMATE=false
    for pattern in "${LEGITIMATE_PATTERNS[@]}"; do
      if echo "$line" | grep -qE "$pattern"; then
        IS_LEGITIMATE=true
        break
      fi
    done
    
    # 保留合法条目，删除可疑条目
    if [ "$IS_SUSPICIOUS" = true ]; then
      echo "  ❌ 删除可疑条目: $line"
    elif [ "$IS_LEGITIMATE" = true ]; then
      NEW_CRON+="$line"$'\n'
      echo "  ✅ 保留合法条目: $line"
    else
      # 未知条目，询问用户（这里默认保留，但标记为未知）
      echo "  ⚠️  未知条目（保留）: $line"
      NEW_CRON+="$line"$'\n'
    fi
  done <<< "$CURRENT_CRON"
  
  # 应用新的 crontab
  echo -n "$NEW_CRON" | crontab -
  echo "✅ 已更新 crontab"
else
  echo "✅ 无需清理（crontab 为空）"
fi
echo ""

# 5. 删除可疑文件
echo "[5/5] 删除可疑文件..."
echo "----------------------------------------"
SUSPICIOUS_FILES=(
  "/run/user/1000/.update"
  "/var/tmp/.update"
  "/tmp/.update"
)

for file in "${SUSPICIOUS_FILES[@]}"; do
  if [ -f "$file" ] || [ -d "$file" ]; then
    echo "⚠️  发现可疑文件: $file"
    echo "  文件信息:"
    ls -la "$file" 2>/dev/null || true
    echo "  文件类型:"
    file "$file" 2>/dev/null || true
    echo ""
    echo "  删除文件..."
    sudo rm -rf "$file" 2>/dev/null && echo "  ✅ 已删除" || echo "  ⚠️  删除失败（可能需要手动删除）"
  else
    echo "✅ 文件不存在: $file"
  fi
done
echo ""

# 6. 验证清理结果
echo "=========================================="
echo "🔍 验证清理结果"
echo "=========================================="
echo ""
echo "当前 crontab 内容："
echo "----------------------------------------"
crontab -l 2>/dev/null || echo "（无内容）"
echo ""

# 检查是否还有可疑条目
REMAINING_SUSPICIOUS=false
CURRENT_CRON=$(crontab -l 2>/dev/null || echo "")
for pattern in "${SUSPICIOUS_PATTERNS[@]}"; do
  if echo "$CURRENT_CRON" | grep -qE "$pattern"; then
    REMAINING_SUSPICIOUS=true
    break
  fi
done

if [ "$REMAINING_SUSPICIOUS" = true ]; then
  echo "⚠️  警告: 仍有可疑条目存在，请手动检查"
else
  echo "✅ 未发现可疑条目"
fi
echo ""

# 7. 显示合法条目
echo "合法 crontab 条目（应该保留的）:"
echo "----------------------------------------"
LEGITIMATE_COUNT=0
while IFS= read -r line; do
  if [[ -n "$line" ]] && [[ ! "$line" =~ ^[[:space:]]*# ]]; then
    for pattern in "${LEGITIMATE_PATTERNS[@]}"; do
      if echo "$line" | grep -qE "$pattern"; then
        echo "  ✅ $line"
        ((LEGITIMATE_COUNT++))
        break
      fi
    done
  fi
done <<< "$CURRENT_CRON"

if [ "$LEGITIMATE_COUNT" -eq 0 ]; then
  echo "  （无合法条目）"
fi
echo ""

echo "=========================================="
echo "✅ 清理完成"
echo "=========================================="
echo ""
echo "备份文件: $BACKUP_FILE"
echo ""
echo "建议后续操作："
echo "  1. 检查系统日志: sudo tail -100 /var/log/syslog | grep -E '\.update|startup'"
echo "  2. 检查进程: ps aux | grep -E '\.update|startup' | grep -v grep"
echo "  3. 检查网络连接: sudo netstat -tulpn | grep -E '\.update|startup'"
echo "  4. 运行安全检查: sudo rkhunter --check"
echo ""
