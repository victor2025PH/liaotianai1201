"""
Session 文件导出和跨服务器部署 API
"""
import logging
import zipfile
import tempfile
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Response
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user, get_db
from app.models.user import User
from utils.session_encryption import get_session_manager
from utils.session_permissions import get_session_permission_manager
from utils.session_audit import log_session_access
from app.core.permissions import PermissionCode, check_permission

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/export-session/{session_name}")
async def export_session_file(
    session_name: str,
    include_config: bool = Query(False, description="是否包含配置文件"),
    decrypt: bool = Query(False, description="是否解密后导出（如果已加密）"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    导出 Session 文件（用于跨服务器部署）
    
    Args:
        session_name: Session 文件名（不含扩展名）
        include_config: 是否包含环境变量配置模板
        decrypt: 是否解密后导出（如果已加密）
    """
    check_permission(current_user, PermissionCode.SESSION_DOWNLOAD.value, db)
    
    try:
        from group_ai_service.config import get_group_ai_config
        config = get_group_ai_config()
        sessions_dir = Path(config.session_files_directory)
        
        # 查找 Session 文件（支持加密和明文）
        session_manager = get_session_manager()
        all_sessions = session_manager.list_sessions()
        
        session_file = None
        is_encrypted = False
        
        # 查找匹配的 Session 文件
        for s in all_sessions:
            if s.stem == session_name:
                session_file = s
                is_encrypted = session_manager.encryptor and session_manager.encryptor.is_encrypted_file(s)
                break
        
        if not session_file or not session_file.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session 文件未找到: {session_name}"
            )
        
        # 读取 Session 文件内容
        if is_encrypted:
            if decrypt and session_manager.encryptor:
                # 解密后导出
                encrypted_data = session_file.read_bytes()
                session_data = session_manager.encryptor.decrypt_session(encrypted_data)
                file_extension = ".session"
            else:
                # 导出加密文件
                session_data = session_file.read_bytes()
                file_extension = ".enc"
        else:
            session_data = session_file.read_bytes()
            file_extension = ".session"
        
        # 记录审计日志
        log_session_access(
            user_id=current_user.id,
            user_email=current_user.email,
            action="download",
            file_path=str(session_file),
            success=True,
            metadata={"decrypt": decrypt, "include_config": include_config}
        )
        
        # 如果只需要单个文件
        if not include_config:
            return Response(
                content=session_data,
                media_type="application/octet-stream",
                headers={
                    "Content-Disposition": f'attachment; filename="{session_name}{file_extension}"',
                    "Content-Type": "application/octet-stream"
                }
            )
        
        # 如果需要包含配置，创建 ZIP 包
        with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as tmp_file:
            zip_path = Path(tmp_file.name)
            
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # 添加 Session 文件
                zipf.writestr(f"{session_name}{file_extension}", session_data)
                
                # 添加配置文件模板
                config_template = f"""# Session 部署配置
# 将此文件重命名为 .env 并填入实际值

# Telegram API 配置（必需）
TELEGRAM_API_ID=your_api_id
TELEGRAM_API_HASH=your_api_hash

# Session 文件配置
SESSION_FILE={session_name}{file_extension}
SESSION_FILES_DIRECTORY=sessions

# Session 加密配置（如果 Session 文件已加密）
SESSION_ENCRYPTION_ENABLED={'true' if is_encrypted else 'false'}
SESSION_ENCRYPTION_KEY=your_encryption_key_here
# 或使用密码
# SESSION_ENCRYPTION_PASSWORD=your_password_here

# OpenAI 配置（用于 AI 聊天）
OPENAI_API_KEY=your_openai_api_key

# 其他配置
LOG_LEVEL=INFO
"""
                zipf.writestr("env.example", config_template)
                
                # 添加部署说明
                deploy_readme = f"""# Session 文件部署说明

## 文件说明

1. **{session_name}{file_extension}**: Session 文件
   - 如果文件扩展名是 .enc，表示已加密
   - 如果文件扩展名是 .session，表示明文

2. **env.example**: 环境变量配置模板
   - 复制为 .env 并填入实际值
   - 如果 Session 文件已加密，必须配置 SESSION_ENCRYPTION_KEY 或 SESSION_ENCRYPTION_PASSWORD

## 部署步骤

### 1. 解压文件

```bash
unzip {session_name}_deploy.zip
cd {session_name}_deploy
```

### 2. 配置环境变量

```bash
cp env.example .env
# 编辑 .env 文件，填入实际配置
```

### 3. 创建 sessions 目录

```bash
mkdir -p sessions
mv {session_name}{file_extension} sessions/
```

### 4. 安装依赖

```bash
pip install -r requirements.txt
```

### 5. 验证 Session 文件

```bash
python scripts/verify_session.py {session_name}
```

### 6. 启动服务

```bash
python main.py
```

## 验证清单

- [ ] Session 文件已放置在 sessions/ 目录
- [ ] 环境变量已正确配置（.env 文件）
- [ ] 如果 Session 文件已加密，加密密钥已配置
- [ ] Telegram API ID 和 Hash 已配置
- [ ] 依赖已安装
- [ ] Session 文件验证通过
- [ ] 服务可以正常启动并连接 Telegram

## 故障排查

### Session 文件无法读取

1. 检查文件权限：`chmod 600 sessions/{session_name}{file_extension}`
2. 如果已加密，检查加密密钥是否正确
3. 检查文件是否完整（文件大小应该 > 0）

### 无法连接 Telegram

1. 检查网络连接
2. 检查 Telegram API ID 和 Hash 是否正确
3. 检查 Session 文件是否有效（可能需要重新登录）

### 加密文件无法解密

1. 检查 SESSION_ENCRYPTION_KEY 是否正确
2. 如果使用密码，检查 SESSION_ENCRYPTION_PASSWORD 是否正确
3. 确认加密密钥与导出时使用的密钥一致

## 支持

如有问题，请联系系统管理员。
"""
                zipf.writestr("README.md", deploy_readme)
        
        # 返回 ZIP 文件
        return FileResponse(
            path=zip_path,
            filename=f"{session_name}_deploy.zip",
            media_type="application/zip",
            background=lambda: zip_path.unlink()  # 下载后删除临时文件
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"导出 Session 文件失败: {e}", exc_info=True)
        log_session_access(
            user_id=current_user.id,
            user_email=current_user.email,
            action="download",
            file_path=session_name,
            success=False,
            metadata={"error": str(e)}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"导出 Session 文件失败: {str(e)}"
        )


@router.get("/export-sessions-batch")
async def export_sessions_batch(
    session_names: str = Query(..., description="Session 文件名列表（逗号分隔）"),
    include_config: bool = Query(True, description="是否包含配置文件"),
    decrypt: bool = Query(False, description="是否解密后导出"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    批量导出 Session 文件
    """
    check_permission(current_user, PermissionCode.SESSION_DOWNLOAD.value, db)
    
    try:
        from group_ai_service.config import get_group_ai_config
        config = get_group_ai_config()
        session_manager = get_session_manager()
        all_sessions = session_manager.list_sessions()
        
        session_name_list = [name.strip() for name in session_names.split(",")]
        
        # 创建临时 ZIP 文件
        with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as tmp_file:
            zip_path = Path(tmp_file.name)
            
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                exported_count = 0
                
                for session_name in session_name_list:
                    # 查找 Session 文件
                    session_file = None
                    is_encrypted = False
                    
                    for s in all_sessions:
                        if s.stem == session_name:
                            session_file = s
                            is_encrypted = session_manager.encryptor and session_manager.encryptor.is_encrypted_file(s)
                            break
                    
                    if not session_file or not session_file.exists():
                        logger.warning(f"Session 文件未找到: {session_name}")
                        continue
                    
                    # 读取文件内容
                    if is_encrypted:
                        if decrypt and session_manager.encryptor:
                            encrypted_data = session_file.read_bytes()
                            session_data = session_manager.encryptor.decrypt_session(encrypted_data)
                            file_extension = ".session"
                        else:
                            session_data = session_file.read_bytes()
                            file_extension = ".enc"
                    else:
                        session_data = session_file.read_bytes()
                        file_extension = ".session"
                    
                    # 添加到 ZIP
                    zipf.writestr(f"sessions/{session_name}{file_extension}", session_data)
                    exported_count += 1
                    
                    # 记录审计日志
                    log_session_access(
                        user_id=current_user.id,
                        user_email=current_user.email,
                        action="download",
                        file_path=str(session_file),
                        success=True,
                        metadata={"batch": True, "decrypt": decrypt}
                    )
                
                if exported_count == 0:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="未找到任何 Session 文件"
                    )
                
                # 添加配置文件模板
                if include_config:
                    config_template = f"""# Session 批量部署配置
# 将此文件重命名为 .env 并填入实际值

# Telegram API 配置（必需）
TELEGRAM_API_ID=your_api_id
TELEGRAM_API_HASH=your_api_hash

# Session 文件配置
SESSION_FILES_DIRECTORY=sessions

# Session 加密配置（如果 Session 文件已加密）
SESSION_ENCRYPTION_ENABLED=true
SESSION_ENCRYPTION_KEY=your_encryption_key_here

# OpenAI 配置
OPENAI_API_KEY=your_openai_api_key

# 导出的 Session 文件列表
EXPORTED_SESSIONS={','.join(session_name_list)}
"""
                    zipf.writestr("env.example", config_template)
                    
                    deploy_readme = f"""# Session 批量部署说明

## 导出的 Session 文件

共导出 {exported_count} 个 Session 文件：
{chr(10).join(f'- {name}' for name in session_name_list[:exported_count])}

## 部署步骤

1. 解压文件到目标服务器
2. 配置环境变量（复制 env.example 为 .env）
3. 确保 sessions/ 目录存在
4. 验证所有 Session 文件
5. 启动服务

详细说明请参考单个 Session 部署说明。
"""
                    zipf.writestr("README.md", deploy_readme)
        
        return FileResponse(
            path=zip_path,
            filename=f"sessions_batch_{exported_count}_deploy.zip",
            media_type="application/zip",
            background=lambda: zip_path.unlink()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"批量导出 Session 文件失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"批量导出失败: {str(e)}"
        )


@router.get("/verify-session/{session_name}")
async def verify_session_file(
    session_name: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    验证 Session 文件是否可以在其他服务器上使用
    """
    check_permission(current_user, PermissionCode.SESSION_VIEW.value, db)
    
    try:
        from group_ai_service.config import get_group_ai_config
        config = get_group_ai_config()
        session_manager = get_session_manager()
        all_sessions = session_manager.list_sessions()
        
        # 查找 Session 文件
        session_file = None
        is_encrypted = False
        
        for s in all_sessions:
            if s.stem == session_name:
                session_file = s
                is_encrypted = session_manager.encryptor and session_manager.encryptor.is_encrypted_file(s)
                break
        
        if not session_file or not session_file.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session 文件未找到: {session_name}"
            )
        
        # 验证结果
        verification_result = {
            "session_name": session_name,
            "file_path": str(session_file),
            "file_size": session_file.stat().st_size,
            "is_encrypted": is_encrypted,
            "exists": True,
            "readable": False,
            "valid": False,
            "issues": []
        }
        
        # 检查文件是否可读
        try:
            if is_encrypted:
                if session_manager.encryptor:
                    encrypted_data = session_file.read_bytes()
                    decrypted_data = session_manager.encryptor.decrypt_session(encrypted_data)
                    verification_result["readable"] = True
                    verification_result["decrypted_size"] = len(decrypted_data)
                else:
                    verification_result["issues"].append("Session 文件已加密，但未配置加密密钥")
            else:
                data = session_file.read_bytes()
                verification_result["readable"] = True
                verification_result["decrypted_size"] = len(data)
        except Exception as e:
            verification_result["issues"].append(f"无法读取文件: {str(e)}")
        
        # 检查文件大小（Session 文件通常应该 > 0）
        if verification_result.get("decrypted_size", 0) == 0:
            verification_result["issues"].append("Session 文件为空或无效")
        else:
            verification_result["valid"] = True
        
        # 检查文件权限
        try:
            import stat
            file_stat = session_file.stat()
            mode = stat.filemode(file_stat.st_mode)
            verification_result["permissions"] = mode
            if mode != "-rw-------" and mode != "-rw-r--r--":
                verification_result["issues"].append(f"文件权限可能不安全: {mode}，建议使用 600")
        except Exception as e:
            verification_result["issues"].append(f"无法检查文件权限: {str(e)}")
        
        return {
            "success": len(verification_result["issues"]) == 0,
            "verification": verification_result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"验证 Session 文件失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"验证失败: {str(e)}"
        )

