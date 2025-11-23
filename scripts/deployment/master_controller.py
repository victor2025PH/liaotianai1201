#!/usr/bin/env python3
"""
主節點控制器
統一管理多個工作節點，實現Session文件的智能分配和風控
"""

import os
import json
import subprocess
import time
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import argparse

import sys
from pathlib import Path

# 添加当前目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from session_distributor import SessionDistributor, ServerNode, SessionFile, RiskControlStrategy


@dataclass
class DeploymentConfig:
    """部署配置"""
    host: str
    user: str = "root"
    password: str = ""
    node_id: str = ""
    deploy_dir: str = "/opt/group-ai"
    max_accounts: int = 5
    location: str = ""
    telegram_api_id: str = ""
    telegram_api_hash: str = ""
    openai_api_key: str = ""


class MasterController:
    """主節點控制器"""
    
    def __init__(self, config_file: str = "data/master_config.json"):
        self.config_file = config_file
        self.distributor = SessionDistributor()
        self.servers: Dict[str, DeploymentConfig] = {}
        self._load_config()
    
    def _load_config(self):
        """加載配置"""
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for node_id, config in data.get('servers', {}).items():
                    self.servers[node_id] = DeploymentConfig(**config)
    
    def _save_config(self):
        """保存配置"""
        os.makedirs(os.path.dirname(self.config_file) or '.', exist_ok=True)
        data = {
            'servers': {
                node_id: asdict(config)
                for node_id, config in self.servers.items()
            }
        }
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def add_server(self, config: DeploymentConfig):
        """添加服務器"""
        if not config.node_id:
            config.node_id = f"worker-{config.host.replace('.', '-')}"
        
        self.servers[config.node_id] = config
        self._save_config()
        print(f"[OK] 服務器 {config.node_id} ({config.host}) 已添加到配置")
    
    def deploy_server(self, node_id: str) -> bool:
        """部署單個服務器"""
        if node_id not in self.servers:
            print(f"✗ 服務器 {node_id} 不存在")
            return False
        
        config = self.servers[node_id]
        print(f"\n開始部署服務器: {config.host} (節點ID: {node_id})")
        
        # 調用自動部署腳本
        deploy_script = Path(__file__).parent / "auto_deploy.py"
        cmd = [
            sys.executable,
            str(deploy_script),
            "--host", config.host,
            "--user", config.user,
            "--password", config.password,
            "--node-id", config.node_id,
            "--deploy-dir", config.deploy_dir,
            "--max-accounts", str(config.max_accounts),
            "--telegram-api-id", config.telegram_api_id,
            "--telegram-api-hash", config.telegram_api_hash,
            "--openai-api-key", config.openai_api_key,
        ]
        
        try:
            # 設置環境變量以支持UTF-8編碼
            env = os.environ.copy()
            env['PYTHONIOENCODING'] = 'utf-8'
            env['LC_ALL'] = 'en_US.UTF-8'
            
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                timeout=1800,
                encoding='utf-8',
                errors='replace',
                env=env
            )
            if result.returncode == 0:
                print(f"[OK] 服務器 {node_id} 部署成功")
                
                # 註冊節點到分配器
                node = ServerNode(
                    node_id=config.node_id,
                    host=config.host,
                    port=8000,
                    max_accounts=config.max_accounts,
                    location=config.location
                )
                self.distributor.register_node(node)
                
                return True
            else:
                print(f"[FAIL] 服務器 {node_id} 部署失敗:")
                if result.stdout:
                    print("標準輸出:", result.stdout[-500:])  # 只顯示最後500字符
                if result.stderr:
                    print("錯誤輸出:", result.stderr[-500:])  # 只顯示最後500字符
                return False
        except Exception as e:
            print(f"[FAIL] 部署過程出錯: {e}")
            return False
    
    def deploy_all_servers(self):
        """部署所有服務器"""
        print(f"\n開始部署 {len(self.servers)} 個服務器...")
        
        results = {}
        for node_id in self.servers:
            results[node_id] = self.deploy_server(node_id)
            time.sleep(5)  # 部署間隔
        
        print(f"\n部署完成:")
        for node_id, success in results.items():
            status = "[OK]" if success else "[FAIL]"
            print(f"  {status} {node_id}")
    
    def distribute_sessions(self, sessions_dir: str = "sessions"):
        """分配Session文件到所有服務器"""
        print(f"\n開始分配Session文件...")
        
        # 獲取分配結果
        distribution = self.distributor.distribute_all_sessions(sessions_dir)
        
        if not distribution:
            print("沒有可用的服務器節點")
            return
        
        # 上傳Session文件到對應服務器
        for node_id, session_files in distribution.items():
            if node_id not in self.servers:
                print(f"警告: 節點 {node_id} 不在配置中，跳過")
                continue
            
            config = self.servers[node_id]
            print(f"\n上傳Session文件到 {node_id} ({config.host})...")
            
            for session_file in session_files:
                self._upload_session_file(session_file, config)
        
        # 顯示分配報告
        report = self.distributor.get_distribution_report()
        print(f"\n分配完成:")
        print(f"  總Session數: {report['total_sessions']}")
        for node in report['nodes']:
            print(f"  {node['node_id']}: {node['assigned_sessions']} 個Session")
    
    def _upload_session_file(self, session_file: str, config: DeploymentConfig):
        """上傳Session文件到服務器"""
        # 使用scp上傳（需要配置SSH密鑰或使用sshpass）
        remote_path = f"{config.deploy_dir}/sessions/{Path(session_file).name}"
        
        # 嘗試使用sshpass
        try:
            cmd = [
                'sshpass', '-p', config.password,
                'scp', '-o', 'StrictHostKeyChecking=accept-new',
                session_file,
                f"{config.user}@{config.host}:{remote_path}"
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            if result.returncode == 0:
                print(f"  [OK] {Path(session_file).name}")
            else:
                print(f"  [FAIL] {Path(session_file).name}: {result.stderr}")
        except FileNotFoundError:
            print(f"  [WARN] sshpass未安裝，請手動上傳: {session_file}")
        except Exception as e:
            print(f"  [FAIL] {Path(session_file).name}: {e}")
    
    def show_status(self):
        """顯示所有服務器狀態"""
        report = self.distributor.get_distribution_report()
        
        print(f"\n服務器狀態報告:")
        print(f"{'='*60}")
        print(f"{'節點ID':<20} {'主機':<20} {'已分配':<10} {'負載':<10}")
        print(f"{'-'*60}")
        
        for node in report['nodes']:
            print(f"{node['node_id']:<20} {node['host']:<20} "
                  f"{node['assigned_sessions']}/{node['max_accounts']:<9} "
                  f"{node['load_percentage']:.1f}%")
        
        print(f"{'='*60}")
        print(f"總計: {report['total_sessions']} 個Session, {report['total_nodes']} 個節點")


def main():
    import sys
    
    parser = argparse.ArgumentParser(description='主節點控制器')
    parser.add_argument('--add-server', help='添加服務器 (格式: host,user,password,node_id,max_accounts,location)')
    parser.add_argument('--deploy', help='部署服務器 (節點ID)')
    parser.add_argument('--deploy-all', action='store_true', help='部署所有服務器')
    parser.add_argument('--distribute', action='store_true', help='分配Session文件')
    parser.add_argument('--sessions-dir', default='sessions', help='Session文件目錄')
    parser.add_argument('--status', action='store_true', help='顯示狀態')
    
    args = parser.parse_args()
    
    controller = MasterController()
    
    if args.add_server:
        # 添加服務器
        parts = args.add_server.split(',')
        config = DeploymentConfig(
            host=parts[0],
            user=parts[1] if len(parts) > 1 else "root",
            password=parts[2] if len(parts) > 2 else "",
            node_id=parts[3] if len(parts) > 3 else "",
            max_accounts=int(parts[4]) if len(parts) > 4 else 5,
            location=parts[5] if len(parts) > 5 else ""
        )
        controller.add_server(config)
    
    if args.deploy:
        controller.deploy_server(args.deploy)
    
    if args.deploy_all:
        controller.deploy_all_servers()
    
    if args.distribute:
        controller.distribute_sessions(args.sessions_dir)
    
    if args.status:
        controller.show_status()


if __name__ == '__main__':
    import sys
    main()

