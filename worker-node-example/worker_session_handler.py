#!/usr/bin/env python3
"""
Worker 节点 Session 文件处理示例
用于处理来自服务器的 list_sessions 和 upload_session 命令
"""

import os
import base64
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

# 配置
SESSIONS_DIR = Path(os.getenv("SESSIONS_DIR", "/sessions"))  # Session 文件夹路径
MAX_FILE_SIZE = 10 * 1024 * 1024  # 最大文件大小：10MB


def handle_list_sessions_command(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    处理 list_sessions 命令
    
    扫描本地 /sessions 文件夹，返回所有 .session 文件列表
    
    Args:
        params: 命令参数（通常为空）
    
    Returns:
        包含 sessions 列表的响应数据
    """
    try:
        sessions = []
        
        # 确保目录存在
        if not SESSIONS_DIR.exists():
            logger.warning(f"Session 目录不存在: {SESSIONS_DIR}，将创建")
            SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
            return {
                "success": True,
                "data": {
                    "sessions": []
                }
            }
        
        # 扫描所有 .session 文件
        for session_file in SESSIONS_DIR.glob("*.session"):
            try:
                stat = session_file.stat()
                sessions.append({
                    "filename": session_file.name,
                    "size": stat.st_size,
                    "modified_time": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    "path": str(session_file.absolute())
                })
            except Exception as e:
                logger.error(f"读取文件信息失败 {session_file}: {e}")
                continue
        
        logger.info(f"扫描到 {len(sessions)} 个 Session 文件")
        
        return {
            "success": True,
            "data": {
                "sessions": sessions
            }
        }
    
    except Exception as e:
        logger.error(f"处理 list_sessions 命令失败: {e}", exc_info=True)
        return {
            "success": False,
            "error": f"扫描 Session 文件失败: {str(e)}"
        }


def handle_upload_session_command(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    处理 upload_session 命令
    
    接收 base64 编码的文件内容，解码后保存到本地 /sessions 文件夹
    
    Args:
        params: 命令参数，包含：
            - filename: 文件名
            - file_content: base64 编码的文件内容
            - file_size: 文件大小（字节）
    
    Returns:
        包含保存的文件信息的响应数据
    """
    try:
        filename = params.get("filename")
        file_content_b64 = params.get("file_content")
        file_size = params.get("file_size", 0)
        
        if not filename:
            return {
                "success": False,
                "error": "缺少文件名"
            }
        
        if not file_content_b64:
            return {
                "success": False,
                "error": "缺少文件内容"
            }
        
        # 验证文件扩展名
        if not filename.endswith('.session'):
            return {
                "success": False,
                "error": "只支持 .session 文件"
            }
        
        # 验证文件大小
        if file_size > MAX_FILE_SIZE:
            return {
                "success": False,
                "error": f"文件大小超过限制（最大 {MAX_FILE_SIZE / 1024 / 1024}MB）"
            }
        
        # 确保目录存在
        SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
        
        # 解码 base64
        try:
            file_content = base64.b64decode(file_content_b64)
            actual_size = len(file_content)
            
            # 验证实际大小
            if actual_size != file_size:
                logger.warning(f"文件大小不匹配: 声明 {file_size}, 实际 {actual_size}")
            
            if actual_size > MAX_FILE_SIZE:
                return {
                    "success": False,
                    "error": f"文件大小超过限制（最大 {MAX_FILE_SIZE / 1024 / 1024}MB）"
                }
        except Exception as e:
            return {
                "success": False,
                "error": f"解码文件内容失败: {str(e)}"
            }
        
        # 保存文件
        file_path = SESSIONS_DIR / filename
        
        # 如果文件已存在，添加后缀
        counter = 1
        original_path = file_path
        while file_path.exists():
            stem = original_path.stem
            file_path = SESSIONS_DIR / f"{stem}_{counter}.session"
            counter += 1
        
        try:
            with open(file_path, "wb") as f:
                f.write(file_content)
            
            # 设置文件权限（仅所有者可读可写）
            os.chmod(file_path, 0o600)
            
            logger.info(f"Session 文件已保存: {file_path} (大小: {actual_size} bytes)")
            
            return {
                "success": True,
                "data": {
                    "filename": file_path.name,
                    "path": str(file_path.absolute()),
                    "size": actual_size
                }
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"保存文件失败: {str(e)}"
            }
    
    except Exception as e:
        logger.error(f"处理 upload_session 命令失败: {e}", exc_info=True)
        return {
            "success": False,
            "error": f"上传 Session 文件失败: {str(e)}"
        }


def process_command(command: Dict[str, Any]) -> Dict[str, Any]:
    """
    处理命令并返回结果
    
    Args:
        command: 命令字典，包含：
            - action: 命令动作（list_sessions 或 upload_session）
            - params: 命令参数
            - command_id: 命令 ID（用于标识响应）
    
    Returns:
        命令执行结果，包含 command_id
    """
    action = command.get("action")
    params = command.get("params", {})
    command_id = command.get("command_id")
    
    logger.info(f"处理命令: {action} (ID: {command_id})")
    
    # 根据 action 调用相应的处理函数
    if action == "list_sessions":
        result = handle_list_sessions_command(params)
    elif action == "upload_session":
        result = handle_upload_session_command(params)
    else:
        result = {
            "success": False,
            "error": f"未知命令: {action}"
        }
        logger.warning(f"未知命令: {action}")
    
    # 添加 command_id 以便后端识别
    if command_id:
        result["command_id"] = command_id
    
    return result


# ============ 集成示例 ============

def integrate_with_worker_heartbeat():
    """
    集成到 Worker 节点心跳循环的示例代码
    
    在 Worker 节点的心跳循环中，应该：
    1. 获取待执行的命令
    2. 处理命令
    3. 在心跳响应中包含命令执行结果
    """
    import requests
    import time
    
    SERVER_URL = os.getenv("SERVER_URL", "https://aikz.usdt2026.cc")
    NODE_ID = os.getenv("NODE_ID", "PC-001")
    
    while True:
        try:
            # 1. 获取待执行的命令
            commands_response = requests.get(
                f"{SERVER_URL}/api/v1/workers/{NODE_ID}/commands",
                timeout=10
            )
            
            command_responses = {}
            
            if commands_response.ok:
                commands_data = commands_response.json()
                commands = commands_data.get("commands", [])
                
                # 2. 处理每个命令
                for command in commands:
                    result = process_command(command)
                    command_id = command.get("command_id")
                    if command_id:
                        command_responses[command_id] = result
                        logger.info(f"命令 {command_id} 处理完成: {result.get('success')}")
            
            # 3. 发送心跳（包含命令响应）
            heartbeat_data = {
                "node_id": NODE_ID,
                "status": "online",
                "account_count": 0,
                "accounts": [],
                "command_responses": command_responses if command_responses else None
            }
            
            heartbeat_response = requests.post(
                f"{SERVER_URL}/api/v1/workers/heartbeat",
                json=heartbeat_data,
                timeout=10
            )
            
            if heartbeat_response.ok:
                logger.debug(f"心跳成功: {NODE_ID}")
            else:
                logger.warning(f"心跳失败: {heartbeat_response.status_code}")
        
        except Exception as e:
            logger.error(f"心跳循环错误: {e}", exc_info=True)
        
        # 等待 30 秒后再次心跳
        time.sleep(30)


if __name__ == "__main__":
    # 测试代码
    logging.basicConfig(level=logging.INFO)
    
    # 测试 list_sessions
    print("测试 list_sessions 命令...")
    result = handle_list_sessions_command({})
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    # 测试 upload_session（需要提供 base64 编码的文件内容）
    # print("测试 upload_session 命令...")
    # test_params = {
    #     "filename": "test.session",
    #     "file_content": base64.b64encode(b"test content").decode('utf-8'),
    #     "file_size": len(b"test content")
    # }
    # result = handle_upload_session_command(test_params)
    # print(json.dumps(result, indent=2, ensure_ascii=False))

