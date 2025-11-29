"""
Worker 节点客户端示例
用于 computer_001 和 computer_002 等 Worker 节点
"""

import requests
import time
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class WorkerClient:
    """Worker 节点客户端"""
    
    def __init__(self, node_id: str, master_url: str = "http://aikz.usdt2026.cc"):
        """
        初始化 Worker 客户端
        
        Args:
            node_id: 节点ID，如 computer_001, computer_002
            master_url: 主节点URL
        """
        self.node_id = node_id
        self.master_url = master_url.rstrip('/')
        self.api_base = f"{self.master_url}/api/v1/workers"
        self.accounts: List[Dict[str, Any]] = []
        self.config: Dict[str, Any] = {
            "chat_interval_min": 30,
            "chat_interval_max": 120,
            "auto_chat_enabled": False,
            "redpacket_enabled": False,
            "redpacket_interval": 300
        }
        self.auto_chat_running = False
        
    def load_accounts(self):
        """从本地加载账号列表（需要根据实际情况实现）"""
        # TODO: 从本地数据库或配置文件加载账号
        # 示例：
        self.accounts = [
            # {
            #     "phone": "+1234567890",
            #     "first_name": "账号1",
            #     "status": "online",
            #     "role_name": "角色1"
            # }
        ]
        logger.info(f"加载了 {len(self.accounts)} 个账号")
    
    def send_heartbeat(self) -> List[Dict[str, Any]]:
        """
        发送心跳到主节点
        
        Returns:
            待执行的命令列表
        """
        try:
            # 准备心跳数据
            heartbeat_data = {
                "node_id": self.node_id,
                "status": "online",
                "account_count": len(self.accounts),
                "accounts": self.accounts,
                "metadata": {
                    "config": self.config,
                    "auto_chat_running": self.auto_chat_running,
                    "timestamp": datetime.now().isoformat()
                }
            }
            
            # 发送心跳
            response = requests.post(
                f"{self.api_base}/heartbeat",
                json=heartbeat_data,
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            
            logger.info(f"心跳发送成功，收到 {len(data.get('pending_commands', []))} 个待执行命令")
            return data.get("pending_commands", [])
            
        except requests.exceptions.RequestException as e:
            logger.error(f"发送心跳失败: {e}")
            return []
        except Exception as e:
            logger.error(f"处理心跳响应失败: {e}", exc_info=True)
            return []
    
    def get_commands(self) -> List[Dict[str, Any]]:
        """获取待执行的命令"""
        try:
            response = requests.get(
                f"{self.api_base}/{self.node_id}/commands",
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            return data.get("commands", [])
        except requests.exceptions.RequestException as e:
            logger.error(f"获取命令失败: {e}")
            return []
        except Exception as e:
            logger.error(f"处理命令响应失败: {e}", exc_info=True)
            return []
    
    def clear_commands(self):
        """清除命令队列"""
        try:
            response = requests.delete(
                f"{self.api_base}/{self.node_id}/commands",
                timeout=10
            )
            response.raise_for_status()
            logger.info("命令队列已清除")
        except requests.exceptions.RequestException as e:
            logger.error(f"清除命令队列失败: {e}")
        except Exception as e:
            logger.error(f"处理清除命令响应失败: {e}", exc_info=True)
    
    def execute_command(self, command: Dict[str, Any]) -> bool:
        """
        执行命令
        
        Args:
            command: 命令字典，包含 action 和 params
            
        Returns:
            是否执行成功
        """
        action = command.get("action")
        params = command.get("params", {})
        
        logger.info(f"执行命令: {action}, 参数: {params}")
        
        try:
            if action == "start_auto_chat":
                return self.start_auto_chat(params)
            elif action == "stop_auto_chat":
                return self.stop_auto_chat()
            elif action == "set_config":
                return self.set_config(params)
            elif action == "create_group":
                return self.create_group(params)
            else:
                logger.warning(f"未知命令: {action}")
                return False
        except Exception as e:
            logger.error(f"执行命令失败: {e}", exc_info=True)
            return False
    
    def start_auto_chat(self, params: Dict[str, Any]) -> bool:
        """启动自动聊天"""
        try:
            group_id = params.get("group_id", 0)
            logger.info(f"启动自动聊天 (group_id: {group_id})")
            
            # TODO: 实现启动自动聊天的逻辑
            # 例如：启动定时任务、设置标志位等
            
            self.auto_chat_running = True
            logger.info("自动聊天已启动")
            return True
        except Exception as e:
            logger.error(f"启动自动聊天失败: {e}", exc_info=True)
            return False
    
    def stop_auto_chat(self) -> bool:
        """停止自动聊天"""
        try:
            logger.info("停止自动聊天")
            
            # TODO: 实现停止自动聊天的逻辑
            # 例如：停止定时任务、清除标志位等
            
            self.auto_chat_running = False
            logger.info("自动聊天已停止")
            return True
        except Exception as e:
            logger.error(f"停止自动聊天失败: {e}", exc_info=True)
            return False
    
    def set_config(self, config: Dict[str, Any]) -> bool:
        """设置配置"""
        try:
            logger.info(f"设置配置: {config}")
            
            # 更新配置
            self.config.update(config)
            
            logger.info(f"配置已更新: {self.config}")
            return True
        except Exception as e:
            logger.error(f"设置配置失败: {e}", exc_info=True)
            return False
    
    def create_group(self, params: Dict[str, Any]) -> bool:
        """创建群组"""
        try:
            creator_phone = params.get("creator_phone")
            title = params.get("title", "AI 自动聊天群组")
            description = params.get("description", "")
            
            logger.info(f"创建群组: {title} (创建者: {creator_phone})")
            
            # TODO: 实现创建群组的逻辑
            # 例如：调用 Telegram API 创建群组
            
            logger.info("群组创建成功")
            return True
        except Exception as e:
            logger.error(f"创建群组失败: {e}", exc_info=True)
            return False
    
    def run(self, heartbeat_interval: int = 30):
        """
        运行 Worker 节点主循环
        
        Args:
            heartbeat_interval: 心跳间隔（秒），默认 30 秒
        """
        logger.info(f"Worker 节点 {self.node_id} 启动...")
        logger.info(f"主节点URL: {self.master_url}")
        logger.info(f"心跳间隔: {heartbeat_interval} 秒")
        
        # 加载账号
        self.load_accounts()
        
        try:
            while True:
                try:
                    # 1. 发送心跳并获取待执行的命令
                    commands = self.send_heartbeat()
                    
                    # 2. 执行收到的命令
                    executed_commands = []
                    for command in commands:
                        if self.execute_command(command):
                            executed_commands.append(command)
                    
                    # 3. 如果执行了命令，清除命令队列
                    if executed_commands:
                        self.clear_commands()
                    
                    # 4. 等待下次心跳
                    time.sleep(heartbeat_interval)
                    
                except KeyboardInterrupt:
                    logger.info("收到停止信号，Worker 节点正在停止...")
                    break
                except Exception as e:
                    logger.error(f"Worker 节点循环错误: {e}", exc_info=True)
                    time.sleep(heartbeat_interval)
                    
        except Exception as e:
            logger.error(f"Worker 节点运行失败: {e}", exc_info=True)
        finally:
            logger.info("Worker 节点已停止")


def main():
    """主函数"""
    import sys
    
    # 从命令行参数获取节点ID
    if len(sys.argv) > 1:
        node_id = sys.argv[1]
    else:
        node_id = "computer_001"  # 默认节点ID
    
    # 从环境变量获取主节点URL
    import os
    master_url = os.getenv("MASTER_URL", "http://aikz.usdt2026.cc")
    
    # 创建并运行 Worker 客户端
    worker = WorkerClient(node_id=node_id, master_url=master_url)
    worker.run()


if __name__ == "__main__":
    main()

