# 數據庫遷移與初始化

本文檔說明數據庫遷移策略和初始化數據腳本。

---

## 數據庫遷移策略

### admin-backend 數據庫

#### 當前狀態

- **ORM 框架**：SQLAlchemy
- **遷移工具**：目前使用 SQLAlchemy 的 `Base.metadata.create_all()` 自動創建表結構
- **遷移文件位置**：`migrations/` 目錄（主要用於主程序的 `chat_history.db`）

#### 首次部署

**步驟 1：創建數據庫**

如果使用 SQLite（開發環境）：
```bash
# 數據庫文件會在首次運行時自動創建
# 位置：admin-backend/admin.db
```

如果使用 PostgreSQL（生產環境）：
```bash
# 創建數據庫
createdb admin_db

# 或使用 psql
psql -U postgres -c "CREATE DATABASE admin_db;"
```

**步驟 2：應用遷移**

當前實現：在 `admin-backend/app/main.py` 的 `on_startup` 事件中自動創建表：

```python
@app.on_event("startup")
def on_startup() -> None:
    Base.metadata.create_all(bind=engine)
    # ... 初始化默認用戶和角色
```

**手動執行**：
```bash
cd admin-backend
poetry run python -c "from app.db import Base, engine; Base.metadata.create_all(bind=engine)"
```

#### 未來遷移工具（TODO）

**建議使用 Alembic**：

1. **安裝 Alembic**：
   ```bash
   cd admin-backend
   poetry add alembic
   ```

2. **初始化 Alembic**：
   ```bash
   poetry run alembic init alembic
   ```

3. **配置 `alembic.ini` 和 `alembic/env.py`**：
   - 設置 `sqlalchemy.url` 從環境變量讀取
   - 設置 `target_metadata = Base.metadata`

4. **創建遷移**：
   ```bash
   poetry run alembic revision --autogenerate -m "描述"
   ```

5. **應用遷移**：
   ```bash
   poetry run alembic upgrade head
   ```

6. **回滾遷移**：
   ```bash
   poetry run alembic downgrade -1  # 回滾一個版本
   poetry run alembic downgrade base  # 回滾到初始狀態
   ```

---

## 主程序數據庫遷移

### chat_history.db 遷移

**遷移腳本**：`scripts/run_migrations.py`

**遷移文件位置**：`migrations/__init__.py`（定義 `MIGRATIONS` 列表）

**執行遷移**：
```bash
python -m scripts.run_migrations
```

**遷移流程**：
1. 自動備份數據庫到 `backup/db_bak/`
2. 檢查 `schema_migrations` 表，記錄已應用的遷移
3. 執行未應用的遷移
4. 更新遷移記錄

**回滾遷移**：

目前沒有自動回滾機制，需要手動操作：

1. **恢復備份**：
   ```bash
   # 從 backup/db_bak/ 中找到遷移前的備份文件
   cp backup/db_bak/before-migrate-YYYYMMDD-HHMMSS-chat_history.db data/chat_history.db
   ```

2. **手動刪除遷移記錄**（如果需要）：
   ```sql
   DELETE FROM schema_migrations WHERE version = '遷移版本號';
   ```

---

## 初始化數據

### admin-backend 初始化數據

#### 默認管理員用戶

在 `admin-backend/app/main.py` 的 `on_startup` 事件中自動創建：

```python
# 創建默認管理員用戶
admin_user = get_user_by_email(db, settings.admin_default_email)
if not admin_user:
    admin_user = create_user(
        db,
        email=settings.admin_default_email,
        password=settings.admin_default_password,
        is_superuser=True,
    )
    # 分配管理員角色
    admin_role = create_role(db, name="admin", description="管理員")
    assign_role_to_user(db, user_id=admin_user.id, role_id=admin_role.id)
```

**環境變量**：
- `ADMIN_DEFAULT_EMAIL`：默認管理員郵箱（默認：`admin@example.com`）
- `ADMIN_DEFAULT_PASSWORD`：默認管理員密碼（默認：`changeme123`）

**注意**：首次登錄後應立即修改密碼。

#### 默認角色和權限

**TODO：考慮增加初始化腳本**

建議創建 `admin-backend/scripts/init_data.py`：

```python
# 示例結構（待實現）
def init_roles_and_permissions():
    """初始化默認角色和權限"""
    # 創建角色：admin, user, viewer
    # 創建權限：read_dashboard, write_settings, manage_users
    # 分配權限到角色
    pass
```

### 主程序初始化數據

#### 會話模板

**位置**：`ai_models/dialogue_scene_scripts.yaml`

**說明**：包含對話場景腳本，用於 AI 對話生成。

**初始化**：文件已存在，無需額外初始化。

#### AI 場景配置

**位置**：`ai_models/intro_segments.yaml`

**說明**：包含介紹片段配置。

**初始化**：文件已存在，無需額外初始化。

#### 測試賬號

**TODO：考慮增加初始化腳本**

建議創建 `scripts/init_test_accounts.py`：

```python
# 示例結構（待實現）
def init_test_accounts():
    """初始化測試賬號"""
    # 創建測試會話賬號
    # 導入測試會話文件
    # 設置測試標籤
    pass
```

---

## 數據庫備份與恢復

### 自動備份

**主程序數據庫**：
- 遷移前自動備份到 `backup/db_bak/`
- 備份文件名格式：`before-migrate-YYYYMMDD-HHMMSS-chat_history.db`

**admin-backend 數據庫**：
- **TODO：考慮增加自動備份腳本**

建議創建 `admin-backend/scripts/backup_db.py`：

```python
# 示例結構（待實現）
def backup_database():
    """備份 admin-backend 數據庫"""
    # SQLite: 複製文件
    # PostgreSQL: 使用 pg_dump
    pass
```

### 手動備份

#### SQLite 備份

```bash
# admin-backend
cp admin-backend/admin.db backup/admin_backup_$(date +%Y%m%d_%H%M%S).db

# 主程序
cp data/chat_history.db backup/db_bak/chat_history_backup_$(date +%Y%m%d_%H%M%S).db
```

#### PostgreSQL 備份

```bash
# 使用 pg_dump
pg_dump $DATABASE_URL > backup/admin_backup_$(date +%Y%m%d_%H%M%S).sql

# 或使用 pg_dump 的自定義格式（支持壓縮）
pg_dump -Fc $DATABASE_URL > backup/admin_backup_$(date +%Y%m%d_%H%M%S).dump
```

### 恢復數據庫

#### SQLite 恢復

```bash
# 停止服務
# 恢復備份文件
cp backup/admin_backup_YYYYMMDD_HHMMSS.db admin-backend/admin.db

# 重啟服務
```

#### PostgreSQL 恢復

```bash
# 使用 psql
psql $DATABASE_URL < backup/admin_backup_YYYYMMDD_HHMMSS.sql

# 或使用 pg_restore（自定義格式）
pg_restore -d $DATABASE_URL backup/admin_backup_YYYYMMDD_HHMMSS.dump
```

---

## 數據庫結構

### admin-backend 數據庫表

| 表名 | 說明 | 模型文件 |
|------|------|---------|
| `users` | 用戶表 | `admin-backend/app/models/user.py` |
| `roles` | 角色表 | `admin-backend/app/models/role.py` |
| `permissions` | 權限表 | `admin-backend/app/models/permission.py` |
| `user_roles` | 用戶-角色關聯表 | `admin-backend/app/models/user_role.py` |
| `role_permissions` | 角色-權限關聯表 | `admin-backend/app/models/role_permission.py` |

### 主程序數據庫表

| 表名 | 說明 | 備註 |
|------|------|------|
| `chat_history` | 聊天歷史 | 主程序使用 |
| `session_accounts` | 會話賬戶 | 主程序使用 |
| `schema_migrations` | 遷移記錄表 | 遷移系統使用 |

---

## 遷移最佳實踐

### 1. 遷移前檢查

- [ ] 確認數據庫已備份
- [ ] 確認當前數據庫版本
- [ ] 確認遷移文件已測試

### 2. 遷移執行

- [ ] 在測試環境先執行遷移
- [ ] 驗證遷移後的數據完整性
- [ ] 在生產環境執行遷移（建議在維護窗口）

### 3. 遷移後驗證

- [ ] 檢查表結構是否正確
- [ ] 檢查數據是否完整
- [ ] 檢查應用是否正常運行

### 4. 回滾準備

- [ ] 保留遷移前的數據庫備份
- [ ] 記錄回滾步驟
- [ ] 準備回滾腳本（如果需要）

---

## 初始化腳本清單

### 已實現

- ✅ 默認管理員用戶創建（`admin-backend/app/main.py`）
- ✅ 主程序數據庫遷移（`scripts/run_migrations.py`）

### 待實現（TODO）

- [ ] 角色和權限初始化腳本（`admin-backend/scripts/init_roles_and_permissions.py`）
- [ ] 測試賬號初始化腳本（`scripts/init_test_accounts.py`）
- [ ] admin-backend 數據庫自動備份腳本（`admin-backend/scripts/backup_db.py`）
- [ ] Alembic 遷移工具集成（`admin-backend/alembic/`）

---

## 故障排查

### 問題：遷移失敗

**排查步驟**：
1. 檢查數據庫連接是否正常
2. 檢查遷移文件語法是否正確
3. 檢查是否有數據衝突
4. 查看遷移日誌

### 問題：數據丟失

**恢復步驟**：
1. 停止服務
2. 從備份恢復數據庫
3. 檢查數據完整性
4. 重啟服務

### 問題：遷移後應用無法啟動

**排查步驟**：
1. 檢查表結構是否正確
2. 檢查 ORM 模型是否與數據庫結構匹配
3. 檢查是否有必要的數據缺失
4. 查看應用日誌

---

**最後更新**: 2024-12-19
