# Telegram API 實際集成指南

> **更新日期**: 2024-12-19  
> **狀態**: 待完善

---

## 概述

本文檔說明如何完善 Telegram API 的實際集成，特別是紅包功能的實際操作。

---

## 紅包功能集成

### 當前狀態

目前紅包處理器 (`RedpacketHandler`) 已實現：
- ✅ 紅包檢測（關鍵詞匹配）
- ✅ 參與策略（5 種策略）
- ✅ 參與決策邏輯
- ⏳ 實際搶紅包操作（待完善）

### 實現方案

#### 方案 1: 使用 Telegram Bot API

如果紅包是通過 Bot 發送的，可以使用 Bot API：

```python
async def participate_redpacket_bot(
    self,
    account_id: str,
    redpacket: RedpacketInfo,
    client: Client
) -> RedpacketResult:
    """通過 Bot API 參與紅包"""
    try:
        # 點擊紅包按鈕
        # 注意：這需要根據實際的 Bot 實現
        # 通常需要調用 callback_query
        
        # 示例（需要根據實際 Bot 實現調整）
        # await client.request_callback_answer(
        #     chat_id=redpacket.group_id,
        #     message_id=redpacket.message_id,
        #     callback_data="grab_redpacket"
        # )
        
        # 或者直接發送命令
        # await client.send_message(
        #     chat_id=redpacket.group_id,
        #     text="/grab_redpacket"
        # )
        
        pass
    except Exception as e:
        logger.error(f"參與紅包失敗: {e}")
        return RedpacketResult(
            redpacket_id=redpacket.redpacket_id,
            account_id=account_id,
            success=False,
            error=str(e)
        )
```

#### 方案 2: 使用 Telegram Client API

如果紅包是通過第三方服務發送的，可能需要：

1. **檢測紅包消息類型**
   ```python
   # 檢查消息是否包含紅包
   if message.game or message.invoice:
       # 可能是紅包相關消息
       pass
   ```

2. **點擊內聯按鈕**
   ```python
   # 如果消息包含內聯按鈕
   if message.reply_markup:
       for row in message.reply_markup.inline_keyboard:
           for button in row:
               if "紅包" in button.text or "grab" in button.text.lower():
                   # 點擊按鈕
                   await client.request_callback_answer(
                       chat_id=message.chat.id,
                       message_id=message.id,
                       callback_data=button.callback_data
                   )
   ```

3. **處理 FloodWait**
   ```python
   from pyrogram.errors import FloodWait
   
   try:
       # 執行操作
       await client.send_message(...)
   except FloodWait as e:
       logger.warning(f"FloodWait: 等待 {e.value} 秒")
       await asyncio.sleep(e.value)
       # 重試
   ```

### 實現步驟

1. **完善 `participate` 方法**

   更新 `group_ai_service/redpacket_handler.py` 中的 `participate` 方法：

   ```python
   async def participate(
       self,
       account_id: str,
       redpacket: RedpacketInfo,
       client: Client
   ) -> RedpacketResult:
       """參與紅包（執行搶紅包操作）"""
       try:
           # 1. 檢查消息是否仍然有效
           try:
               message = await client.get_messages(
                   redpacket.group_id,
                   redpacket.message_id
               )
           except Exception as e:
               logger.error(f"無法獲取消息: {e}")
               return RedpacketResult(
                   redpacket_id=redpacket.redpacket_id,
                   account_id=account_id,
                   success=False,
                   error="消息不存在或已過期"
               )
           
           # 2. 檢測紅包類型並執行相應操作
           # 方案 A: 內聯按鈕
           if message.reply_markup:
               # 查找紅包相關按鈕
               button_found = False
               for row in message.reply_markup.inline_keyboard:
                   for button in row:
                       if self._is_redpacket_button(button):
                           try:
                               await client.request_callback_answer(
                                   chat_id=redpacket.group_id,
                                   message_id=redpacket.message_id,
                                   callback_data=button.callback_data
                               )
                               button_found = True
                               break
                           except FloodWait as e:
                               await asyncio.sleep(e.value)
                               # 重試或放棄
                               return RedpacketResult(
                                   redpacket_id=redpacket.redpacket_id,
                                   account_id=account_id,
                                   success=False,
                                   error=f"FloodWait: {e.value}秒"
                               )
                   if button_found:
                       break
               
               if button_found:
                   # 等待結果（可能需要監聽後續消息）
                   await asyncio.sleep(1)
                   # TODO: 解析結果消息獲取金額
                   amount = None  # 需要從結果消息中提取
                   
                   return RedpacketResult(
                       redpacket_id=redpacket.redpacket_id,
                       account_id=account_id,
                       success=True,
                       amount=amount
                   )
           
           # 方案 B: 文本命令
           # 如果紅包需要通過命令參與
           # await client.send_message(
           #     chat_id=redpacket.group_id,
           #     text="/grab_redpacket"
           # )
           
           # 方案 C: 其他方式
           # 根據實際的紅包實現調整
           
           return RedpacketResult(
               redpacket_id=redpacket.redpacket_id,
               account_id=account_id,
               success=False,
               error="未找到有效的參與方式"
           )
       
       except Exception as e:
           logger.error(f"參與紅包失敗: {e}", exc_info=True)
           return RedpacketResult(
               redpacket_id=redpacket.redpacket_id,
               account_id=account_id,
               success=False,
               error=str(e)
           )
   
   def _is_redpacket_button(self, button) -> bool:
       """判斷按鈕是否為紅包相關"""
       text = button.text.lower()
       redpacket_keywords = ["紅包", "红包", "grab", "領取", "領紅包"]
       return any(keyword in text for keyword in redpacket_keywords)
   ```

2. **完善紅包檢測**

   更新 `detect_redpacket` 方法以檢測更多類型的紅包：

   ```python
   async def detect_redpacket(self, message: Message) -> Optional[RedpacketInfo]:
       """檢測紅包消息"""
       # 方法 1: 檢查消息文本
       text = (message.text or "").lower()
       has_keyword = any(
           keyword in text 
           for keyword in ["紅包", "红包", "red packet", "redpacket"]
       )
       
       # 方法 2: 檢查內聯按鈕
       has_redpacket_button = False
       if message.reply_markup:
           for row in message.reply_markup.inline_keyboard:
               for button in row:
                   if self._is_redpacket_button(button):
                       has_redpacket_button = True
                       break
       
       # 方法 3: 檢查消息類型
       # 某些紅包可能使用特殊消息類型
       is_special_type = False
       # if message.game or message.invoice:
       #     is_special_type = True
       
       if not (has_keyword or has_redpacket_button or is_special_type):
           return None
       
       # 創建紅包信息
       redpacket_id = f"{message.chat.id}_{message.id}"
       
       # 去重檢查
       if redpacket_id in self.detected_redpackets:
           existing = self.detected_redpackets[redpacket_id]
           time_diff = (datetime.now() - existing.timestamp).total_seconds()
           if time_diff < 300:
               return None
       
       redpacket = RedpacketInfo(
           redpacket_id=redpacket_id,
           group_id=message.chat.id if message.chat else 0,
           sender_id=message.from_user.id if message.from_user else 0,
           message_id=message.id,
           timestamp=message.date or datetime.now(),
           redpacket_type="normal"
       )
       
       # 提取金額
       # ... 現有邏輯 ...
       
       self.detected_redpackets[redpacket_id] = redpacket
       return redpacket
   ```

3. **集成到對話管理器**

   更新 `dialogue_manager.py` 中的紅包處理邏輯：

   ```python
   if should_participate:
       # 獲取賬號的 client
       account = account_manager.accounts.get(account_id)
       if account and account.client:
           result = await self.redpacket_handler.participate(
               account_id=account_id,
               redpacket=redpacket,
               client=account.client
           )
           
           if result.success:
               logger.info(
                   f"成功參與紅包（賬號: {account_id}, "
                   f"紅包: {redpacket.redpacket_id}, "
                   f"金額: {result.amount}）"
               )
           else:
               logger.warning(
                   f"參與紅包失敗（賬號: {account_id}, "
                   f"錯誤: {result.error}）"
               )
   ```

---

## 新成員檢測集成

### 實現方案

```python
@client.on_message(filters.new_chat_members)
async def handle_new_member(client: Client, message: Message):
    """處理新成員加入"""
    if not message.new_chat_members:
        return
    
    for new_member in message.new_chat_members:
        # 觸發新成員事件
        await dialogue_manager.process_message(
            account_id=account_id,
            group_id=message.chat.id,
            message=message,
            account_config=account_config
        )
```

---

## 錯誤處理

### FloodWait 處理

```python
from pyrogram.errors import FloodWait, RPCError

async def safe_telegram_call(func, *args, max_retries=3, **kwargs):
    """安全的 Telegram API 調用，自動處理 FloodWait"""
    for attempt in range(max_retries):
        try:
            return await func(*args, **kwargs)
        except FloodWait as e:
            if attempt < max_retries - 1:
                logger.warning(f"FloodWait: 等待 {e.value} 秒後重試")
                await asyncio.sleep(e.value)
            else:
                raise
        except RPCError as e:
            logger.error(f"RPC 錯誤: {e}")
            raise
```

---

## 測試

### 測試實際紅包操作

```python
async def test_real_redpacket():
    """測試實際紅包操作（需要真實環境）"""
    # 1. 創建測試賬號
    # 2. 加入測試群組
    # 3. 發送測試紅包
    # 4. 檢測並參與
    # 5. 驗證結果
    pass
```

---

## 注意事項

1. **Rate Limiting**
   - Telegram 有嚴格的速率限制
   - 需要實現適當的延遲和重試機制

2. **安全性**
   - 不要過於頻繁地操作
   - 避免觸發 Telegram 的安全機制

3. **兼容性**
   - 不同類型的紅包可能需要不同的處理方式
   - 需要根據實際情況調整

---

## 下一步

1. **實現實際的搶紅包操作**
   - 根據實際的紅包類型實現
   - 處理各種邊界情況

2. **完善錯誤處理**
   - FloodWait 處理
   - 網絡錯誤重試
   - 超時處理

3. **測試和驗證**
   - 在真實環境中測試
   - 驗證各種場景

---

**狀態**: ⏳ 待實現，需要根據實際的 Telegram 紅包實現調整

