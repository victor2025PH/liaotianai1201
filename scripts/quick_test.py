#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import os
from pathlib import Path

# 添加項目根目錄
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

print("="*60)
print("核心功能快速測試")
print("="*60)
print()

# 測試 1: 導入協同管理器
print("[測試 1] 導入協同管理器...")
try:
    from group_ai_service.coordination_manager import CoordinationManager, ReplyPriority
    print("✅ 協同管理器導入成功")
    manager = CoordinationManager()
    print("✅ 協同管理器創建成功")
except Exception as e:
    print(f"❌ 失敗: {e}")
    import traceback
    traceback.print_exc()

print()

# 測試 2: 導入消息分析器
print("[測試 2] 導入消息分析器...")
try:
    from group_ai_service.message_analyzer import MessageAnalyzer
    print("✅ 消息分析器導入成功")
    analyzer = MessageAnalyzer()
    print("✅ 消息分析器創建成功")
    
    # 測試意圖識別
    class MockMsg:
        def __init__(self, text):
            self.text = text
    
    msg = MockMsg("你好")
    intent = analyzer.detect_intent(msg, "zh")
    if intent:
        print(f"✅ 意圖識別測試成功: {intent.intent_type}")
    else:
        print("⚠️  意圖未匹配（可能關鍵詞需要擴展）")
except Exception as e:
    print(f"❌ 失敗: {e}")
    import traceback
    traceback.print_exc()

print()

# 測試 3: 導入劇本引擎
print("[測試 3] 導入劇本引擎...")
try:
    from group_ai_service.script_engine import ScriptEngine
    print("✅ 劇本引擎導入成功")
    engine = ScriptEngine()
    print("✅ 劇本引擎創建成功")
    
    # 檢查熱更新方法
    if hasattr(engine, 'update_script'):
        print("✅ 熱更新方法存在")
    else:
        print("❌ 熱更新方法不存在")
except Exception as e:
    print(f"❌ 失敗: {e}")
    import traceback
    traceback.print_exc()

print()

# 測試 4: 檢查對話管理器
print("[測試 4] 檢查對話管理器中的新成員檢測...")
try:
    from group_ai_service.dialogue_manager import DialogueManager
    print("✅ 對話管理器導入成功")
    
    if hasattr(DialogueManager, '_check_new_member'):
        print("✅ 新成員檢測方法存在")
    else:
        print("❌ 新成員檢測方法不存在")
except Exception as e:
    print(f"❌ 失敗: {e}")
    import traceback
    traceback.print_exc()

print()
print("="*60)
print("測試完成")
print("="*60)
