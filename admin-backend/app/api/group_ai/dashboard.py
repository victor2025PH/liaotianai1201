"""
群組AI系統儀表板API
從數據庫和遠程服務器收集真實統計數據
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List
from fastapi import APIRouter
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, case

from app.db import SessionLocal
from app.models.group_ai import GroupAIAccount, GroupAIDialogueHistory, GroupAIMetric
from app.api.group_ai.servers import load_server_configs

logger = logging.getLogger(__name__)

router = APIRouter(tags=["dashboard"])


def get_dashboard_stats() -> Dict[str, Any]:
    """獲取儀表板統計數據（從群組AI系統）- 優化版本：合併查詢減少數據庫往返"""
    db: Session = SessionLocal()
    try:
        # 計算今日開始時間
        now = datetime.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        yesterday_start = today_start - timedelta(days=1)
        
        # 優化查詢 1：一次性獲取今日和昨日的會話統計（使用條件聚合）
        try:
            session_stats = db.query(
                # 今日會話量
                func.sum(case((GroupAIDialogueHistory.timestamp >= today_start, 1), else_=0)).label('today_sessions'),
                # 昨日會話量
                func.sum(case((
                    and_(
                        GroupAIDialogueHistory.timestamp >= yesterday_start,
                        GroupAIDialogueHistory.timestamp < today_start
                    ), 1
                ), else_=0)).label('yesterday_sessions'),
                # 總會話量（用於成功率計算）
                func.count(GroupAIDialogueHistory.id).label('total_sessions'),
                # 今日成功會話量（有回復的）
                func.sum(case((
                    and_(
                        GroupAIDialogueHistory.timestamp >= today_start,
                        GroupAIDialogueHistory.reply_text.isnot(None),
                        GroupAIDialogueHistory.reply_text != ""
                    ), 1
                ), else_=0)).label('today_successful'),
                # 昨日成功會話量
                func.sum(case((
                    and_(
                        GroupAIDialogueHistory.timestamp >= yesterday_start,
                        GroupAIDialogueHistory.timestamp < today_start,
                        GroupAIDialogueHistory.reply_text.isnot(None),
                        GroupAIDialogueHistory.reply_text != ""
                    ), 1
                ), else_=0)).label('yesterday_successful'),
                # 總成功會話量
                func.sum(case((
                    and_(
                        GroupAIDialogueHistory.reply_text.isnot(None),
                        GroupAIDialogueHistory.reply_text != ""
                    ), 1
                ), else_=0)).label('total_successful'),
            ).first()
            
            today_sessions = int(session_stats.today_sessions or 0)
            yesterday_sessions = int(session_stats.yesterday_sessions or 0)
            total_sessions = int(session_stats.total_sessions or 0)
            today_successful = int(session_stats.today_successful or 0)
            yesterday_successful = int(session_stats.yesterday_successful or 0)
            total_successful = int(session_stats.total_successful or 0)
        except Exception as e:
            logger.warning(f"獲取會話統計失敗，使用備用查詢: {e}")
            # 備用查詢（如果條件聚合不支持）
            today_sessions = db.query(func.count(GroupAIDialogueHistory.id)).filter(
                GroupAIDialogueHistory.timestamp >= today_start
            ).scalar() or 0
            yesterday_sessions = db.query(func.count(GroupAIDialogueHistory.id)).filter(
                and_(
                    GroupAIDialogueHistory.timestamp >= yesterday_start,
                    GroupAIDialogueHistory.timestamp < today_start
                )
            ).scalar() or 0
            total_sessions = db.query(func.count(GroupAIDialogueHistory.id)).scalar() or 0
            total_successful = db.query(func.count(GroupAIDialogueHistory.id)).filter(
                GroupAIDialogueHistory.reply_text.isnot(None),
                GroupAIDialogueHistory.reply_text != ""
            ).scalar() or 0
            today_successful = db.query(func.count(GroupAIDialogueHistory.id)).filter(
                and_(
                    GroupAIDialogueHistory.timestamp >= today_start,
                    GroupAIDialogueHistory.reply_text.isnot(None),
                    GroupAIDialogueHistory.reply_text != ""
                )
            ).scalar() or 0
            yesterday_successful = db.query(func.count(GroupAIDialogueHistory.id)).filter(
                and_(
                    GroupAIDialogueHistory.timestamp >= yesterday_start,
                    GroupAIDialogueHistory.timestamp < today_start,
                    GroupAIDialogueHistory.reply_text.isnot(None),
                    GroupAIDialogueHistory.reply_text != ""
                )
            ).scalar() or 0
        
        sessions_change = calculate_change(today_sessions, yesterday_sessions)
        success_rate = (total_successful / total_sessions * 100) if total_sessions > 0 else 0.0
        yesterday_success_rate = (yesterday_successful / yesterday_sessions * 100) if yesterday_sessions > 0 else 0.0
        success_rate_change = calculate_change(success_rate, yesterday_success_rate, is_percentage=True)
        
        # 優化查詢 2：一次性獲取 Token 用量統計
        try:
            token_stats = db.query(
                func.sum(case((
                    and_(
                        GroupAIMetric.metric_type == "token_usage",
                        GroupAIMetric.timestamp >= today_start
                    ), GroupAIMetric.metric_value
                ), else_=0)).label('today_token'),
                func.sum(case((
                    and_(
                        GroupAIMetric.metric_type == "token_usage",
                        GroupAIMetric.timestamp >= yesterday_start,
                        GroupAIMetric.timestamp < today_start
                    ), GroupAIMetric.metric_value
                ), else_=0)).label('yesterday_token'),
            ).first()
            
            token_usage = float(token_stats.today_token or 0)
            yesterday_token = float(token_stats.yesterday_token or 0)
        except Exception as e:
            logger.warning(f"獲取 Token 統計失敗，使用備用查詢: {e}")
            token_usage = db.query(func.sum(GroupAIMetric.metric_value)).filter(
                GroupAIMetric.metric_type == "token_usage",
                GroupAIMetric.timestamp >= today_start
            ).scalar() or 0
            yesterday_token = db.query(func.sum(GroupAIMetric.metric_value)).filter(
                GroupAIMetric.metric_type == "token_usage",
                and_(
                    GroupAIMetric.timestamp >= yesterday_start,
                    GroupAIMetric.timestamp < today_start
                )
            ).scalar() or 0
        
        token_usage_change = calculate_change(token_usage, yesterday_token)
        
        # 優化查詢 3：一次性獲取錯誤數統計
        try:
            error_stats = db.query(
                func.count(case((
                    and_(
                        GroupAIMetric.metric_type == "error",
                        GroupAIMetric.timestamp >= today_start
                    ), GroupAIMetric.id
                ), else_=None)).label('today_errors'),
                func.count(case((
                    and_(
                        GroupAIMetric.metric_type == "error",
                        GroupAIMetric.timestamp >= yesterday_start,
                        GroupAIMetric.timestamp < today_start
                    ), GroupAIMetric.id
                ), else_=None)).label('yesterday_errors'),
            ).first()
            
            error_count = int(error_stats.today_errors or 0)
            yesterday_errors = int(error_stats.yesterday_errors or 0)
        except Exception as e:
            logger.warning(f"獲取錯誤統計失敗，使用備用查詢: {e}")
            error_count = db.query(func.count(GroupAIMetric.id)).filter(
                GroupAIMetric.metric_type == "error",
                GroupAIMetric.timestamp >= today_start
            ).scalar() or 0
            yesterday_errors = db.query(func.count(GroupAIMetric.id)).filter(
                GroupAIMetric.metric_type == "error",
                and_(
                    GroupAIMetric.timestamp >= yesterday_start,
                    GroupAIMetric.timestamp < today_start
                )
            ).scalar() or 0
        
        error_count_change = calculate_change(yesterday_errors, error_count, reverse=True)
        
        # 優化查詢 4：一次性獲取響應時間統計
        try:
            response_time_stats = db.query(
                func.avg(case((
                    and_(
                        GroupAIMetric.metric_type == "response_time",
                        GroupAIMetric.timestamp >= today_start
                    ), GroupAIMetric.metric_value
                ), else_=None)).label('today_avg_response'),
                func.avg(case((
                    and_(
                        GroupAIMetric.metric_type == "response_time",
                        GroupAIMetric.timestamp >= yesterday_start,
                        GroupAIMetric.timestamp < today_start
                    ), GroupAIMetric.metric_value
                ), else_=None)).label('yesterday_avg_response'),
            ).first()
            
            avg_response_time = float(response_time_stats.today_avg_response or 0.0)
            yesterday_avg_response = float(response_time_stats.yesterday_avg_response or 0.0)
        except Exception as e:
            logger.warning(f"獲取響應時間統計失敗，使用備用查詢: {e}")
            avg_response_time = db.query(func.avg(GroupAIMetric.metric_value)).filter(
                GroupAIMetric.metric_type == "response_time",
                GroupAIMetric.timestamp >= today_start
            ).scalar() or 0.0
            yesterday_avg_response = db.query(func.avg(GroupAIMetric.metric_value)).filter(
                GroupAIMetric.metric_type == "response_time",
                and_(
                    GroupAIMetric.timestamp >= yesterday_start,
                    GroupAIMetric.timestamp < today_start
                )
            ).scalar() or 0.0
        
        response_time_change = calculate_change(yesterday_avg_response, avg_response_time, reverse=True, is_time=True)
        
        # 優化查詢 5：一次性獲取活躍用戶統計
        try:
            # 注意：distinct 和條件聚合可能需要特殊處理
            active_users = db.query(func.count(func.distinct(GroupAIDialogueHistory.user_id))).filter(
                GroupAIDialogueHistory.timestamp >= today_start
            ).scalar() or 0
            
            yesterday_active = db.query(func.count(func.distinct(GroupAIDialogueHistory.user_id))).filter(
                and_(
                    GroupAIDialogueHistory.timestamp >= yesterday_start,
                    GroupAIDialogueHistory.timestamp < today_start
                )
            ).scalar() or 0
        except Exception as e:
            logger.warning(f"獲取活躍用戶統計失敗: {e}")
            active_users = 0
            yesterday_active = 0
        
        active_users_change = calculate_change(active_users, yesterday_active)
        
        # 7. 最近會話（最近10條）
        recent_sessions = db.query(GroupAIDialogueHistory).order_by(
            GroupAIDialogueHistory.timestamp.desc()
        ).limit(10).all()
        
        recent_sessions_list = []
        for session in recent_sessions:
            # 計算消息數（簡化：假設每條對話歷史是一條消息）
            messages = 1  # 可以從context_snapshot中獲取更準確的數量
            
            # 判斷狀態（有回復則為completed）
            status = "completed" if session.reply_text else "active"
            
            # 持續時間（簡化）
            duration = "1m 30s"  # 可以從時間戳計算
            
            recent_sessions_list.append({
                "id": session.id,
                "user": f"user_{session.user_id}",
                "messages": messages,
                "status": status,
                "duration": duration,
                "timestamp": session.timestamp.isoformat() if session.timestamp else datetime.now().isoformat(),
                "started_at": session.timestamp.isoformat() if session.timestamp else datetime.now().isoformat(),
            })
        
        # 8. 最近錯誤（從指標表或日誌）
        recent_errors = db.query(GroupAIMetric).filter(
            GroupAIMetric.metric_type == "error"
        ).order_by(GroupAIMetric.timestamp.desc()).limit(5).all()
        
        recent_errors_list = []
        for error in recent_errors:
            # 從extra_data中提取錯誤信息
            extra_data = error.extra_data or {}
            error_type = extra_data.get("type", "系統錯誤")
            error_message = extra_data.get("message", "未知錯誤")
            severity = extra_data.get("severity", "medium")
            
            # 計算時間差
            time_diff = datetime.now() - error.timestamp if error.timestamp else timedelta(0)
            minutes_ago = int(time_diff.total_seconds() / 60)
            
            recent_errors_list.append({
                "id": error.id,
                "type": error_type,
                "message": error_message,
                "severity": severity,
                "timestamp": f"{minutes_ago} 分鐘前" if minutes_ago > 0 else "剛剛",
            })
        
        return {
            "stats": {
                "today_sessions": today_sessions,
                "success_rate": round(success_rate, 1),
                "token_usage": int(token_usage),
                "error_count": error_count,
                "avg_response_time": round(avg_response_time, 1) if avg_response_time > 0 else 0.0,
                "active_users": active_users,
                "sessions_change": sessions_change,
                "success_rate_change": success_rate_change,
                "token_usage_change": token_usage_change,
                "error_count_change": error_count_change,
                "response_time_change": response_time_change,
                "active_users_change": active_users_change,
            },
            "recent_sessions": recent_sessions_list,
            "recent_errors": recent_errors_list,
        }
    except Exception as e:
        logger.exception(f"獲取儀表板統計數據失敗: {e}")
        # 返回空數據而不是模擬數據
        return {
            "stats": {
                "today_sessions": 0,
                "success_rate": 0.0,
                "token_usage": 0,
                "error_count": 0,
                "avg_response_time": 0.0,
                "active_users": 0,
                "sessions_change": "0%",
                "success_rate_change": "0%",
                "token_usage_change": "0%",
                "error_count_change": "0%",
                "response_time_change": "0%",
                "active_users_change": "0%",
            },
            "recent_sessions": [],
            "recent_errors": [],
        }
    finally:
        db.close()


def calculate_change(current: float, previous: float, reverse: bool = False, is_percentage: bool = False, is_time: bool = False) -> str:
    """計算變化百分比或時間差"""
    if previous == 0:
        if current > 0:
            return f"+{current:.1f}{'%' if is_percentage else 's' if is_time else ''}" if not is_percentage else f"+{current:.1f}%"
        return "0%"
    
    if reverse:
        # 對於錯誤數和響應時間，減少是好的
        change = previous - current
        if change > 0:
            if is_time:
                return f"-{change:.1f}s"
            percentage = (change / previous * 100) if not is_percentage else change
            return f"-{percentage:.1f}%"
        elif change < 0:
            if is_time:
                return f"+{abs(change):.1f}s"
            percentage = (abs(change) / previous * 100) if not is_percentage else abs(change)
            return f"+{percentage:.1f}%"
        return "0%"
    else:
        # 對於會話量、成功率等，增加是好的
        change = current - previous
        if change > 0:
            percentage = (change / previous * 100) if not is_percentage else change
            return f"+{percentage:.1f}%"
        elif change < 0:
            percentage = (abs(change) / previous * 100) if not is_percentage else abs(change)
            return f"-{percentage:.1f}%"
        return "0%"


@router.get("/")
async def get_dashboard():
    """獲取儀表板統計數據（從群組AI系統）"""
    return get_dashboard_stats()

