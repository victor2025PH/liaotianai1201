"""
定時告警檢查服務 - 自動定期執行告警規則檢查
"""
import asyncio
import logging
from typing import Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class ScheduledAlertChecker:
    """定時告警檢查服務"""
    
    def __init__(self, interval_seconds: int = 300):
        """
        初始化定時告警檢查服務
        
        Args:
            interval_seconds: 檢查間隔（秒），默認 300 秒（5 分鐘）
        """
        self.interval_seconds = interval_seconds
        self.task: Optional[asyncio.Task] = None
        self.stop_event: Optional[asyncio.Event] = None
        self.is_running = False
    
    async def _check_alerts(self):
        """執行告警檢查"""
        try:
            # 動態導入，避免循環依賴
            from app.db import SessionLocal
            from app.crud import alert_rule as crud_alert_rule
            
            # 創建數據庫會話
            db = SessionLocal()
            try:
                # 從數據庫讀取啟用的告警規則
                enabled_rules = crud_alert_rule.get_enabled_alert_rules(db)
                
                if not enabled_rules:
                    logger.debug("沒有啟用的告警規則，跳過檢查")
                    return
                
                # 獲取監控服務實例（使用全局實例）
                from app.api.group_ai.monitor import monitor_service
                
                # 執行告警檢查
                new_alerts = monitor_service.check_alerts(alert_rules=enabled_rules)
                
                if new_alerts:
                    logger.info(f"定時告警檢查發現 {len(new_alerts)} 個新告警")
                    
                    # 發送 Telegram 告警通知
                    try:
                        from app.services.telegram_alert_service import get_telegram_alert_service
                        telegram_service = get_telegram_alert_service()
                        
                        if telegram_service.enabled:
                            # 轉換告警格式
                            alert_dicts = []
                            for alert in new_alerts:
                                alert_level = "error" if alert.alert_type == "error" else "warning" if alert.alert_type == "warning" else "info"
                                alert_dicts.append({
                                    "alert_type": alert.alert_type,
                                    "alert_level": alert_level,
                                    "message": alert.message,
                                    "account_id": alert.account_id,
                                    "timestamp": alert.timestamp,
                                })
                            
                            # 批量發送
                            results = await telegram_service.send_batch_alerts(alert_dicts)
                            logger.info(f"Telegram 告警發送完成: 成功 {results['sent']}, 失敗 {results['failed']}, 抑制 {results['suppressed']}")
                    except Exception as e:
                        logger.error(f"發送 Telegram 告警失敗: {e}", exc_info=True)
                    
                    for alert in new_alerts:
                        logger.warning(f"告警: {alert.alert_type} - {alert.message}")
                else:
                    logger.debug(f"定時告警檢查完成，未發現新告警（檢查了 {len(enabled_rules)} 個規則）")
            
            except Exception as e:
                logger.error(f"執行定時告警檢查失敗: {e}", exc_info=True)
            
            finally:
                db.close()
        
        except Exception as e:
            logger.error(f"定時告警檢查服務錯誤: {e}", exc_info=True)
    
    async def _run_periodic(self):
        """週期性執行告警檢查"""
        logger.info(f"定時告警檢查服務已啟動，檢查間隔: {self.interval_seconds} 秒")
        
        # 立即執行一次檢查
        await self._check_alerts()
        
        while not self.stop_event.is_set():
            try:
                # 等待指定的間隔時間
                await asyncio.wait_for(
                    self.stop_event.wait(),
                    timeout=self.interval_seconds
                )
                # 如果 stop_event 被設置，退出循環
                if self.stop_event.is_set():
                    break
            except asyncio.TimeoutError:
                # 超時表示間隔時間到了，執行檢查
                await self._check_alerts()
        
        logger.info("定時告警檢查服務已停止")
    
    def start(self):
        """啟動定時告警檢查服務"""
        if self.is_running:
            logger.warning("定時告警檢查服務已經在運行中")
            return
        
        self.stop_event = asyncio.Event()
        self.task = asyncio.create_task(self._run_periodic())
        self.is_running = True
        logger.info("定時告警檢查服務已啟動")
    
    def stop(self):
        """停止定時告警檢查服務"""
        if not self.is_running:
            logger.warning("定時告警檢查服務未運行")
            return
        
        if self.stop_event:
            self.stop_event.set()
        
        if self.task and not self.task.done():
            self.task.cancel()
            logger.info("定時告警檢查任務已取消")
        
        self.is_running = False
        logger.info("定時告警檢查服務已停止")
    
    async def check_once(self):
        """手動觸發一次告警檢查（不等待間隔）"""
        await self._check_alerts()


# 全局實例（單例模式）
_scheduled_checker: Optional[ScheduledAlertChecker] = None


def get_scheduled_checker() -> ScheduledAlertChecker:
    """獲取定時告警檢查服務實例"""
    global _scheduled_checker
    if _scheduled_checker is None:
        from app.core.config import get_settings
        settings = get_settings()
        # 從環境變量讀取檢查間隔（默認 300 秒 = 5 分鐘）
        interval_seconds = getattr(settings, 'alert_check_interval_seconds', 300)
        _scheduled_checker = ScheduledAlertChecker(interval_seconds=interval_seconds)
    return _scheduled_checker

