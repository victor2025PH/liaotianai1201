# 下一步操作指南

## 📋 当前状态

✅ 已更新配置文件 `data/master_config.json`
- `los-angeles` 节点IP已更新为 `165.154.235.170`

---

## 🎯 下一步操作步骤

### 步骤 1: 验证配置文件格式

**执行位置：本地**

```bash
# 验证JSON格式是否正确
python -m json.tool data/master_config.json > /dev/null && echo "配置文件格式正确" || echo "配置文件格式错误"
```

**作用：** 确保JSON格式正确，避免语法错误

---

### 步骤 2: 测试SSH连接

**执行位置：本地（如果已安装paramiko）或服务器**

#### 方法1: 使用检测工具（推荐）

**执行位置：本地**

```bash
# 安装依赖（如果还没有）
pip install paramiko

# 运行检测工具
python scripts/server/update-server-ips.py
```

**作用：** 自动测试所有工作节点的SSH连接

#### 方法2: 手动测试SSH连接

**执行位置：本地或服务器**

```bash
# 测试 los-angeles 节点连接
ssh ubuntu@165.154.235.170

# 如果连接成功，输入密码：8iDcGrYb52Fxpzee
# 连接成功后，运行以下命令验证：
hostname -I
ls -la /home/ubuntu
exit
```

**作用：** 验证SSH连接是否正常，确保主节点可以连接到工作节点

---

### 步骤 3: 将配置文件推送到服务器

**执行位置：本地**

```bash
# 1. 添加文件到Git
git add data/master_config.json

# 2. 提交更改
git commit -m "更新工作节点IP: los-angeles -> 165.154.235.170"

# 3. 推送到GitHub（根据你的规则，不自动push）
# git push
```

**作用：** 保存配置更改到Git仓库

**注意：** 根据你的规则，只执行 `git add` 和 `git commit`，不执行 `git push`

---

### 步骤 4: 在服务器上更新配置文件

**执行位置：服务器（SSH登录到主节点）**

```bash
# 方法1: 从GitHub拉取最新代码（如果已推送）
cd /home/ubuntu/telegram-ai-system
git pull origin main  # 或 master，根据你的分支名

# 方法2: 直接编辑配置文件
nano /home/ubuntu/telegram-ai-system/data/master_config.json
# 或
vim /home/ubuntu/telegram-ai-system/data/master_config.json

# 找到 los-angeles 节点，将 host 改为 165.154.235.170
```

**作用：** 确保服务器上的配置文件是最新的

---

### 步骤 5: 重启后端服务

**执行位置：服务器**

```bash
# 重启后端服务以加载新配置
sudo systemctl restart luckyred-api

# 等待几秒
sleep 3

# 检查服务状态
sudo systemctl status luckyred-api --no-pager | head -20

# 查看日志确认没有错误
sudo journalctl -u luckyred-api -n 30 --no-pager | grep -i "server\|config\|error"
```

**作用：** 让后端服务重新加载配置文件

---

### 步骤 6: 验证服务器列表API

**执行位置：服务器**

```bash
# 测试服务器列表API（需要先登录获取token）
# 方法1: 使用curl测试（需要token）
curl -X GET "http://localhost:8000/api/v1/group-ai/servers/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json"

# 方法2: 查看后端日志
sudo journalctl -u luckyred-api -f
# 然后在前端访问服务器列表页面，观察日志输出
```

**作用：** 验证后端API能否正确读取和返回服务器列表

---

### 步骤 7: 在前端验证

**执行位置：浏览器**

1. **访问前端页面**
   - 打开浏览器，访问你的前端地址
   - 登录系统

2. **导航到服务器列表页面**
   - 在左侧菜单找到"群组 AI" → "节点管理" 或 "服务器列表"
   - 或直接访问：`/group-ai/servers`

3. **检查服务器列表**
   - 应该能看到所有配置的工作节点
   - 检查 `los-angeles` 节点的状态
   - 如果显示"在线"或"连接成功"，说明配置正确

4. **检查节点详情**
   - 点击节点查看详细信息
   - 确认IP地址显示为 `165.154.235.170`
   - 检查账号数量、状态等信息

**作用：** 验证前端能否正常显示服务器列表

---

## 🔍 故障排查

### 问题1: SSH连接失败

**症状：** 无法连接到工作节点

**解决方法：**
```bash
# 1. 检查IP是否正确
ping 165.154.235.170

# 2. 检查SSH服务是否运行
ssh -v ubuntu@165.154.235.170

# 3. 检查防火墙设置
# 确保端口22开放
```

---

### 问题2: 服务器列表加载失败

**症状：** 前端显示"加载服务器列表失败"

**解决方法：**
```bash
# 1. 检查配置文件是否存在
ls -la /home/ubuntu/telegram-ai-system/data/master_config.json

# 2. 检查配置文件格式
python3 -m json.tool /home/ubuntu/telegram-ai-system/data/master_config.json

# 3. 查看后端日志
sudo journalctl -u luckyred-api -n 50 --no-pager | grep -i "server\|config\|error"

# 4. 重启后端服务
sudo systemctl restart luckyred-api
```

---

### 问题3: 节点状态显示"离线"

**症状：** 节点显示为离线或连接失败

**解决方法：**
```bash
# 1. 测试SSH连接
ssh ubuntu@165.154.235.170

# 2. 检查后端日志
sudo journalctl -u luckyred-api -n 50 --no-pager | grep "los-angeles"

# 3. 验证密码是否正确
# 如果密码错误，更新配置文件中的密码
```

---

## ✅ 完成检查清单

- [ ] 配置文件格式正确
- [ ] SSH连接测试成功
- [ ] 配置文件已提交到Git
- [ ] 服务器上的配置文件已更新
- [ ] 后端服务已重启
- [ ] 服务器列表API测试通过
- [ ] 前端能正常显示服务器列表
- [ ] 节点状态显示正常

---

## 📝 快速命令序列

**在服务器上执行（一键验证）：**

```bash
# 1. 检查配置文件
cat /home/ubuntu/telegram-ai-system/data/master_config.json | grep -A 5 "los-angeles"

# 2. 测试SSH连接（需要手动输入密码）
ssh -o ConnectTimeout=5 ubuntu@165.154.235.170 "echo 'SSH连接成功'"

# 3. 重启后端服务
sudo systemctl restart luckyred-api && sleep 3 && sudo systemctl status luckyred-api --no-pager | head -15

# 4. 查看日志
sudo journalctl -u luckyred-api -n 20 --no-pager | grep -i "server\|config"
```

---

## 🎯 预期结果

完成所有步骤后，你应该能够：

1. ✅ 在前端看到所有工作节点
2. ✅ `los-angeles` 节点显示为"在线"
3. ✅ 可以查看每个节点的详细信息
4. ✅ 可以注册新账号并自动分配到工作节点
5. ✅ 系统能够正常监控工作节点状态

---

## 💡 提示

- 如果某个步骤失败，查看对应的故障排查部分
- 确保所有工作节点的SSH密码正确
- 定期检查服务器列表，确保所有节点在线
- 如果IP地址再次变化，重复步骤1-7
