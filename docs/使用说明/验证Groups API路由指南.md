# 验证 Groups API 路由指南

## 概述

本文档提供详细的流程和方法来验证 Groups API 路由是否在 Swagger 文档中可见。

---

## 方法一：通过 Swagger UI 可视化验证（推荐）

### 步骤 1: 访问 Swagger UI

1. 打开浏览器
2. 访问: `http://localhost:8000/docs`
3. 等待页面完全加载

### 步骤 2: 查找 Groups 标签

1. 在 Swagger UI 页面中，查找左侧的标签列表
2. 查找名为 **"groups"** 的标签
3. 点击该标签展开

### 步骤 3: 验证端点

应该能看到以下 3 个端点：

1. **POST /api/v1/group-ai/groups/create**
   - 描述: 創建新的Telegram群組並啟動群聊
   - 请求参数: `account_id`, `title`, `description`(可选), `member_ids`(可选), `auto_reply`(可选)

2. **POST /api/v1/group-ai/groups/join**
   - 描述: 加入Telegram群組並啟動群聊
   - 请求参数: `account_id`, `group_username`(可选), `group_id`(可选), `invite_link`(可选), `auto_reply`(可选)

3. **POST /api/v1/group-ai/groups/start-chat**
   - 描述: 啟動群組聊天（開始監聽和自動回復）
   - 请求参数: `account_id`, `group_id`, `auto_reply`(可选)

### 步骤 4: 测试端点（可选）

1. 点击任意端点展开
2. 点击 "Try it out" 按钮
3. 填写请求参数
4. 点击 "Execute" 执行
5. 查看响应结果

**预期结果:**
- 如果端点存在但参数错误: 返回 HTTP 422 (验证错误)
- 如果端点不存在: 返回 HTTP 404
- 如果端点存在且参数正确: 返回 HTTP 200 或 201

---

## 方法二：通过 OpenAPI JSON 验证

### 步骤 1: 获取 OpenAPI JSON

在浏览器中访问: `http://localhost:8000/openapi.json`

### 步骤 2: 搜索 Groups 相关路径

在 JSON 中搜索以下路径：

```json
{
  "paths": {
    "/api/v1/group-ai/groups/create": {...},
    "/api/v1/group-ai/groups/join": {...},
    "/api/v1/group-ai/groups/start-chat": {...}
  }
}
```

### 步骤 3: 检查 Tags

查找 "tags" 数组，应该包含：

```json
{
  "tags": [
    {
      "name": "groups",
      "description": "..."
    }
  ]
}
```

---

## 方法三：使用自动化验证脚本（最简单）

### 运行验证脚本

```bash
# 在项目根目录执行
python scripts/test/verify_groups_api.py
```

### 脚本功能

脚本会自动：
1. ✅ 检查 Swagger UI 页面是否可访问
2. ✅ 获取 OpenAPI JSON 文档
3. ✅ 验证所有 Groups API 端点是否存在
4. ✅ 检查 "groups" 标签
5. ✅ 测试实际 API 调用
6. ✅ 生成详细的验证报告

### 预期输出

```
============================================================
验证 Swagger 文档中的 Groups API 路由
============================================================

[1] 获取 OpenAPI JSON 文档...
✅ OpenAPI文档获取成功

[2] 检查 Groups API 路径...
  ✅ /api/v1/group-ai/groups/create - 方法: ['post']
  ✅ /api/v1/group-ai/groups/join - 方法: ['post']
  ✅ /api/v1/group-ai/groups/start-chat - 方法: ['post']

[3] 检查 'groups' 标签...
  ✅ 找到 'groups' 标签: {'name': 'groups'}

[4] 查找所有包含 'groups' 的路径...
  找到 3 个groups相关路径:
    - /api/v1/group-ai/groups/create ['post']
    - /api/v1/group-ai/groups/join ['post']
    - /api/v1/group-ai/groups/start-chat ['post']

[5] 测试实际API调用...
  ✅ /api/v1/group-ai/groups/create - HTTP 422 (验证错误，说明端点存在)

============================================================
验证结果总结
============================================================
✅ 找到的端点: 3/3
  ✅ /api/v1/group-ai/groups/create
  ✅ /api/v1/group-ai/groups/join
  ✅ /api/v1/group-ai/groups/start-chat

✅ Groups API 路由验证成功！
```

---

## 方法四：使用 curl 命令验证

### 测试创建群组端点

```bash
curl -X POST "http://localhost:8000/api/v1/group-ai/groups/create" \
  -H "Content-Type: application/json" \
  -d '{"account_id":"test","title":"test"}'
```

**预期响应:**
- HTTP 422: 端点存在，但参数验证失败（正常）
- HTTP 404: 端点不存在（需要检查路由配置）

### 测试加入群组端点

```bash
curl -X POST "http://localhost:8000/api/v1/group-ai/groups/join" \
  -H "Content-Type: application/json" \
  -d '{"account_id":"test","group_username":"test"}'
```

### 测试启动群聊端点

```bash
curl -X POST "http://localhost:8000/api/v1/group-ai/groups/start-chat" \
  -H "Content-Type: application/json" \
  -d '{"account_id":"test","group_id":-1001234567890}'
```

---

## 方法五：使用 PowerShell 验证（Windows）

### 测试端点

```powershell
# 测试创建群组端点
$response = Invoke-WebRequest -Uri "http://localhost:8000/api/v1/group-ai/groups/create" `
  -Method POST `
  -ContentType "application/json" `
  -Body '{"account_id":"test","title":"test"}' `
  -ErrorAction Stop

Write-Host "状态码: $($response.StatusCode)"
```

**状态码说明:**
- 422: ✅ 端点存在（验证错误是正常的）
- 404: ❌ 端点不存在
- 200/201: ✅ 端点存在且请求成功

---

## 常见问题排查

### 问题 1: Swagger UI 中看不到 groups 标签

**可能原因:**
1. 后端服务未完全重新加载
2. groups 模块导入失败
3. 路由未正确注册

**解决方法:**
1. 检查后端日志: `admin-backend/backend.log`
2. 查找是否有导入错误
3. 手动重启后端服务

### 问题 2: API 端点返回 404

**可能原因:**
1. 路由配置错误
2. prefix 重复或缺失
3. 服务未重新加载

**解决方法:**
1. 检查 `admin-backend/app/api/group_ai/__init__.py`
2. 确认 `router.include_router(groups.router, prefix="/groups", tags=["groups"])`
3. 重启后端服务

### 问题 3: 端点存在但功能不工作

**可能原因:**
1. GroupManager 导入失败
2. 依赖服务未初始化
3. 数据库连接问题

**解决方法:**
1. 检查后端日志中的错误信息
2. 验证 GroupManager 模块是否正确导入
3. 检查 ServiceManager 是否正常初始化

---

## 验证清单

使用以下清单确保所有功能正常：

- [ ] Swagger UI 页面可访问 (`http://localhost:8000/docs`)
- [ ] 能看到 "groups" 标签
- [ ] 能看到 3 个 groups 端点
- [ ] 每个端点都能展开查看详情
- [ ] 测试 API 调用返回 422（验证错误）而不是 404
- [ ] 前端界面中的"创建群组"按钮可用
- [ ] 后端日志中没有导入错误

---

## 快速验证命令

### 一键验证（推荐）

```bash
python scripts/test/verify_groups_api.py
```

### 手动验证

```bash
# 1. 检查Swagger UI
curl http://localhost:8000/docs

# 2. 检查OpenAPI JSON
curl http://localhost:8000/openapi.json | grep -i groups

# 3. 测试API端点
curl -X POST http://localhost:8000/api/v1/group-ai/groups/create \
  -H "Content-Type: application/json" \
  -d '{"account_id":"test","title":"test"}'
```

---

## 总结

**最简单的方法:** 运行自动化验证脚本
```bash
python scripts/test/verify_groups_api.py
```

**最直观的方法:** 访问 Swagger UI
```
http://localhost:8000/docs
```

**最快速的方法:** 使用 curl 测试端点
```bash
curl -X POST http://localhost:8000/api/v1/group-ai/groups/create \
  -H "Content-Type: application/json" \
  -d '{"account_id":"test","title":"test"}'
```

如果返回 HTTP 422，说明端点存在且正常工作！

