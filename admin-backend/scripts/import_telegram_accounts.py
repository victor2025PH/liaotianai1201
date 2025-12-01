"""
批量導入 Telegram 賬號配置

支持從 TXT 或 Excel 文件導入多個 Telegram 賬號配置。

TXT 格式（每行一個賬號）:
  API_ID|API_HASH|SESSION_NAME
  或
  API_ID,API_HASH,SESSION_NAME

Excel 格式:
  列名: API_ID, API_HASH, SESSION_NAME
"""
import sys
from pathlib import Path
import csv
from typing import List, Dict, Optional
import logging

# 添加項目根目錄到路徑
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

try:
    import openpyxl
    EXCEL_SUPPORT = True
except ImportError:
    EXCEL_SUPPORT = False
    logging.warning("openpyxl 未安裝，不支持 Excel 文件。使用: pip install openpyxl")

from sqlalchemy.orm import Session
from app.db import SessionLocal
from app.models.group_ai import GroupAIAccount

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def parse_txt_file(file_path: Path) -> List[Dict[str, str]]:
    """解析 TXT 文件"""
    accounts = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            # 支持 | 或 , 分隔符
            if '|' in line:
                parts = [p.strip() for p in line.split('|')]
            elif ',' in line:
                parts = [p.strip() for p in line.split(',')]
            else:
                logger.warning(f"第 {line_num} 行格式錯誤，跳過: {line}")
                continue
            
            if len(parts) != 3:
                logger.warning(f"第 {line_num} 行格式錯誤（需要3個字段），跳過: {line}")
                continue
            
            accounts.append({
                'api_id': parts[0],
                'api_hash': parts[1],
                'session_name': parts[2]
            })
    
    return accounts


def parse_excel_file(file_path: Path) -> List[Dict[str, str]]:
    """解析 Excel 文件"""
    if not EXCEL_SUPPORT:
        raise ImportError("openpyxl 未安裝，無法讀取 Excel 文件")
    
    accounts = []
    workbook = openpyxl.load_workbook(file_path)
    sheet = workbook.active
    
    # 讀取表頭
    headers = [cell.value for cell in sheet[1]]
    
    # 查找列索引
    try:
        api_id_idx = headers.index('API_ID')
        api_hash_idx = headers.index('API_HASH')
        session_name_idx = headers.index('SESSION_NAME')
    except ValueError as e:
        raise ValueError(f"Excel 文件缺少必需的列: {e}")
    
    # 讀取數據
    for row_num, row in enumerate(sheet.iter_rows(min_row=2, values_only=True), 2):
        if not any(row):  # 跳過空行
            continue
        
        api_id = str(row[api_id_idx]).strip() if row[api_id_idx] else None
        api_hash = str(row[api_hash_idx]).strip() if row[api_hash_idx] else None
        session_name = str(row[session_name_idx]).strip() if row[session_name_idx] else None
        
        if not all([api_id, api_hash, session_name]):
            logger.warning(f"第 {row_num} 行數據不完整，跳過")
            continue
        
        accounts.append({
            'api_id': api_id,
            'api_hash': api_hash,
            'session_name': session_name
        })
    
    return accounts


def save_accounts_to_db(accounts: List[Dict[str, str]], db: Session) -> int:
    """將賬號配置保存到數據庫"""
    saved_count = 0
    
    for account_data in accounts:
        # 檢查是否已存在（根據 session_name）
        existing = db.query(GroupAIAccount).filter(
            GroupAIAccount.phone_number == account_data['session_name']
        ).first()
        
        if existing:
            # 更新現有賬號的配置
            if not existing.config:
                existing.config = {}
            existing.config['telegram_api_id'] = account_data['api_id']
            existing.config['telegram_api_hash'] = account_data['api_hash']
            existing.config['telegram_session_name'] = account_data['session_name']
            logger.info(f"更新賬號配置: {account_data['session_name']}")
        else:
            # 創建新賬號記錄（僅配置，不啟動）
            new_account = GroupAIAccount(
                account_id=account_data['session_name'],  # 使用 session_name 作為 account_id
                phone_number=account_data['session_name'],
                name=account_data['session_name'],
                active=False,
                config={
                    'telegram_api_id': account_data['api_id'],
                    'telegram_api_hash': account_data['api_hash'],
                    'telegram_session_name': account_data['session_name']
                }
            )
            db.add(new_account)
            logger.info(f"創建新賬號配置: {account_data['session_name']}")
        
        saved_count += 1
    
    db.commit()
    return saved_count


def import_accounts(file_path: str, format: Optional[str] = None):
    """導入賬號配置"""
    file_path = Path(file_path)
    
    if not file_path.exists():
        raise FileNotFoundError(f"文件不存在: {file_path}")
    
    # 自動檢測格式
    if format is None:
        if file_path.suffix.lower() == '.xlsx' or file_path.suffix.lower() == '.xls':
            format = 'excel'
        else:
            format = 'txt'
    
    logger.info(f"讀取 {format.upper()} 文件: {file_path}")
    
    # 解析文件
    if format == 'excel':
        accounts = parse_excel_file(file_path)
    else:
        accounts = parse_txt_file(file_path)
    
    if not accounts:
        logger.warning("未找到任何賬號配置")
        return
    
    logger.info(f"找到 {len(accounts)} 個賬號配置")
    
    # 保存到數據庫
    db = SessionLocal()
    try:
        saved_count = save_accounts_to_db(accounts, db)
        logger.info(f"✅ 成功導入 {saved_count} 個賬號配置")
    except Exception as e:
        db.rollback()
        logger.error(f"❌ 導入失敗: {e}", exc_info=True)
        raise
    finally:
        db.close()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="批量導入 Telegram 賬號配置")
    parser.add_argument("file", help="配置文件路徑（TXT 或 Excel）")
    parser.add_argument("--format", choices=['txt', 'excel'], help="文件格式（自動檢測）")
    
    args = parser.parse_args()
    
    try:
        import_accounts(args.file, args.format)
        print("✅ 導入完成")
    except Exception as e:
        print(f"❌ 導入失敗: {e}")
        sys.exit(1)
