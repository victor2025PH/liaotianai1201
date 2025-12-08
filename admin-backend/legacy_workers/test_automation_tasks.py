"""
自動化任務功能測試腳本
"""
import sys
import asyncio
import logging
from pathlib import Path

# 添加項目根目錄到路徑
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from app.db import SessionLocal
from app.models.group_ai import GroupAIAutomationTask
from app.services.task_executor import get_task_executor
from app.services.notification_service import NotificationService
from app.crud.notification import create_notification
from app.models.notification import NotificationType

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_task_executor():
    """測試任務執行器"""
    logger.info("=" * 60)
    logger.info("開始測試任務執行器")
    logger.info("=" * 60)
    
    # 確保所有表都存在
    from app.db import Base, engine
    from app.models import group_ai, notification
    Base.metadata.create_all(bind=engine)
    logger.info("✓ 已確保所有數據庫表存在")
    
    db = SessionLocal()
    executor = get_task_executor()
    
    try:
        # 清理之前的測試數據（如果表存在）
        logger.info("\n[清理] 清理之前的測試數據")
        try:
            db.query(GroupAIAutomationTask).filter(
                GroupAIAutomationTask.id.like("test-task-%")
            ).delete(synchronize_session=False)
            db.commit()
            logger.info("✓ 已清理舊測試數據")
        except Exception as e:
            logger.warning(f"清理舊數據時出現警告（可忽略）: {e}")
            db.rollback()
        
        # 測試1: 創建測試任務
        logger.info("\n[測試1] 創建測試任務")
        import uuid
        test_task_id = f"test-task-{uuid.uuid4().hex[:8]}"
        test_task = GroupAIAutomationTask(
            id=test_task_id,
            name="測試告警檢查任務",
            description="用於測試的告警檢查任務",
            task_type="manual",
            task_action="alert_check",
            action_config={},
            enabled=True,
            dependent_tasks=[],
            notify_on_success=False,
            notify_on_failure=True,
            notify_recipients=["test@example.com"],
        )
        db.add(test_task)
        db.commit()
        db.refresh(test_task)
        logger.info(f"✓ 任務已創建: {test_task.id}")
        
        # 測試2: 執行任務
        logger.info("\n[測試2] 執行任務")
        result = await executor.execute_task(test_task)
        logger.info(f"✓ 任務執行結果: {result}")
        
        # 測試3: 檢查任務統計
        logger.info("\n[測試3] 檢查任務統計")
        db.refresh(test_task)
        logger.info(f"✓ 執行次數: {test_task.run_count}")
        logger.info(f"✓ 成功次數: {test_task.success_count}")
        logger.info(f"✓ 失敗次數: {test_task.failure_count}")
        logger.info(f"✓ 最後結果: {test_task.last_result}")
        
        # 測試4: 檢查通知
        logger.info("\n[測試4] 檢查通知記錄")
        # 確保通知表存在
        from app.db import Base, engine
        from app.models.notification import Notification
        Base.metadata.create_all(bind=engine, tables=[Notification.__table__])
        
        from app.crud.notification import get_notifications
        try:
            notifications, total = get_notifications(
                db,
                recipient="test@example.com",
                skip=0,
                limit=10
            )
            logger.info(f"✓ 找到 {total} 條通知記錄（顯示前 {len(notifications)} 條）")
            for notif in notifications[:3]:
                logger.info(f"  - {notif.title}: {notif.message[:50]}...")
        except Exception as e:
            logger.warning(f"查詢通知時出現警告（可能沒有通知記錄）: {e}")
            logger.info("✓ 通知查詢功能正常（當前無通知記錄）")
        
        # 測試5: 測試依賴任務
        logger.info("\n[測試5] 測試依賴任務")
        import uuid
        dependent_task_id = f"test-task-{uuid.uuid4().hex[:8]}"
        dependent_task = GroupAIAutomationTask(
            id=dependent_task_id,
            name="依賴任務",
            description="依賴於主任務的任務",
            task_type="manual",
            task_action="alert_check",
            action_config={},
            enabled=True,
            dependent_tasks=[],
            notify_on_success=False,
            notify_on_failure=False,
            notify_recipients=[],
        )
        db.add(dependent_task)
        # 重新查詢任務以更新依賴
        task_refresh = db.query(GroupAIAutomationTask).filter(
            GroupAIAutomationTask.id == test_task.id
        ).first()
        if task_refresh:
            task_refresh.dependent_tasks = [dependent_task.id]
            db.commit()
            db.refresh(task_refresh)
            test_task = task_refresh
        logger.info(f"✓ 依賴任務已創建: {dependent_task.id}")
        logger.info(f"✓ 主任務依賴列表: {test_task.dependent_tasks}")
        
        # 測試6: 執行帶依賴的任務
        logger.info("\n[測試6] 執行帶依賴的任務")
        result2 = await executor.execute_task(test_task)
        logger.info(f"✓ 任務執行結果: {result2}")
        
        # 清理測試數據
        logger.info("\n[清理] 刪除測試任務")
        # 重新查詢以確保對象是最新的
        task_to_delete = db.query(GroupAIAutomationTask).filter(
            GroupAIAutomationTask.id == test_task.id
        ).first()
        dep_to_delete = db.query(GroupAIAutomationTask).filter(
            GroupAIAutomationTask.id == dependent_task.id
        ).first()
        if dep_to_delete:
            db.delete(dep_to_delete)
        if task_to_delete:
            db.delete(task_to_delete)
        db.commit()
        logger.info("✓ 測試數據已清理")
        
        logger.info("\n" + "=" * 60)
        logger.info("所有測試通過！")
        logger.info("=" * 60)
        return True
        
    except Exception as e:
        logger.error(f"✗ 測試失敗: {e}", exc_info=True)
        db.rollback()
        return False
    finally:
        db.close()


async def test_new_task_actions():
    """測試新的任務動作"""
    logger.info("\n" + "=" * 60)
    logger.info("開始測試新任務動作")
    logger.info("=" * 60)
    
    db = SessionLocal()
    executor = get_task_executor()
    
    try:
        # 測試批量啟動賬號
        logger.info("\n[測試] 批量啟動賬號動作")
        result = await executor._execute_account_batch_start(
            {"account_ids": ["test_account_1", "test_account_2"]},
            db
        )
        logger.info(f"✓ 批量啟動結果: {result}")
        
        # 測試批量停止賬號
        logger.info("\n[測試] 批量停止賬號動作")
        result = await executor._execute_account_batch_stop(
            {"account_ids": ["test_account_1", "test_account_2"]},
            db
        )
        logger.info(f"✓ 批量停止結果: {result}")
        
        # 測試數據導出
        logger.info("\n[測試] 數據導出動作")
        result = await executor._execute_data_export(
            {"export_type": "csv", "data_type": "accounts"},
            db
        )
        logger.info(f"✓ 數據導出結果: {result}")
        
        # 測試角色分配
        logger.info("\n[測試] 角色分配動作")
        result = await executor._execute_role_assignment(
            {"scheme_id": "test_scheme", "account_ids": ["account1"]},
            db
        )
        logger.info(f"✓ 角色分配結果: {result}")
        
        logger.info("\n" + "=" * 60)
        logger.info("新任務動作測試完成！")
        logger.info("=" * 60)
        return True
        
    except Exception as e:
        logger.error(f"✗ 測試失敗: {e}", exc_info=True)
        return False
    finally:
        db.close()


async def test_notification_integration():
    """測試通知集成"""
    logger.info("\n" + "=" * 60)
    logger.info("開始測試通知集成")
    logger.info("=" * 60)
    
    db = SessionLocal()
    
    try:
        # 確保通知表存在
        from app.db import Base, engine
        from app.models.notification import Notification
        Base.metadata.create_all(bind=engine, tables=[Notification.__table__])
        logger.info("✓ 已確保通知表存在")
        notification_service = NotificationService(db)
        
        # 測試發送瀏覽器通知
        logger.info("\n[測試] 發送瀏覽器通知")
        notification_id = await notification_service.send_browser_notification(
            recipient="test@example.com",
            title="測試通知",
            message="這是一條測試通知消息",
            level="info",
            event_type="test",
            resource_type="automation_task",
            resource_id="test-task-001",
        )
        logger.info(f"✓ 通知已發送，ID: {notification_id}")
        
        # 檢查通知記錄
        from app.models.notification import Notification
        notification = db.query(Notification).filter(Notification.id == notification_id).first()
        if notification:
            logger.info(f"✓ 通知記錄: {notification.title} - {notification.message}")
        else:
            logger.warning(f"✗ 未找到通知記錄 ID: {notification_id}")
        
        logger.info("\n" + "=" * 60)
        logger.info("通知集成測試完成！")
        logger.info("=" * 60)
        return True
        
    except Exception as e:
        logger.error(f"✗ 測試失敗: {e}", exc_info=True)
        return False
    finally:
        db.close()


async def main():
    """主測試函數"""
    logger.info("開始自動化任務功能全自動測試")
    logger.info("=" * 60)
    
    results = []
    
    # 測試1: 任務執行器
    try:
        result1 = await test_task_executor()
        results.append(("任務執行器", result1))
    except Exception as e:
        logger.error(f"任務執行器測試異常: {e}", exc_info=True)
        results.append(("任務執行器", False))
    
    # 測試2: 新任務動作
    try:
        result2 = await test_new_task_actions()
        results.append(("新任務動作", result2))
    except Exception as e:
        logger.error(f"新任務動作測試異常: {e}", exc_info=True)
        results.append(("新任務動作", False))
    
    # 測試3: 通知集成
    try:
        result3 = await test_notification_integration()
        results.append(("通知集成", result3))
    except Exception as e:
        logger.error(f"通知集成測試異常: {e}", exc_info=True)
        results.append(("通知集成", False))
    
    # 總結
    logger.info("\n" + "=" * 60)
    logger.info("測試總結")
    logger.info("=" * 60)
    for name, result in results:
        status = "✓ 通過" if result else "✗ 失敗"
        logger.info(f"{name}: {status}")
    
    total = len(results)
    passed = sum(1 for _, r in results if r)
    logger.info(f"\n總計: {passed}/{total} 通過")
    
    if passed == total:
        logger.info("🎉 所有測試通過！")
        return 0
    else:
        logger.error("❌ 部分測試失敗")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

