#!/bin/bash
# ============================================================
# Deep Clean Virus - Comprehensive Security Cleanup
# ============================================================
#
# Running Environment: Server Linux Environment
# Function: Kill virus processes, clean files, remove cron jobs, check SSH keys, harden Redis
#
# WARNING: This script will modify system files and services. Use with caution.
# One-click execution: sudo bash scripts/server/deep_clean_virus.sh
# ============================================================

set -e

echo "============================================================"
echo "🔒 深度清理病毒 - 全面安全检查"
echo "============================================================"
echo ""
echo "⚠️  警告：此脚本将修改系统文件和配置，请确保您有权限执行"
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 步骤 1: 查杀进程与文件
echo "============================================================"
echo "[1/5] 查杀进程与文件"
echo "============================================================"

# 1.1 强制杀死病毒进程
echo ""
echo "[1.1] 强制杀死病毒进程..."
VIRUS_PROCESSES=(".monitor" ".update" "kdevtmpfsi" "kinsing")
KILLED_COUNT=0

for proc in "${VIRUS_PROCESSES[@]}"; do
  PIDS=$(pgrep -f "$proc" 2>/dev/null || true)
  if [ -n "$PIDS" ]; then
    echo "  发现 $proc 进程: $PIDS"
    for pid in $PIDS; do
      if kill -9 "$pid" 2>/dev/null; then
        echo -e "  ${GREEN}✅ 已杀死进程 $pid${NC}"
        KILLED_COUNT=$((KILLED_COUNT + 1))
      else
        echo -e "  ${YELLOW}⚠️  无法杀死进程 $pid（可能已不存在）${NC}"
      fi
    done
  else
    echo "  ✅ 未发现 $proc 进程"
  fi
done

if [ $KILLED_COUNT -gt 0 ]; then
  echo -e "${GREEN}✅ 已杀死 $KILLED_COUNT 个病毒进程${NC}"
else
  echo "✅ 未发现病毒进程"
fi

# 1.2 删除病毒文件
echo ""
echo "[1.2] 删除病毒文件..."
VIRUS_FILES=("/data/.monitor" "/data/.update")
DELETED_COUNT=0

for file in "${VIRUS_FILES[@]}"; do
  if [ -e "$file" ]; then
    echo "  发现病毒文件: $file"
    if rm -rf "$file" 2>/dev/null; then
      echo -e "  ${GREEN}✅ 已删除: $file${NC}"
      DELETED_COUNT=$((DELETED_COUNT + 1))
    else
      echo -e "  ${YELLOW}⚠️  删除失败，尝试使用 chattr 解锁后删除...${NC}"
      chattr -i "$file" 2>/dev/null || true
      chattr -a "$file" 2>/dev/null || true
      rm -rf "$file" 2>/dev/null && echo -e "  ${GREEN}✅ 已删除: $file${NC}" || echo -e "  ${RED}❌ 删除失败: $file${NC}"
    fi
  else
    echo "  ✅ 文件不存在: $file"
  fi
done

# 1.3 锁定 /data 目录（防止病毒复活）
echo ""
echo "[1.3] 锁定 /data 目录（防止病毒复活）..."
if [ -d "/data" ]; then
  # 先解锁（如果已锁定）
  chattr -i /data 2>/dev/null || true
  chattr -a /data 2>/dev/null || true
  
  # 锁定目录（禁止写入）
  if chattr +i /data 2>/dev/null; then
    echo -e "  ${GREEN}✅ 已锁定 /data 目录（使用 chattr +i）${NC}"
    echo "  ⚠️  注意：如果需要恢复写入权限，请执行: sudo chattr -i /data"
  else
    echo -e "  ${YELLOW}⚠️  锁定失败（可能需要 root 权限）${NC}"
  fi
else
  echo "  ⚠️  /data 目录不存在"
fi

# 步骤 2: 清理定时任务（Crontab）
echo ""
echo "============================================================"
echo "[2/5] 清理定时任务（Crontab）"
echo "============================================================"

# 2.1 备份并清空 ubuntu 用户的 Crontab
echo ""
echo "[2.1] 清理 ubuntu 用户的 Crontab..."
if crontab -u ubuntu -l 2>/dev/null | grep -q .; then
  echo "  发现 ubuntu 用户的定时任务："
  crontab -u ubuntu -l 2>/dev/null | while read line; do
    echo "    $line"
  done
  
  # 备份
  BACKUP_FILE="/tmp/crontab_ubuntu_backup_$(date +%Y%m%d_%H%M%S).txt"
  crontab -u ubuntu -l > "$BACKUP_FILE" 2>/dev/null || true
  echo "  已备份到: $BACKUP_FILE"
  
  # 清空
  if crontab -u ubuntu -r 2>/dev/null; then
    echo -e "  ${GREEN}✅ 已清空 ubuntu 用户的 Crontab${NC}"
  else
    echo -e "  ${YELLOW}⚠️  清空失败（可能没有定时任务）${NC}"
  fi
else
  echo "  ✅ ubuntu 用户没有定时任务"
fi

# 2.2 备份并清空 root 用户的 Crontab
echo ""
echo "[2.2] 清理 root 用户的 Crontab..."
if sudo crontab -l 2>/dev/null | grep -q .; then
  echo "  发现 root 用户的定时任务："
  sudo crontab -l 2>/dev/null | while read line; do
    echo "    $line"
  done
  
  # 备份
  BACKUP_FILE="/tmp/crontab_root_backup_$(date +%Y%m%d_%H%M%S).txt"
  sudo crontab -l > "$BACKUP_FILE" 2>/dev/null || true
  echo "  已备份到: $BACKUP_FILE"
  
  # 清空
  if sudo crontab -r 2>/dev/null; then
    echo -e "  ${GREEN}✅ 已清空 root 用户的 Crontab${NC}"
  else
    echo -e "  ${YELLOW}⚠️  清空失败（可能没有定时任务）${NC}"
  fi
else
  echo "  ✅ root 用户没有定时任务"
fi

# 2.3 检查系统级定时任务目录
echo ""
echo "[2.3] 检查系统级定时任务目录..."
SUSPICIOUS_CRON_FILES=()

# 检查 /etc/cron.d/
echo "  检查 /etc/cron.d/..."
if [ -d "/etc/cron.d" ]; then
  for file in /etc/cron.d/*; do
    if [ -f "$file" ] && [ "$(basename "$file")" != "README" ]; then
      # 检查是否包含可疑内容
      if grep -qiE "(monitor|update|kdevtmpfsi|kinsing|wget.*http|curl.*http)" "$file" 2>/dev/null; then
        echo -e "    ${RED}⚠️  发现可疑文件: $file${NC}"
        SUSPICIOUS_CRON_FILES+=("$file")
      else
        echo "    ✅ 正常文件: $file"
      fi
    fi
  done
fi

# 检查 /etc/cron.hourly/
echo "  检查 /etc/cron.hourly/..."
if [ -d "/etc/cron.hourly" ]; then
  for file in /etc/cron.hourly/*; do
    if [ -f "$file" ] && [ -x "$file" ]; then
      # 检查是否包含可疑内容
      if grep -qiE "(monitor|update|kdevtmpfsi|kinsing|wget.*http|curl.*http)" "$file" 2>/dev/null; then
        echo -e "    ${RED}⚠️  发现可疑文件: $file${NC}"
        SUSPICIOUS_CRON_FILES+=("$file")
      else
        echo "    ✅ 正常文件: $file"
      fi
    fi
  done
fi

# 删除可疑文件
if [ ${#SUSPICIOUS_CRON_FILES[@]} -gt 0 ]; then
  echo ""
  echo "  发现 ${#SUSPICIOUS_CRON_FILES[@]} 个可疑定时任务文件，准备删除..."
  for file in "${SUSPICIOUS_CRON_FILES[@]}"; do
    if sudo rm -f "$file" 2>/dev/null; then
      echo -e "    ${GREEN}✅ 已删除: $file${NC}"
    else
      echo -e "    ${RED}❌ 删除失败: $file${NC}"
    fi
  done
else
  echo "  ✅ 未发现可疑定时任务文件"
fi

# 步骤 3: 检查 SSH 后门
echo ""
echo "============================================================"
echo "[3/5] 检查 SSH 后门"
echo "============================================================"

# 3.1 检查 ubuntu 用户的 authorized_keys
echo ""
echo "[3.1] 检查 /home/ubuntu/.ssh/authorized_keys..."
UBUNTU_SSH_KEY="/home/ubuntu/.ssh/authorized_keys"
if [ -f "$UBUNTU_SSH_KEY" ]; then
  echo "  文件内容："
  LINE_NUM=0
  SUSPICIOUS_KEYS=()
  while IFS= read -r line || [ -n "$line" ]; do
    LINE_NUM=$((LINE_NUM + 1))
    if [ -n "$line" ] && [[ ! "$line" =~ ^# ]]; then
      echo "    第 $LINE_NUM 行: ${line:0:80}..."
      # 检查是否包含可疑内容（非标准密钥格式）
      if [[ ! "$line" =~ ^(ssh-rsa|ssh-ed25519|ecdsa-sha2-nistp256|ecdsa-sha2-nistp384|ecdsa-sha2-nistp521) ]]; then
        echo -e "      ${RED}⚠️  可疑：非标准密钥格式${NC}"
        SUSPICIOUS_KEYS+=("$LINE_NUM:$line")
      fi
    fi
  done < "$UBUNTU_SSH_KEY"
  
  if [ ${#SUSPICIOUS_KEYS[@]} -gt 0 ]; then
    echo ""
    echo -e "  ${YELLOW}⚠️  发现 ${#SUSPICIOUS_KEYS[@]} 个可疑密钥${NC}"
    echo "  请手动检查并决定是否删除"
    echo "  备份文件: ${UBUNTU_SSH_KEY}.backup_$(date +%Y%m%d_%H%M%S)"
    cp "$UBUNTU_SSH_KEY" "${UBUNTU_SSH_KEY}.backup_$(date +%Y%m%d_%H%M%S)"
  else
    echo "  ✅ 未发现可疑密钥"
  fi
else
  echo "  ✅ 文件不存在（正常，如果从未设置过 SSH 密钥）"
fi

# 3.2 检查 root 用户的 authorized_keys
echo ""
echo "[3.2] 检查 /root/.ssh/authorized_keys..."
ROOT_SSH_KEY="/root/.ssh/authorized_keys"
if [ -f "$ROOT_SSH_KEY" ]; then
  echo "  文件内容："
  LINE_NUM=0
  SUSPICIOUS_KEYS=()
  while IFS= read -r line || [ -n "$line" ]; do
    LINE_NUM=$((LINE_NUM + 1))
    if [ -n "$line" ] && [[ ! "$line" =~ ^# ]]; then
      echo "    第 $LINE_NUM 行: ${line:0:80}..."
      # 检查是否包含可疑内容
      if [[ ! "$line" =~ ^(ssh-rsa|ssh-ed25519|ecdsa-sha2-nistp256|ecdsa-sha2-nistp384|ecdsa-sha2-nistp521) ]]; then
        echo -e "      ${RED}⚠️  可疑：非标准密钥格式${NC}"
        SUSPICIOUS_KEYS+=("$LINE_NUM:$line")
      fi
    fi
  done < "$ROOT_SSH_KEY"
  
  if [ ${#SUSPICIOUS_KEYS[@]} -gt 0 ]; then
    echo ""
    echo -e "  ${YELLOW}⚠️  发现 ${#SUSPICIOUS_KEYS[@]} 个可疑密钥${NC}"
    echo "  请手动检查并决定是否删除"
    echo "  备份文件: ${ROOT_SSH_KEY}.backup_$(date +%Y%m%d_%H%M%S)"
    sudo cp "$ROOT_SSH_KEY" "${ROOT_SSH_KEY}.backup_$(date +%Y%m%d_%H%M%S)"
  else
    echo "  ✅ 未发现可疑密钥"
  fi
else
  echo "  ✅ 文件不存在（正常，如果从未设置过 SSH 密钥）"
fi

# 步骤 4: Redis 安全加固
echo ""
echo "============================================================"
echo "[4/5] Redis 安全加固"
echo "============================================================"

# 4.1 查找 Redis 配置文件
echo ""
echo "[4.1] 查找 Redis 配置文件..."
REDIS_CONF=""
POSSIBLE_PATHS=(
  "/etc/redis/redis.conf"
  "/etc/redis.conf"
  "/usr/local/etc/redis.conf"
  "/opt/redis/redis.conf"
)

for path in "${POSSIBLE_PATHS[@]}"; do
  if [ -f "$path" ]; then
    REDIS_CONF="$path"
    echo "  ✅ 找到配置文件: $REDIS_CONF"
    break
  fi
done

if [ -z "$REDIS_CONF" ]; then
  echo -e "  ${YELLOW}⚠️  未找到 Redis 配置文件（可能未安装 Redis）${NC}"
  echo "  跳过 Redis 安全加固步骤"
else
  # 4.2 备份配置文件
  echo ""
  echo "[4.2] 备份 Redis 配置文件..."
  BACKUP_FILE="${REDIS_CONF}.backup_$(date +%Y%m%d_%H%M%S)"
  sudo cp "$REDIS_CONF" "$BACKUP_FILE"
  echo "  ✅ 已备份到: $BACKUP_FILE"
  
  # 4.3 检查并修复 bind 设置
  echo ""
  echo "[4.3] 检查 bind 设置..."
  if grep -q "^bind 127.0.0.1" "$REDIS_CONF" 2>/dev/null; then
    echo "  ✅ bind 127.0.0.1 已设置"
  elif grep -q "^bind" "$REDIS_CONF" 2>/dev/null; then
    echo -e "  ${YELLOW}⚠️  发现其他 bind 设置，将修改为 127.0.0.1${NC}"
    sudo sed -i 's/^bind .*/bind 127.0.0.1/' "$REDIS_CONF"
    echo "  ✅ 已修改为 bind 127.0.0.1"
  else
    echo -e "  ${YELLOW}⚠️  未找到 bind 设置，将添加 bind 127.0.0.1${NC}"
    echo "bind 127.0.0.1" | sudo tee -a "$REDIS_CONF" > /dev/null
    echo "  ✅ 已添加 bind 127.0.0.1"
  fi
  
  # 4.4 检查并设置 requirepass
  echo ""
  echo "[4.4] 检查 requirepass 设置..."
  if grep -q "^requirepass" "$REDIS_CONF" 2>/dev/null; then
    echo "  ✅ requirepass 已设置"
    # 显示密码（隐藏部分字符）
    PASSWORD=$(grep "^requirepass" "$REDIS_CONF" | head -1 | awk '{print $2}')
    if [ -n "$PASSWORD" ]; then
      PASSWORD_MASKED="${PASSWORD:0:4}****"
      echo "  当前密码: $PASSWORD_MASKED"
    fi
  else
    echo -e "  ${YELLOW}⚠️  requirepass 未设置，将生成随机密码${NC}"
    # 生成随机密码
    RANDOM_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
    echo "requirepass $RANDOM_PASSWORD" | sudo tee -a "$REDIS_CONF" > /dev/null
    echo -e "  ${GREEN}✅ 已设置密码: $RANDOM_PASSWORD${NC}"
    echo -e "  ${YELLOW}⚠️  请保存此密码，应用需要更新 Redis 连接配置${NC}"
  fi
  
  # 4.5 重启 Redis 服务
  echo ""
  echo "[4.5] 重启 Redis 服务..."
  if systemctl is-active --quiet redis 2>/dev/null || systemctl is-active --quiet redis-server 2>/dev/null; then
    REDIS_SERVICE=""
    if systemctl list-units --type=service | grep -q "redis.service"; then
      REDIS_SERVICE="redis"
    elif systemctl list-units --type=service | grep -q "redis-server.service"; then
      REDIS_SERVICE="redis-server"
    fi
    
    if [ -n "$REDIS_SERVICE" ]; then
      sudo systemctl restart "$REDIS_SERVICE" && echo -e "  ${GREEN}✅ Redis 服务已重启${NC}" || echo -e "  ${RED}❌ Redis 服务重启失败${NC}"
    else
      echo -e "  ${YELLOW}⚠️  无法确定 Redis 服务名称，请手动重启${NC}"
    fi
  else
    echo "  ⚠️  Redis 服务未运行（可能未安装或已停止）"
  fi
fi

# 步骤 5: 最终检查
echo ""
echo "============================================================"
echo "[5/5] 最终检查"
echo "============================================================"

# 5.1 再次检查病毒进程
echo ""
echo "[5.1] 再次检查病毒进程..."
VIRUS_FOUND=false
for proc in "${VIRUS_PROCESSES[@]}"; do
  if pgrep -f "$proc" > /dev/null 2>&1; then
    echo -e "  ${RED}❌ 仍发现 $proc 进程${NC}"
    VIRUS_FOUND=true
  fi
done
if [ "$VIRUS_FOUND" = false ]; then
  echo -e "  ${GREEN}✅ 未发现病毒进程${NC}"
fi

# 5.2 检查病毒文件
echo ""
echo "[5.2] 再次检查病毒文件..."
FILES_FOUND=false
for file in "${VIRUS_FILES[@]}"; do
  if [ -e "$file" ]; then
    echo -e "  ${RED}❌ 仍存在病毒文件: $file${NC}"
    FILES_FOUND=true
  fi
done
if [ "$FILES_FOUND" = false ]; then
  echo -e "  ${GREEN}✅ 未发现病毒文件${NC}"
fi

# 5.3 显示系统资源使用情况
echo ""
echo "[5.3] 系统资源使用情况..."
echo "  CPU 使用率（Top 5 进程）:"
top -b -n 1 | head -n 12 | tail -n 7 || echo "  无法获取 CPU 信息"

echo ""
echo "============================================================"
echo "✅ 深度清理完成"
echo "============================================================"
echo ""
echo "📋 清理摘要："
echo "  - 已杀死病毒进程: $KILLED_COUNT 个"
echo "  - 已删除病毒文件: $DELETED_COUNT 个"
echo "  - 已清理定时任务: ubuntu 和 root 用户"
echo "  - 已检查 SSH 密钥"
if [ -n "$REDIS_CONF" ]; then
  echo "  - 已加固 Redis 配置"
fi
echo ""
echo "⚠️  重要提示："
echo "  1. /data 目录已锁定（chattr +i），如需恢复写入权限："
echo "     sudo chattr -i /data"
echo "  2. 如果修改了 Redis 密码，请更新应用配置"
echo "  3. 建议重启服务器以确保所有更改生效"
echo "  4. 定期检查系统日志：sudo journalctl -xe"
echo ""

