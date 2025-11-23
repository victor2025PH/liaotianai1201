# GitHub Actions CI/CD 工作流說明

本目錄包含項目的 CI/CD 自動化工作流配置。

---

## 工作流文件

### 1. `ci.yml` - 主 CI 工作流

**功能**:
- 後端代碼檢查（Ruff, Black）
- 後端測試（Pytest + 覆蓋率）
- 前端代碼檢查（ESLint, TypeScript）
- 前端構建驗證
- 前端 E2E 測試（Playwright）
- 主程序服務測試

**觸發條件**:
- Push 到 `main` 或 `develop` 分支
- Pull Request 到 `main` 或 `develop` 分支

**執行時間**: 約 5-10 分鐘

---

### 2. `code-quality.yml` - 代碼質量檢查

**功能**:
- 後端代碼質量檢查（Ruff, Black, Bandit）
- 前端代碼質量檢查（ESLint, TypeScript）
- 構建大小檢查

**觸發條件**:
- Push 到 `main` 或 `develop` 分支
- Pull Request 到 `main` 或 `develop` 分支
- 每週一自動運行（定期檢查）

---

### 3. `release.yml` - 發布流程

**功能**:
- 構建和測試驗證
- 自動創建 GitHub Release
- 生成發布說明

**觸發條件**:
- 推送版本標籤（`v*.*.*`）
- 手動觸發（workflow_dispatch）

**使用方式**:
```bash
# 創建版本標籤
git tag v1.0.0
git push origin v1.0.0
```

---

### 4. `dependency-review.yml` - 依賴審查

**功能**:
- 審查 Pull Request 中的依賴變更
- 檢查安全漏洞
- 檢查許可證兼容性

**觸發條件**:
- Pull Request 到 `main` 或 `develop` 分支

---

## 本地運行 CI 檢查

### 後端檢查

```bash
cd admin-backend
poetry run ruff check .
poetry run black --check .
poetry run pytest --cov=app --cov-report=html
```

### 前端檢查

```bash
cd saas-demo
npm run lint
npx tsc --noEmit
npm run build
npm run test:e2e
```

---

## 測試覆蓋率

### 目標

- **後端**: 80%+
- **前端 E2E**: 80%+

### 查看覆蓋率報告

1. 訪問 GitHub Actions 頁面
2. 下載 `backend-coverage-html` 構建產物
3. 打開 `index.html` 查看覆蓋率報告

---

## 環境變量

### CI 環境變量

工作流中使用的環境變量：

**後端測試**:
- `DATABASE_URL`: PostgreSQL 測試數據庫
- `REDIS_URL`: Redis 測試服務
- `JWT_SECRET`: 測試用 Secret
- `DISABLE_AUTH`: `true`（測試環境）

**前端構建**:
- `NEXT_PUBLIC_API_BASE_URL`: API 基礎地址

---

## 故障排除

### 測試失敗

1. 檢查測試日誌
2. 下載測試報告
3. 檢查環境變量配置
4. 檢查服務依賴（PostgreSQL, Redis）

### 構建失敗

1. 檢查構建日誌
2. 檢查依賴安裝
3. 檢查 Node.js/Python 版本

### 覆蓋率報告缺失

1. 檢查 `pytest-cov` 是否安裝
2. 檢查 `--cov` 參數是否正確
3. 檢查覆蓋率文件是否生成

---

## 相關文檔

- [CI/CD 流程完善報告](../docs/开发笔记/CI_CD流程完善报告.md)
- [GitHub Actions 文檔](https://docs.github.com/en/actions)

---

**最後更新**: 2025-01-XX

