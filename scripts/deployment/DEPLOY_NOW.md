# 立即部署指南

## 当前服务器信息

- **IP地址**: 165.154.254.99
- **用户**: root
- **密码**: Along2025!!!
- **节点ID**: worker-01
- **最大账号数**: 5

## 部署状态

服务器已添加到配置，正在后台执行部署...

## 查看部署进度

部署过程可能需要15-30分钟，包括：

1. ✅ 基础环境部署（更新系统、安装工具、Python 3.11）
2. ⏳ 上传项目文件
3. ⏳ 安装Python依赖
4. ⏳ 创建配置文件
5. ⏳ 创建启动脚本

## 部署完成后

1. **配置API密钥**:
   ```bash
   ssh root@165.154.254.99
   vi /opt/group-ai/.env
   ```
   修改：
   - `TELEGRAM_API_ID`
   - `TELEGRAM_API_HASH`
   - `OPENAI_API_KEY`

2. **上传Session文件**:
   ```bash
   scp *.session root@165.154.254.99:/opt/group-ai/sessions/
   ```

3. **启动服务**:
   ```bash
   ssh root@165.154.254.99 'systemctl start group-ai-worker'
   ```

4. **查看日志**:
   ```bash
   ssh root@165.154.254.99 'tail -f /opt/group-ai/logs/worker.log'
   ```

## 如果部署失败

查看详细错误信息：
```bash
python scripts/deployment/master_controller.py --deploy worker-01
```

或手动执行部署步骤，参考：
- `scripts/deployment/QUICK_DEPLOY.md`
- `scripts/deployment/README_AUTO.md`

