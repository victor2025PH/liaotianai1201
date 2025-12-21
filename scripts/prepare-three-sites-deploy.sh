#!/bin/bash
# ============================================================
# 准备三个网站的部署
# ============================================================
# 功能：检查三个网站的文件，确保可以部署
# 使用方法：bash scripts/prepare-three-sites-deploy.sh
# ============================================================

set -e

echo "============================================================"
echo "🔍 检查三个网站的部署准备"
echo "============================================================"
echo ""

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 检查的网站
SITES=(
  "tgmini20251220:tgmini.usdt2026.cc:3001"
  "hbwy20251220:hongbao.usdt2026.cc:3002"
  "aizkw20251219:aikz.usdt2026.cc:3003"
)

ALL_OK=true

for SITE_INFO in "${SITES[@]}"; do
  IFS=':' read -r DIR DOMAIN PORT <<< "$SITE_INFO"
  SITE_DIR="$REPO_ROOT/$DIR"
  
  echo "检查: $DIR"
  echo "----------------------------------------"
  
  # 检查目录是否存在
  if [ ! -d "$SITE_DIR" ]; then
    echo -e "${RED}❌ 目录不存在: $SITE_DIR${NC}"
    ALL_OK=false
    continue
  fi
  
  echo -e "${GREEN}✅ 目录存在${NC}"
  
  # 检查 package.json
  if [ ! -f "$SITE_DIR/package.json" ]; then
    echo -e "${RED}❌ package.json 不存在${NC}"
    ALL_OK=false
  else
    echo -e "${GREEN}✅ package.json 存在${NC}"
    # 显示项目名称
    PROJECT_NAME=$(grep -o '"name": "[^"]*"' "$SITE_DIR/package.json" | cut -d'"' -f4 || echo "N/A")
    echo "   项目名称: $PROJECT_NAME"
  fi
  
  # 检查 vite.config.ts
  if [ ! -f "$SITE_DIR/vite.config.ts" ]; then
    echo -e "${YELLOW}⚠️  vite.config.ts 不存在${NC}"
  else
    echo -e "${GREEN}✅ vite.config.ts 存在${NC}"
  fi
  
  # 检查 .env.local（如果存在，提醒不要提交）
  if [ -f "$SITE_DIR/.env.local" ]; then
    echo -e "${YELLOW}⚠️  .env.local 存在（需要手动上传，不要提交到 Git）${NC}"
    
    # 检查是否在 Git 中
    if git ls-files --error-unmatch "$DIR/.env.local" >/dev/null 2>&1; then
      echo -e "${RED}❌ .env.local 被 Git 跟踪（需要移除）${NC}"
      echo "   执行: git rm --cached $DIR/.env.local"
      ALL_OK=false
    else
      echo -e "${GREEN}✅ .env.local 未被 Git 跟踪${NC}"
    fi
  else
    echo -e "${GREEN}✅ .env.local 不存在（可选）${NC}"
  fi
  
  # 检查 .gitignore
  if [ -f "$SITE_DIR/.gitignore" ]; then
    if grep -q "\.env" "$SITE_DIR/.gitignore"; then
      echo -e "${GREEN}✅ .gitignore 包含 .env${NC}"
    else
      echo -e "${YELLOW}⚠️  .gitignore 未包含 .env${NC}"
    fi
  fi
  
  echo ""
done

# 检查 GitHub Actions 工作流
echo "检查 GitHub Actions 工作流..."
echo "----------------------------------------"
if [ -f ".github/workflows/deploy-three-sites.yml" ]; then
  echo -e "${GREEN}✅ deploy-three-sites.yml 存在${NC}"
else
  echo -e "${RED}❌ deploy-three-sites.yml 不存在${NC}"
  ALL_OK=false
fi
echo ""

# 总结
echo "============================================================"
if [ "$ALL_OK" = true ]; then
  echo -e "${GREEN}✅ 所有检查通过，可以部署${NC}"
  echo ""
  echo "下一步："
  echo "  1. 提交代码到 GitHub"
  echo "  2. GitHub Actions 会自动触发部署"
  echo "  3. 或者手动触发: GitHub Actions > Run workflow"
else
  echo -e "${RED}❌ 发现问题，请先修复${NC}"
  exit 1
fi
echo "============================================================"
