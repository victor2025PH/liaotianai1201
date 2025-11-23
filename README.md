# Smart TG Business AI · 专业级业务聊天机器人/AI分身矩阵系统

---

## 项目简介

本项目是一个面向**Telegram、Web、企业微信等平台**的**真人化AI业务聊天机器人**与**分身矩阵管理系统**，  
适用于**批量引流、业务陪伴、客户成长管理、批量AI自动推广与项目合作撮合**等全场景，  
兼容**云控自动加好友/群发/批量聊天、AI身份变换/批量TTS/表情/冷场陪伴、标签成长体系**，支持**数据库+Excel双视图数据管理、全自动数据备份与恢复**。

---

## 核心亮点功能

- **AI分身矩阵**：上千号TG分身/批量账号云控，每天每个分身自动加5-10个华人好友
- **高度真人化聊天**：身份唯一，AI分身可批量聊天、身份/专业/情感切换，回复多变
- **业务全场景覆盖**：批量推广/群控/私域引流/业务Q&A/项目撮合一站式
- **成长陪伴&智能分流**：长期陪伴、冷场唤醒、标签打标/成长引导/数据追踪
- **AI自动TTS语音/表情/图片**：所有对话支持AI语音男声/表情/图片自动推送
- **Excel+数据库双管理**：支持数据表头中英文、批量导入导出、结构化查询
- **内容池极简可扩展**：所有身份、fewshot、FAQ、业务分流、成长池均用yaml一键管理
- **自动初始化与备份**：首次运行自动创建所有必要目录、数据库、表格，支持定时全量备份
- **日志、异常、数据安全**：全局日志系统、分天归档、可定制远程报警
- **支持后续Web/WebAPI/企业微信/多平台接入**，模块化架构随时升级

---

## 工程结构（简明版）

- Telegram 业务主控：`main.py`
- 配置与路径管理：`config.py`
- 业务工具与模块：存放于 `utils/`
- 话术与身份配置：`ai_models/`
- 数据与备份：`data/`、`backup/`、`logs/`
- 文档与样例：`docs/`

---

## 环境配置

1. 将 `docs/env.example` 复制为项目根目录或 `config.py` 同级目录下的 `.env` 文件。
2. 填入以下必填变量：

   | 变量名 | 说明 |
   | --- | --- |
   | `TELEGRAM_API_ID` | Telegram 开发者 API ID（整型） |
   | `TELEGRAM_API_HASH` | Telegram API Hash |
| `TELEGRAM_SESSION_NAME` | Pyrogram Session 名称（当使用本地 `.session` 文件时可与下方 `TELEGRAM_SESSION_FILE` 相同） |
| `TELEGRAM_SESSION_STRING` | （可选）已生成的 Telegram session 字串，推荐用于无头部署 |
| `TELEGRAM_SESSION_FILE` | （可选）已存在的 Telegram session 文件路径，若提供将覆盖 `TELEGRAM_SESSION_NAME` |
   | `OPENAI_API_KEY` | OpenAI API Key |
   | `OPENAI_MODEL` | 默认调用的 OpenAI 模型名称（可选，默认 `gpt-4`） |
   | `OPENAI_VISION_MODEL` | OpenAI Vision 模型名称（可选，默认 `gpt-4o-mini-vision`） |
   | `TENCENT_SECRET_ID` | 腾讯云 SecretId（若使用腾讯服务） |
   | `TENCENT_SECRET_KEY` | 腾讯云 SecretKey（若使用腾讯服务） |
| `ADD_FRIENDS_RATE_PER_MINUTE` | 每分钟允许的自动加好友上限（默认 15，人为控制风控速率） |
| `GREET_RATE_PER_MINUTE` | 每分钟欢迎消息最大发送次数（默认 20） |
| `AUTO_REPLY_RATE_PER_MINUTE` | 每分钟批量自动回复最大发送次数（默认 30） |
| `TAG_ANALYZE_RATE_PER_MINUTE` | 每分钟允许执行的标签分析次数（默认 25） |
| `AUTO_GREET_INTERVAL_SECONDS` | 定时欢迎任务执行间隔秒数（默认 300） |
| `AUTO_REPLY_INTERVAL_SECONDS` | 批量问候/回覆轮询间隔秒数（默认 180） |
| `AUTO_TAG_ANALYZE_INTERVAL_SECONDS` | 标签分析轮询间隔秒数（默认 900） |
| `AUTO_BACKUP_INTERVAL_SECONDS` | 备份排程执行间隔秒数（默认 3600） |

3. 运行前确保已安装 `requirements.txt` 所列依赖，并在启动终端中加载上述环境变量；建议根据实际风控策略调整节流与轮询参数。

---

## 自动化任务与启动方式

- `main.py` 在启动 Pyrogram 客户端后，会通过 `asyncio.create_task` 并行运行四个后台任务：新好友欢迎、批量问候与自动回复、标签分析、数据备份排程。
- 若部署多实例，需依据账号配额调整 `.env` 中的速率与轮询参数，避免过度触发 Telegram 风控。
- 服务器关闭或任务异常时，后台任务具备自动捕获与重启机制，并记录至 `logs/bot.log`。
- 本地调试时可照常运行 `python main.py`，生产建议使用守护进程（systemd、PM2 或容器编排）确保程序持续运行。

---

## 本地敏感信息防护

1. 安装预提交钩子：

   ```bash
   pip install pre-commit detect-secrets
   pre-commit install
   ```

2. 每次 `git commit` 将自动执行敏感信息扫描，命中后需先移除或审查。
3. 若出现误报，可执行 `detect-secrets audit .secrets.baseline` 进行标记。
4. 更多规范与处理流程，参见 `docs/安全準則.md`。

---

## 数据库迁移与备份

### 主程序数据库迁移

1. 运行迁移前会自动备份当前数据库到 `backup/db_bak/`：

   ```bash
   python -m scripts.run_migrations
   ```

2. 迁移脚本会记录版本至 `schema_migrations`，确保只执行一次。
3. 新增迁移可在 `migrations/__init__.py` 中追加条目（含 `version`、`description` 与 SQL `statements`）。

### 后端数据库迁移（admin-backend）

使用 Alembic 进行数据库迁移：

1. **首次部署**：
   ```bash
   cd admin-backend
   # 使用备份脚本（推荐，自动备份 + 迁移）
   poetry run python -m scripts.run_migrations
   
   # 或直接使用 Alembic
   poetry run alembic upgrade head
   ```

2. **创建新迁移**：
   ```bash
   poetry run alembic revision --autogenerate -m "描述变更内容"
   ```

3. **详细说明**：查看 `admin-backend/docs/MIGRATION_GUIDE.md`

---

## 健康检查端点

### 后端 API（admin-backend）

- **`/health`** - 基础健康检查端点
- **`/healthz`** - Kubernetes 健康检查端点（标准）

两个端点功能相同，返回 `{"status": "ok"}`，无需认证。

### 使用示例

```bash
# 健康检查
curl http://localhost:8000/health
# 或
curl http://localhost:8000/healthz

# 预期响应
{"status":"ok"}
```

### Kubernetes 部署

如果使用 Kubernetes，推荐使用 `/healthz` 作为 liveness 和 readiness probe：

```yaml
livenessProbe:
  httpGet:
    path: /healthz
    port: 8000
  initialDelaySeconds: 30
  periodSeconds: 10

readinessProbe:
  httpGet:
    path: /healthz
    port: 8000
  initialDelaySeconds: 10
  periodSeconds: 5
```

---

## 自动化测试与覆盖率

- 安装开发依赖后，执行 `python -m pytest` 运行异步单元/集成测试。
- 若需观测覆盖率，执行：

  ```bash
  python -m pytest --cov=utils --cov-report=term-missing
  ```

- CI/CD 流程已完善，每次提交自动运行测试和代码检查，测试覆盖率目标 80%+。

## CI/CD 流程

项目已配置完整的 GitHub Actions CI/CD 工作流：

### 自动化检查

- **代码检查**: Ruff、Black、ESLint、TypeScript
- **测试执行**: 单元测试、集成测试、E2E 测试
- **测试覆盖率**: 自动生成覆盖率报告（目标 80%+）
- **构建验证**: 自动验证前端和后端构建

### 工作流文件

- `.github/workflows/ci.yml` - 主 CI 工作流
- `.github/workflows/code-quality.yml` - 代码质量检查
- `.github/workflows/release.yml` - 自动化发布流程
- `.github/workflows/dependency-review.yml` - 依赖安全审查

### 本地运行 CI 检查

**后端**:
```bash
cd admin-backend
poetry run ruff check .
poetry run black --check .
poetry run pytest --cov=app
```

**前端**:
```bash
cd saas-demo
npm run lint
npx tsc --noEmit
npm run build
npm run test:e2e
```

详细说明请参考: [CI/CD 流程完善报告](docs/开发笔记/CI_CD流程完善报告.md)

---
