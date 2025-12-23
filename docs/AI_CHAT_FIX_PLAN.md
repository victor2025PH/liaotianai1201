# AI 对话功能修复方案

## 问题诊断

### 当前问题
1. 访问 `https://aiadmin.usdt2026.cc/api/v1/frontend-config/ai-keys` 返回 `{"detail": "Not Found"}`
2. 前端无法获取 AI API Keys，导致 AI 对话功能不可用
3. **关键问题**：后端日志显示 `Config file '{env_file}' not found.` 和 `OPENAI_API_KEY未设置`

### 根本原因
从图片分析发现：
- **真实项目路径**：`/home/ubuntu/telegram-ai-system/`
- **后端目录**：`/home/ubuntu/telegram-ai-system/admin-backend/`
- **问题**：Pydantic Settings 在查找 `.env` 文件时，工作目录可能不正确，导致找不到配置文件

### 已修复的问题
✅ **路由前缀重复问题**：`frontend_config.py` 中的 prefix 已从 `/api/v1/frontend-config` 改为 `/frontend-config`
✅ **.env 文件查找问题**：修改 `config.py` 使用绝对路径查找 `.env` 文件

## 完整修复方案

### 步骤 1: 验证后端路由注册

**文件**: `admin-backend/app/api/__init__.py`

确认 `frontend_config.router` 已包含：
```python
from app.api import frontend_config
router.include_router(frontend_config.router)  # 第 35 行
```

### 步骤 2: 检查后端服务状态

在服务器上执行：
```bash
# 检查 PM2 进程
pm2 list

# 检查后端日志
pm2 logs backend --lines 50

# 检查后端是否监听正确端口
netstat -tlnp | grep :8000
# 或
lsof -i :8000
```

### 步骤 3: 验证环境变量配置

**文件**: `/home/ubuntu/telegram-ai-system/admin-backend/.env`

确保包含以下配置：
```env
OPENAI_API_KEY=sk-your-openai-key-here
GEMINI_API_KEY=your-gemini-key-here
```

### 步骤 4: 测试后端 API（本地测试）

在服务器上执行：
```bash
# 进入后端目录
cd /home/ubuntu/telegram-ai-system/admin-backend

# 激活虚拟环境（如果使用）
source venv/bin/activate

# 测试 API 端点
curl http://127.0.0.1:8000/api/v1/frontend-config/ai-keys
```

### 步骤 5: 检查 PM2 配置

**文件**: `/home/ubuntu/telegram-ai-system/ecosystem.config.js`

确保 `cwd` 配置正确：
```javascript
{
  name: "backend",
  cwd: "/home/ubuntu/telegram-ai-system/admin-backend",  // 确保这个路径正确
  // ...
}
```

### 步骤 6: 重启服务

```bash
# 重启后端（使用正确的路径）
cd /home/ubuntu/telegram-ai-system

# 删除旧进程
pm2 delete backend 2>/dev/null || true

# 重新启动（使用 ecosystem.config.js）
pm2 start ecosystem.config.js --only backend

# 或使用 PM2 命令直接启动
cd /home/ubuntu/telegram-ai-system/admin-backend
pm2 start ./start.sh \
  --name backend \
  --cwd /home/ubuntu/telegram-ai-system/admin-backend \
  --update-env \
  --error /home/ubuntu/telegram-ai-system/logs/backend-error.log \
  --output /home/ubuntu/telegram-ai-system/logs/backend-out.log

# 保存配置
pm2 save

# 重新加载 Nginx
sudo nginx -t
sudo nginx -s reload
```

### 步骤 7: 验证修复

1. **测试后端 API**:
   ```bash
   curl http://127.0.0.1:8000/api/v1/frontend-config/ai-keys
   ```
   应该返回：
   ```json
   {
     "openai_api_key": "sk-...",
     "gemini_api_key": "...",
     "default_language": "zh-CN",
     "ai_model": "gpt-4o-mini"
   }
   ```

2. **测试远程 API**:
   ```bash
   curl -k https://aiadmin.usdt2026.cc/api/v1/frontend-config/ai-keys
   ```
   （使用 `-k` 忽略 SSL 证书错误，如果证书有问题）

3. **测试前端**:
   - 访问 `https://aizkw.usdt2026.cc`
   - 打开浏览器开发者工具 (F12)
   - 查看 Console 和 Network 标签
   - 尝试发送 AI 消息

## 常见问题排查

### 问题 1: 仍然返回 404

**可能原因**:
- Nginx 配置错误
- 后端服务未运行
- 路由未正确注册

**解决方案**:
```bash
# 检查后端是否运行
pm2 list | grep backend

# 检查后端日志
pm2 logs backend --lines 100

# 检查路由注册
cd /home/ubuntu/telegram-ai-system/admin-backend
source venv/bin/activate
python -c "
from app.main import app
for route in app.routes:
    if hasattr(route, 'path'):
        print(f'{route.methods if hasattr(route, \"methods\") else \"N/A\"} {route.path}')
" | grep frontend-config
```

### 问题 2: 返回空 API Key

**可能原因**:
- `.env` 文件未配置
- 环境变量未加载
- `.env` 文件路径不正确

**解决方案**:
```bash
# 检查 .env 文件
cat /home/ubuntu/telegram-ai-system/admin-backend/.env | grep -E "OPENAI_API_KEY|GEMINI_API_KEY"

# 检查环境变量是否加载
cd /home/ubuntu/telegram-ai-system/admin-backend
source venv/bin/activate
python -c "
from app.core.config import get_settings
settings = get_settings()
print(f'OpenAI Key: {settings.openai_api_key[:10]}...' if settings.openai_api_key else 'OpenAI Key: 未设置')
print(f'Gemini Key: {settings.gemini_api_key[:10]}...' if settings.gemini_api_key else 'Gemini Key: 未设置')
print(f'Env file path: {settings.model_config.get(\"env_file\", \"未设置\")}')
"

# 重启服务以重新加载环境变量
pm2 restart backend --update-env
```

### 问题 3: CORS 错误

**已修复**：`admin-backend/app/core/config.py` 中的 `cors_origins` 已包含所有前端域名。

### 问题 4: 前端无法连接

**可能原因**:
- API 地址配置错误
- 网络问题
- SSL 证书问题

**解决方案**:
检查前端 `aiConfig.ts` 文件中的 `API_BASE_URL`:
```typescript
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'https://aiadmin.usdt2026.cc';
```

### 问题 5: 后端找不到 .env 文件

**已修复**：`admin-backend/app/core/config.py` 已更新为使用绝对路径查找 `.env` 文件。

**验证方法**:
```bash
cd /home/ubuntu/telegram-ai-system/admin-backend
source venv/bin/activate
python -c "
from app.core.config import Settings
import os
print('Env file path:', Settings._env_file_path)
print('File exists:', os.path.exists(Settings._env_file_path))
"
```

## 完整测试流程

### 1. 后端测试
```bash
# 在服务器上
curl -X GET http://127.0.0.1:8000/api/v1/frontend-config/ai-keys \
  -H "Content-Type: application/json"
```

### 2. 前端测试
1. 打开 `https://aizkw.usdt2026.cc`
2. 打开浏览器开发者工具 (F12)
3. 切换到 Network 标签
4. 尝试发送 AI 消息
5. 查看是否有对 `/api/v1/frontend-config/ai-keys` 的请求
6. 检查响应内容

### 3. AI 对话测试
1. 在聊天界面输入测试消息
2. 检查是否优先使用 Gemini
3. 如果 Gemini 失败，检查是否自动切换到 OpenAI
4. 查看 Console 日志确认流程

## 修改文件清单

### 已修改
- ✅ `admin-backend/app/api/frontend_config.py` - 修复路由前缀
- ✅ `admin-backend/app/core/config.py` - 修复 .env 文件查找路径
- ✅ `scripts/verify_ai_api.sh` - 更新路径为正确值

### 需要验证
- ⚠️ `admin-backend/app/api/__init__.py` - 确认路由已注册
- ⚠️ `/home/ubuntu/telegram-ai-system/admin-backend/.env` - 确认 API Keys 已配置
- ⚠️ `/home/ubuntu/telegram-ai-system/ecosystem.config.js` - 确认 PM2 配置正确
- ⚠️ Nginx 配置 - 确认代理设置正确

## 下一步行动

1. **立即执行**: 在服务器上重启后端服务
2. **验证**: 测试 API 端点是否可访问
3. **配置**: 确认环境变量已设置
4. **测试**: 在前端网站测试 AI 对话功能

## 快速修复命令（在服务器上执行）

```bash
# 1. 进入项目目录
cd /home/ubuntu/telegram-ai-system

# 2. 检查 .env 文件
cat admin-backend/.env | grep -E "OPENAI_API_KEY|GEMINI_API_KEY"

# 3. 重启后端
pm2 delete backend 2>/dev/null || true
pm2 start ecosystem.config.js --only backend
pm2 save

# 4. 等待几秒后测试
sleep 5
curl http://127.0.0.1:8000/api/v1/frontend-config/ai-keys

# 5. 查看日志
pm2 logs backend --lines 30
```
