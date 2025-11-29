# 检查 Worker 节点心跳

## 问题

前端页面显示 401 Unauthorized，且没有显示 Worker 节点和账号。

## 可能的原因

1. **前端代码未重新构建**：修复后的代码还没有部署
2. **Worker 节点未重启**：修复后的心跳代码还没有生效
3. **心跳请求格式仍不正确**：虽然修复了代码，但节点还没有使用新代码
4. **后端未收到心跳**：网络问题或配置问题

## 检查步骤

### 1. 检查后端是否收到心跳

在服务器上执行：

```bash
# 检查后端日志
sudo journalctl -u liaotian-backend -n 100 --no-pager | grep -i "worker\|heartbeat"

# 直接测试 Workers API
curl http://127.0.0.1:8000/api/v1/workers/ | python3 -m json.tool
```

### 2. 检查 Worker 节点日志

在 `computer_001` 和 `computer_002` 上：

1. 确认已经使用修复后的代码重启
2. 检查日志中是否有心跳发送成功的消息
3. 如果没有，检查是否有错误信息

### 3. 检查前端代码

1. 确认前端代码已经重新构建
2. 清除浏览器缓存
3. 强制刷新页面（Ctrl+F5）

## 快速修复

### 方法 1: 使用批处理脚本

运行 `deploy/立即修复前端和检查心跳.bat`

### 方法 2: 手动执行

```powershell
# 1. 上传前端文件
scp saas-demo/src/app/group-ai/nodes/page.tsx ubuntu@165.154.233.55:/home/ubuntu/liaotian/saas-demo/src/app/group-ai/nodes/page.tsx

# 2. 上传后端文件
scp admin-backend/app/api/workers.py ubuntu@165.154.233.55:/home/ubuntu/liaotian/admin-backend/app/api/workers.py

# 3. 重启后端
ssh ubuntu@165.154.233.55 "sudo systemctl restart liaotian-backend"

# 4. 重新构建前端
ssh ubuntu@165.154.233.55 "cd /home/ubuntu/liaotian/saas-demo && export NVM_DIR=\"$HOME/.nvm\" && [ -s \"$NVM_DIR/nvm.sh\" ] && . \"$NVM_DIR/nvm.sh\" && nvm use 20 && npm run build && sudo systemctl restart liaotian-frontend"
```

## 验证

修复后应该看到：

1. ✅ 前端不再显示 401 错误
2. ✅ 节点列表显示 `computer_001` 和 `computer_002`
3. ✅ 每个节点显示账号数量和状态
4. ✅ 账号列表显示已登录的账号信息

