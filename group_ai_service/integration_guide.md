# 新方案整合指南

## 📋 概述

本文檔說明如何將新的統一消息處理中心整合到現有系統中。

## 🔄 整合步驟

### 步驟 1: 更新 ServiceManager

在 `service_manager.py` 中初始化 UnifiedMessageHandler：

```python
from group_ai_service.unified_message_handler import UnifiedMessageHandler
from group_ai_service.unified_config_manager import ConfigManager

class ServiceManager:
    def __init__(self):
        # ... 現有初始化代碼 ...
        
        # 初始化統一消息處理中心
        self.unified_message_handler = UnifiedMessageHandler(
            redpacket_handler=self.redpacket_handler,
            dialogue_manager=self.dialogue_manager
        )
        
        # 初始化統一配置管理器
        self.config_manager = ConfigManager()
        
        # 設置 ActionExecutor 的 account_manager
        self.unified_message_handler.action_executor.account_manager = self.account_manager
```

### 步驟 2: 更新 SessionPool

`session_pool.py` 已經更新，會自動使用 UnifiedMessageHandler（如果已初始化）。

### 步驟 3: 替換重複的紅包檢測邏輯

在所有使用紅包檢測的地方，替換為使用 `RedpacketProcessor`：

**替換前**:
```python
def _is_redpacket_message(self, text: str) -> bool:
    keywords = ["紅包", "红包", "🧧", "💰", "packet", "hongbao"]
    return any(kw in text.lower() for kw in keywords)
```

**替換後**:
```python
from group_ai_service.unified_message_handler import RedpacketProcessor

redpacket_processor = RedpacketProcessor()
if redpacket_processor.is_redpacket_message(message):
    # 處理紅包
    pass
```

### 步驟 4: 使用統一配置管理

在需要獲取配置的地方，使用 `ConfigManager`：

```python
from group_ai_service.unified_config_manager import ConfigManager

config_manager = ConfigManager()

# 獲取最終配置
final_config = config_manager.get_config(
    account_id="account_001",
    group_id=-1001234567890,
    role_id="role_001"
)

# 使用配置
chat_interval = final_config.chat.interval_min
redpacket_probability = final_config.redpacket.probability
```

## 📝 遷移檢查清單

- [ ] 更新 ServiceManager 初始化 UnifiedMessageHandler
- [ ] 確認 SessionPool 使用新的處理器
- [ ] 替換所有重複的紅包檢測邏輯
- [ ] 替換所有重複的消息處理邏輯
- [ ] 使用統一配置管理系統
- [ ] 測試消息處理流程
- [ ] 測試紅包檢測和搶奪
- [ ] 測試關鍵詞觸發
- [ ] 測試定時消息

## ⚠️ 注意事項

1. **向後兼容**: 新系統設計為向後兼容，如果 UnifiedMessageHandler 初始化失敗，會回退到原有處理方式
2. **逐步遷移**: 建議逐步遷移，先測試新系統，確認無誤後再完全切換
3. **配置遷移**: 現有的 AccountConfig 可以通過 `convert_from_account_config()` 轉換為 UnifiedConfig

## 🐛 故障排查

### 問題 1: UnifiedMessageHandler 未初始化

**症狀**: 日誌顯示 "統一消息處理中心已初始化並整合到 SessionPool" 但實際未使用

**解決**: 檢查初始化代碼，確保 redpacket_handler 和 dialogue_manager 已正確傳入

### 問題 2: ActionExecutor 無法發送消息

**症狀**: 消息處理成功但未實際發送

**解決**: 確保 ActionExecutor 的 account_manager 已正確設置

### 問題 3: 配置衝突

**症狀**: 配置未按預期生效

**解決**: 檢查配置層級，確保配置優先級正確（任務 > 賬號 > 角色 > 群組 > 全局）
