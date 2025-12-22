# Phase 4: 风控与指纹管理使用指南

## 概述

Phase 4 实现了设备指纹管理和 Proxy IP 绑定检查，确保每个 Agent 看起来都像是一台独立的真实手机，并防止意外使用本地 IP 导致封号。

## 功能特性

### 1. 设备指纹生成

- **自动生成**: Agent 首次启动时自动生成设备指纹
- **持久化**: 指纹保存在 `device.json` 文件中
- **一致性**: 同一 Session 永远使用同一个设备指纹（严禁修改）
- **真实性**: 伪装成官方 Telegram App，不使用 Telethon 默认标识

### 2. Proxy IP 绑定检查

- **强制检查**: 如果配置了 Proxy，启动时必须通过检查
- **IP 验证**: 支持验证期望的出口 IP 是否匹配
- **安全拒绝**: 如果检查失败，拒绝启动并报警

## 配置说明

### 配置文件: `agent/config.json`

```json
{
  "agent_id": "your-agent-id",
  "server_url": "ws://your-server:8000/api/v1/agents/ws",
  "proxy": "socks5://user:pass@proxy-host:1080",
  "expected_ip": "1.2.3.4",
  "heartbeat_interval": 30,
  "reconnect_interval": 30,
  "reconnect_max_attempts": -1
}
```

### 配置项说明

- **`proxy`** (可选): Proxy URL
  - 格式: `http://user:pass@host:port` 或 `socks5://user:pass@host:port`
  - 如果配置了 Proxy，启动时会强制检查
  - 如果未配置，Agent 可以正常启动（但建议生产环境必须配置）

- **`expected_ip`** (可选): 期望的出口 IP
  - 如果提供了此值，会验证 Proxy 的出口 IP 是否匹配
  - 用于确保 Proxy 配置正确

## 设备指纹文件: `agent/device.json`

设备指纹会自动生成并保存到此文件。**严禁手动修改**此文件，否则可能导致 Telegram 封号。

示例内容:

```json
{
  "platform": "android",
  "device_model": "Xiaomi 13",
  "system_version": "Android 13.0",
  "app_version": "10.5.0",
  "lang_code": "zh-cn",
  "manufacturer": "Xiaomi",
  "sdk_version": 33
}
```

## 使用流程

### 1. 首次启动

```bash
cd agent
python main.py
```

首次启动时：
1. 检查 Proxy IP 绑定（如果配置了 Proxy）
2. 生成设备指纹并保存到 `device.json`
3. 打印设备指纹信息
4. 启动 WebSocket 客户端

### 2. 后续启动

后续启动时：
1. 检查 Proxy IP 绑定（如果配置了 Proxy）
2. **读取已存在的设备指纹**（不会重新生成）
3. 使用相同的设备指纹启动

### 3. Telethon 集成示例

```python
from telethon import TelegramClient
from telethon.sessions import StringSession
from agent.utils.device_fingerprint import get_or_create_device_fingerprint
from agent.config import get_proxy

# 获取设备指纹
device_fingerprint = get_or_create_device_fingerprint()
device_params = device_fingerprint.to_telethon_params()

# 获取 Proxy
proxy_url = get_proxy()

# 初始化 Telethon 客户端
client = TelegramClient(
    session=StringSession(session_string),
    api_id=api_id,
    api_hash=api_hash,
    device_model=device_params["device_model"],
    system_version=device_params["system_version"],
    app_version=device_params["app_version"],
    lang_code=device_params["lang_code"],
    proxy=proxy_url  # 如果配置了 Proxy
)

await client.start()
```

## 安全注意事项

### ⚠️ 重要警告

1. **不要修改 `device.json`**: 
   - 一旦生成，严禁修改
   - 修改会导致 Telegram 检测到设备变化，可能导致封号

2. **必须配置 Proxy**:
   - 生产环境强烈建议配置 Proxy
   - 使用本地 IP 裸连容易被 Telegram 关联封号

3. **验证 Proxy IP**:
   - 建议配置 `expected_ip` 来验证 Proxy 是否正确
   - 如果 IP 不匹配，Agent 会拒绝启动

4. **设备指纹一致性**:
   - 同一个 Session 文件必须使用同一个设备指纹
   - 如果更换 Session，可以删除 `device.json` 重新生成

## 故障排查

### 问题 1: Proxy IP 检查失败

**错误信息**: `Proxy IP 绑定检查失败: ...`

**解决方案**:
1. 检查 Proxy URL 格式是否正确
2. 验证 Proxy 服务是否可用
3. 检查网络连接
4. 如果不需要 Proxy，可以删除 `proxy` 配置项

### 问题 2: 设备指纹文件损坏

**错误信息**: `加载设备指纹失败: ...`

**解决方案**:
1. 删除 `device.json` 文件
2. 重新启动 Agent，会自动生成新的设备指纹

### 问题 3: IP 不匹配

**错误信息**: `IP 不匹配: 期望 xxx, 实际 yyy`

**解决方案**:
1. 检查 Proxy 配置是否正确
2. 更新 `expected_ip` 为实际的出口 IP
3. 或者删除 `expected_ip` 配置项（不进行 IP 验证）

## 支持的设备列表

### Android 设备
- Xiaomi 13
- Samsung Galaxy S23
- Google Pixel 7
- Huawei Mate 30 Pro
- OnePlus 6
- OPPO Find X3 Pro
- vivo X70 Pro+
- Realme GT 2 Pro

### iOS 设备
- iPhone 13 Pro
- iPhone 14 Pro
- iPhone 13 mini
- iPhone 14 Pro Max

## 技术细节

### 设备指纹生成逻辑

1. 随机选择平台（Android 或 iOS）
2. 从预置设备列表中随机选择设备型号
3. 随机选择 Telegram App 版本（10.4.0 - 10.6.0）
4. 随机选择语言代码
5. 生成系统版本（基于设备模板）

### Proxy IP 检查逻辑

1. 解析 Proxy URL
2. 通过 Proxy 请求多个 IP 检查服务
3. 获取当前出口 IP
4. 如果提供了 `expected_ip`，验证是否匹配
5. 如果检查失败，抛出异常并拒绝启动

## 下一步

- 集成 Telethon 客户端（使用设备指纹参数）
- 实现 Session 管理（与设备指纹绑定）
- 添加更多设备型号和系统版本
- 实现设备指纹轮换策略（可选）
