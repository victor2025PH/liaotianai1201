"""
Telegram注册服务
"""
import asyncio
import logging
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any

from sqlalchemy.orm import Session
from pyrogram import Client
from pyrogram.errors import SessionPasswordNeeded, FloodWait, PhoneNumberBanned, AuthKeyUnregistered, PhoneCodeExpired, PhoneCodeInvalid

from app.models.telegram_registration import UserRegistration, SessionFile, AntiDetectionLog
from app.services.anti_detection_service import AntiDetectionService
from app.services.rate_limiter_service import RateLimiterService
from app.core.config import get_settings

logger = logging.getLogger(__name__)


class TelegramRegistrationService:
    """Telegram注册服务"""
    
    def __init__(self, db: Session):
        self.db = db
        self.anti_detection = AntiDetectionService(db)
        self.rate_limiter = RateLimiterService(db)
        self.settings = get_settings()
        self.mock_mode = self.settings.telegram_registration_mock_mode
        self.mock_code = self.settings.telegram_registration_mock_code
    
    async def start_registration(
        self,
        phone: str,
        country_code: str,
        node_id: str,
        api_id: Optional[int] = None,
        api_hash: Optional[str] = None,
        session_name: Optional[str] = None,
        use_proxy: bool = False,
        proxy_url: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        device_fingerprint: Optional[str] = None,
    ) -> Dict[str, Any]:
        """开始注册流程"""
        
        # 1. 验证手机号格式
        if not self._validate_phone(phone):
            raise ValueError("手机号格式无效")
        
        # 2. 检查速率限制
        registration_data = {
            'phone': phone,
            'ip_address': ip_address,
            'device_fingerprint': device_fingerprint,
        }
        allowed, error_msg, retry_after = self.rate_limiter.check_rate_limit(registration_data)
        if not allowed:
            raise ValueError(f"{error_msg}，请等待 {retry_after} 秒后重试")
        
        # 3. 风险评估
        risk_data = {
            'phone': phone,
            'ip_address': ip_address,
            'user_agent': user_agent,
            'device_fingerprint': device_fingerprint,
        }
        risk_score = self.anti_detection.calculate_risk_score(risk_data)
        
        # 4. 检查是否应该阻止
        if self.anti_detection.should_block(risk_score):
            # 记录阻止事件
            self.anti_detection.log_event(
                event_type='registration_blocked',
                risk_level='critical',
                risk_score=risk_score,
                ip_address=ip_address,
                user_agent=user_agent,
                device_fingerprint=device_fingerprint,
                action_taken='blocked',
                behavior_pattern=risk_data
            )
            raise ValueError(f"风险评分过高 ({risk_score})，注册被阻止")
        
        # 5. 检查是否已存在相同的 phone + node_id 组合
        existing_registration = self.db.query(UserRegistration).filter(
            UserRegistration.phone == phone,
            UserRegistration.node_id == node_id
        ).first()
        
        # 5.1. 额外检查：是否有其他服务器的 code_sent 记录
        other_server_registration = self.db.query(UserRegistration).filter(
            UserRegistration.phone == phone,
            UserRegistration.node_id != node_id,
            UserRegistration.status == 'code_sent',
            UserRegistration.phone_code_hash.isnot(None)
        ).first()
        
        # 用于标记是否切换了服务器
        server_switched = False
        is_valid = True  # 默认值，如果 other_server_registration 为 None，则 is_valid 为 True
        
        if other_server_registration:
            # 检查其他服务器的记录是否真的有效
            is_valid = True
            reason = ""
            
            # 检查1: 是否有错误信息（说明发送可能失败）
            if other_server_registration.error_message:
                is_valid = False
                reason = f"其他服务器记录有错误: {other_server_registration.error_message}"
                logger.warning(f"发现其他服务器上的验证码记录有错误: phone={phone}, "
                             f"其他服务器={other_server_registration.node_id}, "
                             f"错误={other_server_registration.error_message}")
            
            # 检查2: 记录是否过期（超过10分钟）
            if other_server_registration.updated_at:
                time_diff = (datetime.utcnow() - other_server_registration.updated_at).total_seconds()
                if time_diff > 600:  # 10分钟
                    is_valid = False
                    reason = f"其他服务器记录已过期（{int(time_diff/60)}分钟前）"
                    logger.warning(f"发现其他服务器上的验证码记录已过期: phone={phone}, "
                                 f"其他服务器={other_server_registration.node_id}, "
                                 f"时间差={int(time_diff/60)}分钟")
            
            # 检查3: 重试次数过多（可能发送失败）
            if other_server_registration.retry_count >= 3:
                is_valid = False
                reason = f"其他服务器记录重试次数过多（{other_server_registration.retry_count}次）"
                logger.warning(f"发现其他服务器上的验证码记录重试次数过多: phone={phone}, "
                             f"其他服务器={other_server_registration.node_id}, "
                             f"重试次数={other_server_registration.retry_count}")
            
            if is_valid:
                # 记录有效，提示用户使用正确的服务器
                logger.warning(f"发现其他服务器上的有效验证码记录: phone={phone}, "
                             f"其他服务器={other_server_registration.node_id}, "
                             f"当前服务器={node_id}, "
                             f"其他服务器hash={other_server_registration.phone_code_hash}")
                raise ValueError(
                    f'该手机号 {phone} 已在服务器 {other_server_registration.node_id} 上发送了验证码。'
                    f'请使用服务器 {other_server_registration.node_id} 进行验证，'
                    f'或先取消现有注册后再重新开始。'
                )
            else:
                # 记录无效，允许使用新服务器，但记录警告
                logger.info(f"发现其他服务器上的无效验证码记录，允许使用新服务器: phone={phone}, "
                          f"其他服务器={other_server_registration.node_id}, "
                          f"当前服务器={node_id}, "
                          f"原因={reason}")
                # 将旧记录标记为失败，避免再次检查
                other_server_registration.status = 'failed'
                other_server_registration.error_message = f'记录无效，已切换到服务器 {node_id}。原因: {reason}'
                self.db.commit()
                logger.info(f"已将其他服务器的无效记录标记为失败: registration_id={other_server_registration.id}")
                # 标记需要重新发送验证码
                server_switched = True
                logger.warning(f"[重要] 已切换到新服务器 {node_id}，将重新发送验证码。"
                             f"旧服务器 {other_server_registration.node_id} 的验证码已失效，"
                             f"请使用新服务器发送的验证码")
        
        if existing_registration:
            # 如果已存在，根据状态决定处理方式
            if existing_registration.status == 'completed':
                raise ValueError(f'该手机号 {phone} 已在服务器 {node_id} 上完成注册，请使用其他手机号或服务器')
            elif existing_registration.status == 'code_sent' and existing_registration.phone_code_hash:
                # 如果验证码已发送且 hash 存在，直接返回现有记录，避免重新生成 hash 导致验证码失效
                logger.info(f"发现已发送验证码的注册记录 {existing_registration.id}，返回现有记录")
                expires_at = existing_registration.updated_at + timedelta(minutes=10) if existing_registration.updated_at else None
                return {
                    'registration_id': str(existing_registration.id),
                    'status': 'code_sent',
                    'message': '验证码已发送，请使用已收到的验证码',
                    'phone_code_hash': existing_registration.phone_code_hash,
                    'expires_in': 600,  # 10分钟
                    'expires_at': expires_at.isoformat() if expires_at else None,
                    'risk_score': existing_registration.risk_score,
                }
            elif existing_registration.status in ['pending', 'code_sent']:
                # 如果还在进行中但没有 hash，更新现有记录并重新开始
                logger.info(f"发现进行中的注册记录 {existing_registration.id}，更新并重新开始")
                existing_registration.api_id = api_id
                existing_registration.api_hash = api_hash
                existing_registration.session_name = session_name or phone.replace("+", "").replace("-", "")
                existing_registration.status = 'pending'
                existing_registration.phone_code_hash = None
                existing_registration.error_message = None
                existing_registration.retry_count += 1
                existing_registration.risk_score = risk_score
                existing_registration.user_agent = user_agent
                existing_registration.ip_address = ip_address
                existing_registration.updated_at = datetime.utcnow()
                registration = existing_registration
                self.db.commit()
                self.db.refresh(registration)
            elif existing_registration.status == 'failed':
                # 如果之前失败，重置状态并重新开始
                logger.info(f"发现失败的注册记录 {existing_registration.id}，重置并重新开始")
                existing_registration.api_id = api_id
                existing_registration.api_hash = api_hash
                existing_registration.session_name = session_name or phone.replace("+", "").replace("-", "")
                existing_registration.status = 'pending'
                existing_registration.phone_code_hash = None
                existing_registration.error_message = None
                existing_registration.retry_count += 1
                existing_registration.risk_score = risk_score
                existing_registration.user_agent = user_agent
                existing_registration.ip_address = ip_address
                existing_registration.updated_at = datetime.utcnow()
                registration = existing_registration
                self.db.commit()
                self.db.refresh(registration)
            else:
                # 其他状态，返回错误
                raise ValueError(f'该手机号 {phone} 在服务器 {node_id} 上已有注册记录（状态: {existing_registration.status}），请先取消或完成现有注册')
        else:
            # 6. 创建新的注册记录
            registration = UserRegistration(
                phone=phone,
                country_code=country_code,
                api_id=api_id,
                api_hash=api_hash,
                node_id=node_id,
                session_name=session_name or phone.replace("+", "").replace("-", ""),
                status='pending',
                risk_score=risk_score,
                ip_address=ip_address,
                user_agent=user_agent,
            )
            self.db.add(registration)
            self.db.commit()
            self.db.refresh(registration)
        
        # 7. 记录开始事件
        self.anti_detection.log_event(
            registration_id=registration.id,
            event_type='registration_start',
            risk_level=self.anti_detection.get_risk_level(risk_score),
            risk_score=risk_score,
            ip_address=ip_address,
            user_agent=user_agent,
            device_fingerprint=device_fingerprint,
            action_taken='allowed',
            behavior_pattern=risk_data
        )
        
        # 7. 发送验证码（异步执行）
        try:
            if self.mock_mode:
                # 模拟模式：生成假的验证码哈希
                logger.info(f"[MOCK MODE] 模拟发送验证码到 {registration.phone}")
                phone_code_hash = f"mock_hash_{registration.id}"
                registration.phone_code_hash = phone_code_hash
                registration.status = 'code_sent'
                # 在模拟模式下，将验证码存储在 error_message 字段中（临时）
                registration.error_message = f"MOCK_CODE:{self.mock_code}"
                self.db.commit()
                
                logger.info(f"[MOCK MODE] 模拟验证码: {self.mock_code} (仅用于测试)")
            else:
                # 如果没有提供 hash，从 Telegram API 获取
                phone_code_hash = await self._send_code(
                    registration=registration,
                    use_proxy=use_proxy,
                    proxy_url=proxy_url
                )
                registration.phone_code_hash = phone_code_hash
                registration.status = 'code_sent'
                self.db.commit()
            
            expires_at = datetime.utcnow() + timedelta(minutes=10)
            
            return {
                'registration_id': str(registration.id),
                'status': 'code_sent',
                'message': '验证码已发送' + (' (模拟模式)' if self.mock_mode else '') + 
                          ('。注意：已切换到新服务器，请使用新收到的验证码' if server_switched else ''),
                'phone_code_hash': phone_code_hash,
                'expires_in': 600,  # 10分钟
                'expires_at': expires_at.isoformat(),
                'risk_score': risk_score,
                'server_switched': server_switched,  # 标记是否切换了服务器
            }
        except PhoneNumberBanned:
            registration.status = 'failed'
            registration.error_message = '手机号已被封禁'
            self.db.commit()
            raise ValueError('手机号已被封禁，请使用其他号码')
        except FloodWait as e:
            registration.status = 'failed'
            registration.error_message = f'触发速率限制，请等待 {e.value} 秒'
            self.db.commit()
            raise ValueError(f'触发速率限制，请等待 {e.value} 秒后重试')
        except Exception as e:
            logger.error(f"发送验证码失败: {e}", exc_info=True)
            registration.status = 'failed'
            registration.error_message = str(e)
            self.db.commit()
            raise ValueError(f'发送验证码失败: {str(e)}')
    
    async def verify_code(
        self,
        registration_id: str,
        code: str,
        password: Optional[str] = None,
    ) -> Dict[str, Any]:
        """验证OTP码"""
        
        registration = self.db.query(UserRegistration).filter(
            UserRegistration.id == registration_id
        ).first()
        
        if not registration:
            raise ValueError("注册记录不存在")
        
        if registration.status != 'code_sent':
            logger.error(f"[验证码验证] 状态不允许: registration_id={registration.id}, status={registration.status}")
            raise ValueError(f"当前状态不允许验证: {registration.status}")
        
        # 记录验证开始（包含服务器信息）
        logger.info(f"[验证码验证] 开始验证: registration_id={registration.id}, phone={registration.phone}, "
                   f"node_id={registration.node_id}, phone_code_hash={registration.phone_code_hash}, "
                   f"code_length={len(code) if code else 0}")
        logger.info(f"[验证码验证] ✅ 自动使用服务器 {registration.node_id} 进行验证（这是发送验证码的服务器）")
        logger.info(f"[验证码验证] 确保验证码和 phone_code_hash 在同一个服务器上匹配")
        
        # 不再检查验证码过期，由 Telegram API 后端控制验证码有效性
        try:
            # 模拟模式：检查验证码
            if self.mock_mode:
                # 从 error_message 中获取模拟验证码
                mock_code_stored = registration.error_message or ""
                expected_code = self.mock_code
                if mock_code_stored.startswith("MOCK_CODE:"):
                    expected_code = mock_code_stored.split("MOCK_CODE:")[1]
                
                logger.info(f"[MOCK MODE] 验证码验证: 输入={code}, 期望={expected_code}")
                if code != expected_code:
                    registration.retry_count += 1
                    self.db.commit()
                    logger.warning(f"[MOCK MODE] 验证码错误: registration_id={registration.id}, "
                                 f"输入={code}, 期望={expected_code}, retry_count={registration.retry_count}")
                    raise ValueError(f'验证码错误（模拟模式，正确验证码: {expected_code}）')
                
                logger.info(f"[MOCK MODE] 验证码验证成功: registration_id={registration.id}, code={code}")
                
                # 生成模拟的 session 文件
                session_file = await self._create_mock_session(registration)
            else:
                # 验证码验证
                session_file = await self._verify_and_create_session(
                    registration=registration,
                    code=code,
                    password=password
                )
            
            registration.status = 'completed'
            registration.completed_at = datetime.utcnow()
            registration.session_file_path = session_file['file_path']
            self.db.commit()
            
            # 创建Session文件记录
            session_file_record = SessionFile(
                registration_id=registration.id,
                session_name=session_file['session_name'],
                file_path=session_file['file_path'],
                file_size=session_file.get('file_size'),
                file_hash=session_file.get('file_hash'),
                server_node_id=registration.node_id,
                is_valid=True,
                extra_metadata=session_file.get('metadata'),
            )
            self.db.add(session_file_record)
            self.db.commit()
            
            # 记录完成事件
            self.anti_detection.log_event(
                registration_id=registration.id,
                event_type='registration_completed',
                risk_level='low',
                risk_score=registration.risk_score,
                action_taken='completed',
            )
            
            return {
                'registration_id': str(registration.id),
                'status': 'completed',
                'message': '注册成功',
                'session_file': {
                    'session_name': session_file['session_name'],
                    'file_path': session_file['file_path'],
                    'server_node_id': registration.node_id,
                    'file_size': session_file.get('file_size'),
                    'created_at': datetime.utcnow().isoformat(),
                }
            }
        except SessionPasswordNeeded:
            if not password:
                registration.status = 'verified'
                self.db.commit()
                return {
                    'registration_id': str(registration.id),
                    'status': 'password_required',
                    'message': '需要两步验证密码',
                }
            else:
                # 已经有密码，继续验证
                return await self.verify_code(registration_id, code, password)
        except Exception as e:
            logger.error(f"验证失败: {e}", exc_info=True)
            registration.status = 'failed'
            registration.error_message = str(e)
            registration.retry_count += 1
            self.db.commit()
            raise ValueError(f'验证失败: {str(e)}')
    
    def _load_server_config(self, node_id: str) -> Optional[Dict[str, Any]]:
        """加载服务器配置"""
        from pathlib import Path as PathLib
        import json
        
        project_root = PathLib(__file__).parent.parent.parent.parent
        config_path = project_root / "data" / "master_config.json"
        if not config_path.exists():
            return None
        with open(config_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            servers = data.get('servers', {})
            return servers.get(node_id)
    
    async def _send_code(
        self,
        registration: UserRegistration,
        use_proxy: bool = False,
        proxy_url: Optional[str] = None,
    ) -> str:
        """发送验证码（在服务器上执行）"""
        try:
            import paramiko
            import json
            
            # 获取服务器配置
            server_config = self._load_server_config(registration.node_id)
            if not server_config:
                raise ValueError(f"服务器配置不存在: {registration.node_id}")
            
            host = server_config.get('host')
            user = server_config.get('user', 'ubuntu')
            password = server_config.get('password')
            
            if not host or not password:
                raise ValueError(f"服务器配置不完整: {registration.node_id}")
            
            # 构建脚本
            script_content = self._build_send_code_script(
                registration=registration,
                use_proxy=use_proxy,
                proxy_url=proxy_url
            )
            
            # 通过SSH执行
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(host, username=user, password=password, timeout=30)
            
            try:
                # 上传脚本
                script_path = f"/tmp/send_code_{registration.id}.py"
                sftp = ssh.open_sftp()
                with tempfile.NamedTemporaryFile(mode='w', delete=False, encoding='utf-8') as f:
                    f.write(script_content)
                    temp_script = f.name
                
                try:
                    sftp.put(temp_script, script_path)
                    sftp.chmod(script_path, 0o755)
                finally:
                    sftp.close()
                    import os
                    os.unlink(temp_script)
                
                # 执行脚本
                stdin, stdout, stderr = ssh.exec_command(
                    f"cd /home/ubuntu && python3 {script_path} 2>&1",
                    get_pty=False
                )
                
                # 读取输出
                output = stdout.read().decode('utf-8', errors='ignore')
                error_output = stderr.read().decode('utf-8', errors='ignore')
                
                # 记录详细的执行输出
                logger.info(f"[远程发送验证码] 脚本执行完成: registration_id={registration.id}, "
                           f"phone={registration.phone}, node_id={registration.node_id}, "
                           f"output_length={len(output)}, error_output_length={len(error_output)}")
                logger.info(f"[远程发送验证码] 完整输出: {output[:500]}")
                if error_output:
                    logger.warning(f"[远程发送验证码] 错误输出: {error_output[:500]}")
                
                # 如果输出中没有 CODE_SENT，记录警告
                if 'CODE_SENT:' not in output:
                    logger.warning(f"[远程发送验证码] 警告: 脚本执行完成但未找到 CODE_SENT 标记, "
                                 f"registration_id={registration.id}, phone={registration.phone}, "
                                 f"node_id={registration.node_id}, output={output[:200]}")
                
                # 解析输出
                if 'CODE_SENT:' in output:
                    phone_code_hash = output.split('CODE_SENT:')[1].strip().split('\n')[0]
                    logger.info(f"[远程发送验证码] 验证码发送成功: registration_id={registration.id}, "
                               f"phone={registration.phone}, phone_code_hash={phone_code_hash}")
                    return phone_code_hash
                elif 'ERROR:PHONE_BANNED' in output:
                    logger.error(f"[远程发送验证码] 手机号被封禁: registration_id={registration.id}, "
                               f"phone={registration.phone}")
                    raise PhoneNumberBanned("手机号已被封禁")
                elif 'ERROR:FLOOD_WAIT:' in output:
                    wait_time = int(output.split('ERROR:FLOOD_WAIT:')[1].strip().split('\n')[0])
                    logger.warning(f"[远程发送验证码] 触发速率限制: registration_id={registration.id}, "
                                 f"phone={registration.phone}, wait_time={wait_time}")
                    raise FloodWait(value=wait_time)
                else:
                    logger.error(f"[远程发送验证码] 发送失败: registration_id={registration.id}, "
                               f"phone={registration.phone}, output={output[:500]}, "
                               f"error_output={error_output[:500]}")
                    raise ValueError(f"发送验证码失败: {error_output or output}")
            finally:
                ssh.close()
        except ImportError:
            # paramiko未安装，使用本地实现（仅用于开发测试）
            logger.warning("paramiko未安装，使用本地实现（仅用于开发测试）")
            return await self._send_code_local(registration, use_proxy, proxy_url)
    
    async def _send_code_local(
        self,
        registration: UserRegistration,
        use_proxy: bool = False,
        proxy_url: Optional[str] = None,
    ) -> str:
        """本地发送验证码（仅用于开发测试）"""
        proxy = None
        if use_proxy and proxy_url:
            proxy = self._parse_proxy(proxy_url)
        
        client = Client(
            registration.session_name,
            api_id=registration.api_id,
            api_hash=registration.api_hash,
            workdir="sessions",
            proxy=proxy
        )
        
        try:
            await client.connect()
            
            # 检查是否已授权（使用 get_me() 来检查）
            # 如果已授权，会返回用户信息；如果未授权，会抛出 AuthKeyUnregistered
            try:
                me = await client.get_me()
                if me:
                    await client.disconnect()
                    raise ValueError("Session已存在且有效")
            except AuthKeyUnregistered:
                # 未授权，可以继续发送验证码
                pass
            
            # 发送验证码
            logger.info(f"[本地发送验证码] 调用 send_code: phone={registration.phone}, "
                       f"api_id={registration.api_id}, session_name={registration.session_name}")
            sent_code = await client.send_code(registration.phone)
            logger.info(f"[本地发送验证码] 验证码发送成功: phone={registration.phone}, "
                       f"phone_code_hash={sent_code.phone_code_hash}, "
                       f"phone_code_hash_type={type(sent_code.phone_code_hash)}")
            await client.disconnect()
            
            return sent_code.phone_code_hash
        finally:
            if client.is_connected:
                await client.disconnect()
    
    def _build_send_code_script(
        self,
        registration: UserRegistration,
        use_proxy: bool = False,
        proxy_url: Optional[str] = None,
    ) -> str:
        """构建发送验证码脚本"""
        if use_proxy and proxy_url:
            from urllib.parse import urlparse
            parsed = urlparse(proxy_url)
            proxy_config = f"""proxy = {{
    "scheme": "{parsed.scheme}",
    "hostname": "{parsed.hostname}",
    "port": {parsed.port or (443 if parsed.scheme == 'https' else 80)},
}}
if "{parsed.username}":
    proxy["username"] = "{parsed.username}"
if "{parsed.password}":
    proxy["password"] = "{parsed.password}"
"""
        else:
            proxy_config = "proxy = None"
        
        return f"""#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import asyncio
import sys
sys.path.insert(0, '/home/ubuntu')

from pyrogram import Client
from pyrogram.errors import PhoneNumberBanned, FloodWait, AuthKeyUnregistered, PhoneCodeExpired, PhoneCodeInvalid

API_ID = {registration.api_id or 'None'}
API_HASH = '{registration.api_hash or ""}'
PHONE = {repr(registration.phone)}
SESSION_NAME = '{registration.session_name}'
{proxy_config}

async def send_code():
    client = Client(
        SESSION_NAME,
        api_id=API_ID,
        api_hash=API_HASH,
        workdir="/home/ubuntu/sessions",
        proxy=proxy
    )
    
    try:
        await client.connect()
        
        # 使用 get_me() 来检查是否已授权
        # 如果已授权，会返回用户信息；如果未授权，会抛出 AuthKeyUnregistered
        try:
            me = await client.get_me()
            if me:
                print("ERROR:ALREADY_AUTHORIZED")
                return
        except AuthKeyUnregistered:
            # 未授权，可以继续发送验证码
            pass
        
        print("DEBUG: 准备发送验证码到 " + str(PHONE))
        sent_code = await client.send_code(PHONE)
        print("DEBUG: send_code 调用成功，phone_code_hash=" + str(sent_code.phone_code_hash))
        print("CODE_SENT:" + str(sent_code.phone_code_hash))
    except PhoneNumberBanned:
        print("ERROR:PHONE_BANNED")
    except FloodWait as e:
        print("ERROR:FLOOD_WAIT:" + str(e.value))
    finally:
        if client.is_connected:
            await client.disconnect()

if __name__ == "__main__":
    asyncio.run(send_code())
"""
    
    async def _create_mock_session(
        self,
        registration: UserRegistration,
    ) -> Dict[str, Any]:
        """创建模拟的 Session 文件（仅用于测试）"""
        import os
        import json
        from pathlib import Path
        
        # 确定 session 文件路径
        if registration.node_id:
            # 服务器路径
            server_config = self._load_server_config(registration.node_id)
            if server_config:
                sessions_dir = server_config.get('sessions_dir', '/home/ubuntu/sessions')
            else:
                sessions_dir = 'sessions'
        else:
            sessions_dir = 'sessions'
        
        session_name = registration.session_name or registration.phone.replace("+", "").replace("-", "")
        session_file_path = f"{sessions_dir}/{session_name}.session"
        
        # 创建模拟的 session 文件内容（空的 SQLite 数据库）
        # 注意：这只是用于测试，不是真正的有效 session
        logger.info(f"[MOCK MODE] 创建模拟 Session 文件: {session_file_path}")
        
        # 如果是本地模式，直接创建文件
        if not registration.node_id or not self._load_server_config(registration.node_id):
            # 本地创建
            Path(sessions_dir).mkdir(parents=True, exist_ok=True)
            # 创建一个最小的 SQLite 文件（仅用于测试）
            import sqlite3
            db_path = Path(sessions_dir) / f"{session_name}.session"
            conn = sqlite3.connect(str(db_path))
            conn.execute("CREATE TABLE IF NOT EXISTS sessions (key TEXT PRIMARY KEY, value TEXT)")
            conn.execute("INSERT OR REPLACE INTO sessions VALUES ('mock', 'true')")
            conn.commit()
            conn.close()
            
            file_size = db_path.stat().st_size
            logger.info(f"[MOCK MODE] 模拟 Session 文件已创建: {db_path} ({file_size} 字节)")
        else:
            # 服务器模式：通过 SSH 创建
            try:
                import paramiko
                server_config = self._load_server_config(registration.node_id)
                host = server_config.get('host')
                user = server_config.get('user', 'ubuntu')
                server_password = server_config.get('password')
                
                ssh = paramiko.SSHClient()
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                ssh.connect(host, username=user, password=server_password, timeout=30)
                
                try:
                    # 创建目录
                    ssh.exec_command(f"mkdir -p {sessions_dir}")
                    # 创建模拟 session 文件
                    create_script = f"""python3 << 'EOF'
import sqlite3
import os
os.makedirs('{sessions_dir}', exist_ok=True)
db_path = '{session_file_path}'
conn = sqlite3.connect(db_path)
conn.execute("CREATE TABLE IF NOT EXISTS sessions (key TEXT PRIMARY KEY, value TEXT)")
conn.execute("INSERT OR REPLACE INTO sessions VALUES ('mock', 'true')")
conn.commit()
conn.close()
print(f"MOCK_SESSION_CREATED:{db_path}")
EOF"""
                    stdin, stdout, stderr = ssh.exec_command(create_script)
                    output = stdout.read().decode('utf-8', errors='ignore')
                    if 'MOCK_SESSION_CREATED:' in output:
                        logger.info(f"[MOCK MODE] 服务器上模拟 Session 文件已创建")
                    file_size = 1024  # 模拟文件大小
                finally:
                    ssh.close()
            except Exception as e:
                logger.warning(f"[MOCK MODE] 无法在服务器上创建模拟文件: {e}")
                file_size = 1024
        
        return {
            'session_name': session_name,
            'file_path': session_file_path,
            'file_size': file_size,
            'file_hash': 'mock_hash',
            'metadata': {
                'mock_mode': True,
                'created_at': datetime.utcnow().isoformat(),
                'note': '这是模拟模式生成的测试 Session 文件，不能用于真实登录'
            }
        }
    
    async def _verify_and_create_session(
        self,
        registration: UserRegistration,
        code: str,
        password: Optional[str] = None,
    ) -> Dict[str, Any]:
        """验证并创建Session（在服务器上执行）"""
        try:
            import paramiko
            import json
            
            # 获取服务器配置（自动使用发送验证码时的同一服务器）
            logger.info(f"[远程验证] ✅ 自动分配服务器: {registration.node_id}（这是发送验证码的服务器）")
            logger.info(f"[远程验证] 准备在服务器 {registration.node_id} 上执行验证")
            server_config = self._load_server_config(registration.node_id)
            if not server_config:
                logger.error(f"[远程验证] 服务器配置不存在: {registration.node_id}")
                raise ValueError(f"服务器配置不存在: {registration.node_id}")
            
            host = server_config.get('host')
            user = server_config.get('user', 'ubuntu')
            password_config = server_config.get('password')
            
            if not host or not password_config:
                logger.error(f"[远程验证] 服务器配置不完整: {registration.node_id}, host={host}, has_password={bool(password_config)}")
                raise ValueError(f"服务器配置不完整: {registration.node_id}")
            
            logger.info(f"[远程验证] 连接到服务器: {registration.node_id} ({host}), "
                       f"使用 phone_code_hash={registration.phone_code_hash}")
            logger.info(f"[远程验证] ✅ 验证码和 phone_code_hash 将在同一服务器上匹配，确保验证成功")
            
            # 构建验证脚本
            script_content = self._build_verify_script(
                registration=registration,
                code=code,
                password=password
            )
            
            # 通过SSH执行
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(host, username=user, password=password_config, timeout=30)
            
            try:
                # 上传脚本
                script_path = f"/tmp/verify_session_{registration.id}.py"
                sftp = ssh.open_sftp()
                with tempfile.NamedTemporaryFile(mode='w', delete=False, encoding='utf-8') as f:
                    f.write(script_content)
                    temp_script = f.name
                
                try:
                    sftp.put(temp_script, script_path)
                    sftp.chmod(script_path, 0o755)
                finally:
                    sftp.close()
                    import os
                    os.unlink(temp_script)
                
                # 执行脚本
                stdin, stdout, stderr = ssh.exec_command(
                    f"cd /home/ubuntu && python3 {script_path} 2>&1",
                    get_pty=False
                )
                
                # 读取输出
                output = stdout.read().decode('utf-8', errors='ignore')
                error_output = stderr.read().decode('utf-8', errors='ignore')
                
                # 记录远程执行输出
                logger.info(f"[远程验证] 脚本执行完成: registration_id={registration.id}, "
                           f"output_length={len(output)}, output_preview={output[:200]}")
                if error_output:
                    logger.warning(f"[远程验证] 脚本错误输出: registration_id={registration.id}, "
                                 f"error_output={error_output[:200]}")
                
                # 解析输出
                if 'SUCCESS:' in output:
                    # 提取用户信息
                    user_info_line = output.split('SUCCESS:')[1].strip().split('\n')[0]
                    logger.info(f"[远程验证] 验证成功: registration_id={registration.id}, "
                               f"user_info={user_info_line}")
                    user_info = json.loads(user_info_line)
                    
                    # 获取Session文件信息
                    session_path = f"/home/ubuntu/sessions/{registration.session_name}.session"
                    stdin2, stdout2, stderr2 = ssh.exec_command(
                        f"stat -c '%s' {session_path} 2>/dev/null || echo '0'"
                    )
                    file_size = int(stdout2.read().decode('utf-8').strip() or '0')
                    
                    # 计算文件哈希
                    stdin3, stdout3, stderr3 = ssh.exec_command(
                        f"sha256sum {session_path} 2>/dev/null | cut -d' ' -f1 || echo ''"
                    )
                    file_hash = stdout3.read().decode('utf-8').strip()
                    
                    return {
                        'session_name': registration.session_name,
                        'file_path': session_path,
                        'file_size': file_size,
                        'file_hash': file_hash,
                        'metadata': user_info
                    }
                elif 'ERROR:PHONE_CODE_EXPIRED' in output or 'PhoneCodeExpired' in output:
                    logger.error(f"[远程验证] PhoneCodeExpired: registration_id={registration.id}, "
                               f"phone={registration.phone}, phone_code_hash={registration.phone_code_hash}, "
                               f"code={code}, output={output[:500]}")
                    registration.status = 'failed'
                    registration.error_message = '验证码无效，请重新获取验证码'
                    self.db.commit()
                    raise ValueError('验证码无效，请重新获取验证码')
                elif 'ERROR:PHONE_CODE_INVALID' in output or 'PhoneCodeInvalid' in output:
                    logger.error(f"[远程验证] PhoneCodeInvalid: registration_id={registration.id}, "
                               f"phone={registration.phone}, phone_code_hash={registration.phone_code_hash}, "
                               f"code={code}, output={output[:500]}")
                    registration.retry_count += 1
                    self.db.commit()
                    raise ValueError('验证码错误，请检查后重试')
                elif 'ERROR:PASSWORD_REQUIRED' in output:
                    raise SessionPasswordNeeded("需要两步验证密码")
                elif 'ERROR:' in output:
                    error_msg = output.split('ERROR:')[1].strip().split('\n')[0]
                    raise ValueError(f"验证失败: {error_msg}")
                else:
                    raise ValueError(f"验证失败: {error_output or output}")
            finally:
                ssh.close()
        except ImportError:
            # paramiko未安装，使用本地实现（仅用于开发测试）
            logger.warning("paramiko未安装，使用本地实现（仅用于开发测试）")
            return await self._verify_and_create_session_local(registration, code, password)
    
    async def _verify_and_create_session_local(
        self,
        registration: UserRegistration,
        code: str,
        password: Optional[str] = None,
    ) -> Dict[str, Any]:
        """本地验证并创建Session（仅用于开发测试）"""
        proxy = None
        
        client = Client(
            registration.session_name,
            api_id=registration.api_id,
            api_hash=registration.api_hash,
            workdir="sessions",
            proxy=proxy
        )
        
        try:
            await client.connect()
            
            # 验证码验证
            logger.info(f"[本地验证] 调用 sign_in: phone={registration.phone}, "
                       f"phone_code_hash={registration.phone_code_hash}, code={code}")
            try:
                await client.sign_in(
                    registration.phone,
                    registration.phone_code_hash,
                    code
                )
                logger.info(f"[本地验证] sign_in 成功: registration_id={registration.id}")
            except PhoneCodeExpired as e:
                logger.error(f"[本地验证] PhoneCodeExpired: registration_id={registration.id}, "
                           f"phone={registration.phone}, phone_code_hash={registration.phone_code_hash}, "
                           f"code={code}, error={str(e)}")
                registration.status = 'failed'
                registration.error_message = '验证码无效，请重新获取验证码'
                self.db.commit()
                raise ValueError('验证码无效，请重新获取验证码')
            except PhoneCodeInvalid as e:
                logger.error(f"[本地验证] PhoneCodeInvalid: registration_id={registration.id}, "
                           f"phone={registration.phone}, phone_code_hash={registration.phone_code_hash}, "
                           f"code={code}, error={str(e)}")
                registration.retry_count += 1
                self.db.commit()
                raise ValueError('验证码错误，请检查后重试')
            except SessionPasswordNeeded:
                if not password:
                    raise
                await client.check_password(password)
            
            # 获取用户信息
            me = await client.get_me()
            
            # 保存Session
            await client.storage.save()
            session_path = Path(client.storage.file.name).resolve()
            
            # 计算文件哈希
            import hashlib
            file_hash = hashlib.sha256(session_path.read_bytes()).hexdigest()
            
            await client.disconnect()
            
            return {
                'session_name': registration.session_name,
                'file_path': str(session_path),
                'file_size': session_path.stat().st_size,
                'file_hash': file_hash,
                'metadata': {
                    'user_id': me.id,
                    'username': me.username,
                    'first_name': me.first_name,
                    'last_name': me.last_name,
                }
            }
        finally:
            if client.is_connected:
                await client.disconnect()
    
    def _build_verify_script(
        self,
        registration: UserRegistration,
        code: str,
        password: Optional[str] = None,
    ) -> str:
        """构建验证脚本"""
        password_line = f'PASSWORD = "{password}"' if password else 'PASSWORD = None'
        
        return f"""#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import asyncio
import sys
import json
sys.path.insert(0, '/home/ubuntu')

from pyrogram import Client
from pyrogram.errors import SessionPasswordNeeded, PhoneCodeExpired, PhoneCodeInvalid

API_ID = {registration.api_id or 'None'}
API_HASH = '{registration.api_hash or ""}'
PHONE = {repr(registration.phone)}
SESSION_NAME = '{registration.session_name}'
PHONE_CODE_HASH = '{registration.phone_code_hash}'
CODE = {repr(code)}
{password_line}

async def verify():
    client = Client(
        SESSION_NAME,
        api_id=API_ID,
        api_hash=API_HASH,
        workdir="/home/ubuntu/sessions"
    )
    
    try:
        await client.connect()
        
        print("DEBUG: 准备验证验证码")
        print("DEBUG: PHONE=" + str(PHONE))
        print("DEBUG: PHONE_CODE_HASH=" + str(PHONE_CODE_HASH))
        print("DEBUG: CODE=" + str(CODE))
        print("DEBUG: CODE类型=" + str(type(CODE)))
        print("DEBUG: CODE长度=" + str(len(str(CODE))))
        
        try:
            await client.sign_in(PHONE, PHONE_CODE_HASH, CODE)
        except PhoneCodeExpired:
            print("ERROR:PHONE_CODE_EXPIRED")
            return
        except PhoneCodeInvalid:
            print("ERROR:PHONE_CODE_INVALID")
            return
        except SessionPasswordNeeded:
            if not PASSWORD:
                print("ERROR:PASSWORD_REQUIRED")
                return
            await client.check_password(PASSWORD)
        
        me = await client.get_me()
        user_info = {{
            "user_id": me.id,
            "username": me.username or "",
            "first_name": me.first_name or "",
            "last_name": me.last_name or "",
        }}
        print(f"SUCCESS:{{json.dumps(user_info)}}")
    finally:
        if client.is_connected:
            await client.disconnect()

if __name__ == "__main__":
    asyncio.run(verify())
"""
    
    def _validate_phone(self, phone: str) -> bool:
        """验证手机号格式"""
        import re
        pattern = r'^\+?[1-9]\d{1,14}$'
        return bool(re.match(pattern, phone))
    
    def _parse_proxy(self, proxy_url: str) -> Dict[str, Any]:
        """解析代理URL"""
        from urllib.parse import urlparse
        
        parsed = urlparse(proxy_url)
        proxy = {
            "scheme": parsed.scheme,
            "hostname": parsed.hostname,
            "port": parsed.port or (443 if parsed.scheme == 'https' else 80),
        }
        if parsed.username:
            proxy["username"] = parsed.username
        if parsed.password:
            proxy["password"] = parsed.password
        return proxy
    
    def get_registration_status(self, registration_id: str) -> Dict[str, Any]:
        """获取注册状态"""
        registration = self.db.query(UserRegistration).filter(
            UserRegistration.id == registration_id
        ).first()
        
        if not registration:
            raise ValueError("注册记录不存在")
        
        expires_at = None
        if registration.status == 'code_sent' and registration.updated_at:
            expires_at = registration.updated_at + timedelta(minutes=10)
        
        return {
            'registration_id': str(registration.id),
            'status': registration.status,
            'message': self._get_status_message(registration.status),
            'phone': registration.phone,
            'node_id': registration.node_id,
            'created_at': registration.created_at.isoformat(),
            'updated_at': registration.updated_at.isoformat(),
            'expires_at': expires_at.isoformat() if expires_at else None,
            'risk_score': registration.risk_score,
            'error_message': registration.error_message,
        }
    
    def _get_status_message(self, status: str) -> str:
        """获取状态消息"""
        messages = {
            'pending': '正在初始化...',
            'code_sent': '等待验证码输入',
            'verified': '等待两步验证密码',
            'completed': '注册成功',
            'failed': '注册失败',
        }
        return messages.get(status, '未知状态')
    
    def cancel_registration(self, registration_id: str) -> Dict[str, Any]:
        """取消注册"""
        registration = self.db.query(UserRegistration).filter(
            UserRegistration.id == registration_id
        ).first()
        
        if not registration:
            raise ValueError("注册记录不存在")
        
        if registration.status in ['completed', 'failed']:
            raise ValueError(f"无法取消已完成或失败的注册: {registration.status}")
        
        registration.status = 'failed'
        registration.error_message = '用户取消'
        self.db.commit()
        
        return {
            'message': '注册已取消'
        }

