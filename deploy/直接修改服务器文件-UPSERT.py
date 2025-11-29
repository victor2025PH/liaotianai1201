#!/usr/bin/env python3
"""
直接在服务器上修改 accounts.py 文件，添加 UPSERT 功能
通过 SSH 连接到服务器并修改文件
"""
import paramiko
import sys
from pathlib import Path

# 服务器配置
SERVER_IP = "165.154.233.55"
USERNAME = "ubuntu"
# 注意：密码应该从环境变量或配置文件读取，这里仅作示例
PASSWORD = None  # 需要通过 SSH 密钥认证

# 文件路径
REMOTE_FILE = "~/liaotian/admin-backend/app/api/group_ai/accounts.py"

# UPSERT 代码片段（需要替换的部分）
OLD_CODE = """                else:
                    # 尝试从账号信息中获取 server_id（从账号显示信息中的节点信息）
                    logger.warning(f"賬號 {account_id} 不存在，且未提供 server_id。request.server_id={request.server_id}")
                    logger.warning(f"請求完整參數: {request.model_dump()}")
                    
                    # 提供更详细的错误信息，帮助用户理解问题
                    error_detail = f"賬號 {account_id} 不存在。"
                    error_detail += " 請確認: 1) 賬號已在遠程服務器上運行；2) 提供了正確的 server_id（節點ID）；3) 賬號已同步到數據庫。"
                    if not request.server_id:
                        error_detail += f" 當前請求未提供 server_id。"
                    
                    raise HTTPException(
                        status_code=404,
                        detail=error_detail
                    )"""

NEW_CODE = """                else:
                    # UPSERT 模式：如果账号不存在，直接创建新记录
                    logger.info(f"賬號 {account_id} 不存在，使用 UPSERT 模式創建新記錄")
                    logger.info(f"請求參數: {request.model_dump()}")
                    
                    # 確保至少提供了 server_id 才能創建記錄
                    if not request.server_id:
                        logger.warning(f"創建新賬號需要提供 server_id，但請求中未提供")
                        raise HTTPException(
                            status_code=400,
                            detail=f"創建新賬號時必須提供 server_id。請在請求中包含 server_id 字段。"
                        )
                    
                    # 嘗試從遠程服務器掃描獲取更多信息（可選，不影響創建）
                    session_file_path = request.session_file or f"{account_id}.session"
                    
                    # 如果提供了 server_id，嘗試掃描獲取 session_file 信息（可選）
                    try:
                        from app.api.group_ai.account_management import scan_server_accounts, SessionUploader
                        uploader = SessionUploader()
                        
                        if request.server_id in uploader.servers:
                            server_node = uploader.servers[request.server_id]
                            logger.info(f"嘗試掃描服務器 {request.server_id} 獲取賬號信息（可選）")
                            server_accounts = scan_server_accounts(server_node, db)
                            
                            # 嘗試匹配賬號
                            account_id_str = str(account_id).strip()
                            server_account = next(
                                (acc for acc in server_accounts if str(acc.account_id).strip() == account_id_str),
                                None
                            )
                            
                            if server_account:
                                # 如果掃描到，使用掃描到的 session_file
                                session_file_path = request.session_file or server_account.session_file
                                logger.info(f"在服務器上找到賬號，使用 session_file: {session_file_path}")
                            else:
                                logger.info(f"服務器上未掃描到賬號 {account_id}，將使用默認 session_file 創建記錄")
                        else:
                            logger.info(f"服務器 {request.server_id} 不在配置中，將使用默認值創建記錄")
                    except Exception as e:
                        logger.warning(f"掃描服務器時出錯（不影響創建）: {e}，將使用默認值創建記錄")
                    
                    # 使用請求中的字段創建新的數據庫記錄
                    # 必填字段使用請求中的值或默認值
                    db_account = GroupAIAccount(
                        account_id=account_id,
                        session_file=session_file_path,
                        script_id=request.script_id or "",
                        server_id=request.server_id,  # 必須提供
                        group_ids=request.group_ids or [],
                        active=request.active if request.active is not None else True,
                        reply_rate=request.reply_rate or 0.3,
                        redpacket_enabled=request.redpacket_enabled if request.redpacket_enabled is not None else True,
                        redpacket_probability=request.redpacket_probability or 0.5,
                        max_replies_per_hour=request.max_replies_per_hour or 50,
                        min_reply_interval=request.min_reply_interval or 3,
                        display_name=request.display_name
                    )
                    db.add(db_account)
                    db.commit()
                    db.refresh(db_account)
                    logger.info(f"✅ UPSERT: 已創建新賬號 {account_id} 的數據庫記錄（server_id: {request.server_id}, script_id: {request.script_id or ''}）")"""

def modify_remote_file():
    """通过 SSH 修改远程服务器上的文件"""
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        # 连接到服务器（使用密钥认证）
        ssh.connect(SERVER_IP, username=USERNAME, key_filename=None, timeout=10)
        
        # 读取远程文件
        sftp = ssh.open_sftp()
        remote_file_path = REMOTE_FILE.replace("~", "/home/ubuntu")
        
        # 读取文件内容
        with sftp.open(remote_file_path, 'r') as f:
            content = f.read().decode('utf-8')
        
        # 备份文件
        backup_path = f"{remote_file_path}.bak"
        sftp.putfo(io.BytesIO(content.encode('utf-8')), backup_path)
        print(f"✓ 已备份文件到: {backup_path}")
        
        # 替换代码
        if OLD_CODE in content:
            new_content = content.replace(OLD_CODE, NEW_CODE)
            
            # 写入新内容
            with sftp.open(remote_file_path, 'w') as f:
                f.write(new_content.encode('utf-8'))
            
            print(f"✓ 文件已修改: {remote_file_path}")
            return True
        else:
            print("⚠ 未找到需要替换的代码，可能已经修改过")
            return False
            
    except Exception as e:
        print(f"✗ 错误: {e}")
        return False
    finally:
        ssh.close()

if __name__ == "__main__":
    import io
    success = modify_remote_file()
    sys.exit(0 if success else 1)
