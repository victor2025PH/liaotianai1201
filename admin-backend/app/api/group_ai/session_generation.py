"""
Session生成API
支持在远程服务器上生成Telegram Session文件
"""
import asyncio
import json
import logging
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_active_user
from app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/session-generation", tags=["session-generation"])


class SessionGenerationRequest(BaseModel):
    """Session生成请求"""
    node_id: str  # 服务器节点ID
    phone: str  # 手机号（含国家代码）
    api_id: Optional[int] = None  # API ID（可选，使用服务器默认配置）
    api_hash: Optional[str] = None  # API Hash（可选，使用服务器默认配置）
    session_name: Optional[str] = None  # Session名称（可选，默认使用手机号）
    use_proxy: bool = False  # 是否使用代理
    proxy_url: Optional[str] = None  # 代理URL


class SessionGenerationStatus(BaseModel):
    """Session生成状态"""
    task_id: str
    status: str  # pending, sending_code, waiting_code, verifying, completed, failed
    message: str
    phone_code_hash: Optional[str] = None  # 验证码哈希（用于验证）
    error: Optional[str] = None


class SessionVerificationRequest(BaseModel):
    """验证码验证请求"""
    task_id: str
    code: str  # 验证码
    password: Optional[str] = None  # 两步验证密码（如果需要）


# 存储生成任务状态（生产环境应使用Redis）
generation_tasks: Dict[str, Dict[str, Any]] = {}


def get_master_config_path() -> Path:
    """获取主节点配置文件路径"""
    project_root = Path(__file__).parent.parent.parent.parent.parent
    return project_root / "data" / "master_config.json"


def load_server_config(node_id: str) -> Optional[Dict]:
    """加载服务器配置"""
    config_path = get_master_config_path()
    if not config_path.exists():
        return None
    
    with open(config_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        servers = data.get('servers', {})
        return servers.get(node_id)


async def generate_session_on_server(
    node_id: str,
    phone: str,
    api_id: Optional[int],
    api_hash: Optional[str],
    session_name: Optional[str],
    use_proxy: bool,
    proxy_url: Optional[str],
    task_id: str
) -> Dict[str, Any]:
    """在服务器上生成session（异步执行）"""
    try:
        server_config = load_server_config(node_id)
        if not server_config:
            raise ValueError(f"服务器配置不存在: {node_id}")
        
        host = server_config.get('host')
        user = server_config.get('user', 'ubuntu')
        password = server_config.get('password')
        
        if not host or not password:
            raise ValueError(f"服务器配置不完整: {node_id}")
        
        # 更新任务状态
        generation_tasks[task_id]['status'] = 'sending_code'
        generation_tasks[task_id]['message'] = '正在发送验证码...'
        
        # 构建生成脚本
        session_name_value = session_name or phone.replace("+", "").replace("-", "")
        script_content = f"""#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import asyncio
import sys
import json
from pathlib import Path

# 添加项目路径
sys.path.insert(0, '/home/ubuntu')

from pyrogram import Client
from pyrogram.errors import SessionPasswordNeeded, FloodWait, PhoneNumberBanned, AuthKeyUnregistered

API_ID = {api_id if api_id else 'None'}
API_HASH = '{api_hash or ""}'
PHONE = '{phone}'
SESSION_NAME = '{session_name_value}'
USE_PROXY = {str(use_proxy).lower()}
PROXY_URL = '{proxy_url or ""}'

async def generate():
    proxy = None
    if USE_PROXY and PROXY_URL:
        # 解析代理URL
        if PROXY_URL.startswith('http://') or PROXY_URL.startswith('https://'):
            from urllib.parse import urlparse
            parsed = urlparse(PROXY_URL)
            proxy = {{
                "scheme": parsed.scheme,
                "hostname": parsed.hostname,
                "port": parsed.port or (443 if parsed.scheme == 'https' else 80),
            }}
            if parsed.username:
                proxy["username"] = parsed.username
            if parsed.password:
                proxy["password"] = parsed.password
    
    client = Client(
        SESSION_NAME,
        api_id=API_ID,
        api_hash=API_HASH,
        workdir="/home/ubuntu/sessions",
        proxy=proxy
    )
    
    try:
        await client.connect()
        
        # 检查是否已授权（使用 get_me() 来检查）
        # 如果已授权，会返回用户信息；如果未授权，会抛出 AuthKeyUnregistered
        try:
            me = await client.get_me()
            if me:
                print(f"ALREADY_AUTHORIZED:{{me.id}}")
                await client.disconnect()
                return
        except AuthKeyUnregistered:
            # 未授权，可以继续发送验证码
            pass
        
        # 发送验证码
        try:
            sent_code = await client.send_code(PHONE)
            print(f"CODE_SENT:{{sent_code.phone_code_hash}}")
        except PhoneNumberBanned:
            print("ERROR:PHONE_BANNED")
            return
        except FloodWait as e:
            print(f"ERROR:FLOOD_WAIT:{{e.value}}")
            return
        
        # 等待验证码输入（通过状态文件）
        state_file = Path(f"/tmp/session_gen_{{SESSION_NAME}}.json")
        import time
        max_wait = 300  # 最多等待5分钟
        waited = 0
        while waited < max_wait:
            if state_file.exists():
                state = json.loads(state_file.read_text())
                code = state.get('code')
                if code:
                    try:
                        await client.sign_in(PHONE, sent_code.phone_code_hash, code)
                        me = await client.get_me()
                        print(f"SUCCESS:{{me.id}}")
                        state_file.unlink()
                        return
                    except SessionPasswordNeeded:
                        password = state.get('password')
                        if password:
                            await client.check_password(password)
                            me = await client.get_me()
                            print(f"SUCCESS:{{me.id}}")
                            state_file.unlink()
                            return
                        else:
                            print("ERROR:PASSWORD_REQUIRED")
                            return
                    except Exception as e:
                        print(f"ERROR:SIGN_IN_FAILED:{{str(e)}}")
                        state_file.unlink()
                        return
            await asyncio.sleep(1)
            waited += 1
        
        print("ERROR:TIMEOUT")
    finally:
        if client.is_connected:
            await client.disconnect()

if __name__ == "__main__":
    import json
    asyncio.run(generate())
"""
        
        # 使用SSH执行脚本
        import paramiko
        
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(host, username=user, password=password, timeout=30)
        
        # 上传脚本
        script_path = f"/tmp/generate_session_{task_id}.py"
        sftp = ssh.open_sftp()
        with tempfile.NamedTemporaryFile(mode='w', delete=False, encoding='utf-8') as f:
            f.write(script_content)
            temp_script = f.name
        
        try:
            sftp.put(temp_script, script_path)
            sftp.chmod(script_path, 0o755)
        finally:
            sftp.close()
            os.unlink(temp_script)
        
        # 执行脚本（后台执行）
        stdin, stdout, stderr = ssh.exec_command(
            f"cd /home/ubuntu && python3 {script_path} 2>&1",
            get_pty=False
        )
        
        # 读取输出
        output = ""
        error_output = ""
        
        # 非阻塞读取
        import select
        import time
        
        max_wait = 60  # 最多等待60秒获取初始输出
        waited = 0
        
        while waited < max_wait:
            if stdout.channel.recv_ready():
                output += stdout.channel.recv(1024).decode('utf-8', errors='ignore')
                if 'CODE_SENT:' in output:
                    # 提取phone_code_hash
                    for line in output.split('\n'):
                        if 'CODE_SENT:' in line:
                            phone_code_hash = line.split('CODE_SENT:')[1].strip()
                            generation_tasks[task_id]['phone_code_hash'] = phone_code_hash
                            generation_tasks[task_id]['status'] = 'waiting_code'
                            generation_tasks[task_id]['message'] = '验证码已发送，请查收'
                            break
                    break
                elif 'ERROR:' in output:
                    error_msg = output.split('ERROR:')[1].strip()
                    generation_tasks[task_id]['status'] = 'failed'
                    generation_tasks[task_id]['error'] = error_msg
                    generation_tasks[task_id]['message'] = f'错误: {error_msg}'
                    break
                elif 'ALREADY_AUTHORIZED:' in output:
                    generation_tasks[task_id]['status'] = 'completed'
                    generation_tasks[task_id]['message'] = 'Session已存在且有效'
                    break
            
            if stderr.channel.recv_stderr_ready():
                error_output += stderr.channel.recv_stderr(1024).decode('utf-8', errors='ignore')
            
            time.sleep(0.5)
            waited += 0.5
        
        ssh.close()
        
        return {
            'status': generation_tasks[task_id].get('status', 'pending'),
            'output': output,
            'error': error_output
        }
        
    except Exception as e:
        logger.error(f"生成session失败: {e}", exc_info=True)
        generation_tasks[task_id]['status'] = 'failed'
        generation_tasks[task_id]['error'] = str(e)
        generation_tasks[task_id]['message'] = f'生成失败: {str(e)}'
        raise


@router.post("/start", response_model=SessionGenerationStatus)
async def start_session_generation(
    request: SessionGenerationRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """开始生成session"""
    import uuid
    task_id = str(uuid.uuid4())
    
    # 初始化任务状态
    generation_tasks[task_id] = {
        'status': 'pending',
        'message': '正在初始化...',
        'phone_code_hash': None,
        'error': None,
        'node_id': request.node_id,
        'phone': request.phone,
    }
    
    # 在后台执行生成任务
    background_tasks.add_task(
        generate_session_on_server,
        request.node_id,
        request.phone,
        request.api_id,
        request.api_hash,
        request.session_name,
        request.use_proxy,
        request.proxy_url,
        task_id
    )
    
    return SessionGenerationStatus(
        task_id=task_id,
        status='pending',
        message='任务已创建，正在发送验证码...'
    )


@router.post("/verify", response_model=SessionGenerationStatus)
async def verify_code(
    request: SessionVerificationRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """验证验证码"""
    if request.task_id not in generation_tasks:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    task = generation_tasks[request.task_id]
    node_id = task['node_id']
    phone = task['phone']
    
    server_config = load_server_config(node_id)
    if not server_config:
        raise HTTPException(status_code=404, detail="服务器配置不存在")
    
    host = server_config.get('host')
    user = server_config.get('user', 'ubuntu')
    password = server_config.get('password')
    
    # 创建状态文件
    session_name = phone.replace("+", "").replace("-", "")
    state_file = f"/tmp/session_gen_{session_name}.json"
    
    import paramiko
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(host, username=user, password=password, timeout=30)
    
    state_data = {
        'code': request.code,
        'password': request.password
    }
    
    try:
        sftp = ssh.open_sftp()
        with tempfile.NamedTemporaryFile(mode='w', delete=False, encoding='utf-8') as f:
            json.dump(state_data, f)
            temp_file = f.name
        
        try:
            sftp.put(temp_file, state_file)
        finally:
            sftp.close()
            os.unlink(temp_file)
        
        # 等待验证结果
        import time
        max_wait = 30
        waited = 0
        
        while waited < max_wait:
            # 检查脚本输出
            stdin, stdout, stderr = ssh.exec_command(
                f"tail -n 20 /tmp/generate_session_{request.task_id}.log 2>/dev/null || echo ''",
                timeout=5
            )
            output = stdout.read().decode('utf-8', errors='ignore')
            
            if 'SUCCESS:' in output:
                task['status'] = 'completed'
                task['message'] = 'Session生成成功'
                break
            elif 'ERROR:' in output:
                error_msg = output.split('ERROR:')[1].strip()
                task['status'] = 'failed'
                task['error'] = error_msg
                task['message'] = f'验证失败: {error_msg}'
                break
            
            time.sleep(1)
            waited += 1
        
        ssh.close()
        
    except Exception as e:
        logger.error(f"验证失败: {e}", exc_info=True)
        task['status'] = 'failed'
        task['error'] = str(e)
        task['message'] = f'验证失败: {str(e)}'
    
    return SessionGenerationStatus(
        task_id=request.task_id,
        status=task['status'],
        message=task['message'],
        error=task.get('error')
    )


@router.get("/status/{task_id}", response_model=SessionGenerationStatus)
async def get_generation_status(
    task_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """获取生成状态"""
    if task_id not in generation_tasks:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    task = generation_tasks[task_id]
    return SessionGenerationStatus(
        task_id=task_id,
        status=task['status'],
        message=task['message'],
        phone_code_hash=task.get('phone_code_hash'),
        error=task.get('error')
    )

