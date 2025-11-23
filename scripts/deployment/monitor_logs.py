#!/usr/bin/env python3
"""
監控所有服務器的運行日誌
"""

import sys
import subprocess
import time
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent))

from master_controller import MasterController


class LogMonitor:
    """日誌監控器"""
    
    def __init__(self):
        self.controller = MasterController()
        self.errors: Dict[str, List[Dict]] = defaultdict(list)
        self.last_positions: Dict[str, int] = {}
    
    def monitor_all_servers(self, duration: int = 300):
        """監控所有服務器日誌"""
        print("=" * 60)
        print("開始監控服務器日誌")
        print("=" * 60)
        print()
        
        if not self.controller.servers:
            print("沒有已配置的服務器")
            return
        
        start_time = time.time()
        
        try:
            while time.time() - start_time < duration:
                for node_id, config in self.controller.servers.items():
                    self._check_server_logs(node_id, config)
                time.sleep(10)  # 每10秒檢查一次
        except KeyboardInterrupt:
            print("\n監控已停止")
        
        # 顯示錯誤摘要
        self._show_error_summary()
    
    def _check_server_logs(self, node_id: str, config):
        """檢查單個服務器的日誌"""
        log_file = f"{config.deploy_dir}/logs/worker.log"
        
        # 使用SSH讀取日誌
        cmd = [
            'sshpass', '-p', config.password,
            'ssh', '-o', 'StrictHostKeyChecking=accept-new',
            f'{config.user}@{config.host}',
            f'tail -n 50 {log_file} 2>/dev/null || echo "日誌文件不存在或無法讀取"'
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                self._analyze_logs(node_id, lines)
        except Exception as e:
            print(f"[WARN] {node_id}: 無法讀取日誌: {e}")
    
    def _analyze_logs(self, node_id: str, lines: List[str]):
        """分析日誌，提取錯誤信息"""
        error_patterns = [
            (r'ERROR|Error|error', 'ERROR'),
            (r'Exception|Traceback', 'EXCEPTION'),
            (r'Failed|失敗', 'FAILED'),
            (r'Connection.*refused|連接.*拒絕', 'CONNECTION_ERROR'),
            (r'Timeout|超時', 'TIMEOUT'),
            (r'Permission.*denied|權限.*拒絕', 'PERMISSION_ERROR'),
        ]
        
        for line in lines:
            for pattern, error_type in error_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    error_info = {
                        'timestamp': datetime.now().isoformat(),
                        'type': error_type,
                        'message': line.strip(),
                        'node_id': node_id
                    }
                    self.errors[node_id].append(error_info)
                    print(f"[ERROR] {node_id}: {line.strip()}")
                    break
    
    def _show_error_summary(self):
        """顯示錯誤摘要"""
        if not self.errors:
            print("\n[OK] 未發現錯誤")
            return
        
        print("\n" + "=" * 60)
        print("錯誤摘要")
        print("=" * 60)
        
        for node_id, error_list in self.errors.items():
            print(f"\n{node_id}:")
            error_types = defaultdict(int)
            for error in error_list:
                error_types[error['type']] += 1
            
            for error_type, count in error_types.items():
                print(f"  {error_type}: {count} 次")
            
            # 顯示最近的錯誤
            print("  最近的錯誤:")
            for error in error_list[-5:]:
                print(f"    [{error['timestamp']}] {error['message'][:100]}")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='監控服務器日誌')
    parser.add_argument('--duration', type=int, default=300, help='監控時長（秒）')
    
    args = parser.parse_args()
    
    monitor = LogMonitor()
    monitor.monitor_all_servers(args.duration)


if __name__ == '__main__':
    main()

