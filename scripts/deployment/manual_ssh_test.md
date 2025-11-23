# 手动 SSH 测试指南

如果自动脚本无法连接，请按照以下步骤手动测试：

## 方法 1: 使用 PowerShell SSH

```powershell
# 直接连接
ssh ubuntu@165.154.233.179

# 输入密码: 8iDcGrYb52Fxpzee
```

## 方法 2: 使用 PuTTY

1. 下载并打开 PuTTY
2. 主机名: `165.154.233.179`
3. 端口: `22`
4. 连接类型: `SSH`
5. 用户名: `ubuntu`
6. 密码: `8iDcGrYb52Fxpzee`

## 方法 3: 使用 Windows Terminal

```powershell
# 在 Windows Terminal 中
ssh ubuntu@165.154.233.179
# 输入密码: 8iDcGrYb52Fxpzee
```

## 验证密码

如果手动连接也失败，可能的原因：

1. **密码已被更改**
   - 联系服务器提供商确认密码
   - 检查服务器控制面板

2. **密码输入错误**
   - 确认密码: `8iDcGrYb52Fxpzee`
   - 注意大小写
   - 检查是否有隐藏字符

3. **SSH 配置问题**
   - 服务器可能禁用了密码认证
   - 需要 SSH 密钥认证

4. **网络问题**
   - 检查防火墙设置
   - 验证 IP 地址是否正确

## 如果密码确实被更改

如果确认密码已被更改，请：

1. 获取新密码
2. 更新所有脚本中的密码
3. 或使用环境变量：

```powershell
$env:SERVER_PASSWORD = "新密码"
.\scripts\deployment\check_deployment.ps1 -ServerIP 165.154.233.179 -Password $env:SERVER_PASSWORD
```

