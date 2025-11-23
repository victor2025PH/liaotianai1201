# 防风控 Session 生成指南

## 概述

Telegram 对批量创建 session 有严格的风控机制。本指南介绍如何使用改进的防风控工具生成 session 文件。

## 风控机制分析

### Telegram 可能检测的行为

1. **短时间内大量创建 session**
   - 同一 IP 地址
   - 同一 API 凭证
   - 短时间内连续操作

2. **异常的设备信息**
   - 相同的设备型号
   - 相同的系统版本
   - 异常的用户代理

3. **异常的行为模式**
   - 没有延迟
   - 操作过于机械化
   - 没有模拟真实用户行为

## 防风控措施

### 1. 随机延迟

- **连接前延迟**: 2-5 秒随机延迟
- **验证码后延迟**: 3-8 秒随机延迟
- **Session 间隔**: 60-180 秒随机间隔

### 2. 设备信息模拟

- 随机设备型号（iPhone、Samsung、Xiaomi 等）
- 随机系统版本
- 随机应用版本
- 随机语言代码

### 3. 速率限制

- **每小时限制**: 最多 3 个 session
- **每天限制**: 最多 10 个 session

### 4. IP 代理支持（可选）

- 支持 HTTP/HTTPS/SOCKS5 代理
- 可以分散到不同 IP 地址

## 使用方法

### 基本用法

```bash
python tools/session_manager/generate_session_anti_detection.py
```

### 带参数用法

```bash
# 使用代理
python tools/session_manager/generate_session_anti_detection.py \
    --api-id YOUR_API_ID \
    --api-hash YOUR_API_HASH \
    --phone +1234567890 \
    --proxy socks5://127.0.0.1:1080

# 使用 HTTP 代理（带认证）
python tools/session_manager/generate_session_anti_detection.py \
    --proxy http://username:password@proxy.example.com:8080

# 自定义设备信息
python tools/session_manager/generate_session_anti_detection.py \
    --device-info '{"device_model":"iPhone 14 Pro","system_version":"iOS 17.0"}'

# 跳过延迟（仅用于测试）
python tools/session_manager/generate_session_anti_detection.py \
    --skip-delay
```

## 最佳实践

### 1. 分散生成时间

- 不要在短时间内生成多个 session
- 建议每个 session 之间间隔 1-3 小时
- 每天最多生成 5-8 个 session

### 2. 使用不同 IP

- 使用代理服务器分散 IP
- 每个 IP 每天最多生成 2-3 个 session
- 使用住宅代理比数据中心代理更好

### 3. 使用不同 API 凭证

- 不要使用同一个 API ID/Hash 生成大量 session
- 建议每个 API 凭证每天最多生成 3-5 个 session
- 分散到不同的 Telegram 账号

### 4. 模拟真实用户行为

- 生成 session 后，先正常使用一段时间
- 不要立即用于自动化操作
- 添加好友、加入群组等正常操作

### 5. 监控和记录

- 记录每个 session 的生成时间
- 记录使用的 IP 和 API 凭证
- 如果出现封禁，分析原因

## 常见问题

### Q1: 为什么我的 session 被封了？

可能原因：
- 短时间内生成太多 session
- 使用相同的 IP 地址
- 使用相同的 API 凭证
- 生成后立即用于自动化操作

解决方案：
- 增加延迟时间
- 使用代理分散 IP
- 使用不同的 API 凭证
- 生成后先正常使用

### Q2: 如何知道是否触发了风控？

常见错误：
- `FloodWait`: 速率限制
- `PhoneNumberBanned`: 手机号被封
- `AUTH_KEY_DUPLICATED`: Session 冲突
- `PHONE_NUMBER_INVALID`: 手机号无效

### Q3: 可以使用 VPN 吗？

可以，但建议：
- 使用稳定的 VPN 服务
- 不要频繁切换 IP
- 使用住宅 IP 比数据中心 IP 更好

### Q4: 如何批量生成 session？

不建议批量生成。如果必须：
1. 使用脚本自动化，但增加延迟
2. 使用多个代理 IP
3. 使用多个 API 凭证
4. 分散到多天完成
5. 每个 session 生成后先测试

## 配置说明

### 修改防风控配置

编辑 `tools/session_manager/generate_session_anti_detection.py` 中的 `ANTI_DETECTION_CONFIG`:

```python
ANTI_DETECTION_CONFIG = {
    "min_delay_between_sessions": 60,  # 增加间隔时间
    "max_sessions_per_hour": 2,  # 降低每小时限制
    "max_sessions_per_day": 5,  # 降低每天限制
    # ...
}
```

## 监控脚本

可以创建一个监控脚本来跟踪 session 生成：

```python
# monitor_session_generation.py
import json
from pathlib import Path
from datetime import datetime

def track_session_generation(session_name, api_id, ip_address):
    log_file = Path("session_generation_log.json")
    if log_file.exists():
        logs = json.loads(log_file.read_text())
    else:
        logs = []
    
    logs.append({
        "session_name": session_name,
        "api_id": api_id,
        "ip_address": ip_address,
        "timestamp": datetime.now().isoformat(),
    })
    
    log_file.write_text(json.dumps(logs, indent=2))
```

## 总结

1. **慢速生成**: 不要急于生成大量 session
2. **分散资源**: 使用不同的 IP、API 凭证
3. **模拟真实**: 生成后先正常使用
4. **监控记录**: 跟踪生成情况，分析问题
5. **遵守限制**: 不要超过推荐的速率限制

记住：**质量比数量更重要**。少量稳定可用的 session 比大量被封的 session 更有价值。

