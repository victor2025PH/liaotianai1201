# Implementation Plan

- [-] 1. 创建环境变量模式定义和核心数据模型

  - 创建 `config/env_schema.yaml` 文件，定义所有环境变量的模式
  - 实现 `utils/env_schema.py`，包含 `EnvVarDefinition` 和 `EnvSchema` 数据模型
  - 添加从 YAML 文件加载模式的功能
  - _Requirements: 1.5, 4.3, 8.5_

- [ ]* 1.1 为环境变量模式编写属性测试
  - **Property 7: 验证幂等性**
  - **验证需求: Requirements 1.1, 7.2**

- [ ] 2. 实现环境变量加载器
  - 实现 `utils/env_loader.py` 中的 `EnvLoader` 类
  - 支持从多个源加载环境变量（系统环境、.env 文件、服务特定文件）
  - 实现优先级顺序：系统环境 > .env.local > 服务特定 .env > 根 .env
  - 记录加载的配置源
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_

- [ ]* 2.1 为环境变量加载器编写属性测试
  - **Property 5: 配置源优先级**
  - **验证需求: Requirements 6.1, 6.2, 6.3, 6.4**

- [ ] 3. 实现配置验证引擎
  - 实现 `utils/env_validator.py` 中的 `EnvValidator` 类
  - 实现类型验证（int, float, bool, str, url, path, enum）
  - 实现约束验证（min/max 值、正则表达式、枚举值）
  - 实现必填项检查
  - 实现生产环境安全检查（检测不安全的默认值）
  - 实现错误收集和格式化
  - _Requirements: 1.1, 1.2, 1.3, 3.1, 3.2, 3.3, 3.4, 3.5, 5.4, 5.5_

- [ ]* 3.1 为类型验证编写属性测试
  - **Property 2: 类型安全性**
  - **验证需求: Requirements 3.1, 3.2, 3.3**

- [ ]* 3.2 为约束验证编写属性测试
  - **Property 3: 约束一致性**
  - **验证需求: Requirements 3.1, 3.2, 3.3, 3.4**

- [ ]* 3.3 为必填变量检查编写属性测试
  - **Property 1: 必填变量完整性**
  - **验证需求: Requirements 1.1, 1.2**

- [ ]* 3.4 为生产环境安全检查编写属性测试
  - **Property 6: 生产环境安全性**
  - **验证需求: Requirements 5.4**

- [ ] 4. 实现统一配置管理器
  - 实现 `utils/config_manager.py` 中的 `ConfigManager` 类
  - 集成加载器和验证器
  - 实现 `load_and_validate()` 方法（支持 fail-fast 模式）
  - 实现 `get()` 方法获取配置值
  - 实现敏感数据遮蔽功能
  - _Requirements: 1.1, 1.4, 5.2, 5.3_

- [ ]* 4.1 为敏感数据遮蔽编写属性测试
  - **Property 4: 敏感数据遮蔽**
  - **验证需求: Requirements 5.2, 5.3**

- [ ] 5. 创建环境变量模式定义文件
  - 创建 `config/env_schema.yaml`，定义所有现有环境变量
  - 包含 Telegram API 配置（TELEGRAM_API_ID, TELEGRAM_API_HASH, TELEGRAM_SESSION_NAME）
  - 包含 OpenAI API 配置（OPENAI_API_KEY, OPENAI_MODEL, OPENAI_VISION_MODEL）
  - 包含数据库配置（DATABASE_URL）
  - 包含后端配置（JWT_SECRET, BACKEND_PORT, CORS_ORIGINS）
  - 包含前端配置（NEXT_PUBLIC_API_URL）
  - 为每个变量添加类型、约束、描述、示例
  - _Requirements: 4.1, 4.2, 4.3, 8.1, 8.5_

- [ ] 6. 创建 .env.example 模板文件
  - 创建根目录 `.env.example`，包含所有共享环境变量
  - 创建 `admin-backend/.env.example`，包含后端特定变量
  - 创建 `saas-demo/.env.example`，包含前端特定变量
  - 为每个变量添加注释说明
  - 提供示例值（非敏感数据）
  - _Requirements: 2.1, 2.5, 8.1, 8.2_

- [ ] 7. 更新 .gitignore 文件
  - 确保 `.env` 文件不被提交到版本控制
  - 添加 `.env.local`、`.env.production` 等变体
  - 确保 `.env.example` 文件会被提交
  - _Requirements: 2.1, 2.2_

- [ ] 8. 集成到主应用 (main.py)
  - 更新 `config.py`，使用新的 `ConfigManager` 替代现有的环境变量加载
  - 在 `main_async()` 函数开始时调用 `config_manager.load_and_validate()`
  - 移除现有的 `validate_required_env_on_startup()` 函数（由新系统替代）
  - 更新所有配置访问代码使用 `config_manager.get()`
  - _Requirements: 1.1, 1.2, 1.3, 1.4_

- [ ] 9. 集成到后端服务 (admin-backend)
  - 更新 `admin-backend/app/core/config.py`，使用新的配置管理系统
  - 在 `on_startup()` 事件中添加配置验证
  - 更新所有使用 `get_settings()` 的代码
  - 确保后端特定的环境变量被正确加载和验证
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 4.5_

- [ ] 10. 集成到前端 (saas-demo)
  - 创建前端配置验证脚本（在构建时运行）
  - 更新 `package.json` 添加配置验证步骤
  - 确保 `NEXT_PUBLIC_*` 环境变量被正确验证
  - _Requirements: 1.1, 1.2, 1.3, 4.5_

- [ ] 11. 创建独立验证脚本
  - 创建 `scripts/validate_env.py`，可独立运行的验证脚本
  - 支持交互模式（显示详细错误和建议）
  - 支持 CI 模式（非交互，返回退出码）
  - 支持指定服务（main, backend, frontend）
  - 显示加载的配置源和验证结果摘要
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

- [ ] 12. 更新 README.md 文档
  - 添加 `<a id="env-vars"></a>` 锚点和"环境变量配置"章节
  - 添加 `<a id="verify"></a>` 锚点和"验证步骤"章节
  - 列出所有必填环境变量的表格
  - 提供快速开始指南（复制 .env.example、填写配置、验证）
  - 添加常见问题解答（如何获取 API 密钥、加载顺序等）
  - 添加故障排查指南
  - _Requirements: 8.1, 8.2, 8.3, 8.4_

- [ ]* 12.1 为错误消息格式编写单元测试
  - **Property 8: 错误消息完整性**
  - **验证需求: Requirements 1.2, 1.3, 7.4**

- [ ] 13. 编写单元测试
  - 为 `env_schema.py` 编写测试（模式加载、验证）
  - 为 `env_loader.py` 编写测试（多源加载、优先级）
  - 为 `env_validator.py` 编写测试（所有类型和约束验证）
  - 为 `config_manager.py` 编写测试（集成测试、敏感数据遮蔽）
  - 确保测试覆盖率 > 80%
  - _Requirements: 所有需求_

- [ ]* 13.1 编写属性测试生成器
  - 实现 `environment_configs()` 生成器（生成随机配置）
  - 实现 `valid_environment_configs()` 生成器（生成有效配置）
  - 实现 `sensitive_value()` 生成器（生成敏感值）

- [ ] 14. 编写集成测试
  - 测试完整的配置加载和验证流程
  - 测试与 main.py 的集成
  - 测试与 admin-backend 的集成
  - 测试错误场景（缺失变量、无效值、类型错误）
  - 测试配置源优先级
  - _Requirements: 所有需求_

- [ ] 15. Checkpoint - 确保所有测试通过
  - 确保所有测试通过，如有问题请询问用户

- [ ] 16. 创建迁移指南
  - 编写 `docs/migration/env-config-migration.md`
  - 说明如何从旧配置系统迁移到新系统
  - 提供迁移检查清单
  - 说明向后兼容性和破坏性变更
  - _Requirements: 8.3_

- [ ] 17. 更新部署文档
  - 更新 `admin-backend/DEPLOY_QUICKSTART.md`
  - 添加环境变量配置步骤
  - 添加生产环境配置建议
  - 添加密钥管理最佳实践
  - _Requirements: 8.3, 8.4_

- [ ] 18. 添加 pre-commit hooks
  - 创建 `.pre-commit-config.yaml`（如果不存在）
  - 添加检查防止提交 `.env` 文件
  - 添加检查确保 `.env.example` 与模式同步
  - _Requirements: 2.2_

- [ ] 19. 更新 CI/CD 配置
  - 在 CI 流程中添加环境变量验证步骤
  - 确保测试环境使用正确的配置
  - 添加配置验证到部署流程
  - _Requirements: 7.5_

- [ ] 20. Final Checkpoint - 确保所有测试通过
  - 确保所有测试通过，如有问题请询问用户
