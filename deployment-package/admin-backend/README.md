# Smart TG Admin Backend

FastAPI 后端服务，提供企业后台管理系统所需的账户、活动、告警与指令 API。

## 快速开始

1. **安装依赖**
   ```bash
   cd admin-backend
   poetry install
   ```

2. **初始化环境变量**
   ```bash
   # 复制环境变量模板（如果存在）
   cp .env.example .env  # 或从项目根目录复制 docs/env.example
   
   # 填写必填环境变量
   # - DATABASE_URL: 数据库连接（默认: sqlite:///./admin.db）
   # - JWT_SECRET: JWT 密钥（⚠️ 生产环境必须修改！）
   # - ADMIN_DEFAULT_EMAIL: 管理员邮箱（默认: admin@example.com）
   # - ADMIN_DEFAULT_PASSWORD: 管理员密码（⚠️ 生产环境必须修改！）
   ```
   
   > **注意**：生产环境必须修改 `JWT_SECRET` 和 `ADMIN_DEFAULT_PASSWORD`，否则会收到警告。

3. **数据库迁移**
   ```bash
   # 使用备份脚本（推荐，自动备份 + 迁移）
   poetry run python -m scripts.run_migrations
   
   # 或直接使用 Alembic
   poetry run alembic upgrade head
   ```
   
   > **注意**: 首次部署时，迁移脚本会自动创建所有数据表。迁移前会自动备份数据库到 `backup/db_bak/`。

4. **启动开发服务器**
   ```bash
   poetry run uvicorn app.main:app --reload
   ```
   默认运行在 `http://127.0.0.1:8000`

5. **运行测试**
   ```bash
   # 运行所有测试
   poetry run pytest tests/ -v
   
   # 运行测试并生成覆盖率报告
   poetry run pytest tests/ --cov=app --cov-report=term-missing --cov-report=html
   ```

## 项目结构
```
admin-backend/
├── app/
│   ├── api/          # 路由模块
│   ├── core/         # 配置、JWT、OAuth2、权限
│   ├── models/       # SQLAlchemy 模型
│   ├── schemas/      # Pydantic schema
│   ├── services/     # 业务逻辑
│   └── main.py       # FastAPI 应用入口
├── tests/            # 单元与集成测试
├── migrations/       # Alembic 迁移
└── pyproject.toml
```

## CI/CD 流程

项目配置了 GitHub Actions CI/CD 流程，包含以下工作流：

### 1. 持续集成（CI）
**文件**: `.github/workflows/ci.yml`

**触发条件**:
- Push 到 `main` 或 `develop` 分支
- 创建 Pull Request

**工作流程**:
1. **代码质量检查**
   - Ruff 代码检查（lint）
   - Black 代码格式化检查
   - 前端 ESLint 检查

2. **自动化测试**
   - 后端单元测试和集成测试
   - 测试覆盖率检查（阈值：70%）
   - 上传覆盖率报告

3. **前端构建**
   - 前端 E2E 测试（Playwright）
   - 前端构建验证

4. **Docker 构建**
   - 验证 Docker 镜像构建

### 2. 测试覆盖率
**文件**: `.github/workflows/test-coverage.yml`

**触发条件**:
- Push 到 `main` 或 `develop` 分支
- Pull Request
- 定时任务（每天 UTC 02:00）
- 手动触发

**功能**:
- 生成详细的测试覆盖率报告
- 上传到 Codecov（如果配置）
- 生成 HTML 覆盖率报告供下载

### 本地运行 CI 检查

在提交代码前，可以本地运行 CI 检查：

```bash
# 代码检查
poetry run ruff check app tests
poetry run black --check app tests

# 运行测试
poetry run pytest tests/ -v

# 生成覆盖率报告
poetry run pytest tests/ --cov=app --cov-report=html
```

### CI/CD 环境变量

CI/CD 流程使用以下测试环境变量：

- `DATABASE_URL`: `sqlite:///./test_admin.db`
- `JWT_SECRET`: `test_jwt_secret_for_ci`
- `ADMIN_DEFAULT_EMAIL`: `admin@test.com`
- `ADMIN_DEFAULT_PASSWORD`: `testpass123`

## 下一步
- ✅ 实作 RBAC 权限模型与用户管理
- ✅ 对接 Session 服务、Redpacket Bot 与监控数据接口
- ✅ 撰写自动化测试与 CI/CD 脚本
- 🔄 提高测试覆盖率（目标：80%+）
- 🔄 添加 E2E 测试

