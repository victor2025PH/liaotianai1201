#!/bin/bash

# 快速應用配置到三個項目的腳本
# 使用方法: ./apply-to-projects.sh

set -e

# 顏色輸出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}=========================================="
echo "React/Vite 項目自動化配置應用工具"
echo "==========================================${NC}"

# 項目配置
PROJECTS=("aizkw" "tgmini" "hongbao")
BASE_DIR="/home/ubuntu"

# 檢查模板文件是否存在
TEMPLATE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ ! -f "${TEMPLATE_DIR}/src/config.ts" ]; then
    echo -e "${RED}❌ 錯誤: 找不到模板文件${NC}"
    echo "請確保在模板目錄中運行此腳本"
    exit 1
fi

echo -e "${YELLOW}請確認以下信息：${NC}"
echo "1. 項目目錄基礎路徑: ${BASE_DIR}"
echo "2. 項目列表: ${PROJECTS[@]}"
echo ""
read -p "是否繼續？(y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "已取消"
    exit 0
fi

# 為每個項目應用配置
for PROJECT in "${PROJECTS[@]}"; do
    echo -e "\n${GREEN}處理項目: ${PROJECT}${NC}"
    
    # 構建項目路徑（根據實際情況修改）
    PROJECT_DIR="${BASE_DIR}/${PROJECT}20251219"
    
    # 檢查項目目錄是否存在
    if [ ! -d "${PROJECT_DIR}" ]; then
        echo -e "${YELLOW}⚠️  警告: 項目目錄不存在: ${PROJECT_DIR}${NC}"
        echo "請手動確認目錄路徑"
        continue
    fi
    
    echo "項目目錄: ${PROJECT_DIR}"
    
    # 創建必要的目錄
    mkdir -p "${PROJECT_DIR}/src"
    mkdir -p "${PROJECT_DIR}/.github/workflows"
    
    # 複製配置文件
    echo "📋 複製配置文件..."
    
    # 複製 config.ts
    if [ -f "${TEMPLATE_DIR}/src/config.ts" ]; then
        cp "${TEMPLATE_DIR}/src/config.ts" "${PROJECT_DIR}/src/config.ts"
        echo "  ✅ 已複製 src/config.ts"
    fi
    
    # 複製 ecosystem.config.js
    if [ -f "${TEMPLATE_DIR}/ecosystem.config.js" ]; then
        cp "${TEMPLATE_DIR}/ecosystem.config.js" "${PROJECT_DIR}/ecosystem.config.js"
        # 替換項目名稱
        sed -i "s/name: \"frontend\"/name: \"${PROJECT}\"/g" "${PROJECT_DIR}/ecosystem.config.js"
        echo "  ✅ 已複製 ecosystem.config.js"
    fi
    
    # 複製 GitHub Actions 配置
    if [ -f "${TEMPLATE_DIR}/.github/workflows/deploy.yml" ]; then
        cp "${TEMPLATE_DIR}/.github/workflows/deploy.yml" "${PROJECT_DIR}/.github/workflows/deploy.yml"
        # 替換項目名稱和目錄
        sed -i "s/PROJECT_NAME=\"aizkw\"/PROJECT_NAME=\"${PROJECT}\"/g" "${PROJECT_DIR}/.github/workflows/deploy.yml"
        sed -i "s|PROJECT_DIR=\"/home/ubuntu/aizkw20251219\"|PROJECT_DIR=\"${PROJECT_DIR}\"|g" "${PROJECT_DIR}/.github/workflows/deploy.yml"
        echo "  ✅ 已複製 .github/workflows/deploy.yml"
    fi
    
    # 複製測試文件
    if [ -f "${TEMPLATE_DIR}/DEPLOY_TEST.md" ]; then
        cp "${TEMPLATE_DIR}/DEPLOY_TEST.md" "${PROJECT_DIR}/DEPLOY_TEST.md"
        echo "  ✅ 已複製 DEPLOY_TEST.md"
    fi
    
    echo -e "${GREEN}✅ 項目 ${PROJECT} 配置完成${NC}"
    echo ""
    echo -e "${YELLOW}下一步操作：${NC}"
    echo "1. 編輯 ${PROJECT_DIR}/src/config.ts，填入實際聯繫方式"
    echo "2. 檢查 ${PROJECT_DIR}/.github/workflows/deploy.yml 中的目錄路徑"
    echo "3. 在項目代碼中替換硬編碼的聯繫方式為 config.ts 引用"
    echo ""
done

echo -e "${GREEN}=========================================="
echo "✅ 所有項目配置完成！"
echo "==========================================${NC}"
echo ""
echo -e "${YELLOW}重要提醒：${NC}"
echo "1. 請檢查每個項目的 config.ts，填入實際信息"
echo "2. 請確認 GitHub Actions 中的項目目錄路徑是否正確"
echo "3. 請在代碼中替換硬編碼的聯繫方式"
echo "4. 確保 GitHub Secrets 已正確配置"
