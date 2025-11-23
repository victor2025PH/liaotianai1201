# 數據庫遷移指南

> **文檔版本**: v1.0  
> **最後更新**: 2025-01-17  
> **遷移工具**: Alembic 1.13.3

---

## 📋 目錄

1. [快速開始](#快速開始)
2. [遷移流程](#遷移流程)
3. [創建遷移](#創建遷移)
4. [應用遷移](#應用遷移)
5. [回滾遷移](#回滾遷移)
6. [數據庫備份](#數據庫備份)
7. [常見問題](#常見問題)

---

## 快速開始

### 首次設置

1. **安裝依賴**（已包含在 `pyproject.toml` 中）
   ```bash
   cd admin-backend
   poetry install
   ```

2. **運行初始遷移**
   ```bash
   poetry run alembic upgrade head
   ```

   或使用備份腳本（推薦）：
   ```bash
   poetry run python -m scripts.run_migrations
   ```

### 日常遷移

```bash
# 使用備份腳本（自動備份 + 遷移）
poetry run python -m scripts.run_migrations

# 或直接使用 Alembic
poetry run alembic upgrade head
```

---

## 遷移流程

### 標準流程

1. **創建遷移文件**
   ```bash
   poetry run alembic revision --autogenerate -m "描述變更內容"
   ```

2. **檢查遷移文件**
   - 檢查生成的遷移文件（位於 `alembic/versions/`）
   - 驗證 `upgrade()` 和 `downgrade()` 函數是否正確

3. **備份數據庫**（自動執行）
   ```bash
   poetry run python -m scripts.backup_db
   ```

4. **應用遷移**
   ```bash
   poetry run alembic upgrade head
   ```

5. **驗證遷移**
   - 檢查數據庫結構
   - 運行測試套件
   - 檢查應用是否正常運行

---

## 創建遷移

### 自動生成遷移（推薦）

```bash
# 基於模型變更自動生成遷移
poetry run alembic revision --autogenerate -m "添加用戶表索引"
```

**注意**：
- Alembic 會比較當前模型與數據庫結構
- 只會檢測到已註冊的模型變更
- 確保所有模型都已導入（在 `alembic/env.py` 中）

### 手動創建遷移

```bash
# 創建空遷移文件
poetry run alembic revision -m "描述變更內容"
```

然後手動編寫 `upgrade()` 和 `downgrade()` 函數。

### 遷移文件命名規範

- 格式：`{序號}_{描述}.py`
- 示例：`004_add_user_avatar_column.py`
- 描述應簡潔明了，說明變更內容

---

## 應用遷移

### 升級到最新版本

```bash
poetry run alembic upgrade head
```

### 升級到特定版本

```bash
# 升級到特定版本
poetry run alembic upgrade {revision_id}

# 示例
poetry run alembic upgrade 003_add_script_version_management
```

### 逐步升級

```bash
# 升級一個版本
poetry run alembic upgrade +1

# 升級兩個版本
poetry run alembic upgrade +2
```

### 使用備份腳本（推薦）

```bash
# 自動備份 + 遷移
poetry run python -m scripts.run_migrations
```

**優點**：
- 自動備份數據庫（遷移前）
- 錯誤處理更完善
- 日誌輸出更清晰

---

## 回滾遷移

### 回滾一個版本

```bash
poetry run alembic downgrade -1
```

### 回滾到特定版本

```bash
poetry run alembic downgrade {revision_id}

# 示例
poetry run alembic downgrade 002_add_indexes
```

### 回滾到初始狀態

```bash
poetry run alembic downgrade base
```

**⚠️ 警告**：回滾會刪除數據，請確保已備份數據庫！

---

## 數據庫備份

### 自動備份（遷移前）

使用遷移腳本會自動備份：

```bash
poetry run python -m scripts.run_migrations
```

備份位置：`admin-backend/backup/db_bak/`

### 手動備份

#### SQLite

```bash
poetry run python -m scripts.backup_db
```

或直接複製：

```bash
cp admin-backend/admin.db admin-backend/backup/db_bak/admin_backup_$(date +%Y%m%d_%H%M%S).db
```

#### PostgreSQL

```bash
# 使用 pg_dump
pg_dump $DATABASE_URL > backup/admin_backup_$(date +%Y%m%d_%H%M%S).sql

# 或使用自定義格式（支持壓縮）
pg_dump -Fc $DATABASE_URL > backup/admin_backup_$(date +%Y%m%d_%H%M%S).dump
```

### 恢復數據庫

#### SQLite

```bash
# 停止應用
# 恢復備份
cp backup/db_bak/before-migrate-YYYYMMDD-HHMMSS-admin.db admin-backend/admin.db
# 重啟應用
```

#### PostgreSQL

```bash
# 使用 psql
psql $DATABASE_URL < backup/admin_backup_YYYYMMDD_HHMMSS.sql

# 或使用 pg_restore（自定義格式）
pg_restore -d $DATABASE_URL backup/admin_backup_YYYYMMDD_HHMMSS.dump
```

---

## 遷移狀態檢查

### 檢查當前版本

```bash
poetry run alembic current
```

### 檢查可用遷移

```bash
poetry run alembic history
```

### 檢查版本差異

```bash
# 顯示詳細歷史
poetry run alembic history --verbose

# 顯示特定版本的詳細信息
poetry run alembic history {revision_id}
```

---

## 常見問題

### 1. 遷移失敗：表已存在

**問題**：運行遷移時提示表已存在。

**解決方案**：
- 檢查數據庫是否已有表結構
- 使用 `alembic current` 檢查當前版本
- 如果需要從頭開始，可以刪除數據庫並重新運行遷移

### 2. 自動生成遷移未檢測到變更

**問題**：修改了模型，但 `alembic revision --autogenerate` 未檢測到變更。

**解決方案**：
1. 確保所有模型都在 `alembic/env.py` 中導入
2. 檢查模型定義是否正確（表名、字段名等）
3. 手動創建遷移文件

### 3. 遷移文件衝突

**問題**：多個開發者創建了衝突的遷移文件。

**解決方案**：
1. 合併遷移文件（手動編輯）
2. 或刪除衝突的遷移文件，重新生成

### 4. 生產環境遷移

**最佳實踐**：
1. ✅ 先在測試環境測試遷移
2. ✅ 備份生產數據庫
3. ✅ 在維護窗口期間執行遷移
4. ✅ 驗證遷移後的應用功能
5. ✅ 準備回滾計劃

---

## 遷移文件結構

### 遷移文件位置

```
admin-backend/
├── alembic/
│   ├── versions/          # 遷移文件目錄
│   │   ├── 000_initial_base_tables.py
│   │   ├── 001_create_group_ai_tables.py
│   │   ├── 002_add_indexes_for_performance.py
│   │   └── 003_add_script_version_management.py
│   ├── env.py             # Alembic 環境配置
│   └── script.py.mako     # 遷移文件模板
├── alembic.ini            # Alembic 配置文件
└── scripts/
    ├── backup_db.py       # 數據庫備份腳本
    └── run_migrations.py  # 遷移運行腳本（含備份）
```

### 遷移文件示例

```python
"""添加用戶頭像字段

Revision ID: 004_add_user_avatar
Revises: 003_add_script_version_management
Create Date: 2025-01-17 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = '004_add_user_avatar'
down_revision = '003_add_script_version_management'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 添加用戶頭像字段
    op.add_column('users', sa.Column('avatar_url', sa.String(500), nullable=True))


def downgrade() -> None:
    # 移除用戶頭像字段
    op.drop_column('users', 'avatar_url')
```

---

## 遷移最佳實踐

### 1. 遷移前檢查

- [ ] 確認數據庫已備份
- [ ] 確認當前數據庫版本（`alembic current`）
- [ ] 確認遷移文件已測試（在測試環境）

### 2. 遷移執行

- [ ] 在測試環境先執行遷移
- [ ] 驗證遷移後的數據完整性
- [ ] 在生產環境執行遷移（建議在維護窗口）

### 3. 遷移後驗證

- [ ] 檢查表結構是否正確（`alembic current`）
- [ ] 檢查數據是否完整
- [ ] 運行測試套件
- [ ] 檢查應用是否正常運行

### 4. 回滾準備

- [ ] 保留遷移前的數據庫備份
- [ ] 記錄回滾步驟
- [ ] 準備回滾腳本（如果需要）

---

## 與主程序的遷移對比

### admin-backend（Alembic）

- **工具**: Alembic
- **配置文件**: `alembic.ini`, `alembic/env.py`
- **遷移文件**: `alembic/versions/*.py`
- **執行命令**: `poetry run alembic upgrade head`
- **備份腳本**: `scripts/run_migrations.py`

### 主程序（自定義遷移）

- **工具**: 自定義遷移系統（`migrations/__init__.py`）
- **遷移文件**: `migrations/__init__.py`
- **執行命令**: `python -m scripts.run_migrations`
- **備份**: 自動備份到 `backup/db_bak/`

**建議**：未來可以考慮統一遷移策略，將主程序也遷移到 Alembic。

---

## 相關文檔

- [Alembic 官方文檔](https://alembic.sqlalchemy.org/)
- [SQLAlchemy 文檔](https://docs.sqlalchemy.org/)
- `docs/开发笔记/DB_MIGRATION_AND_SEEDING.md` - 數據庫遷移與初始化詳細說明
- `README.md` - 項目快速開始指南

---

**文檔維護**: 如有問題或建議，請提交 Issue 或 Pull Request。

