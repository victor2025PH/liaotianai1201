"""
群組AI系統日誌API
從遠程服務器和本地服務收集真實日誌
增強：時間範圍過濾、錯誤分析、聚合統計
"""
import logging
import json
import subprocess
from pathlib import Path
from typing import List, Optional, Dict
from datetime import datetime, timedelta
from fastapi import APIRouter, Query, HTTPException, Depends
from pydantic import BaseModel
from collections import Counter, defaultdict

from app.api.deps import get_current_active_user
from app.models.user import User
from app.services.log_aggregator import get_log_aggregator

# 延迟导入以避免循环导入
# from app.api.group_ai.servers import load_server_configs

logger = logging.getLogger(__name__)

router = APIRouter()


class LogEntry(BaseModel):
    """日誌條目"""
    id: str
    level: str  # error, warning, info
    type: str
    message: str
    severity: str  # high, medium, low
    timestamp: datetime
    source: Optional[str] = None


class LogList(BaseModel):
    """日誌列表響應"""
    items: List[LogEntry]
    total: int
    page: int
    page_size: int


class LogStatistics(BaseModel):
    """日誌統計"""
    total_logs: int
    logs_by_level: Dict[str, int]
    logs_by_source: Dict[str, int]
    error_count: int
    warning_count: int
    recent_errors: List[LogEntry]


def get_remote_server_logs(servers_config: dict, lines: int = 100) -> List[dict]:
    """從遠程服務器獲取日誌"""
    all_logs = []
    
    for node_id, config in servers_config.items():
        try:
            host = config.get('host', '')
            user = config.get('user', 'ubuntu')
            password = config.get('password', '')
            deploy_dir = config.get('deploy_dir', '/opt/group-ai')
            log_file = f"{deploy_dir}/logs/worker.log"
            
            # 嘗試使用paramiko
            try:
                import paramiko
                ssh = paramiko.SSHClient()
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                ssh.connect(host, username=user, password=password, timeout=5)
                
                # 使用journalctl獲取systemd服務日誌
                stdin, stdout, stderr = ssh.exec_command(
                    f'sudo journalctl -u group-ai-worker -n {lines} --no-pager 2>&1'
                )
                log_output = stdout.read().decode('utf-8')
                
                if not log_output.strip() or "No entries" in log_output:
                    stdin, stdout, stderr = ssh.exec_command(
                        f'tail -n {lines} {log_file} 2>/dev/null || echo "日誌文件不存在"'
                    )
                    log_output = stdout.read().decode('utf-8')
                
                ssh.close()
                
                # 解析日誌
                import re
                for line in log_output.strip().split('\n'):
                    if line.strip() and "日誌文件不存在" not in line:
                        journal_match = re.match(
                            r'(\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})\s+\S+\s+\S+\[.*?\]:\s*(.+)',
                            line
                        )
                        if journal_match:
                            timestamp_str, message = journal_match.groups()
                            level_match = re.match(r'(\w+):', message)
                            level = level_match.group(1).lower() if level_match else "info"
                            message_clean = re.sub(r'^\w+:', '', message).strip()
                            
                            all_logs.append({
                                "timestamp": timestamp_str.strip(),
                                "level": level,
                                "message": message_clean,
                                "source": f"server_{node_id}",
                                "type": "system",
                            })
            except ImportError:
                logger.warning(f"paramiko未安裝，跳過服務器 {node_id}")
            except Exception as e:
                logger.warning(f"獲取服務器 {node_id} 日誌失敗: {e}")
                continue
        except Exception as e:
            logger.warning(f"處理服務器 {node_id} 配置失敗: {e}")
            continue
    
    return all_logs


def get_local_logs(log_dir: Path = None, lines: int = 100) -> List[dict]:
    """從本地日誌文件獲取日誌"""
    all_logs = []
    
    if log_dir is None:
        possible_dirs = [
            Path.cwd() / "logs",
            Path(__file__).parent.parent.parent.parent.parent / "logs",
            Path(__file__).parent.parent.parent.parent.parent / "group_ai_service" / "logs",
        ]
        for dir_path in possible_dirs:
            if dir_path.exists():
                log_dir = dir_path
                break
    
    if log_dir and log_dir.exists():
        log_files = list(log_dir.glob("*.log")) + list(log_dir.glob("*.txt"))
        
        for log_file in log_files:
            try:
                with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                    file_lines = f.readlines()
                    recent_lines = file_lines[-lines:] if len(file_lines) > lines else file_lines
                    
                    for line in recent_lines:
                        line = line.strip()
                        if not line:
                            continue
                        
                        # 嘗試解析標準日誌格式
                        import re
                        match = re.match(
                            r'(\d{4}-\d{2}-\d{2}[\s\d:]+)\s+(\w+)\s+(.+)',
                            line
                        )
                        if match:
                            timestamp_str, level, message = match.groups()
                            all_logs.append({
                                "timestamp": timestamp_str.strip(),
                                "level": level.lower(),
                                "message": message.strip(),
                                "source": "local",
                                "type": "application",
                            })
                        else:
                            all_logs.append({
                                "timestamp": datetime.now().isoformat(),
                                "level": "info",
                                "message": line,
                                "source": "local",
                                "type": "application",
                            })
            except Exception as e:
                logger.warning(f"讀取日誌文件 {log_file} 失敗: {e}")
                continue
    
    return all_logs


@router.get("/", response_model=LogList, dependencies=[Depends(get_current_active_user)])
async def list_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    level: Optional[str] = Query(None, pattern="^(error|warning|info)$"),
    q: Optional[str] = Query(None, description="搜索關鍵詞"),
    source: Optional[str] = Query(None, description="日誌來源（過濾）"),
    start_time: Optional[str] = Query(None, description="開始時間（ISO 8601格式）"),
    end_time: Optional[str] = Query(None, description="結束時間（ISO 8601格式）"),
    current_user: User = Depends(get_current_active_user),
) -> LogList:
    """獲取系統日誌列表（從遠程服務器和本地服務，支持時間範圍過濾）"""
    try:
        # 1. 從遠程服務器獲取日誌
        from app.api.group_ai.servers import load_server_configs
        servers_config = load_server_configs()
        remote_logs = get_remote_server_logs(servers_config, lines=page_size * 3)
        
        # 2. 從本地日誌文件獲取日誌
        local_logs = get_local_logs(lines=page_size * 2)
        
        # 3. 合併所有日誌
        all_logs = remote_logs + local_logs
        
        # 4. 按時間排序（最新的在前）
        all_logs.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        
        # 5. 過濾級別
        if level:
            all_logs = [log for log in all_logs if log.get("level") == level]
        
        # 5.5. 過濾來源
        if source:
            all_logs = [log for log in all_logs if log.get("source", "").lower() == source.lower()]
        
        # 5.6. 時間範圍過濾
        if start_time or end_time:
            try:
                start_dt = datetime.fromisoformat(start_time.replace("Z", "+00:00")) if start_time else None
                end_dt = datetime.fromisoformat(end_time.replace("Z", "+00:00")) if end_time else None
                
                filtered_logs = []
                for log in all_logs:
                    log_timestamp = log.get("timestamp")
                    if isinstance(log_timestamp, str):
                        try:
                            log_dt = datetime.fromisoformat(log_timestamp.replace("Z", "+00:00"))
                        except:
                            continue
                    elif isinstance(log_timestamp, datetime):
                        log_dt = log_timestamp
                    else:
                        continue
                    
                    if start_dt and log_dt < start_dt:
                        continue
                    if end_dt and log_dt > end_dt:
                        continue
                    
                    filtered_logs.append(log)
                
                all_logs = filtered_logs
            except Exception as e:
                logger.warning(f"時間範圍過濾失敗: {e}")
        
        # 6. 搜索關鍵詞
        if q:
            q_lower = q.lower()
            all_logs = [
                log for log in all_logs
                if q_lower in log.get("message", "").lower()
                or q_lower in log.get("source", "").lower()
                or q_lower in log.get("type", "").lower()
            ]
        
        # 7. 分頁
        total = len(all_logs)
        start = (page - 1) * page_size
        end = start + page_size
        paginated_logs = all_logs[start:end]
        
        # 8. 轉換為LogEntry格式
        log_entries = []
        for idx, log in enumerate(paginated_logs):
            try:
                timestamp_str = log.get("timestamp", "")
                if isinstance(timestamp_str, str):
                    try:
                        timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
                    except:
                        timestamp = datetime.now()
                elif isinstance(timestamp_str, datetime):
                    timestamp = timestamp_str
                else:
                    timestamp = datetime.now()
                
                log_entries.append(LogEntry(
                    id=f"log_{page}_{idx}",
                    level=log.get("level", "info"),
                    type=log.get("type", "system"),
                    message=log.get("message", ""),
                    severity="high" if log.get("level") == "error" else "medium" if log.get("level") == "warning" else "low",
                    timestamp=timestamp,
                    source=log.get("source"),
                ))
            except Exception as e:
                logger.warning(f"轉換日誌條目失敗: {e}")
                continue
        
        # 将日志添加到聚合器（用于后续分析）
        aggregator = get_log_aggregator()
        for log_dict in all_logs:
            try:
                aggregator.add_log(log_dict)
            except Exception as agg_err:
                logger.debug(f"添加日志到聚合器失败: {agg_err}")
        
        return LogList(
            items=log_entries,
            total=total,
            page=page,
            page_size=page_size,
        )
    
    except Exception as e:
        logger.error(f"獲取日誌列表失敗: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"獲取日誌列表失敗: {str(e)}")


@router.get("/statistics", response_model=LogStatistics, dependencies=[Depends(get_current_active_user)])
async def get_log_statistics(
    hours: int = Query(24, ge=1, le=168, description="統計時間範圍（小時）"),
    use_aggregation: bool = Query(True, description="是否使用日誌聚合器"),
    current_user: User = Depends(get_current_active_user),
) -> LogStatistics:
    """獲取日誌統計信息（錯誤分析、聚合統計）"""
    try:
        # 优先使用聚合器
        if use_aggregation:
            aggregator = get_log_aggregator()
            stats = aggregator.get_statistics()
            
            # 转换recent_errors为LogEntry格式
            recent_errors = []
            for idx, error_log in enumerate(stats.get("recent_errors", [])[:10]):
                try:
                    timestamp = error_log.get("timestamp")
                    if isinstance(timestamp, str):
                        timestamp = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                    elif not isinstance(timestamp, datetime):
                        timestamp = datetime.now()
                    
                    recent_errors.append(LogEntry(
                        id=f"error_{idx}",
                        level=error_log.get("level", "error"),
                        type=error_log.get("type", "application"),
                        message=error_log.get("message", ""),
                        severity="high",
                        timestamp=timestamp,
                        source=error_log.get("source")
                    ))
                except Exception as e:
                    logger.debug(f"转换错误日志失败: {e}")
                    continue
            
            return LogStatistics(
                total_logs=stats.get("total_logs", 0),
                logs_by_level=stats.get("logs_by_level", {}),
                logs_by_source=stats.get("logs_by_source", {}),
                logs_by_type=stats.get("logs_by_type", {}),
                error_count=stats.get("error_count", 0),
                warning_count=stats.get("warning_count", 0),
                info_count=stats.get("info_count", 0),
                top_error_patterns=stats.get("top_error_patterns", {}),
                recent_errors=recent_errors,
                buffer_size=stats.get("buffer_size", 0)
            )
        
        # 回退到原始方法
        from app.api.group_ai.servers import load_server_configs
        servers_config = load_server_configs()
        
        # 獲取指定時間範圍內的日誌
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours)
        
        remote_logs = get_remote_server_logs(servers_config, lines=1000)
        local_logs = get_local_logs(lines=1000)
        all_logs = remote_logs + local_logs
        
        # 時間範圍過濾
        filtered_logs = []
        for log in all_logs:
            log_timestamp = log.get("timestamp")
            if isinstance(log_timestamp, str):
                try:
                    log_dt = datetime.fromisoformat(log_timestamp.replace("Z", "+00:00"))
                except:
                    continue
            elif isinstance(log_timestamp, datetime):
                log_dt = log_timestamp
            else:
                continue
            
            if log_dt >= start_time and log_dt <= end_time:
                filtered_logs.append(log)
        
        # 統計
        logs_by_level = Counter(log.get("level", "info") for log in filtered_logs)
        logs_by_source = Counter(log.get("source", "unknown") for log in filtered_logs)
        
        # 獲取最近的錯誤
        error_logs = [log for log in filtered_logs if log.get("level") == "error"]
        error_logs.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        
        recent_errors = []
        for idx, log in enumerate(error_logs[:10]):
            try:
                timestamp_str = log.get("timestamp", "")
                if isinstance(timestamp_str, str):
                    timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
                elif isinstance(timestamp_str, datetime):
                    timestamp = timestamp_str
                else:
                    timestamp = datetime.now()
                
                recent_errors.append(LogEntry(
                    id=f"error_{idx}",
                    level="error",
                    type=log.get("type", "system"),
                    message=log.get("message", ""),
                    severity="high",
                    timestamp=timestamp,
                    source=log.get("source"),
                ))
            except:
                continue
        
        return LogStatistics(
            total_logs=len(filtered_logs),
            logs_by_level=dict(logs_by_level),
            logs_by_source=dict(logs_by_source),
            error_count=logs_by_level.get("error", 0),
            warning_count=logs_by_level.get("warning", 0),
            recent_errors=recent_errors,
        )
    
    except Exception as e:
        logger.error(f"獲取日誌統計失敗: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"獲取日誌統計失敗: {str(e)}")
