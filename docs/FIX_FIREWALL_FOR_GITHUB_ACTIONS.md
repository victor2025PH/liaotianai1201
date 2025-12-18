# 修复防火墙阻止 GitHub Actions SSH 连接

## 🚨 问题诊断

**错误信息：**
```
dial tcp ***:22: i/o timeout
```

**根本原因：**
GitHub Actions 使用**美国的动态 IP 地址**。如果您的服务器安全组/防火墙设置了：
- 只允许特定 IP
- 只允许国内 IP（白名单）
- 限制来源 IP 范围

那么 GitHub Actions 的 IP 会被阻止，导致连接超时。

---

## ✅ 立即修复（在云服务器控制台）

### 步骤 1：登录云服务器控制台

根据您的云服务商：

- **阿里云**: https://ecs.console.aliyun.com
- **腾讯云**: https://console.cloud.tencent.com/cvm
- **AWS**: https://console.aws.amazon.com/ec2
- **其他**: 登录相应的控制台

### 步骤 2：找到安全组设置

1. 找到您的服务器实例
2. 点击实例 ID 或进入详情
3. 找到 **"安全组"** 或 **"防火墙"** 标签

### 步骤 3：检查入站规则

查看 **入站规则 (Inbound Rules)** 中关于端口 22（SSH）的规则：

**常见配置（可能阻止 GitHub Actions）：**
- ❌ 只允许特定 IP：`1.2.3.4/32`
- ❌ 只允许国内 IP：`1.0.0.0/8, 14.0.0.0/8` 等
- ❌ 限制来源：仅允许您的办公 IP

### 步骤 4：临时允许所有 IP（测试用）

**添加规则：**

| 类型 | 协议 | 端口范围 | 授权对象 | 描述 |
|------|------|----------|----------|------|
| SSH | TCP | 22 | 0.0.0.0/0 | 临时允许所有 IP（用于 GitHub Actions） |

**重要：** 这是临时测试规则。确认 GitHub Actions 能连接后，应该改为更安全的配置（见下方）。

### 步骤 5：验证

添加规则后：
1. 等待 1-2 分钟让规则生效
2. 重新运行 GitHub Actions 部署
3. 查看是否成功

---

## 🔒 安全配置（推荐，临时规则生效后）

### 方案 A：使用 GitHub Actions IP 列表（最佳）

GitHub Actions 的 IP 地址列表会定期更新。可以：

1. **使用 GitHub Meta API 获取 IP：**
   ```bash
   curl https://api.github.com/meta
   ```

   返回的 JSON 中包含 `actions` 数组，包含所有 GitHub Actions 使用的 IP 段。

2. **定期更新安全组规则：**
   - 定期（每周/每月）获取最新 IP 列表
   - 更新安全组规则

3. **自动化脚本（可选）：**
   ```bash
   # 获取 GitHub Actions IP
   curl -s https://api.github.com/meta | jq -r '.actions[]' | while read ip; do
       echo "添加规则: $ip/32"
       # 在您的云服务商 CLI 中添加规则
   done
   ```

### 方案 B：使用更宽松但有限制的规则

如果无法使用 IP 列表，可以：
- 允许常见云服务商 IP 段
- 但安全性较低

### 方案 C：使用 SSH 密钥认证（已配置）

即使允许所有 IP 访问端口 22，只要：
- ✅ 使用 SSH 密钥认证（已配置）
- ✅ 禁用密码登录
- ✅ 定期更新密钥

仍然相对安全。

---

## 📋 各云服务商具体操作

### 阿里云

1. **ECS 控制台** → 实例 → 选择实例
2. **安全组** → **配置规则** → **入方向**
3. **添加安全组规则**：
   - 规则方向：入方向
   - 授权策略：允许
   - 优先级：1
   - 协议类型：自定义 TCP
   - 端口范围：22/22
   - 授权对象：`0.0.0.0/0`（临时测试）
   - 描述：GitHub Actions SSH

4. 点击 **保存**

### 腾讯云

1. **云服务器 CVM** → 实例 → 选择实例
2. **安全组** → **修改规则** → **入站规则**
3. **添加规则**：
   - 类型：自定义
   - 来源：`0.0.0.0/0`
   - 协议端口：TCP:22
   - 策略：允许
   - 备注：GitHub Actions SSH

4. 点击 **完成**

### AWS

1. **EC2 控制台** → Instances → 选择实例
2. **Security** → **Security groups** → 点击安全组 ID
3. **Inbound rules** → **Edit inbound rules**
4. **Add rule**：
   - Type: SSH
   - Source: `0.0.0.0/0`（临时测试）
   - Description: GitHub Actions SSH

5. 点击 **Save rules**

---

## ✅ 验证修复

### 方法 1：从 GitHub Actions 测试

1. 添加安全组规则后，等待 1-2 分钟
2. 在 GitHub Actions 页面点击 **Re-run jobs**
3. 查看日志，应该不再出现 "timeout" 错误

### 方法 2：从本地测试（使用 GitHub IP 模拟）

```bash
# 获取 GitHub Actions IP 段（示例）
# 实际 IP 需要从 https://api.github.com/meta 获取

# 测试连接
ssh -v -o ConnectTimeout=60 ubuntu@your-server-ip
```

---

## 🔍 如果仍然失败

### 检查清单

- [ ] 安全组规则是否已保存并生效？
- [ ] 是否等待了足够时间（1-2分钟）？
- [ ] 服务器实例是否在运行？
- [ ] 服务器内部的防火墙（ufw/iptables）是否允许？

### 检查服务器内部防火墙

```bash
# SSH 登录服务器
ssh ubuntu@your-server-ip

# 检查 ufw
sudo ufw status
# 如果启用，确保允许 SSH
sudo ufw allow 22/tcp

# 检查 iptables
sudo iptables -L -n | grep 22
```

---

## 📝 总结

**关键步骤：**
1. ✅ 登录云服务器控制台
2. ✅ 找到安全组设置
3. ✅ 添加规则：允许 `0.0.0.0/0` 访问 TCP 22（临时测试）
4. ✅ 等待规则生效
5. ✅ 重新运行 GitHub Actions

**如果成功：**
- 说明确实是防火墙/IP 白名单问题
- 可以考虑使用 GitHub Actions IP 列表进行更安全的配置

**配置文件已更新：**
- ✅ `timeout: 60s`（已增加到 60 秒）
- ✅ `command_timeout: 30m`
- ✅ `debug: true`（已启用）
- ✅ `port: 22`（已明确指定）
