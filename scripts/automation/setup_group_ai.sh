#!/bin/bash
# 群組 AI 系統開發環境自動化設置腳本

set -e

echo "=== 群組 AI 系統開發環境設置 ==="

# 顏色定義
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 1. 創建目錄結構
echo -e "${GREEN}[1/6] 創建目錄結構...${NC}"
mkdir -p group_ai_service/{models,utils,tests/{unit,integration,e2e}}
mkdir -p scripts/group_ai
mkdir -p ai_models/group_scripts

# 2. 創建 Python 模塊文件
echo -e "${GREEN}[2/6] 創建 Python 模塊文件...${NC}"

# 主模塊文件
cat > group_ai_service/__init__.py << 'EOF'
"""
Telegram 群組多 AI 賬號智能管理系統
"""
__version__ = "0.1.0"
EOF

# 模型目錄
touch group_ai_service/models/__init__.py
touch group_ai_service/models/account.py
touch group_ai_service/models/script.py
touch group_ai_service/models/dialogue.py
touch group_ai_service/models/redpacket.py
touch group_ai_service/models/monitor.py

# 工具目錄
touch group_ai_service/utils/__init__.py
touch group_ai_service/utils/variable_resolver.py
touch group_ai_service/utils/message_analyzer.py
touch group_ai_service/utils/context_manager.py
touch group_ai_service/utils/ai_generator.py
touch group_ai_service/utils/naturalness_optimizer.py

# 核心服務文件
touch group_ai_service/account_manager.py
touch group_ai_service/script_engine.py
touch group_ai_service/dialogue_manager.py
touch group_ai_service/redpacket_handler.py
touch group_ai_service/monitor_service.py
touch group_ai_service/config.py

# 測試文件
touch group_ai_service/tests/__init__.py
touch group_ai_service/tests/unit/__init__.py
touch group_ai_service/tests/integration/__init__.py
touch group_ai_service/tests/e2e/__init__.py

echo -e "${GREEN}✓ 目錄結構創建完成${NC}"

# 3. 創建數據庫遷移目錄
echo -e "${GREEN}[3/6] 創建數據庫遷移目錄...${NC}"
mkdir -p admin-backend/alembic/versions
touch admin-backend/alembic/versions/.gitkeep

# 4. 創建 API 路由目錄
echo -e "${GREEN}[4/6] 創建 API 路由目錄...${NC}"
mkdir -p admin-backend/app/api/group_ai
touch admin-backend/app/api/group_ai/__init__.py
touch admin-backend/app/api/group_ai/accounts.py
touch admin-backend/app/api/group_ai/scripts.py
touch admin-backend/app/api/group_ai/monitor.py
touch admin-backend/app/api/group_ai/control.py

# 5. 創建前端頁面目錄
echo -e "${GREEN}[5/6] 創建前端頁面目錄...${NC}"
mkdir -p saas-demo/src/app/group-ai/{accounts,scripts,monitor,control}
touch saas-demo/src/app/group-ai/accounts/page.tsx
touch saas-demo/src/app/group-ai/scripts/page.tsx
touch saas-demo/src/app/group-ai/monitor/page.tsx
touch saas-demo/src/app/group-ai/control/page.tsx

# 6. 創建示例劇本文件
echo -e "${GREEN}[6/6] 創建示例劇本文件...${NC}"
cat > ai_models/group_scripts/daily_chat_example.yaml << 'EOF'
script_id: daily_chat_example
version: 1.0
description: 日常聊天劇本示例

scenes:
  - id: greeting
    triggers:
      - type: keyword
        keywords: ["你好", "hello", "hi"]
    responses:
      - template: "你好！很高興認識你 😊"
    next_scene: conversation

  - id: conversation
    triggers:
      - type: message
        min_length: 5
    responses:
      - template: "{{contextual_reply}}"
        ai_generate: true
    next_scene: conversation

variables:
  user_name: "{{extract_name}}"
  conversation_topic: "{{detect_topic}}"
EOF

echo -e "${GREEN}✓ 示例劇本創建完成${NC}"

echo ""
echo -e "${GREEN}=== 設置完成 ===${NC}"
echo "下一步："
echo "1. 安裝依賴: cd admin-backend && poetry install"
echo "2. 初始化數據庫: poetry run alembic upgrade head"
echo "3. 開始開發: 參考 docs/GROUP_AI_DEVELOPMENT_PLAN.md"

