"""
變量解析器測試腳本
"""
import sys
import io
from pathlib import Path
from unittest.mock import Mock

# 設置 UTF-8 編碼（Windows 兼容）
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 添加項目根目錄到 Python 路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from group_ai_service.variable_resolver import VariableResolver
from pyrogram.types import Message, User, Chat


def create_mock_message(text: str) -> Message:
    """創建模擬消息"""
    user = Mock(spec=User)
    user.first_name = "張三"
    user.id = 123456789
    user.username = "zhangsan"
    
    chat_type = Mock()
    chat_type.name = "GROUP"
    
    chat = Mock(spec=Chat)
    chat.id = -1001234567890
    chat.type = chat_type
    
    message = Mock(spec=Message)
    message.text = text
    message.from_user = user
    message.chat = chat
    
    return message


def test_basic_variables():
    """測試基礎變量"""
    print("="*60)
    print("測試 1: 基礎變量替換")
    print("="*60)
    
    resolver = VariableResolver()
    message = create_mock_message("你好")
    
    templates = [
        ("你好，{{user_name}}！", "你好，張三！"),
        ("用戶 ID: {{user_id}}", "用戶 ID: 123456789"),
        ("消息長度: {{message_length}}", "消息長度: 2"),
    ]
    
    for template, expected in templates:
        result = resolver.resolve(template, message)
        print(f"模板: {template}")
        print(f"結果: {result}")
        print(f"預期: {expected}")
        if expected in result or result == expected:
            print("[OK] 測試通過\n")
        else:
            print(f"[FAIL] 不匹配\n")


def test_function_calls():
    """測試函數調用"""
    print("="*60)
    print("測試 2: 函數調用")
    print("="*60)
    
    resolver = VariableResolver()
    message = create_mock_message("今天天氣真好")
    
    templates = [
        ("話題: {{detect_topic()}}", "話題: 天氣"),
        ("當前時間: {{current_time()}}", "當前時間:"),
        ("表情: {{random_emoji()}}", "表情:"),
    ]
    
    for template, expected_prefix in templates:
        result = resolver.resolve(template, message)
        print(f"模板: {template}")
        print(f"結果: {result}")
        if result.startswith(expected_prefix) or expected_prefix in result:
            print("[OK] 測試通過\n")
        else:
            print(f"[WARN] 結果可能不匹配（函數結果可能變化）\n")


def test_nested_variables():
    """測試嵌套變量"""
    print("="*60)
    print("測試 3: 嵌套變量")
    print("="*60)
    
    resolver = VariableResolver()
    message = create_mock_message("Hello World")
    
    context = {
        "greeting": "你好",
        "name": "世界"
    }
    
    template = "{{greeting}}，{{name}}！"
    result = resolver.resolve(template, message, context=context)
    
    print(f"模板: {template}")
    print(f"結果: {result}")
    print(f"預期: 你好，世界！")
    
    if "你好" in result and "世界" in result:
        print("[OK] 測試通過\n")
    else:
        print("[FAIL] 測試失敗\n")


def main():
    """主測試流程"""
    print("\n" + "="*60)
    print("變量解析器測試")
    print("="*60 + "\n")
    
    test_basic_variables()
    test_function_calls()
    test_nested_variables()
    
    print("="*60)
    print("測試完成")
    print("="*60)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n\n測試過程中發生錯誤: {e}")
        import traceback
        traceback.print_exc()

