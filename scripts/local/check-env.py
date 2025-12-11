#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
檢查本地環境變量配置
"""
import os
import sys
from pathlib import Path

# 設置 Windows 終端編碼
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

def check_env():
    """檢查環境變量配置"""
    print("=" * 60)
    print("環境變量配置檢查")
    print("=" * 60)
    
    # 檢查 .env 文件
    project_root = Path(__file__).parent.parent.parent
    env_file = project_root / ".env"
    
    print(f"\n項目根目錄: {project_root}")
    print(f".env 文件路徑: {env_file}")
    
    if env_file.exists():
        print("[通過] .env 文件存在")
        
        # 嘗試加載 .env 文件
        try:
            from dotenv import load_dotenv
            load_dotenv(env_file)
            print("[通過] .env 文件已加載")
        except ImportError:
            print("[警告] python-dotenv 未安裝，無法自動加載 .env")
            print("請手動設置環境變量或安裝: pip install python-dotenv")
    else:
        print("[失敗] .env 文件不存在")
        print(f"請在 {env_file} 創建 .env 文件並配置環境變量")
        return False
    
    # 檢查關鍵環境變量
    print("\n" + "=" * 60)
    print("檢查關鍵環境變量")
    print("=" * 60)
    
    required_vars = [
        "TELEGRAM_API_ID",
        "TELEGRAM_API_HASH",
        "TELEGRAM_SESSION_NAME",
        "OPENAI_API_KEY",
    ]
    
    missing = []
    empty = []
    
    for var in required_vars:
        value = os.getenv(var)
        if value:
            # 檢查值是否為空字符串
            if value.strip() == "":
                print(f"[警告] {var} 存在但值為空")
                empty.append(var)
            else:
                # 對於 API Key，只顯示部分字符
                if var == "OPENAI_API_KEY":
                    if len(value) > 11:
                        masked = value[:7] + "..." + value[-4:]
                    else:
                        masked = "***"
                    print(f"[通過] {var} = {masked}")
                elif var == "TELEGRAM_API_HASH":
                    if len(value) > 11:
                        masked = value[:7] + "..." + value[-4:]
                    else:
                        masked = "***"
                    print(f"[通過] {var} = {masked}")
                else:
                    print(f"[通過] {var} = {value}")
        else:
            print(f"[失敗] {var} 未設置")
            missing.append(var)
    
    print("\n" + "=" * 60)
    if missing:
        print(f"[失敗] 缺失環境變量: {', '.join(missing)}")
        print("\n請在 .env 文件中添加以下配置:")
        for var in missing:
            print(f"  {var}=your_value_here")
        return False
    elif empty:
        print(f"[警告] 以下環境變量值為空: {', '.join(empty)}")
        print("請在 .env 文件中設置正確的值")
        return False
    else:
        print("[成功] 所有必需的環境變量都已配置")
        print("=" * 60)
        return True

def test_openai_connection():
    """測試 OpenAI API 連接"""
    print("\n" + "=" * 60)
    print("測試 OpenAI API 連接")
    print("=" * 60)
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("[跳過] OPENAI_API_KEY 未設置，跳過 API 測試")
        return False
    
    try:
        from openai import AsyncOpenAI
        import asyncio
        
        client = AsyncOpenAI(api_key=api_key)
        
        async def test():
            try:
                response = await client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": "Hello"}],
                    max_tokens=5
                )
                print("[通過] OpenAI API 連接成功")
                print(f"測試回覆: {response.choices[0].message.content}")
                return True
            except Exception as e:
                error_msg = str(e)
                if "401" in error_msg or "invalid_api_key" in error_msg.lower():
                    print("[失敗] OpenAI API Key 無效")
                    print("請檢查 .env 文件中的 OPENAI_API_KEY 是否正確")
                elif "429" in error_msg:
                    print("[警告] OpenAI API 請求過於頻繁，請稍後再試")
                else:
                    print(f"[失敗] OpenAI API 連接失敗: {e}")
                return False
        
        result = asyncio.run(test())
        return result
        
    except ImportError:
        print("[跳過] openai 庫未安裝，跳過 API 測試")
        print("請安裝: pip install openai")
        return False
    except Exception as e:
        print(f"[失敗] 測試過程出錯: {e}")
        return False

if __name__ == "__main__":
    try:
        # 檢查環境變量
        env_ok = check_env()
        
        if env_ok:
            # 測試 OpenAI 連接
            api_ok = test_openai_connection()
            
            if api_ok:
                print("\n" + "=" * 60)
                print("[成功] 環境配置驗證完成，所有測試通過")
                print("=" * 60)
                sys.exit(0)
            else:
                print("\n" + "=" * 60)
                print("[警告] 環境變量已配置，但 OpenAI API 連接失敗")
                print("請檢查 API Key 是否正確")
                print("=" * 60)
                sys.exit(1)
        else:
            print("\n" + "=" * 60)
            print("[失敗] 環境變量配置不完整")
            print("請修復上述問題後重試")
            print("=" * 60)
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\n[中斷] 檢查被用戶中斷")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n[異常] 檢查過程出錯: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

