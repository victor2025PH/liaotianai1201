# SSH Key 配置完成后的下一步操作

## ✅ 验证 SSH 配置

在继续之前，请先验证 SSH 配置是否成功：

### 1. 本地测试 SSH 连接

在 PowerShell 中执行：

```powershell
ssh -i $env:USERPROFILE\.ssh\github_deploy deployer@10.56.61.200 "echo 'SSH 密钥认证成功！'"
```

**如果成功：**
- ✅ 不需要输入密码
- ✅ 直接返回 "SSH 密钥认证成功！"

**如果失败：**
- 检查服务器上的 `~/.ssh/authorized_keys` 文件
- 检查文件权限：`chmod 600 ~/.ssh/authorized_keys`

---

## 🔍 验证 GitHub Secrets 配置

确保 GitHub Secrets 已正确配置：

### 访问 GitHub Secrets 页面

打开：`https://github.com/victor2025PH/liaotianai1201/settings/secrets/actions`

### 检查以下 Secrets 是否存在：

- [ ] **SERVER_SSH_KEY**
  - 值：完整的私钥内容（包括 `-----BEGIN` 和 `-----END` 行）
  
- [ ] **SERVER_HOST**
  - 值：`10.56.61.200`
  
- [ ] **SERVER_USER**
  - 值：`deployer`

**如果没有配置，请立即添加！**

---

## 🚀 测试 GitHub Actions 自动部署

### 方法 1：触发新的部署

1. **在 GitHub 仓库中做一个小修改**（例如修改 README）
2. **提交并推送**：
   ```bash
   git add .
   git commit -m "test: 测试 GitHub Actions 部署"
   git push origin main
   ```
3. **查看 Actions 页面**：
   - 访问：`https://github.com/victor2025PH/liaotianai1201/actions`
   - 应该看到新的工作流运行
   - 点击查看详细信息

### 方法 2：重新运行失败的部署

1. **访问 Actions 页面**：
   - `https://github.com/victor2025PH/liaotianai1201/actions`
   
2. **找到之前的失败部署**，点击进入详情

3. **点击 "Re-run jobs"** 按钮

4. **查看日志**，应该看到：
   - ✅ SSH 连接成功
   - ✅ 代码拉取成功
   - ✅ 部署脚本执行成功
   - ✅ 服务重启成功

---

## 🔧 验证部署结果

部署成功后，验证服务器上的服务：

### 在服务器上检查

```bash
# SSH 登录服务器
ssh deployer@10.56.61.200

# 检查 PM2 服务状态
pm2 status

# 检查端口监听
sudo ss -tlnp | grep -E "3000|8000"

# 查看服务日志
pm2 logs --lines 50
```

### 在浏览器中访问

- **前端：** `http://10.56.61.200`
- **后端 API 文档：** `http://10.56.61.200/docs`
- **后端健康检查：** `http://10.56.61.200/api/health`

---

## 📋 完成检查清单

使用以下清单确认所有步骤已完成：

### SSH 配置
- [ ] SSH 密钥已生成（`github_deploy` 和 `github_deploy.pub`）
- [ ] 公钥已添加到服务器的 `~/.ssh/authorized_keys`
- [ ] 本地 SSH 测试成功（不需要密码）

### GitHub Secrets
- [ ] `SERVER_SSH_KEY` 已配置（完整私钥内容）
- [ ] `SERVER_HOST` 已配置（`10.56.61.200`）
- [ ] `SERVER_USER` 已配置（`deployer`）

### GitHub Actions 部署
- [ ] 工作流运行成功（没有 SSH 认证错误）
- [ ] 代码成功拉取到服务器
- [ ] PM2 服务成功重启
- [ ] 网站可以正常访问

---

## 🎯 后续优化（可选）

### 1. 配置域名和 SSL

如果需要使用域名和 HTTPS：

```bash
# 在服务器上
sudo apt install certbot python3-certbot-nginx

# 配置 SSL（替换为您的域名）
sudo certbot --nginx -d your-domain.com

# 更新 Nginx 配置中的 server_name
sudo nano /etc/nginx/sites-available/telegram-ai-system
# 将 server_name _; 改为 server_name your-domain.com;
sudo systemctl reload nginx
```

### 2. 配置 OPENAI_API_KEY（如果需要 AI 功能）

```bash
# 在服务器上编辑 .env 文件
nano /home/deployer/telegram-ai-system/admin-backend/.env

# 添加：
OPENAI_API_KEY=your_actual_api_key_here

# 重启后端服务
pm2 restart backend --update-env
```

### 3. 安全加固

```bash
# 关闭密码登录，仅使用 SSH Key（可选但推荐）
sudo nano /etc/ssh/sshd_config
# 找到并修改：
# PasswordAuthentication no

# 重启 SSH 服务
sudo systemctl restart ssh
```

**⚠️ 警告：** 在执行此操作前，确保 SSH Key 可以正常使用！

---

## 📚 相关文档

- `docs/DEPLOYMENT_COMPLETE_GUIDE.md` - 完整部署指南
- `docs/DEPLOYMENT_STATUS_SUMMARY.md` - 部署状态总结
- `docs/SETUP_GITHUB_ACTIONS_SSH.md` - SSH 配置指南
- `docs/SETUP_GITHUB_ACTIONS_SSH_WINDOWS.md` - Windows SSH 配置指南

---

## 🐛 如果部署失败

### 常见问题排查

#### 问题 1：SSH 认证失败

**错误信息：** `Permission denied (publickey)`

**解决方法：**
```bash
# 在服务器上检查
ls -la ~/.ssh/
chmod 700 ~/.ssh
chmod 600 ~/.ssh/authorized_keys
```

#### 问题 2：GitHub Actions 工作流失败

**查看日志：**
- 在 GitHub Actions 页面点击失败的作业
- 查看详细错误信息
- 检查是否是 SSH 问题还是部署脚本问题

#### 问题 3：服务未重启

**解决方法：**
```bash
# 在服务器上手动重启
pm2 restart all
pm2 save
```

---

## ✅ 完成！

如果所有步骤都已完成并验证成功，恭喜！您的 Telegram AI 系统现在已经：

- ✅ 成功部署到服务器
- ✅ 配置了自动化部署（GitHub Actions）
- ✅ 服务正常运行
- ✅ 可以通过浏览器访问

**现在您可以：**
- 在本地开发代码
- 推送到 GitHub
- GitHub Actions 自动部署到服务器
- 无需手动操作服务器！

---

**如有任何问题，请查看相关文档或检查服务日志！**
