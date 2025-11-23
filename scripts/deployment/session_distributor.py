#!/usr/bin/env python3
"""
Session文件智能分配器
根據風控策略自動分配Session文件到不同的服務器
"""

import os
import json
import random
import hashlib
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import sqlite3


@dataclass
class ServerNode:
    """服務器節點信息"""
    node_id: str
    host: str
    port: int = 8000
    max_accounts: int = 5
    current_accounts: int = 0
    location: str = ""  # 地理位置標識
    ip_pool: List[str] = None  # IP池（用於風控）
    status: str = "active"  # active, inactive, maintenance
    
    def __post_init__(self):
        if self.ip_pool is None:
            self.ip_pool = []


@dataclass
class SessionFile:
    """Session文件信息"""
    filename: str
    filepath: str
    account_id: str = ""
    phone_number: str = ""
    assigned_node: str = ""
    assigned_time: str = ""
    risk_level: str = "low"  # low, medium, high
    tags: List[str] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []


class RiskControlStrategy:
    """風控策略"""
    
    @staticmethod
    def calculate_risk_score(session: SessionFile, node: ServerNode, 
                            assignment_history: Dict) -> float:
        """計算分配風險分數（越低越好）"""
        risk = 0.0
        
        # 1. 同IP風險（避免同一IP分配過多帳號）
        if node.host in assignment_history:
            same_ip_count = len(assignment_history[node.host])
            if same_ip_count >= 3:
                risk += 10.0 * (same_ip_count - 2)  # 超過3個帳號風險遞增
        
        # 2. 地理位置分散（優先分配到不同地區）
        if node.location:
            location_count = sum(1 for n in assignment_history.values() 
                                if isinstance(n, dict) and n.get('location') == node.location)
            risk += location_count * 2.0
        
        # 3. 節點負載（優先分配到負載較低的節點）
        load_ratio = node.current_accounts / node.max_accounts if node.max_accounts > 0 else 1.0
        risk += load_ratio * 5.0
        
        # 4. Session風險等級
        risk_multiplier = {"low": 1.0, "medium": 1.5, "high": 2.0}
        risk *= risk_multiplier.get(session.risk_level, 1.0)
        
        # 5. 時間分散（避免同時分配）
        if session.assigned_time:
            # 檢查最近分配的時間
            recent_assignments = [t for t in assignment_history.get('timestamps', []) 
                                if (datetime.now() - datetime.fromisoformat(t)).seconds < 3600]
            risk += len(recent_assignments) * 3.0
        
        return risk
    
    @staticmethod
    def should_assign(session: SessionFile, node: ServerNode, 
                     assignment_history: Dict) -> bool:
        """判斷是否應該分配"""
        # 檢查節點容量
        if node.current_accounts >= node.max_accounts:
            return False
        
        # 檢查節點狀態
        if node.status != "active":
            return False
        
        # 檢查風險分數
        risk_score = RiskControlStrategy.calculate_risk_score(
            session, node, assignment_history
        )
        
        # 風險分數超過閾值則不分配
        return risk_score < 50.0  # 可調整閾值


class SessionDistributor:
    """Session分配器"""
    
    def __init__(self, db_path: str = "data/session_distribution.db"):
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """初始化數據庫"""
        os.makedirs(os.path.dirname(self.db_path) or '.', exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 創建服務器節點表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS server_nodes (
                node_id TEXT PRIMARY KEY,
                host TEXT NOT NULL,
                port INTEGER DEFAULT 8000,
                max_accounts INTEGER DEFAULT 5,
                current_accounts INTEGER DEFAULT 0,
                location TEXT,
                ip_pool TEXT,
                status TEXT DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 創建Session分配表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS session_assignments (
                session_id TEXT PRIMARY KEY,
                filename TEXT NOT NULL,
                account_id TEXT,
                phone_number TEXT,
                assigned_node TEXT NOT NULL,
                assigned_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                risk_level TEXT DEFAULT 'low',
                tags TEXT,
                FOREIGN KEY (assigned_node) REFERENCES server_nodes(node_id)
            )
        """)
        
        # 創建分配歷史表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS assignment_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                node_id TEXT NOT NULL,
                assignment_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                risk_score REAL,
                FOREIGN KEY (session_id) REFERENCES session_assignments(session_id),
                FOREIGN KEY (node_id) REFERENCES server_nodes(node_id)
            )
        """)
        
        conn.commit()
        conn.close()
    
    def register_node(self, node: ServerNode):
        """註冊服務器節點"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO server_nodes 
            (node_id, host, port, max_accounts, current_accounts, location, ip_pool, status, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (
            node.node_id, node.host, node.port, node.max_accounts,
            node.current_accounts, node.location,
            json.dumps(node.ip_pool), node.status
        ))
        
        conn.commit()
        conn.close()
    
    def get_available_nodes(self) -> List[ServerNode]:
        """獲取可用的服務器節點"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT node_id, host, port, max_accounts, current_accounts, 
                   location, ip_pool, status
            FROM server_nodes
            WHERE status = 'active'
            ORDER BY current_accounts ASC
        """)
        
        nodes = []
        for row in cursor.fetchall():
            node = ServerNode(
                node_id=row[0],
                host=row[1],
                port=row[2],
                max_accounts=row[3],
                current_accounts=row[4],
                location=row[5] or "",
                ip_pool=json.loads(row[6]) if row[6] else [],
                status=row[7]
            )
            nodes.append(node)
        
        conn.close()
        return nodes
    
    def scan_sessions(self, sessions_dir: str) -> List[SessionFile]:
        """掃描Session文件"""
        sessions = []
        sessions_path = Path(sessions_dir)
        
        if not sessions_path.exists():
            return sessions
        
        for session_file in sessions_path.glob("*.session"):
            # 嘗試從文件名提取帳號ID和電話號碼
            filename = session_file.stem
            account_id = filename
            phone_number = ""
            
            # 提取電話號碼（如果文件名包含）
            import re
            phone_match = re.search(r'(\d{8,})', filename)
            if phone_match:
                phone_number = phone_match.group(1)
            
            session = SessionFile(
                filename=session_file.name,
                filepath=str(session_file),
                account_id=account_id,
                phone_number=phone_number
            )
            sessions.append(session)
        
        return sessions
    
    def assign_session(self, session: SessionFile, 
                      assignment_history: Dict = None) -> Optional[ServerNode]:
        """分配Session到服務器節點"""
        if assignment_history is None:
            assignment_history = {}
        
        available_nodes = self.get_available_nodes()
        
        if not available_nodes:
            return None
        
        # 計算每個節點的風險分數
        node_scores = []
        for node in available_nodes:
            if RiskControlStrategy.should_assign(session, node, assignment_history):
                risk_score = RiskControlStrategy.calculate_risk_score(
                    session, node, assignment_history
                )
                node_scores.append((risk_score, node))
        
        if not node_scores:
            return None
        
        # 選擇風險分數最低的節點
        node_scores.sort(key=lambda x: x[0])
        selected_node = node_scores[0][1]
        
        # 記錄分配
        self._record_assignment(session, selected_node, node_scores[0][0])
        
        return selected_node
    
    def _record_assignment(self, session: SessionFile, node: ServerNode, risk_score: float):
        """記錄分配信息"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        session_id = hashlib.md5(session.filepath.encode()).hexdigest()
        
        # 更新或插入Session分配
        cursor.execute("""
            INSERT OR REPLACE INTO session_assignments
            (session_id, filename, account_id, phone_number, assigned_node, 
             assigned_time, risk_level, tags)
            VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP, ?, ?)
        """, (
            session_id, session.filename, session.account_id,
            session.phone_number, node.node_id,
            session.risk_level, json.dumps(session.tags)
        ))
        
        # 記錄分配歷史
        cursor.execute("""
            INSERT INTO assignment_history
            (session_id, node_id, assignment_time, risk_score)
            VALUES (?, ?, CURRENT_TIMESTAMP, ?)
        """, (session_id, node.node_id, risk_score))
        
        # 更新節點帳號數
        cursor.execute("""
            UPDATE server_nodes
            SET current_accounts = current_accounts + 1,
                updated_at = CURRENT_TIMESTAMP
            WHERE node_id = ?
        """, (node.node_id,))
        
        conn.commit()
        conn.close()
    
    def distribute_all_sessions(self, sessions_dir: str) -> Dict[str, List[str]]:
        """分配所有Session文件"""
        sessions = self.scan_sessions(sessions_dir)
        assignment_history = {}
        distribution = {}
        
        for session in sessions:
            node = self.assign_session(session, assignment_history)
            if node:
                if node.node_id not in distribution:
                    distribution[node.node_id] = []
                distribution[node.node_id].append(session.filepath)
                
                # 更新分配歷史
                if node.host not in assignment_history:
                    assignment_history[node.host] = []
                assignment_history[node.host].append(session.filename)
        
        return distribution
    
    def get_distribution_report(self) -> Dict:
        """獲取分配報告"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 統計各節點分配情況
        cursor.execute("""
            SELECT 
                n.node_id,
                n.host,
                n.max_accounts,
                n.current_accounts,
                COUNT(s.session_id) as assigned_sessions
            FROM server_nodes n
            LEFT JOIN session_assignments s ON n.node_id = s.assigned_node
            WHERE n.status = 'active'
            GROUP BY n.node_id
        """)
        
        nodes_stats = []
        for row in cursor.fetchall():
            nodes_stats.append({
                "node_id": row[0],
                "host": row[1],
                "max_accounts": row[2],
                "current_accounts": row[3],
                "assigned_sessions": row[4],
                "load_percentage": (row[3] / row[2] * 100) if row[2] > 0 else 0
            })
        
        # 統計總體情況
        cursor.execute("SELECT COUNT(*) FROM session_assignments")
        total_sessions = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM server_nodes WHERE status = 'active'")
        total_nodes = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            "total_sessions": total_sessions,
            "total_nodes": total_nodes,
            "nodes": nodes_stats,
            "timestamp": datetime.now().isoformat()
        }


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Session文件智能分配器')
    parser.add_argument('--sessions-dir', default='sessions', help='Session文件目錄')
    parser.add_argument('--register-node', help='註冊服務器節點 (格式: node_id,host,port,max_accounts,location)')
    parser.add_argument('--distribute', action='store_true', help='分配所有Session文件')
    parser.add_argument('--report', action='store_true', help='顯示分配報告')
    
    args = parser.parse_args()
    
    distributor = SessionDistributor()
    
    if args.register_node:
        # 註冊節點
        parts = args.register_node.split(',')
        node = ServerNode(
            node_id=parts[0],
            host=parts[1],
            port=int(parts[2]) if len(parts) > 2 else 8000,
            max_accounts=int(parts[3]) if len(parts) > 3 else 5,
            location=parts[4] if len(parts) > 4 else ""
        )
        distributor.register_node(node)
        print(f"✓ 節點 {node.node_id} 已註冊")
    
    if args.distribute:
        # 分配Session
        distribution = distributor.distribute_all_sessions(args.sessions_dir)
        print(f"\n分配完成:")
        for node_id, sessions in distribution.items():
            print(f"  節點 {node_id}: {len(sessions)} 個Session")
            for session in sessions[:3]:  # 只顯示前3個
                print(f"    - {Path(session).name}")
            if len(sessions) > 3:
                print(f"    ... 還有 {len(sessions) - 3} 個")
    
    if args.report:
        # 顯示報告
        report = distributor.get_distribution_report()
        print(f"\n分配報告:")
        print(f"  總Session數: {report['total_sessions']}")
        print(f"  總節點數: {report['total_nodes']}")
        print(f"\n節點詳情:")
        for node in report['nodes']:
            print(f"  {node['node_id']} ({node['host']}):")
            print(f"    已分配: {node['assigned_sessions']}/{node['max_accounts']}")
            print(f"    負載: {node['load_percentage']:.1f}%")


if __name__ == '__main__':
    main()

