#!/usr/bin/env python3
"""
Worker 节点完整集成示例
展示如何将 Session 文件管理功能集成到现有的 Worker 节点脚本中
"""

import os
import sys
import time
import json
import logging
import requests
from pathlib import Path
from typing import Dict, Any, List, Optional

# 导入 Session 处理模块
from worker_session_handler import process_command

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 配置
CONFIG = {
    "SERVER_URL": os.getenv("SERVER_URL", "https://aikz.usdt2026.cc"),
    "NODE_ID": os.getenv("NODE_ID", "PC-001"),
    "HEARTBEAT_INTERVAL": int(os.getenv("HEARTBEAT_INTERVAL", "30")),  # 心跳间隔（秒）
    "SESSIONS_DIR": os.getenv("SESSIONS_DIR", "/sessions"),
    "API_TOKEN": os.getenv("API_TOKEN", ""),  # 如果需要认证
}


class WorkerNode:
    """Worker 节点主类"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.server_url = config["SERVER_URL"]
        self.node_id = config["NODE_ID"]
        self.heartbeat_interval = config["HEARTBEAT_INTERVAL"]
        self.running = False
        
        # 会话信息（示例）
        self.accounts = []
        self.status = "online"
    
    def get_pending_commands(self) -> List[Dict[str, Any]]:
        """获取待执行的命令"""
        try:
            url = f"{self.server_url}/api/v1/workers/{self.node_id}/commands"
            headers = {}
            if self.config.get("API_TOKEN"):
                headers["Authorization"] = f"Bearer {self.config['API_TOKEN']}"
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.ok:
                data = response.json()
                return data.get("commands", [])
            else:
                logger.warning(f"获取命令失败: HTTP {response.status_code}")
                return []
        
        except Exception as e:
            logger.error(f"获取命令异常: {e}", exc_info=True)
            return []
    
    def send_heartbeat(self, command_responses: Optional[Dict[str, Any]] = None) -> bool:
        """发送心跳到服务器"""
        try:
            url = f"{self.server_url}/api/v1/workers/heartbeat"
            headers = {"Content-Type": "application/json"}
            if self.config.get("API_TOKEN"):
                headers["Authorization"] = f"Bearer {self.config['API_TOKEN']}"
            
            heartbeat_data = {
                "node_id": self.node_id,
                "status": self.status,
                "account_count": len(self.accounts),
                "accounts": self.accounts,
                "command_responses": command_responses
            }
            
            response = requests.post(url, json=heartbeat_data, headers=headers, timeout=10)
            
            if response.ok:
                logger.debug(f"心跳成功: {self.node_id}")
                return True
            else:
                logger.warning(f"心跳失败: HTTP {response.status_code}")
                return False
        
        except Exception as e:
            logger.error(f"发送心跳异常: {e}", exc_info=True)
            return False
    
    def process_commands(self, commands: List[Dict[str, Any]]) -> Dict[str, Any]:
        """处理命令并返回响应"""
        command_responses = {}
        
        for command in commands:
            try:
                # 使用 worker_session_handler 处理命令
                result = process_command(command)
                command_id = command.get("command_id")
                
                if command_id:
                    command_responses[command_id] = result
                    logger.info(f"命令 {command_id} ({command.get('action')}) 处理完成: {result.get('success')}")
            
            except Exception as e:
                logger.error(f"处理命令失败: {e}", exc_info=True)
                command_id = command.get("command_id")
                if command_id:
                    command_responses[command_id] = {
                        "command_id": command_id,
                        "success": False,
                        "error": str(e)
                    }
        
        return command_responses
    
    def heartbeat_loop(self):
        """心跳循环主函数"""
        logger.info(f"Worker 节点启动: {self.node_id}")
        logger.info(f"服务器地址: {self.server_url}")
        logger.info(f"心跳间隔: {self.heartbeat_interval} 秒")
        
        self.running = True
        
        while self.running:
            try:
                # 1. 获取待执行的命令
                commands = self.get_pending_commands()
                
                # 2. 处理命令
                command_responses = {}
                if commands:
                    logger.info(f"收到 {len(commands)} 个待执行命令")
                    command_responses = self.process_commands(commands)
                
                # 3. 发送心跳（包含命令响应）
                self.send_heartbeat(command_responses if command_responses else None)
            
            except KeyboardInterrupt:
                logger.info("收到中断信号，正在停止...")
                self.running = False
                break
            except Exception as e:
                logger.error(f"心跳循环错误: {e}", exc_info=True)
            
            # 等待下次心跳
            if self.running:
                time.sleep(self.heartbeat_interval)
        
        logger.info("Worker 节点已停止")
    
    def stop(self):
        """停止 Worker 节点"""
        self.running = False
        self.status = "offline"
        # 发送最后一次心跳通知服务器节点已离线
        self.send_heartbeat()


def main():
    """主函数"""
    worker = WorkerNode(CONFIG)
    
    try:
        worker.heartbeat_loop()
    except KeyboardInterrupt:
        logger.info("收到中断信号")
        worker.stop()
    except Exception as e:
        logger.error(f"Worker 节点异常退出: {e}", exc_info=True)
        worker.stop()
        sys.exit(1)


if __name__ == "__main__":
    main()

