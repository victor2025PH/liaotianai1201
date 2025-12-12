# 服务自动启动配置指南

## ✅ 好消息

**是的，如果服务已正确配置，重启服务器后前后端以及所有程序会自动开启运行！**

---

## 🔍 如何验证服务是否已启用自动启动

### 方法1: 使用检查脚本（推荐）

**执行位置：服务器**

```bash
# 给脚本添加执行权限
chmod +x scripts/server/check-auto-start.sh

# 运行检查脚本
./scripts/server/check-auto-start.sh
```

**作用：** 检查所有服务的自动启动配置状态

---

### 方法2: 手动检查

**执行位置：服务器**

```bash
# 检查后端服务
sudo systemctl is-enabled luckyred-api

# 检查前端服务
sudo systemctl is-enabled liaotian-frontend

# 检查Telegram Bot服务
sudo systemctl is-enabled telegram-bot

# 检查所有服务状态
sudo systemctl status luckyred-api liaotian-frontend telegram-bot --no-pager
```

**预期结果：**
- 如果显示 `enabled` → ✅ 已启用自动启动
- 如果显示 `disabled` → ⚠️ 未启用自动启动（需要手动启用）

---

## 🔧 如何启用自动启动

如果服务显示 `disabled`，需要手动启用：

**执行位置：服务器**

```bash
# 启用后端服务自动启动
sudo systemctl enable luckyred-api

# 启用前端服务自动启动
sudo systemctl enable liaotian-frontend

# 启用Telegram Bot服务自动启动
sudo systemctl enable telegram-bot

# 重新加载systemd配置
sudo systemctl daemon-reload
```

**作用：** 设置服务在系统启动时自动启动

---

## 📋 服务配置说明

### 1. 后端服务 (luckyred-api)

**服务文件：** `/etc/systemd/system/luckyred-api.service`

**配置特点：**
- ✅ 有 `[Install]` 部分
- ✅ `WantedBy=multi-user.target`（系统启动时自动启动）
- ✅ `Restart=always`（服务崩溃时自动重启）

**验证命令：**
```bash
sudo systemctl status luckyred-api
sudo systemctl is-enabled luckyred-api
```

---

### 2. 前端服务 (liaotian-frontend)

**服务文件：** `/etc/systemd/system/liaotian-frontend.service`

**配置特点：**
- ✅ 有 `[Install]` 部分
- ✅ `WantedBy=multi-user.target`（系统启动时自动启动）
- ✅ `Restart=always`（服务崩溃时自动重启）

**验证命令：**
```bash
sudo systemctl status liaotian-frontend
sudo systemctl is-enabled liaotian-frontend
```

---

### 3. Telegram Bot服务 (telegram-bot)

**服务文件：** `/etc/systemd/system/telegram-bot.service`

**配置特点：**
- ✅ 有 `[Install]` 部分
- ✅ `WantedBy=multi-user.target`（系统启动时自动启动）
- ✅ `Restart=always`（服务崩溃时自动重启）

**验证命令：**
```bash
sudo systemctl status telegram-bot
sudo systemctl is-enabled telegram-bot
```

---

## 🎯 一键验证和启用脚本

**执行位置：服务器**

```bash
# 创建并运行一键脚本
cat > /tmp/verify-auto-start.sh << 'EOF'
#!/bin/bash
echo "=========================================="
echo "验证和启用服务自动启动"
echo "=========================================="
echo ""

SERVICES=("luckyred-api" "liaotian-frontend" "telegram-bot")

for service in "${SERVICES[@]}"; do
    echo "检查服务: $service"
    
    # 检查服务是否存在
    if systemctl list-unit-files | grep -q "^${service}.service"; then
        # 检查是否启用
        if systemctl is-enabled "$service" >/dev/null 2>&1; then
            echo "  ✅ 已启用自动启动"
        else
            echo "  ⚠️  未启用自动启动，正在启用..."
            sudo systemctl enable "$service"
            echo "  ✅ 已启用"
        fi
        
        # 检查当前状态
        if systemctl is-active "$service" >/dev/null 2>&1; then
            echo "  ✅ 当前运行中"
        else
            echo "  ⚠️  当前未运行，正在启动..."
            sudo systemctl start "$service"
            sleep 2
            if systemctl is-active "$service" >/dev/null 2>&1; then
                echo "  ✅ 已启动"
            else
                echo "  ❌ 启动失败，请检查日志: sudo journalctl -u $service -n 50"
            fi
        fi
    else
        echo "  ❌ 服务未安装"
    fi
    echo ""
done

echo "=========================================="
echo "完成！"
echo "=========================================="
EOF

chmod +x /tmp/verify-auto-start.sh
/tmp/verify-auto-start.sh
```

---

## 🔄 重启服务器后的行为

### 系统启动顺序

1. **系统启动** → 加载 systemd
2. **网络就绪** → `After=network.target` 确保网络可用
3. **自动启动服务** → 所有 `enabled` 的服务自动启动
4. **服务运行** → 前后端和Bot服务开始运行

### 服务启动顺序

```
系统启动
  ↓
网络就绪 (network.target)
  ↓
luckyred-api 启动 (后端API)
  ↓
liaotian-frontend 启动 (前端)
  ↓
telegram-bot 启动 (Telegram Bot)
```

---

## ⚠️ 注意事项

### 1. 服务必须被 `enable` 才能自动启动

仅仅有配置文件中的 `WantedBy=multi-user.target` 还不够，必须运行：
```bash
sudo systemctl enable <service-name>
```

### 2. 验证服务是否真的会自动启动

**测试方法：**
```bash
# 1. 确认服务已启用
sudo systemctl is-enabled luckyred-api

# 2. 重启服务器（谨慎操作！）
sudo reboot

# 3. 等待服务器重启后，SSH连接并检查
sudo systemctl status luckyred-api
```

### 3. 如果服务启动失败

**查看日志：**
```bash
# 查看后端服务日志
sudo journalctl -u luckyred-api -n 50 --no-pager

# 查看前端服务日志
sudo journalctl -u liaotian-frontend -n 50 --no-pager

# 查看Bot服务日志
sudo journalctl -u telegram-bot -n 50 --no-pager
```

---

## 📊 服务状态说明

| 状态 | 含义 | 说明 |
|------|------|------|
| `enabled` | 已启用自动启动 | ✅ 系统启动时会自动启动 |
| `disabled` | 未启用自动启动 | ⚠️ 系统启动时不会自动启动 |
| `active` | 当前运行中 | ✅ 服务正在运行 |
| `inactive` | 当前未运行 | ⚠️ 服务已停止 |
| `failed` | 启动失败 | ❌ 服务启动失败，需要检查日志 |

---

## ✅ 完成检查清单

重启服务器前，确认：

- [ ] 所有服务都已 `enabled`（使用 `systemctl is-enabled` 检查）
- [ ] 所有服务当前都在运行（使用 `systemctl status` 检查）
- [ ] 配置文件正确（检查 `/etc/systemd/system/*.service`）
- [ ] 日志没有错误（使用 `journalctl -u <service>` 检查）

---

## 🎯 快速命令

**在服务器上执行（一键检查所有服务）：**

```bash
echo "=== 服务自动启动状态 ===" && \
for service in luckyred-api liaotian-frontend telegram-bot; do
    echo ""
    echo "服务: $service"
    echo "  自动启动: $(sudo systemctl is-enabled $service 2>/dev/null || echo '未安装')"
    echo "  当前状态: $(sudo systemctl is-active $service 2>/dev/null || echo '未运行')"
done
```

---

## 💡 总结

**回答你的问题：**

✅ **是的，如果服务已正确配置并启用（`enabled`），重启服务器后前后端以及所有程序会自动开启运行！**

**验证方法：**
1. 运行 `sudo systemctl is-enabled <service-name>` 检查是否 `enabled`
2. 如果显示 `disabled`，运行 `sudo systemctl enable <service-name>` 启用
3. 重启服务器后，服务会自动启动

**如果服务没有自动启动：**
- 检查服务是否已启用：`sudo systemctl is-enabled <service>`
- 检查服务日志：`sudo journalctl -u <service> -n 50`
- 手动启动测试：`sudo systemctl start <service>`

