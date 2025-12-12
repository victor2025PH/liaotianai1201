# SSH 连接问题排查指南

## 🔍 问题：ssh-server.bat 无法连接服务器

### 可能的原因

1. **密钥认证失败**：服务器没有配置对应的公钥
2. **密码认证未启用**：服务器只允许密钥认证
3. **网络连接问题**：IP地址错误或服务器不可达
4. **防火墙阻止**：端口22被阻止

---

## ✅ 解决方案

### 方案1: 使用密码认证（已修复）

**已更新 `ssh-server.bat`**，现在使用密码认证而不是密钥认证。

**使用方法：**
1. 双击 `ssh-server.bat`
2. 当提示输入密码时，输入：`8iDcGrYb52Fxpzee`
3. 注意：输入密码时不会显示任何字符（这是SSH的安全特性）

---

### 方案2: 手动测试SSH连接

**在PowerShell中执行：**

```powershell
# 测试连接（会提示输入密码）
ssh ubuntu@165.154.235.170

# 如果连接成功，你会看到服务器提示符
# 输入密码：8iDcGrYb52Fxpzee（输入时不会显示）
```

---

### 方案3: 使用详细模式查看错误

**在PowerShell中执行：**

```powershell
# 使用详细模式，查看具体错误信息
ssh -v ubuntu@165.154.235.170
```

**常见错误信息：**
- `Connection timed out` → 网络问题或防火墙阻止
- `Permission denied` → 密码错误或用户不存在
- `Host key verification failed` → 主机密钥问题（已通过 `-o StrictHostKeyChecking=no` 解决）

---

### 方案4: 检查网络连接

**在PowerShell中执行：**

```powershell
# 测试网络连通性
ping 165.154.235.170

# 测试SSH端口是否开放
Test-NetConnection -ComputerName 165.154.235.170 -Port 22
```

---

### 方案5: 使用密钥认证（如果已配置）

如果服务器已配置公钥，可以使用密钥认证：

```powershell
# 使用密钥文件连接
ssh -i scripts/local/keys/server_key ubuntu@165.154.235.170
```

**配置公钥到服务器：**

```powershell
# 1. 读取公钥内容
Get-Content scripts/local/keys/server_key.pub

# 2. SSH登录到服务器（使用密码）
ssh ubuntu@165.154.235.170

# 3. 在服务器上执行（将公钥添加到authorized_keys）
mkdir -p ~/.ssh
chmod 700 ~/.ssh
echo "你的公钥内容" >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
```

---

## 🔧 修复后的脚本说明

### ssh-server.bat（已修复）

**特点：**
- ✅ 使用密码认证（与配置文件一致）
- ✅ 跳过主机密钥验证（避免首次连接问题）
- ✅ 静默模式（减少输出）
- ✅ 自动打开PowerShell窗口

**使用方法：**
1. 双击 `ssh-server.bat`
2. 输入密码：`8iDcGrYb52Fxpzee`
3. 连接成功后，会显示服务器提示符

---

## 📝 配置文件中的认证信息

根据 `data/master_config.json`：

```json
"los-angeles": {
  "host": "165.154.235.170",
  "user": "ubuntu",
  "password": "8iDcGrYb52Fxpzee",
  ...
}
```

**认证方式：** 密码认证
**用户名：** ubuntu
**密码：** 8iDcGrYb52Fxpzee

---

## ⚠️ 常见问题

### Q1: 输入密码时没有反应？

**A:** 这是正常的！SSH为了安全，输入密码时不会显示任何字符（包括 `*`）。直接输入密码后按 Enter。

### Q2: 连接超时？

**A:** 可能的原因：
1. IP地址错误
2. 服务器未运行
3. 防火墙阻止端口22
4. 网络问题

**解决方法：**
```powershell
# 测试网络连通性
ping 165.154.235.170

# 如果ping不通，检查IP地址是否正确
```

### Q3: 权限被拒绝（Permission denied）？

**A:** 可能的原因：
1. 密码错误
2. 用户名错误
3. 服务器不允许密码认证

**解决方法：**
1. 确认密码：`8iDcGrYb52Fxpzee`
2. 确认用户名：`ubuntu`
3. 检查服务器SSH配置（如果可能）

### Q4: 想要使用密钥认证？

**A:** 需要：
1. 确保服务器已配置公钥
2. 修改 `ssh-server.bat`，添加 `-i scripts/local/keys/server_key` 参数

---

## 🎯 快速测试

**在PowerShell中执行：**

```powershell
# 快速测试连接
ssh -o ConnectTimeout=5 ubuntu@165.154.235.170 "echo '连接成功'"
```

如果连接成功，会显示 "连接成功"。

---

## 📚 相关文件

- `ssh-server.bat` - SSH连接脚本（已修复）
- `scripts/local/ssh-to-server.bat` - 另一个SSH连接脚本
- `data/master_config.json` - 服务器配置（包含密码信息）

---

## ✅ 验证修复

修复后，执行以下步骤验证：

1. **双击 `ssh-server.bat`**
2. **等待PowerShell窗口打开**
3. **输入密码：`8iDcGrYb52Fxpzee`**（输入时不会显示）
4. **按 Enter**
5. **如果连接成功，会显示服务器提示符：`ubuntu@...:~$`**

如果仍然无法连接，请查看详细错误信息（使用 `ssh -v`）。

