# 分配剧本问题修复 - 快速参考

## 问题

分配剧本时显示"账号不存在"错误，虽然账号在节点管理和账号管理页面都可见。

## 快速修复命令

### 一键启动服务
```bash
bash ~/liaotian/deploy/一键启动并测试分配剧本.sh
```

### 查看日志
```bash
tail -f /tmp/backend_final.log | grep -E "MIDDLEWARE|UPDATE_ACCOUNT|server_id|账号ID匹配"
```

### 手动启动服务

#### 后端
```bash
cd ~/liaotian/admin-backend
source .venv/bin/activate
nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 > /tmp/backend_final.log 2>&1 &
```

#### 前端
```bash
cd ~/liaotian/saas-demo
nohup npm run dev > /tmp/frontend.log 2>&1 &
```

## 关键修复点

1. **账号ID匹配**：统一字符串类型，去除空格
2. **server_id 传递**：优先使用 server_id，如果没有则使用 node_id
3. **远程服务器扫描**：自动扫描并创建数据库记录
4. **详细日志**：记录所有关键步骤

## 测试

1. 刷新浏览器（Ctrl+Shift+R）
2. 选择 Worker 节点账号
3. 点击"分配剧本"
4. 查看浏览器控制台和后端日志

## 日志文件

- `/tmp/backend_final.log` - 后端详细日志
- `/tmp/frontend.log` - 前端日志

## 相关文档

- `docs/开发笔记/分配剧本问题-最终修复总结.md` - 完整修复说明
- `docs/开发笔记/分配剧本问题-账号ID匹配修复.md` - 账号ID匹配修复详情
