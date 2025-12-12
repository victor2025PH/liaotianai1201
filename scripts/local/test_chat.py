#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能聊天測試腳本
用於驗證 Telegram AI 機器人的核心聊天功能
"""
import asyncio
import sys
import os
from pathlib import Path

# 設置 Windows 終端編碼
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 添加項目根目錄到 Python 路徑
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import config
from utils.business_ai import ai_business_reply
from utils.ai_context_manager import (
    init_history_db,
    add_to_history,
    get_history,
    get_message_count,
    get_turn_count
)
from utils.user_utils import get_user_profile
from utils.prompt_manager import resolve_language_code


async def test_ai_reply():
    """測試 AI 回覆功能"""
    print("=" * 60)
    print("測試 1: AI 智能回覆功能")
    print("=" * 60)
    
    # 初始化數據庫
    init_history_db()
    
    # 測試用戶 ID
    test_user_id = "test_user_001"
    
    # 模擬用戶資料
    user_profile = {
        "first_name": "測試用戶",
        "language": "zh",
        "tags": ["測試", "新用戶"],
        "bio": "這是一個測試用戶",
        "remark": "",
        "country": "TW"
    }
    
    # 測試消息 1: 簡單問候
    print("\n[測試] 測試消息 1: 簡單問候")
    print(f"用戶: 你好")
    await add_to_history(test_user_id, "user", "你好")
    
    context_info = {
        "conversation_stage": "warmup",
        "language": "zh",
        "triggered_intent": None
    }
    
    try:
        reply = await ai_business_reply(
            test_user_id,
            user_profile,
            context_info=context_info,
            history_summary="",
            use_name_in_prompt=False
        )
        print(f"AI 回覆: {reply}")
        print("[通過] AI 回覆測試通過")
    except Exception as e:
        print(f"[失敗] AI 回覆測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 測試消息 2: 繼續對話
    print("\n[測試] 測試消息 2: 繼續對話")
    print(f"用戶: 今天天氣怎麼樣？")
    await add_to_history(test_user_id, "user", "今天天氣怎麼樣？")
    
    try:
        reply = await ai_business_reply(
            test_user_id,
            user_profile,
            context_info=context_info,
            history_summary="",
            use_name_in_prompt=False
        )
        print(f"AI 回覆: {reply}")
        print("[通過] 上下文對話測試通過")
    except Exception as e:
        print(f"[失敗] 上下文對話測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


async def test_context_manager():
    """測試上下文管理功能"""
    print("\n" + "=" * 60)
    print("測試 2: 上下文管理功能")
    print("=" * 60)
    
    test_user_id = "test_user_002"
    init_history_db()
    
    # 測試添加歷史記錄
    print("\n[測試] 測試添加歷史記錄")
    await add_to_history(test_user_id, "user", "第一條消息")
    await add_to_history(test_user_id, "assistant", "第一條回覆")
    await add_to_history(test_user_id, "user", "第二條消息")
    print("[通過] 歷史記錄添加成功")
    
    # 測試獲取歷史記錄
    print("\n[測試] 測試獲取歷史記錄")
    history = await get_history(test_user_id, max_len=10)
    print(f"獲取到 {len(history)} 條歷史記錄")
    for i, h in enumerate(history, 1):
        print(f"  {i}. [{h['role']}]: {h['content'][:50]}...")
    print("[通過] 歷史記錄獲取成功")
    
    # 測試消息計數
    print("\n[測試] 測試消息計數")
    msg_count = await get_message_count(test_user_id)
    print(f"用戶消息總數: {msg_count}")
    print("[通過] 消息計數功能正常")
    
    # 測試輪次計數
    print("\n[測試] 測試輪次計數")
    turn_count = await get_turn_count(test_user_id)
    print(f"對話輪次: {turn_count}")
    print("[通過] 輪次計數功能正常")
    
    return True


async def test_multi_turn_conversation():
    """測試多輪對話"""
    print("\n" + "=" * 60)
    print("測試 3: 多輪對話測試")
    print("=" * 60)
    
    test_user_id = "test_user_003"
    init_history_db()
    
    user_profile = {
        "first_name": "多輪測試",
        "language": "zh",
        "tags": ["測試"],
        "bio": "",
        "remark": "",
        "country": "TW"
    }
    
    # 模擬多輪對話
    test_messages = [
        "你好",
        "我想了解一下你們的服務",
        "有什麼推薦的嗎？",
        "價格怎麼樣？"
    ]
    
    context_info = {
        "conversation_stage": "normal",
        "language": "zh",
        "triggered_intent": None
    }
    
    for i, user_msg in enumerate(test_messages, 1):
        print(f"\n[測試] 第 {i} 輪對話")
        print(f"用戶: {user_msg}")
        await add_to_history(test_user_id, "user", user_msg)
        
        try:
            # 根據輪次調整對話階段
            if i <= 2:
                context_info["conversation_stage"] = "warmup"
            else:
                context_info["conversation_stage"] = "normal"
            
            reply = await ai_business_reply(
                test_user_id,
                user_profile,
                context_info=context_info,
                history_summary="",
                use_name_in_prompt=(i == 1)
            )
            print(f"AI: {reply}")
            
            # 檢查回覆是否合理
            if len(reply) < 5:
                print(f"[警告]  警告: AI 回覆過短: {reply}")
            elif len(reply) > 500:
                print(f"[警告]  警告: AI 回覆過長: {len(reply)} 字符")
            else:
                print(f"[通過] 第 {i} 輪對話完成")
        except Exception as e:
            print(f"[失敗] 第 {i} 輪對話失敗: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    # 驗證歷史記錄
    history = await get_history(test_user_id, max_len=20)
    print(f"\n[統計] 對話歷史統計: 共 {len(history)} 條記錄")
    print("[通過] 多輪對話測試完成")
    
    return True


async def test_language_detection():
    """測試語言檢測"""
    print("\n" + "=" * 60)
    print("測試 4: 語言檢測功能")
    print("=" * 60)
    
    test_cases = [
        ("zh", "你好，今天天氣不錯"),
        ("en", "Hello, how are you today?"),
        ("zh", "我想了解一下"),
        ("en", "What services do you offer?")
    ]
    
    for lang, text in test_cases:
        print(f"\n[測試] 測試語言: {lang}, 文本: {text[:30]}...")
        resolved = resolve_language_code(lang)
        print(f"解析結果: {resolved}")
        print("[通過] 語言檢測正常")
    
    return True


async def run_all_tests():
    """運行所有測試"""
    print("\n" + "=" * 60)
    print("[開始] 智能聊天功能測試")
    print("=" * 60)
    print(f"項目根目錄: {project_root}")
    print(f"數據庫路徑: {config.DB_PATH}")
    print(f"OpenAI 模型: {config.OPENAI_MODEL}")
    print("=" * 60)
    
    results = []
    
    # 測試 1: AI 回覆
    try:
        result = await test_ai_reply()
        results.append(("AI 智能回覆", result))
    except Exception as e:
        print(f"[失敗] AI 回覆測試異常: {e}")
        results.append(("AI 智能回覆", False))
    
    # 測試 2: 上下文管理
    try:
        result = await test_context_manager()
        results.append(("上下文管理", result))
    except Exception as e:
        print(f"[失敗] 上下文管理測試異常: {e}")
        results.append(("上下文管理", False))
    
    # 測試 3: 多輪對話
    try:
        result = await test_multi_turn_conversation()
        results.append(("多輪對話", result))
    except Exception as e:
        print(f"[失敗] 多輪對話測試異常: {e}")
        results.append(("多輪對話", False))
    
    # 測試 4: 語言檢測
    try:
        result = await test_language_detection()
        results.append(("語言檢測", result))
    except Exception as e:
        print(f"[失敗] 語言檢測測試異常: {e}")
        results.append(("語言檢測", False))
    
    # 輸出測試總結
    print("\n" + "=" * 60)
    print("[統計] 測試結果總結")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    for test_name, result in results:
        status = "[通過]" if result else "[失敗]"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
        else:
            failed += 1
    
    print("=" * 60)
    print(f"總計: {len(results)} 個測試")
    print(f"通過: {passed} 個")
    print(f"失敗: {failed} 個")
    print("=" * 60)
    
    if failed == 0:
        print("\n[成功] 所有測試通過！")
        return 0
    else:
        print(f"\n[警告] 有 {failed} 個測試失敗，請檢查上述錯誤信息")
        return 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(run_all_tests())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n[中斷] 測試被用戶中斷")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n[異常] 測試執行異常: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

