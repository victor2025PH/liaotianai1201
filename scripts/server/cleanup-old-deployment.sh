#!/bin/bash
# ============================================================
# 清理舊的部署文件腳本
# ============================================================
# 功能：清理 /home/ubuntu/ 下與 telegram-ai-system 重複的文件
# 使用方法：sudo bash scripts/server/cleanup-old-deployment.sh
# ============================================================

set -e

# 顏色輸出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

PROJECT_DIR="/home/ubuntu/telegram-ai-system"
BACKUP_DIR="/home/ubuntu/old-deployment-backup-$(date +%Y%m%d_%H%M%S)"

echo "============================================================"
echo "🧹 清理舊的部署文件"
echo "============================================================"
echo ""
echo "⚠️  此腳本將清理 /home/ubuntu/ 下與項目相關的舊文件"
echo "   這些文件可能是舊的手動部署遺留"
echo ""
echo "當前正確的部署路徑: $PROJECT_DIR"
echo ""

# 檢查是否為 root 用戶
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}❌ 錯誤：請使用 sudo 運行此腳本${NC}"
    exit 1
fi

# 要清理的目錄列表（與 telegram-ai-system 中重複的）
CLEANUP_DIRS=(
    "admin-backend"
    "saas-demo"
    "deploy"
    "scripts"
    "session_service"
    "tools"
    "utils"
    "group_ai_service"
    "migrations"
    "tests"
)

# 要清理的文件列表
CLEANUP_FILES=(
    "main.py"
    "config.py"
    "requirements.txt"
    "deploy_v2.py"
    "git_deploy.py"
    "ecosystem.config.js"
    "ecosystem.config.js.deprecated"
)

echo "📋 將要清理的項目："
echo ""

# 檢查目錄
echo "目錄："
for dir in "${CLEANUP_DIRS[@]}"; do
    if [ -d "/home/ubuntu/$dir" ] && [ ! -L "/home/ubuntu/$dir" ]; then
        if [ -d "$PROJECT_DIR/$dir" ]; then
            echo -e "  ${YELLOW}⚠️  /home/ubuntu/$dir${NC} (與 $PROJECT_DIR/$dir 重複)"
        else
            echo -e "  ${YELLOW}⚠️  /home/ubuntu/$dir${NC} (項目中不存在，可能是舊文件)"
        fi
    fi
done

# 檢查文件
echo ""
echo "文件："
for file in "${CLEANUP_FILES[@]}"; do
    if [ -f "/home/ubuntu/$file" ]; then
        if [ -f "$PROJECT_DIR/$file" ]; then
            echo -e "  ${YELLOW}⚠️  /home/ubuntu/$file${NC} (與 $PROJECT_DIR/$file 重複)"
        else
            echo -e "  ${YELLOW}⚠️  /home/ubuntu/$file${NC} (項目中不存在，可能是舊文件)"
        fi
    fi
done

echo ""
read -p "是否要備份這些文件到 $BACKUP_DIR？(y/n) " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "創建備份目錄..."
    mkdir -p "$BACKUP_DIR"
    
    # 備份目錄
    for dir in "${CLEANUP_DIRS[@]}"; do
        if [ -d "/home/ubuntu/$dir" ] && [ ! -L "/home/ubuntu/$dir" ]; then
            echo "備份 /home/ubuntu/$dir -> $BACKUP_DIR/$dir"
            cp -r "/home/ubuntu/$dir" "$BACKUP_DIR/" 2>/dev/null || true
        fi
    done
    
    # 備份文件
    for file in "${CLEANUP_FILES[@]}"; do
        if [ -f "/home/ubuntu/$file" ]; then
            echo "備份 /home/ubuntu/$file -> $BACKUP_DIR/$file"
            cp "/home/ubuntu/$file" "$BACKUP_DIR/" 2>/dev/null || true
        fi
    done
    
    echo -e "${GREEN}✅ 備份完成${NC}"
    echo ""
fi

echo ""
read -p "確認刪除這些重複文件？(y/n) " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "取消操作"
    exit 0
fi

# 刪除目錄
echo ""
echo "刪除重複目錄..."
for dir in "${CLEANUP_DIRS[@]}"; do
    if [ -d "/home/ubuntu/$dir" ] && [ ! -L "/home/ubuntu/$dir" ]; then
        echo "刪除 /home/ubuntu/$dir"
        rm -rf "/home/ubuntu/$dir"
    fi
done

# 刪除文件
echo ""
echo "刪除重複文件..."
for file in "${CLEANUP_FILES[@]}"; do
    if [ -f "/home/ubuntu/$file" ]; then
        echo "刪除 /home/ubuntu/$file"
        rm -f "/home/ubuntu/$file"
    fi
done

echo ""
echo "============================================================"
echo -e "${GREEN}✅ 清理完成！${NC}"
echo "============================================================"
echo ""
if [ -d "$BACKUP_DIR" ]; then
    echo "備份位置: $BACKUP_DIR"
    echo "如需恢復，可以從備份目錄複製文件"
fi
echo ""

