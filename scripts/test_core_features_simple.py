#!/usr/bin/env python3
"""
核心功能簡單測試腳本 - 快速驗證功能是否可用
"""
import sys
from pathlib import Path

# 添加項目根目錄到路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_imports():
    """測試所有模塊是否可以導入"""
    print("="*60)
    print("測試 1: 模塊導入")
    print("="*60)
    
    modules = [
        ("group_ai_service.coordination_manager", "CoordinationManager", "協同管理器"),
        ("group_ai_service.message_analyzer", "MessageAnalyzer", "消息分析器"),
        ("group_ai_service.script_engine", "ScriptEngine", "劇本引擎"),
        ("group_ai_service.service_manager", "ServiceManager", "服務管理器"),
    ]
    
    results = []
    for module_name, class_name, desc in modules:
        try:
            module = __import__(module_name, fromlist=[class_name])
            cls = getattr(module, class_name)
            print(f"✅ {desc} ({class_name}) - 導入成功")
            results.append(True)
        except Exception as e:
            print(f"❌ {desc} ({class_name}) - 導入失敗: {e}")
            results.append(False)
    
    return all(results)


def test_coordination_manager_basic():
    """測試協同管理器基本功能"""
    print("\n" + "="*60)
    print("測試 2: 協同管理器基本功能")
    print("="*60)
    
    try:
        from group_ai_service.coordination_manager import CoordinationManager, ReplyPriority
        
        manager = CoordinationManager()
        print("✅ 協同管理器創建成功")
        
        manager.register_account_role("test_account", role_id="test_role", priority=ReplyPriority.HIGH)
        print("✅ 賬號註冊成功")
        
        role = manager.get_account_role("test_account")
        print(f"✅ 獲取角色成功: {role}")
        
        return True
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_message_analyzer_basic():
    """測試消息分析器基本功能"""
    print("\n" + "="*60)
    print("測試 3: 消息分析器基本功能")
    print("="*60)
    
    try:
        from group_ai_service.message_analyzer import MessageAnalyzer
        
        analyzer = MessageAnalyzer()
        print("✅ 消息分析器創建成功")
        
        # 測試意圖識別
        class MockMsg:
            def __init__(self, text):
                self.text = text
        
        message = MockMsg("你好")
        intent = analyzer.detect_intent(message, language="zh")
        if intent:
            print(f"✅ 意圖識別成功: {intent.intent_type}")
        else:
            print("⚠️  意圖未匹配（可能需要擴展關鍵詞）")
        
        # 測試話題檢測
        message2 = MockMsg("我喜歡玩遊戲")
        topic = analyzer.detect_topic(message2, language="zh")
        if topic:
            print(f"✅ 話題檢測成功: {topic.topic}")
        else:
            print("⚠️  話題未匹配（可能需要擴展關鍵詞）")
        
        # 測試情感分析
        message3 = MockMsg("今天天氣真好，我很開心")
        sentiment = analyzer.analyze_sentiment(message3)
        print(f"✅ 情感分析成功: {sentiment.sentiment}")
        
        return True
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_script_engine_basic():
    """測試劇本引擎基本功能"""
    print("\n" + "="*60)
    print("測試 4: 劇本引擎基本功能")
    print("="*60)
    
    try:
        from group_ai_service.script_engine import ScriptEngine
        
        engine = ScriptEngine()
        print("✅ 劇本引擎創建成功")
        
        # 檢查是否有 update_script 方法
        if hasattr(engine, 'update_script'):
            print("✅ 熱更新方法存在")
        else:
            print("❌ 熱更新方法不存在")
            return False
        
        return True
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主函數"""
    print("\n" + "="*60)
    print("核心功能簡單測試")
    print("="*60)
    print("測試內容:")
    print("  1. 模塊導入測試")
    print("  2. 協同管理器基本功能")
    print("  3. 消息分析器基本功能")
    print("  4. 劇本引擎基本功能")
    print("="*60 + "\n")
    
    results = []
    
    results.append(("模塊導入", test_imports()))
    results.append(("協同管理器", test_coordination_manager_basic()))
    results.append(("消息分析器", test_message_analyzer_basic()))
    results.append(("劇本引擎", test_script_engine_basic()))
    
    # 打印結果
    print("\n" + "="*60)
    print("測試結果總結")
    print("="*60)
    
    passed = 0
    for name, result in results:
        status = "✅ 通過" if result else "❌ 失敗"
        print(f"  {name}: {status}")
        if result:
            passed += 1
    
    print(f"\n總計: {passed}/{len(results)} 測試通過")
    
    if passed == len(results):
        print("\n🎉 所有基本功能測試通過！")
        print("\n下一步：運行完整測試腳本 scripts/test_core_features.py")
        return 0
    else:
        print(f"\n⚠️  有 {len(results) - passed} 個測試未通過，請檢查錯誤信息")
        return 1


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except Exception as e:
        print(f"\n❌ 測試腳本執行失敗: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
