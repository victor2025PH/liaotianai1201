# Legacy Workers & Scripts

此目录包含已弃用的独立 worker 脚本和测试文件。

## 说明

这些文件是旧版本的独立实现，功能已经整合到 `group_ai_service/` 中：

- **红包功能**: 已整合到 `group_ai_service/redpacket_handler.py` 和 `dialogue_manager.py`
- **实时监控**: 已整合到 `group_ai_service/monitor_service.py`
- **数据分析**: 已整合到 `group_ai_service/monitor_service.py`
- **服务管理**: 统一由 `group_ai_service/service_manager.py` 管理

## 文件分类

### Worker 脚本 (worker_*.py)
- `worker_auto_redpacket.py` - 自动红包处理（已整合）
- `worker_realtime_monitor.py` - 实时监控（已整合）
- `worker_analytics.py` - 数据分析（已整合）
- `worker_group_manager.py` - 群组管理（已整合）
- 其他 worker 脚本...

### 测试文件 (test_*.py)
- 各种测试脚本，用于验证功能
- 建议使用 `tests/` 目录下的正式测试

### 启动脚本 (start_*.py)
- 独立的启动脚本，已不再使用
- 现在统一通过 `app/main.py` 启动

### 检查脚本 (check_*.py, verify_*.py)
- 各种检查和验证脚本
- 部分功能已整合到主应用

## 迁移指南

如果需要使用这些功能，请使用新的统一接口：

1. **启动服务**: 使用 `uvicorn app.main:app` 或 `python main.py`
2. **红包功能**: 通过 `ServiceManager` 和 `DialogueManager` 自动处理
3. **监控功能**: 通过 `MonitorService` 获取指标
4. **数据分析**: 通过 API 端点 `/api/system/monitor` 获取

## 注意

⚠️ **这些文件已不再维护，请勿直接使用。**

如需参考实现细节，可以查看这些文件，但建议使用新的统一接口。

