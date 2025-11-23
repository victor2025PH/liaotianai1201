"""
測試劇本創建、持久化和回滾功能
"""
import sys
import json
from pathlib import Path

# 添加項目根目錄到路徑
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from app.db import SessionLocal
from app.models.group_ai import GroupAIScript, GroupAIScriptVersion
import requests
import time

# 測試劇本 YAML 內容
TEST_SCRIPT_YAML = """
script_id: test_script_persistence
version: "1.0.0"
name: "測試劇本持久化"
description: "用於測試劇本保存、回滾和日誌功能"

scenes:
  - id: scene_1
    name: "歡迎場景"
    triggers:
      - type: message
        patterns:
          - "你好"
          - "hello"
    responses:
      - type: text
        content: "歡迎使用測試劇本！"
    
  - id: scene_2
    name: "幫助場景"
    triggers:
      - type: message
        patterns:
          - "幫助"
          - "help"
    responses:
      - type: text
        content: "這是測試劇本的幫助信息。"
""".strip()

API_BASE = "http://localhost:8000/api/v1/group-ai/scripts"

def test_create_script():
    """測試創建劇本"""
    print("=" * 60)
    print("測試 1: 創建劇本")
    print("=" * 60)
    
    # 先檢查數據庫
    db = SessionLocal()
    try:
        count_before = db.query(GroupAIScript).count()
        print(f"創建前數據庫中的劇本數量: {count_before}")
        
        existing = db.query(GroupAIScript).filter(
            GroupAIScript.script_id == "test_script_persistence"
        ).first()
        if existing:
            print(f"⚠️  劇本 test_script_persistence 已存在，先刪除...")
            db.delete(existing)
            db.commit()
    finally:
        db.close()
    
    # 發送創建請求
    payload = {
        "script_id": "test_script_persistence",
        "name": "測試劇本持久化",
        "version": "1.0.0",
        "description": "用於測試劇本保存、回滾和日誌功能",
        "yaml_content": TEST_SCRIPT_YAML
    }
    
    print(f"\n📤 發送創建請求...")
    print(f"   劇本 ID: {payload['script_id']}")
    print(f"   名稱: {payload['name']}")
    
    try:
        response = requests.post(
            f"{API_BASE}/",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        print(f"\n📥 響應狀態碼: {response.status_code}")
        
        if response.status_code == 201:
            data = response.json()
            print(f"✅ 創建成功！")
            print(f"   劇本 ID: {data.get('script_id')}")
            print(f"   名稱: {data.get('name')}")
            print(f"   版本: {data.get('version')}")
            print(f"   場景數: {data.get('scene_count')}")
            print(f"   創建時間: {data.get('created_at')}")
        else:
            print(f"❌ 創建失敗！")
            try:
                error_data = response.json()
                print(f"   錯誤詳情: {json.dumps(error_data, indent=2, ensure_ascii=False)}")
            except:
                print(f"   錯誤詳情: {response.text}")
            return False
        
        # 等待一小段時間，確保數據庫操作完成
        time.sleep(0.5)
        
        # 驗證數據庫
        db = SessionLocal()
        try:
            count_after = db.query(GroupAIScript).count()
            print(f"\n📊 創建後數據庫中的劇本數量: {count_after}")
            
            saved_script = db.query(GroupAIScript).filter(
                GroupAIScript.script_id == "test_script_persistence"
            ).first()
            
            if saved_script:
                print(f"✅ 數據庫驗證成功！")
                print(f"   數據庫 ID: {saved_script.id}")
                print(f"   劇本 ID: {saved_script.script_id}")
                print(f"   名稱: {saved_script.name}")
                print(f"   版本: {saved_script.version}")
                print(f"   狀態: {saved_script.status}")
                print(f"   YAML 長度: {len(saved_script.yaml_content)} 字符")
                print(f"   創建時間: {saved_script.created_at}")
                
                # 檢查版本記錄
                version_record = db.query(GroupAIScriptVersion).filter(
                    GroupAIScriptVersion.script_id == "test_script_persistence",
                    GroupAIScriptVersion.version == "1.0.0"
                ).first()
                
                if version_record:
                    print(f"✅ 版本記錄驗證成功！")
                    print(f"   版本: {version_record.version}")
                    print(f"   變更說明: {version_record.change_summary}")
                else:
                    print(f"⚠️  版本記錄不存在")
                
                return True
            else:
                print(f"❌ 數據庫驗證失敗！劇本未保存到數據庫")
                return False
        finally:
            db.close()
            
    except requests.exceptions.RequestException as e:
        print(f"❌ 請求失敗: {e}")
        return False
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_list_scripts():
    """測試列表劇本"""
    print("\n" + "=" * 60)
    print("測試 2: 列表劇本")
    print("=" * 60)
    
    try:
        response = requests.get(
            f"{API_BASE}/",
            params={"limit": 100},
            timeout=10
        )
        
        print(f"📥 響應狀態碼: {response.status_code}")
        
        if response.status_code == 200:
            scripts = response.json()
            print(f"✅ 獲取成功！找到 {len(scripts)} 個劇本")
            
            test_script = next((s for s in scripts if s.get('script_id') == 'test_script_persistence'), None)
            if test_script:
                print(f"✅ 測試劇本在列表中！")
                print(f"   劇本 ID: {test_script.get('script_id')}")
                print(f"   名稱: {test_script.get('name')}")
                print(f"   場景數: {test_script.get('scene_count')}")
                return True
            else:
                print(f"⚠️  測試劇本不在列表中")
                return False
        else:
            print(f"❌ 獲取失敗！")
            try:
                error_data = response.json()
                print(f"   錯誤詳情: {json.dumps(error_data, indent=2, ensure_ascii=False)}")
            except:
                print(f"   錯誤詳情: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_duplicate_script():
    """測試重複創建劇本（應該失敗）"""
    print("\n" + "=" * 60)
    print("測試 3: 重複創建劇本（測試錯誤處理）")
    print("=" * 60)
    
    payload = {
        "script_id": "test_script_persistence",  # 相同的 ID
        "name": "重複的測試劇本",
        "version": "1.0.0",
        "description": "這應該失敗",
        "yaml_content": TEST_SCRIPT_YAML
    }
    
    print(f"📤 嘗試重複創建劇本（相同 ID）...")
    
    try:
        response = requests.post(
            f"{API_BASE}/",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        print(f"📥 響應狀態碼: {response.status_code}")
        
        if response.status_code == 400:
            error_data = response.json()
            print(f"✅ 正確拒絕重複創建！")
            print(f"   錯誤信息: {error_data.get('detail', 'Unknown error')}")
            
            # 驗證數據庫沒有重複記錄
            db = SessionLocal()
            try:
                scripts = db.query(GroupAIScript).filter(
                    GroupAIScript.script_id == "test_script_persistence"
                ).all()
                print(f"📊 數據庫中的記錄數: {len(scripts)}")
                if len(scripts) == 1:
                    print(f"✅ 數據庫驗證成功！沒有重複記錄")
                    return True
                else:
                    print(f"❌ 數據庫驗證失敗！發現 {len(scripts)} 條記錄（應該是1條）")
                    return False
            finally:
                db.close()
        else:
            print(f"❌ 測試失敗！應該返回 400，但返回了 {response.status_code}")
            try:
                error_data = response.json()
                print(f"   響應: {json.dumps(error_data, indent=2, ensure_ascii=False)}")
            except:
                print(f"   響應: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主測試流程"""
    print("\n" + "=" * 60)
    print("劇本持久化測試套件")
    print("=" * 60)
    print(f"API 地址: {API_BASE}")
    print(f"測試時間: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    results = []
    
    # 執行測試
    results.append(("創建劇本", test_create_script()))
    results.append(("列表劇本", test_list_scripts()))
    results.append(("重複創建測試", test_duplicate_script()))
    
    # 總結
    print("\n" + "=" * 60)
    print("測試總結")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ 通過" if result else "❌ 失敗"
        print(f"{status} - {test_name}")
    
    print(f"\n總計: {passed}/{total} 個測試通過")
    
    if passed == total:
        print("\n🎉 所有測試通過！劇本持久化功能正常。")
        return 0
    else:
        print(f"\n⚠️  有 {total - passed} 個測試失敗，請檢查日誌。")
        return 1


if __name__ == "__main__":
    sys.exit(main())

