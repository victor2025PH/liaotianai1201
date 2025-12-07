# 部署后的下一步操作指南

## 📊 当前状态

根据 GitHub Actions 页面显示，最新的部署工作流已成功执行：
- ✅ "Add comprehensive service status check to GitHub Actions deployment w..."
- ✅ 部署到服务器 #29
- ✅ 执行时间: 22 秒
- ✅ 状态: 成功

## 🔍 下一步操作

### 步骤 1: 查看详细的部署日志

1. **访问 GitHub Actions 页面**
   - 链接: https://github.com/victor2025PH/liaotianai1201/actions

2. **点击最新的工作流运行**
   - 找到 "Add comprehensive service status check..." 这一行
   - 点击进入查看详细日志

3. **查看服务状态检查结果**
   - 在日志中查找 "服务状态总结" 部分
   - 确认前后端服务的运行状态

### 步骤 2: 验证服务状态

根据部署日志中的服务状态检查结果，执行相应的操作：

#### 如果后端服务正常 ✅
```bash
# 在服务器上验证
ssh ubuntu@<服务器IP>
curl http://localhost:8000/health
```

#### 如果后端服务异常 ❌
```bash
# 在服务器上执行
ssh ubuntu@<服务器IP>
cd /home/ubuntu/telegram-ai-system
bash scripts/server/diagnose-service.sh
bash scripts/server/fix-service.sh
```

#### 如果前端服务正常 ✅
```bash
# 在服务器上验证
ssh ubuntu@<服务器IP>
curl http://localhost:3000
```

#### 如果前端服务异常 ❌
```bash
# 在服务器上执行
ssh ubuntu@<服务器IP>
cd /home/ubuntu/telegram-ai-system
sudo systemctl status liaotian-frontend
# 或
sudo systemctl status smart-tg-frontend
```

### 步骤 3: 访问服务

如果服务正常运行，可以通过以下方式访问：

#### 后端 API
- **本地访问**: http://localhost:8000
- **API 文档**: http://localhost:8000/docs
- **健康检查**: http://localhost:8000/health

#### 前端界面
- **访问地址**: http://localhost:3000
- **登录页面**: http://localhost:3000/login

### 步骤 4: 持续监控

#### 方式 1: 使用 GitHub Actions
- 每次推送代码到 `main` 分支，GitHub Actions 会自动部署并检查服务状态
- 查看部署日志了解服务状态

#### 方式 2: 在服务器上定期检查
```bash
# 创建定时任务（可选）
crontab -e
# 添加: 0 */6 * * * /home/ubuntu/telegram-ai-system/scripts/server/check-services-running.sh >> /var/log/service-check.log 2>&1
```

#### 方式 3: 使用监控脚本
```bash
# 在服务器上执行
cd /home/ubuntu/telegram-ai-system
bash scripts/server/check-services-running.sh
```

## 🛠️ 常见问题处理

### 问题 1: 后端服务启动失败

**症状**: 部署日志显示 "❌ 后端服务: 未运行"

**解决方案**:
```bash
# 1. 查看服务日志
sudo journalctl -u telegram-backend -n 50

# 2. 检查虚拟环境
cd /home/ubuntu/telegram-ai-system/admin-backend
source venv/bin/activate
pip list

# 3. 手动测试启动
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000

# 4. 如果手动启动成功，检查 systemd 配置
sudo systemctl status telegram-backend
cat /etc/systemd/system/telegram-backend.service
```

### 问题 2: 前端服务启动失败

**症状**: 部署日志显示 "❌ 前端服务: 未运行"

**解决方案**:
```bash
# 1. 检查前端服务配置
sudo systemctl status liaotian-frontend
# 或
sudo systemctl status smart-tg-frontend

# 2. 检查前端代码
cd /home/ubuntu/telegram-ai-system/saas-demo
npm run build

# 3. 手动启动测试
npm start
```

### 问题 3: 端口被占用

**症状**: 部署日志显示端口未监听

**解决方案**:
```bash
# 检查端口占用
sudo lsof -i :8000  # 后端端口
sudo lsof -i :3000  # 前端端口

# 终止占用进程
sudo kill -9 <PID>
```

## 📋 验证清单

部署完成后，请确认以下项目：

- [ ] 后端服务正常运行
  - [ ] systemd 服务状态为 active
  - [ ] 端口 8000 正在监听
  - [ ] 健康检查端点响应正常

- [ ] 前端服务正常运行
  - [ ] systemd 服务状态为 active（如果配置了）
  - [ ] 端口 3000 或 3001 正在监听
  - [ ] HTTP 响应正常

- [ ] 服务可以访问
  - [ ] 后端 API 可以访问
  - [ ] 前端界面可以访问
  - [ ] 登录功能正常

- [ ] GitHub Actions 配置正确
  - [ ] Secrets 已配置
  - [ ] 部署工作流可以正常执行
  - [ ] 服务状态检查正常工作

## 🎯 推荐操作流程

1. **立即执行**: 查看 GitHub Actions 部署日志，确认服务状态
2. **验证服务**: 在服务器上执行检查脚本，确认服务正常运行
3. **测试访问**: 访问前端和后端，确认功能正常
4. **设置监控**: 根据需要设置定期检查或监控

## 📞 获取帮助

如果遇到问题：

1. **查看日志**
   - GitHub Actions 日志: https://github.com/victor2025PH/liaotianai1201/actions
   - 服务器服务日志: `sudo journalctl -u telegram-backend -n 50`

2. **使用诊断脚本**
   ```bash
   bash scripts/server/diagnose-service.sh
   ```

3. **查看文档**
   - `GITHUB_ACTIONS_SETUP.md` - GitHub Actions 配置指南
   - `scripts/server/check-services-running.sh` - 服务检查脚本

---

**最后更新**: 2025-12-07

