# 階段 4: 紅包處理器實現

> **更新日期**: 2025-01-XX  
> **狀態**: ✅ 已完成（包含最新修復）

---

## 完成功能

### ✅ 紅包處理器 (RedpacketHandler)

**文件**: `group_ai_service/redpacket_handler.py`

**功能**:
1. **紅包檢測**
   - 關鍵詞匹配（"紅包", "红包", "red packet" 等）
   - 金額提取（從消息文本中）
   - 去重處理（避免重複處理同一紅包）

2. **參與策略**
   - `RandomStrategy` - 隨機策略
   - `TimeBasedStrategy` - 基於時間的策略
   - `FrequencyStrategy` - 基於頻率的策略
   - `AmountBasedStrategy` - 基於金額的策略
   - `CompositeStrategy` - 組合策略（加權平均）

3. **參與邏輯**
   - 參與決策（基於策略和配置）
   - 參與執行（支持 Telegram API callback_query）
   - 結果記錄和統計
   - ✅ 重複點擊檢測
   - ✅ 金額驗證（防止 amountTo 太小）
   - ✅ 最佳手氣提示（包含發包人信息）
   - ✅ 搶包通知功能

4. **統計分析**
   - 參與次數統計
   - 成功率統計
   - 金額統計

5. **新增功能**（2025-01-XX 更新）
   - ✅ 帶封面紅包按鈕點擊處理
   - ✅ 最佳手氣提示（包含發包人信息）
   - ✅ 重複點擊檢測與防護
   - ✅ 金額驗證（可配置最小金額）
   - ✅ 搶包通知（通知發包人）
   - ✅ FloodWait 異常處理
   - ✅ 自動清理舊數據（避免內存泄漏）

### ✅ 對話管理器集成

**更新**: `group_ai_service/dialogue_manager.py`

**改進**:
1. 集成 `RedpacketHandler`
2. 自動檢測紅包消息
3. 自動決策和參與（如果啟用）

---

## 使用示例

### 創建紅包處理器

```python
from group_ai_service import RedpacketHandler, CompositeStrategy, TimeBasedStrategy, AmountBasedStrategy

# 創建處理器
handler = RedpacketHandler()

# 設置組合策略
strategy = CompositeStrategy([
    (TimeBasedStrategy(peak_hours=[18, 19, 20]), 0.4),
    (AmountBasedStrategy(), 0.6),
])
handler.set_default_strategy(strategy)
```

### 檢測紅包

```python
# 在消息處理中
redpacket = await handler.detect_redpacket(message)
if redpacket:
    print(f"檢測到紅包: {redpacket.redpacket_id}, 金額: {redpacket.amount}")
```

### 參與紅包

```python
# 決策
should_participate = await handler.should_participate(
    account_id="account_1",
    redpacket=redpacket,
    account_config=config,
    context=context
)

if should_participate:
    # 執行參與
    result = await handler.participate(
        account_id="account_1",
        redpacket=redpacket,
        client=client,
        sender_name="發包人姓名",  # 可選，用於最佳手氣提示
        participant_name="參與者姓名"  # 可選，用於搶包通知
    )
    
    if result.success:
        print(f"成功參與，金額: {result.amount}")
    else:
        print(f"參與失敗: {result.error}")
```

---

## 策略說明

### RandomStrategy（隨機策略）

```python
strategy = RandomStrategy(base_probability=0.5)
```

- 固定概率參與
- 適用於簡單場景

### TimeBasedStrategy（時間策略）

```python
strategy = TimeBasedStrategy(
    peak_hours=[18, 19, 20, 21],  # 高峰時段
    peak_probability=0.8,          # 高峰概率
    off_peak_probability=0.3       # 非高峰概率
)
```

- 根據時間段調整參與概率
- 適用於活躍時段優先

### FrequencyStrategy（頻率策略）

```python
strategy = FrequencyStrategy(
    max_per_hour=5,        # 每小時最大參與次數
    cooldown_seconds=300   # 冷卻時間（秒）
)
```

- 控制參與頻率
- 避免過度參與

### AmountBasedStrategy（金額策略）

```python
strategy = AmountBasedStrategy(
    min_amount=0.01,
    max_amount=100.0,
    high_amount_probability=0.9,  # 高金額概率
    low_amount_probability=0.3    # 低金額概率
)
```

- 根據金額調整參與概率
- 高金額優先參與

### CompositeStrategy（組合策略）

```python
strategy = CompositeStrategy([
    (RandomStrategy(0.5), 0.3),      # 權重 0.3
    (TimeBasedStrategy(), 0.4),       # 權重 0.4
    (AmountBasedStrategy(), 0.3),     # 權重 0.3
])
```

- 多個策略的加權平均
- 更靈活的參與邏輯

---

## 測試

### 測試腳本

```bash
py scripts/test_redpacket_handler.py
```

**測試覆蓋**:
- ✅ 紅包檢測
- ✅ 策略評估
- ✅ 參與決策
- ✅ 參與執行（模擬）
- ✅ 統計分析

---

## 待完善功能

1. **Telegram API 集成**
   - 實現實際的搶紅包 API 調用
   - 處理 FloodWait 錯誤
   - 處理各種異常情況

2. **紅包類型檢測**
   - 普通紅包
   - 拼手氣紅包
   - 其他類型

3. **更精確的金額提取**
   - 支持更多格式
   - 支持多種貨幣

4. **狀態追蹤**
   - 紅包狀態（創建、進行中、結束）
   - 參與狀態追蹤

---

## 下一步

1. **完善 Telegram API 集成**
   - 實現實際的搶紅包操作
   - 錯誤處理和重試

2. **開始階段 5**
   - 監控與調控系統開發

3. **性能優化**
   - 紅包檢測優化
   - 策略計算優化

---

**狀態**: ✅ 基礎功能完成，待完善 Telegram API 集成

