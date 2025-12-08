"""
群組AI系統日誌API
從遠程服務器和本地服務收集真實日誌
"""
import logging
import json
import subprocess
from pathlib import Path
from typing import List, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Query, HTTPException, Depends
from pydantic import BaseModel

from app.api.deps import get_current_active_user
from app.models.user import User

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
    metadata: Optional[dict] = None


class LogList(BaseModel):
    """日誌列表"""
    items: List[LogEntry]
    total: int
    page: int
    page_size: int


def get_remote_server_logs(servers_config: dict, lines: int = 100) -> List[dict]:
    """從遠程服務器獲取日誌"""
    all_logs = []
    
    for node_id, config in servers_config.items():
        try:
            import paramiko
            
            host = config.get('host', '')
            user = config.get('user', 'ubuntu')
            password = config.get('password', '')
            
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(host, username=user, password=password, timeout=5)
            
            # 獲取systemd服務日誌
            stdin, stdout, stderr = ssh.exec_command(
                f'sudo journalctl -u group-ai-worker -n {lines} --no-pager 2>&1'
            )
            log_output = stdout.read().decode('utf-8')
            ssh.close()
            
            # 解析日誌
            import re
            for line in log_output.strip().split('\n'):
                if line.strip():
                    # 解析journalctl格式: Nov 16 20:39:55 hostname start.sh[52283]: INFO:__main__:message
                    journal_match = re.match(
                        r'(\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})\s+\S+\s+\S+\[.*?\]:\s*(.+)',
                        line
                    )
                    if journal_match:
                        timestamp_str, message = journal_match.groups()
                        # 提取level
                        level_match = re.match(r'(\w+):', message)
                        level = level_match.group(1) if level_match else "INFO"
                        message_clean = re.sub(r'^\w+:', '', message).strip()
                        
                        # 判斷嚴重性
                        severity = "high" if level in ["ERROR", "CRITICAL"] else "medium" if level in ["WARNING"] else "low"
                        
                        # 判斷類型
                        log_type = "系統錯誤" if level in ["ERROR", "CRITICAL"] else "系統警告" if level == "WARNING" else "系統信息"
                        
                        all_logs.append({
                            "id": f"{node_id}-{len(all_logs)}",
                            "level": level.lower(),
                            "type": log_type,
                            "message": message_clean,
                            "severity": severity,
                            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),  # 簡化時間戳
                            "source": f"{node_id} ({host})",
                            "metadata": {"node_id": node_id, "host": host}
                        })
        except Exception as e:
            logger.warning(f"獲取服務器 {node_id} 日誌失敗: {e}")
            continue
    
    return all_logs


def get_local_logs(log_dir: Path = None, lines: int = 100) -> List[dict]:
    """從本地日誌文件獲取日誌"""
    all_logs = []
    
    if log_dir is None:
        # 嘗試多個可能的日誌目錄
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
        # 查找所有日誌文件
        log_files = list(log_dir.glob("*.log")) + list(log_dir.glob("*.txt"))
        for log_file in log_files[-5:]:  # 只讀取最近5個日誌文件
            try:
                with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                    log_lines = f.readlines()[-lines:]
                    for line in log_lines:
                        if line.strip():
                            # 簡單解析日誌格式: [2024-01-16 20:00:00][INFO][module] message
                            import re
                            match = re.match(r'\[([^\]]+)\]\[(\w+)\]\[([^\]]+)\]\s+(.+)', line)
                            if match:
                                timestamp_str, level, module, message = match.groups()
                                severity = "high" if level in ["ERROR", "CRITICAL"] else "medium" if level == "WARNING" else "low"
                                log_type = "系統錯誤" if level in ["ERROR", "CRITICAL"] else "系統警告" if level == "WARNING" else "系統信息"
                                
                                all_logs.append({
                                    "id": f"local-{len(all_logs)}",
                                    "level": level.lower(),
                                    "type": log_type,
                                    "message": message.strip(),
                                    "severity": severity,
                                    "timestamp": timestamp_str,
                                    "source": f"本地服務 ({module})",
                                    "metadata": {"file": str(log_file.name), "module": module}
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
    current_user: User = Depends(get_current_active_user),
) -> LogList:
    """獲取系統日誌列表（從遠程服務器和本地服務）"""
    try:
        # 1. 從遠程服務器獲取日誌
        # 延迟导入以避免循环导入
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
                # 解析時間戳
                timestamp_str = log.get("timestamp", "")
                if isinstance(timestamp_str, str):
                    # 嘗試多種時間格式
                    try:
                        if " " in timestamp_str:
                            timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
                        else:
                            timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
                    except:
                        timestamp = datetime.now()
                else:
                    timestamp = log.get("timestamp", datetime.now())
                
                log_entries.append(LogEntry(
                    id=log.get("id", f"log-{idx}"),
                    level=log.get("level", "info"),
                    type=log.get("type", "系統信息"),
                    message=log.get("message", ""),
                    severity=log.get("severity", "low"),
                    timestamp=timestamp,
                    source=log.get("source"),
                    metadata=log.get("metadata")
                ))
            except Exception as e:
                logger.warning(f"轉換日誌條目失敗: {e}")
                continue
        
        return LogList(
            items=log_entries,
            total=total,
            page=page,
            page_size=page_size
        )
    
    except Exception as e:
        logger.exception(f"獲取日誌列表失敗: {e}")
        # 返回空列表而不是模擬數據
        return LogList(
            items=[],
            total=0,
            page=page,
            page_size=page_size
        )

