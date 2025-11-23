# 游戏系统对接指南

> **创建日期**: 2025-11-15  
> **状态**: 等待游戏系统代码分析

---

## 当前进度

✅ **已完成**:
- 创建游戏系统 API 客户端框架 (`group_ai_service/game_api_client.py`)
- 更新红包处理器，改为通过 API 检测（不再使用关键词检测）
- 创建 Webhook 接收器 (`admin-backend/app/api/group_ai/game_webhook.py`)
- 集成游戏 API 客户端到 ServiceManager

⏳ **待完成**:
- 分析游戏系统代码，确定实际 API 接口
- 完善 API 客户端实现
- 实现 Telegram API 按钮点击和游戏消息处理
- 完善事件处理逻辑

---

## 需要的信息

为了完成对接，需要以下信息：

### 1. 游戏系统文件夹位置

请提供游戏系统代码的路径，例如：
- `E:\游戏系统\redpacket-game\`
- 或项目内的相对路径

### 2. 游戏系统 API 接口

需要了解：
- API 基础 URL
- 认证方式（API Key、Token 等）
- 接口端点列表
- 请求/响应格式

### 3. Telegram 交互方式

需要了解：
- 红包消息的格式（按钮、游戏消息、命令等）
- 参与红包的方式（点击按钮、发送命令等）
- 如何获取参与结果

---

## 当前实现

### API 客户端 (`group_ai_service/game_api_client.py`)

已实现的基础接口：
- `get_game_status(group_id)` - 获取游戏状态
- `participate_redpacket(account_id, redpacket_id, group_id)` - 参与红包
- `report_participation_result(...)` - 上报参与结果

### Webhook 接收器 (`admin-backend/app/api/group_ai/game_webhook.py`)

已实现的端点：
- `POST /api/v1/game-webhook/events` - 接收游戏系统事件

### 红包处理器更新

- 检测方法改为：游戏系统 API → Telegram API → 事件通知
- 参与方法改为：游戏系统 API → Telegram API 按钮/命令

---

## 下一步

1. **提供游戏系统文件夹路径**
2. **分析游戏系统代码**
3. **完善 API 对接**
4. **测试集成**

---

**请提供游戏系统文件夹路径，我将立即开始分析并完成对接。**

