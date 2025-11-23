# 群組 AI 系統自動化開發指南

> **文檔版本**: v1.0  
> **創建日期**: 2024-12-19

---

## 概述

本文檔說明如何使用自動化工具和腳本進行群組 AI 系統的開發、測試和部署。

---

## 自動化工具清單

### 1. 環境設置腳本

**文件**: `scripts/automation/setup_group_ai.sh`

**功能**: 自動創建項目目錄結構和基礎文件

**使用方法**:
```bash
# Linux/macOS
bash scripts/automation/setup_group_ai.sh

# Windows (使用 Git Bash 或 WSL)
bash scripts/automation/setup_group_ai.sh
```

**執行內容**:
- 創建 `group_ai_service/` 目錄結構
- 創建基礎模塊文件
- 創建 API 路由目錄
- 創建前端頁面目錄
- 創建示例劇本文件

### 2. 代碼質量檢查

**文件**: `scripts/automation/check_code_quality.sh`

**功能**: 自動檢查代碼質量和格式

**使用方法**:
```bash
bash scripts/automation/check_code_quality.sh
```

**檢查項目**:
- Python: Ruff 檢查、Black 格式化、MyPy 類型檢查
- TypeScript: ESLint 檢查
- 文檔完整性

### 3. 自動化測試

**文件**: `scripts/automation/run_group_ai_tests.sh`

**功能**: 運行所有測試並生成報告

**使用方法**:
```bash
bash scripts/automation/run_group_ai_tests.sh
```

**測試類型**:
- 單元測試
- 集成測試
- E2E 測試
- 覆蓋率報告

### 4. 文檔生成

**文件**: `scripts/automation/generate_docs.sh`

**功能**: 自動生成 API 文檔和代碼文檔

**使用方法**:
```bash
bash scripts/automation/generate_docs.sh
```

**生成內容**:
- OpenAPI 規範文件
- 代碼文檔
- README 更新

### 5. 開發環境部署

**文件**: `scripts/automation/deploy_dev.sh`

**功能**: 自動部署到開發環境

**使用方法**:
```bash
bash scripts/automation/deploy_dev.sh [dev|staging|prod]
```

**執行步驟**:
- 構建 Docker 鏡像
- 運行數據庫遷移
- 啟動服務
- 健康檢查

### 6. 階段任務執行

**文件**: `scripts/automation/phase1_tasks.sh`

**功能**: 執行階段 1 的自動化任務

**使用方法**:
```bash
bash scripts/automation/phase1_tasks.sh
```

### 7. 全自動化工作流

**文件**: `scripts/automation/auto_dev_workflow.sh`

**功能**: 執行指定階段的所有自動化任務

**使用方法**:
```bash
# 執行階段 1
bash scripts/automation/auto_dev_workflow.sh 1

# 執行所有階段
bash scripts/automation/auto_dev_workflow.sh all
```

---

## CI/CD 流程

### GitHub Actions Workflow

**文件**: `.github/workflows/group-ai-ci.yml`

**觸發條件**:
- Push 到 `main` 或 `develop` 分支
- Pull Request
- 手動觸發

**執行 Jobs**:
1. **Lint & Format Check**: 代碼檢查
2. **Backend Unit Tests**: 後端單元測試
3. **Integration Tests**: 集成測試
4. **Build Docker**: 構建 Docker 鏡像
5. **Deploy Dev**: 自動部署到開發環境

---

## 開發工作流

### 日常開發流程

1. **開始開發前**:
   ```bash
   # 檢查代碼質量
   bash scripts/automation/check_code_quality.sh
   ```

2. **開發過程中**:
   - 編寫代碼
   - 運行單元測試: `pytest group_ai_service/tests/unit/ -v`
   - 檢查格式: `black group_ai_service/`

3. **提交前**:
   ```bash
   # 運行所有檢查
   bash scripts/automation/check_code_quality.sh
   bash scripts/automation/run_group_ai_tests.sh
   ```

4. **提交後**:
   - GitHub Actions 自動執行 CI/CD
   - 檢查 CI 結果
   - 合併 PR（如果通過）

### 階段性開發流程

**階段 1: 基礎架構搭建**
```bash
# 1. 設置環境
bash scripts/automation/setup_group_ai.sh

# 2. 執行階段任務
bash scripts/automation/phase1_tasks.sh

# 3. 運行測試
bash scripts/automation/run_group_ai_tests.sh
```

**階段 2-6**: 類似流程，使用對應的階段腳本

---

## 測試策略

### 單元測試

**位置**: `group_ai_service/tests/unit/`

**運行**:
```bash
cd admin-backend
poetry run pytest group_ai_service/tests/unit/ -v --cov=group_ai_service
```

### 集成測試

**位置**: `group_ai_service/tests/integration/`

**運行**:
```bash
cd admin-backend
poetry run pytest group_ai_service/tests/integration/ -v
```

### E2E 測試

**位置**: `group_ai_service/tests/e2e/`

**運行**:
```bash
cd admin-backend
poetry run pytest group_ai_service/tests/e2e/ -v
```

---

## 部署流程

### 開發環境

**自動部署**: PR 合併到 `develop` 分支後自動觸發

**手動部署**:
```bash
bash scripts/automation/deploy_dev.sh dev
```

### 測試環境

**手動部署**:
```bash
bash scripts/automation/deploy_dev.sh staging
```

### 生產環境

**手動部署**（需要審批）:
```bash
bash scripts/automation/deploy_dev.sh prod
```

---

## 監控和日誌

### 開發環境監控

- **後端**: http://localhost:8000/health
- **前端**: http://localhost:3000
- **API 文檔**: http://localhost:8000/docs

### 日誌位置

- **後端日誌**: `admin-backend/logs/`
- **前端日誌**: 瀏覽器控制台
- **測試日誌**: `group_ai_service/tests/logs/`

---

## 故障排查

### 常見問題

1. **模塊導入錯誤**
   - 檢查 Python 路徑
   - 確認虛擬環境已激活
   - 檢查 `__init__.py` 文件

2. **測試失敗**
   - 檢查數據庫連接
   - 確認測試數據已加載
   - 查看詳細錯誤日誌

3. **CI/CD 失敗**
   - 查看 GitHub Actions 日誌
   - 檢查代碼格式
   - 確認測試通過

---

## 最佳實踐

1. **代碼提交前**:
   - 運行代碼質量檢查
   - 運行所有測試
   - 確保覆蓋率達標

2. **功能開發**:
   - 先寫測試
   - 小步提交
   - 及時更新文檔

3. **代碼審查**:
   - 檢查代碼質量
   - 確認測試覆蓋
   - 驗證文檔完整性

---

**文檔版本**: v1.0  
**最後更新**: 2024-12-19

