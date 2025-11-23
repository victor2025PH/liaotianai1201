"""
账号管理和去重功能
扫描服务器账号、去重验证、删除重复账号、显示现有账号
"""
import logging
import paramiko
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Set
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_active_user
from app.models.user import User
from app.models.group_ai import GroupAIAccount
from app.middleware.permission import check_permission
from app.core.permissions import PermissionCode
from app.api.group_ai.session_uploader import SessionUploader, ServerNode

logger = logging.getLogger(__name__)

router = APIRouter(tags=["account-management"])


class ServerAccountInfo(BaseModel):
    """服务器账号信息"""
    account_id: str
    session_file: str
    server_id: str
    file_size: int
    modified_time: Optional[str] = None


class AccountComparisonResult(BaseModel):
    """账号对比结果"""
    account_id: str
    in_local: bool
    in_server: bool
    local_info: Optional[Dict] = None
    server_info: Optional[Dict] = None
    is_duplicate: bool = False


class ScanServerAccountsResponse(BaseModel):
    """扫描服务器账号响应"""
    server_id: str
    accounts: List[ServerAccountInfo]
    total_count: int


class CompareAccountsResponse(BaseModel):
    """账号对比响应"""
    local_count: int
    server_count: int
    duplicate_count: int
    comparisons: List[AccountComparisonResult]


class DeleteServerAccountRequest(BaseModel):
    """删除服务器账号请求"""
    server_id: str
    account_id: str
    confirm: bool = False


def extract_account_id_from_filename(filename: str, db: Optional[Session] = None) -> Optional[str]:
    """
    从session文件名中提取账号ID
    
    支持格式:
    - 639277356598.session
    - 639277356598.session.encrypted
    - /path/to/639277356598.session
    - session.session (如果数据库中有对应记录，则从数据库查询)
    """
    # 移除路径和扩展名
    name = Path(filename).stem
    # 如果还有.encrypted等后缀，再移除一次
    if '.' in name:
        name = name.split('.')[0]
    
    # 验证是否为纯数字（Telegram账号ID通常是数字）
    if name.isdigit():
        return name
    
    # 如果文件名不是纯数字（如 session.session），尝试从数据库查询
    if db and name != "session":
        # 尝试通过session_file路径查找对应的account_id
        account = db.query(GroupAIAccount).filter(
            GroupAIAccount.session_file.like(f"%{filename}%")
        ).first()
        if account:
            return account.account_id
    
    # 如果文件名是 "session"，尝试查找该服务器上的账号
    if db and name == "session":
        # 从文件路径中提取服务器信息（如果可能）
        # 或者返回文件名本身作为临时账号ID
        # 这里我们返回 None，让调用者决定如何处理
        pass
    
    # 如果无法提取，返回文件名（去掉扩展名）作为临时账号ID
    # 这样至少可以显示文件存在
    if name and name != "session":
        return name
    
    return None


def scan_server_accounts(server_node: ServerNode, db: Optional[Session] = None) -> List[ServerAccountInfo]:
    """
    扫描服务器上的账号文件
    
    Args:
        server_node: 服务器节点信息
        
    Returns:
        账号信息列表
    """
    accounts = []
    
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(
            server_node.host,
            username=server_node.user,
            password=server_node.password,
            timeout=10
        )
        
        try:
            # 扫描sessions目录
            remote_sessions_dir = f"{server_node.deploy_dir}/sessions"
            logger.info(f"扫描服务器 {server_node.node_id} 的账号目录: {remote_sessions_dir}")
            
            # 首先检查目录是否存在
            stdin, stdout, stderr = ssh.exec_command(f'test -d "{remote_sessions_dir}" && echo "exists" || echo "not_exists"')
            dir_check = stdout.read().decode().strip()
            logger.info(f"目录检查结果: {dir_check}")
            
            if "not_exists" in dir_check:
                # 尝试查找sessions目录可能的位置
                logger.warning(f"目录 {remote_sessions_dir} 不存在，尝试查找sessions目录...")
                stdin, stdout, stderr = ssh.exec_command(f'find {server_node.deploy_dir} -type d -name "sessions" 2>/dev/null | head -5')
                alt_dirs = stdout.read().decode().strip().split('\n')
                alt_dirs = [d.strip() for d in alt_dirs if d.strip()]
                if alt_dirs:
                    logger.info(f"找到可能的sessions目录: {alt_dirs}")
                    remote_sessions_dir = alt_dirs[0]
                else:
                    # 尝试列出deploy_dir下的所有目录
                    stdin, stdout, stderr = ssh.exec_command(f'ls -d {server_node.deploy_dir}/*/ 2>/dev/null | head -10')
                    all_dirs = stdout.read().decode().strip().split('\n')
                    logger.info(f"{server_node.deploy_dir} 下的目录: {all_dirs}")
            
            # 查找所有.session文件（使用多种方法确保找到文件）
            # 方法1: 使用find命令（递归查找）
            stdin, stdout, stderr = ssh.exec_command(
                f'find {remote_sessions_dir} -name "*.session" -type f 2>/dev/null'
            )
            find_output = stdout.read().decode().strip()
            find_error = stderr.read().decode().strip()
            if find_error:
                logger.warning(f"find命令错误: {find_error}")
            find_files = find_output.split('\n') if find_output else []
            find_files = [f.strip() for f in find_files if f.strip()]
            
            # 方法2: 使用ls命令（直接列出）
            stdin, stdout, stderr = ssh.exec_command(
                f'ls -1 {remote_sessions_dir}/*.session 2>/dev/null'
            )
            ls_output = stdout.read().decode().strip()
            ls_error = stderr.read().decode().strip()
            if ls_error and "No such file" not in ls_error:
                logger.warning(f"ls命令错误: {ls_error}")
            ls_files = ls_output.split('\n') if ls_output else []
            ls_files = [f.strip() for f in ls_files if f.strip()]
            
            # 方法3: 使用ls命令列出目录内容（调试用）
            stdin, stdout, stderr = ssh.exec_command(
                f'ls -la {remote_sessions_dir}/ 2>/dev/null | head -20'
            )
            dir_listing = stdout.read().decode().strip()
            if dir_listing:
                logger.info(f"目录 {remote_sessions_dir} 内容:\n{dir_listing}")
            
            # 合并两种方法的结果，去重
            all_files = list(set(find_files + ls_files))
            logger.info(f"服务器 {server_node.node_id} 找到 {len(all_files)} 个session文件: {all_files}")
            
            for file_path in all_files:
                if not file_path.strip():
                    continue
                
                # 获取文件信息
                stdin, stdout, stderr = ssh.exec_command(
                    f'stat -c "%s %Y" "{file_path}" 2>/dev/null'
                )
                stat_output = stdout.read().decode().strip()
                
                if stat_output:
                    try:
                        size, mtime = stat_output.split()
                        file_size = int(size)
                        modified_time = datetime.fromtimestamp(int(mtime)).isoformat()
                    except Exception as e:
                        logger.warning(f"解析文件 {file_path} 的stat信息失败: {e}")
                        file_size = 0
                        modified_time = None
                else:
                    file_size = 0
                    modified_time = None
                
                # 提取账号ID
                # 首先尝试从文件名提取
                account_id = extract_account_id_from_filename(file_path, db)
                
                # 如果无法提取，尝试从数据库查询（通过session_file路径）
                if not account_id and db:
                    try:
                        account = db.query(GroupAIAccount).filter(
                            GroupAIAccount.session_file.like(f"%{Path(file_path).name}%"),
                            GroupAIAccount.server_id == server_node.node_id
                        ).first()
                        if account:
                            account_id = account.account_id
                            logger.info(f"从数据库找到账号ID: {account_id} (文件: {file_path})")
                    except Exception as e:
                        logger.warning(f"从数据库查询账号ID失败: {e}")
                
                # 如果仍然无法提取，使用文件名（去掉扩展名）作为临时账号ID
                if not account_id:
                    name = Path(file_path).stem
                    # 如果文件名是 "session"，使用完整路径的hash作为临时ID
                    if name == "session":
                        import hashlib
                        account_id = f"temp_{hashlib.md5(file_path.encode()).hexdigest()[:8]}"
                        logger.warning(f"无法提取账号ID，使用临时ID: {account_id} (文件: {file_path})")
                    else:
                        account_id = name
                        logger.warning(f"无法提取账号ID，使用文件名: {account_id} (文件: {file_path})")
                
                # 添加账号信息
                accounts.append(ServerAccountInfo(
                    account_id=account_id,
                    session_file=file_path,
                    server_id=server_node.node_id,
                    file_size=file_size,
                    modified_time=modified_time
                ))
                logger.debug(f"找到账号: {account_id} ({file_path})")
        
        finally:
            ssh.close()
        
        logger.info(f"服务器 {server_node.node_id} 扫描完成，找到 {len(accounts)} 个账号")
        return accounts
    
    except paramiko.AuthenticationException as e:
        logger.error(f"扫描服务器 {server_node.node_id} SSH认证失败: {e}", exc_info=True)
        logger.warning(f"扫描服务器 {server_node.node_id} SSH认证失败，返回空列表")
        return []
    except paramiko.SSHException as e:
        logger.error(f"扫描服务器 {server_node.node_id} SSH连接失败: {e}", exc_info=True)
        logger.warning(f"扫描服务器 {server_node.node_id} SSH连接失败，返回空列表")
        return []
    except Exception as e:
        logger.error(f"扫描服务器 {server_node.node_id} 账号失败: {type(e).__name__}: {e}", exc_info=True)
        import traceback
        logger.error(f"扫描服务器 {server_node.node_id} 完整堆栈跟踪:\n{traceback.format_exc()}")
        # 不抛出异常，返回空列表，让调用者决定如何处理
        logger.warning(f"扫描服务器 {server_node.node_id} 失败，返回空列表")
        return []


@router.get("/scan-server-accounts", response_model=List[ScanServerAccountsResponse])
async def scan_all_server_accounts(
    server_id: Optional[str] = Query(None, description="指定服务器ID，如果不提供则扫描所有服务器"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    扫描所有服务器上的账号
    
    返回每个服务器上的账号列表
    """
    logger.info(f"API路由: 开始处理扫描请求，server_id={server_id}, user={current_user.email}")
    try:
        check_permission(current_user, PermissionCode.ACCOUNT_VIEW.value, db)
        logger.info(f"API路由: 权限检查通过")
    except Exception as perm_error:
        logger.error(f"API路由: 权限检查失败: {perm_error}", exc_info=True)
        raise
    
    try:
        uploader = SessionUploader()
        results = []
        logger.info(f"API路由: SessionUploader初始化完成，找到 {len(uploader.servers)} 个服务器")
        
        servers_to_scan = []
        if server_id:
            if server_id not in uploader.servers:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"服务器 {server_id} 不存在"
                )
            servers_to_scan = [uploader.servers[server_id]]
        else:
            servers_to_scan = list(uploader.servers.values())
        
        for server_node in servers_to_scan:
            try:
                logger.info(f"API路由: 开始扫描服务器 {server_node.node_id} (host: {server_node.host}, deploy_dir: {server_node.deploy_dir})")
                logger.info(f"API路由: 数据库会话状态: {db is not None}, {type(db)}")
                # 直接调用同步函数（FastAPI支持在异步函数中调用同步函数）
                # SSH操作是IO密集型，不会阻塞事件循环太久
                # 如果使用 asyncio.to_thread，数据库会话可能在线程间传递有问题
                logger.info(f"API路由: 准备调用 scan_server_accounts({server_node.node_id}, db)")
                accounts = scan_server_accounts(server_node, db)
                logger.info(f"API路由: 服务器 {server_node.node_id} 扫描完成，找到 {len(accounts)} 个账号")
                if accounts:
                    logger.info(f"API路由: 账号列表: {[acc.account_id for acc in accounts]}")
                else:
                    logger.warning(f"API路由: 服务器 {server_node.node_id} 未找到任何账号")
                # 确保accounts是ServerAccountInfo对象列表
                validated_accounts = []
                for acc in accounts:
                    # 确保所有字段都存在且类型正确
                    validated_accounts.append(ServerAccountInfo(
                        account_id=str(acc.account_id),
                        session_file=str(acc.session_file),
                        server_id=str(acc.server_id),
                        file_size=int(acc.file_size) if acc.file_size is not None else 0,
                        modified_time=acc.modified_time if acc.modified_time else None
                    ))
                
                result = ScanServerAccountsResponse(
                    server_id=server_node.node_id,
                    accounts=validated_accounts,
                    total_count=len(validated_accounts)
                )
                results.append(result)
                logger.info(f"API路由: 已添加到results，当前results长度: {len(results)}, 账号数: {len(validated_accounts)}")
            except HTTPException as he:
                # 重新抛出HTTPException
                logger.error(f"API路由: 扫描服务器 {server_node.node_id} 时抛出HTTPException: {he.detail}")
                raise
            except Exception as e:
                # 记录错误但继续处理其他服务器
                logger.error(f"API路由: 扫描服务器 {server_node.node_id} 失败: {type(e).__name__}: {e}", exc_info=True)
                import traceback
                logger.error(f"API路由: 完整堆栈跟踪:\n{traceback.format_exc()}")
                # 返回空结果而不是抛出异常，避免影响其他服务器的扫描
                results.append(ScanServerAccountsResponse(
                    server_id=server_node.node_id,
                    accounts=[],
                    total_count=0
                ))
        
        logger.info(f"API路由: 准备返回 {len(results)} 个服务器的扫描结果")
        for i, result in enumerate(results):
            logger.info(f"API路由: 结果 {i+1}: server_id={result.server_id}, accounts={len(result.accounts)}, total_count={result.total_count}")
            if result.accounts:
                for acc in result.accounts:
                    logger.info(f"API路由:   账号: {acc.account_id}, file: {acc.session_file}")
        
        # 尝试序列化响应，检查是否有问题
        try:
            import json
            from pydantic import json_schema
            # 转换为字典
            result_dicts = [r.model_dump() for r in results]
            logger.info(f"API路由: 响应序列化成功，JSON长度: {len(json.dumps(result_dicts))}")
        except Exception as serial_error:
            logger.error(f"API路由: 响应序列化失败: {serial_error}", exc_info=True)
        
        logger.info(f"API路由: 准备返回 {len(results)} 个结果")
        
        # 直接返回结果，让FastAPI的响应验证来处理
        # 如果响应验证失败，会被ResponseValidationError异常处理器捕获
        # 所有数据已经在添加到results之前进行了验证和类型转换
        return results
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"扫描服务器账号失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"扫描服务器账号失败: {str(e)}"
        )


@router.get("/compare-accounts", response_model=CompareAccountsResponse)
async def compare_local_and_server_accounts(
    server_id: Optional[str] = Query(None, description="指定服务器ID，如果不提供则对比所有服务器"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    对比本地数据库和服务器上的账号，找出重复账号
    
    返回对比结果，包括：
    - 本地账号列表
    - 服务器账号列表
    - 重复账号列表
    """
    check_permission(current_user, PermissionCode.ACCOUNT_VIEW.value, db)
    
    try:
        # 1. 获取本地账号
        local_accounts = db.query(GroupAIAccount).all()
        local_account_ids: Set[str] = {acc.account_id for acc in local_accounts}
        local_account_map: Dict[str, GroupAIAccount] = {
            acc.account_id: acc for acc in local_accounts
        }
        
        # 2. 扫描服务器账号
        uploader = SessionUploader()
        server_account_ids: Set[str] = set()
        server_account_map: Dict[str, Dict] = {}
        
        servers_to_scan = []
        if server_id:
            if server_id not in uploader.servers:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"服务器 {server_id} 不存在"
                )
            servers_to_scan = [uploader.servers[server_id]]
        else:
            servers_to_scan = list(uploader.servers.values())
        
        for server_node in servers_to_scan:
            accounts = scan_server_accounts(server_node, db)
            for acc in accounts:
                server_account_ids.add(acc.account_id)
                if acc.account_id not in server_account_map:
                    server_account_map[acc.account_id] = {
                        "account_id": acc.account_id,
                        "session_file": acc.session_file,
                        "server_id": acc.server_id,
                        "file_size": acc.file_size,
                        "modified_time": acc.modified_time
                    }
        
        # 3. 找出所有账号（本地+服务器）
        all_account_ids = local_account_ids | server_account_ids
        
        # 4. 生成对比结果
        comparisons = []
        duplicate_count = 0
        
        for account_id in all_account_ids:
            in_local = account_id in local_account_ids
            in_server = account_id in server_account_ids
            is_duplicate = in_local and in_server
            
            if is_duplicate:
                duplicate_count += 1
            
            local_info = None
            if in_local:
                local_acc = local_account_map[account_id]
                local_info = {
                    "account_id": local_acc.account_id,
                    "session_file": local_acc.session_file,
                    "server_id": local_acc.server_id,
                    "script_id": local_acc.script_id,
                    "active": local_acc.active
                }
            
            server_info = None
            if in_server:
                server_info = server_account_map[account_id]
            
            comparisons.append(AccountComparisonResult(
                account_id=account_id,
                in_local=in_local,
                in_server=in_server,
                local_info=local_info,
                server_info=server_info,
                is_duplicate=is_duplicate
            ))
        
        return CompareAccountsResponse(
            local_count=len(local_account_ids),
            server_count=len(server_account_ids),
            duplicate_count=duplicate_count,
            comparisons=comparisons
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"对比账号失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"对比账号失败: {str(e)}"
        )


@router.delete("/server-account", status_code=status.HTTP_200_OK)
async def delete_server_account(
    request: DeleteServerAccountRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    删除服务器上的账号文件
    
    需要确认才能删除
    """
    check_permission(current_user, PermissionCode.ACCOUNT_DELETE.value, db)
    
    if not request.confirm:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="需要设置 confirm=true 才能删除账号"
        )
    
    try:
        uploader = SessionUploader()
        
        if request.server_id not in uploader.servers:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"服务器 {request.server_id} 不存在"
            )
        
        server_node = uploader.servers[request.server_id]
        
        # 扫描服务器找到账号文件
        accounts = scan_server_accounts(server_node, db)
        target_account = None
        
        for acc in accounts:
            if acc.account_id == request.account_id:
                target_account = acc
                break
        
        if not target_account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"服务器 {request.server_id} 上未找到账号 {request.account_id}"
            )
        
        # 删除文件
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(
            server_node.host,
            username=server_node.user,
            password=server_node.password,
            timeout=10
        )
        
        try:
            # 删除session文件
            stdin, stdout, stderr = ssh.exec_command(f'rm -f "{target_account.session_file}"')
            exit_status = stdout.channel.recv_exit_status()
            
            if exit_status != 0:
                error_msg = stderr.read().decode()
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"删除文件失败: {error_msg}"
                )
            
            logger.info(f"已删除服务器 {request.server_id} 上的账号 {request.account_id}: {target_account.session_file}")
            
            # 更新数据库记录：如果该账号在数据库中且server_id匹配，则更新server_id为None或删除记录
            try:
                from app.models.group_ai import GroupAIAccount
                db_account = db.query(GroupAIAccount).filter(
                    GroupAIAccount.account_id == request.account_id,
                    GroupAIAccount.server_id == request.server_id
                ).first()
                
                if db_account:
                    # 如果账号的session_file匹配，说明这是从该服务器删除的，更新server_id
                    if db_account.session_file == target_account.session_file:
                        db_account.server_id = None
                        db.commit()
                        logger.info(f"已更新数据库记录：账号 {request.account_id} 的 server_id 已清空")
            except Exception as e:
                logger.warning(f"更新数据库记录失败（不影响删除操作）: {e}")
            
            return {
                "success": True,
                "message": f"已删除服务器 {request.server_id} 上的账号 {request.account_id}",
                "deleted_file": target_account.session_file
            }
        
        finally:
            ssh.close()
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除服务器账号失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除服务器账号失败: {str(e)}"
        )


@router.post("/batch-delete-server-accounts", status_code=status.HTTP_200_OK)
async def batch_delete_server_accounts(
    server_id: str,
    account_ids: List[str],
    confirm: bool = Query(False, description="需要设置为true才能删除"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    批量删除服务器上的账号
    
    需要确认才能删除
    """
    check_permission(current_user, PermissionCode.ACCOUNT_DELETE.value, db)
    
    if not confirm:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="需要设置 confirm=true 才能删除账号"
        )
    
    try:
        uploader = SessionUploader()
        
        if server_id not in uploader.servers:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"服务器 {server_id} 不存在"
            )
        
        server_node = uploader.servers[server_id]
        
        # 扫描服务器找到账号文件
        accounts = scan_server_accounts(server_node, db)
        account_map = {acc.account_id: acc for acc in accounts}
        
        # 找出要删除的账号
        to_delete = []
        not_found = []
        
        for account_id in account_ids:
            if account_id in account_map:
                to_delete.append(account_map[account_id])
            else:
                not_found.append(account_id)
        
        if not to_delete:
            return {
                "success": False,
                "message": "没有找到要删除的账号",
                "not_found": not_found
            }
        
        # 删除文件
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(
            server_node.host,
            username=server_node.user,
            password=server_node.password,
            timeout=10
        )
        
        deleted = []
        failed = []
        
        try:
            for acc in to_delete:
                try:
                    stdin, stdout, stderr = ssh.exec_command(f'rm -f "{acc.session_file}"')
                    exit_status = stdout.channel.recv_exit_status()
                    
                    if exit_status == 0:
                        deleted.append(acc.account_id)
                        logger.info(f"已删除服务器 {server_id} 上的账号 {acc.account_id}: {acc.session_file}")
                    else:
                        error_msg = stderr.read().decode()
                        failed.append({"account_id": acc.account_id, "error": error_msg})
                        logger.error(f"删除账号 {acc.account_id} 失败: {error_msg}")
                
                except Exception as e:
                    failed.append({"account_id": acc.account_id, "error": str(e)})
                    logger.error(f"删除账号 {acc.account_id} 失败: {e}", exc_info=True)
        
        finally:
            ssh.close()
        
        # 更新数据库记录：批量更新已删除账号的server_id
        try:
            from app.models.group_ai import GroupAIAccount
            for account_id in deleted:
                db_account = db.query(GroupAIAccount).filter(
                    GroupAIAccount.account_id == account_id,
                    GroupAIAccount.server_id == server_id
                ).first()
                
                if db_account:
                    # 检查session_file是否匹配（确保是从该服务器删除的）
                    deleted_account = account_map.get(account_id)
                    if deleted_account and db_account.session_file == deleted_account.session_file:
                        db_account.server_id = None
                        logger.debug(f"已更新数据库记录：账号 {account_id} 的 server_id 已清空")
            
            db.commit()
            logger.info(f"已批量更新 {len(deleted)} 个账号的数据库记录")
        except Exception as e:
            logger.warning(f"批量更新数据库记录失败（不影响删除操作）: {e}")
        
        return {
            "success": True,
            "message": f"成功删除 {len(deleted)} 个账号",
            "deleted": deleted,
            "failed": failed,
            "not_found": not_found
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"批量删除服务器账号失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"批量删除服务器账号失败: {str(e)}"
        )


@router.get("/list-all-accounts", status_code=status.HTTP_200_OK)
async def list_all_accounts(
    include_local: bool = Query(True, description="包含本地账号"),
    include_server: bool = Query(True, description="包含服务器账号"),
    server_id: Optional[str] = Query(None, description="指定服务器ID"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    列出所有账号（本地+服务器）
    
    用于显示现有账号，支持过滤
    """
    check_permission(current_user, PermissionCode.ACCOUNT_VIEW.value, db)
    
    result = {
        "local_accounts": [],
        "server_accounts": [],
        "summary": {
            "local_count": 0,
            "server_count": 0,
            "total_count": 0
        }
    }
    
    try:
        # 获取本地账号
        if include_local:
            local_accounts = db.query(GroupAIAccount).all()
            for acc in local_accounts:
                result["local_accounts"].append({
                    "account_id": acc.account_id,
                    "session_file": acc.session_file,
                    "server_id": acc.server_id,
                    "script_id": acc.script_id,
                    "active": acc.active,
                    "display_name": acc.display_name,
                    "username": acc.username,
                    "phone_number": acc.phone_number
                })
            result["summary"]["local_count"] = len(local_accounts)
        
        # 获取服务器账号
        if include_server:
            uploader = SessionUploader()
            servers_to_scan = []
            
            if server_id:
                if server_id not in uploader.servers:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"服务器 {server_id} 不存在"
                    )
                servers_to_scan = [uploader.servers[server_id]]
            else:
                servers_to_scan = list(uploader.servers.values())
            
            for server_node in servers_to_scan:
                accounts = scan_server_accounts(server_node, db)
                for acc in accounts:
                    result["server_accounts"].append({
                        "account_id": acc.account_id,
                        "session_file": acc.session_file,
                        "server_id": acc.server_id,
                        "file_size": acc.file_size,
                        "modified_time": acc.modified_time
                    })
            
            result["summary"]["server_count"] = len(result["server_accounts"])
        
        result["summary"]["total_count"] = result["summary"]["local_count"] + result["summary"]["server_count"]
        
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"列出所有账号失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"列出所有账号失败: {str(e)}"
        )

