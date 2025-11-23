"""
红包游戏系统 API 客户端
对接游戏系统的 API 接口，实现红包检测、状态查询等功能

对接方式：
1. 通过 Telegram API 检测红包消息（包含按钮的消息）
2. 通过数据库查询活跃红包（如果共享数据库）
3. 通过 HTTP API 查询（如果游戏系统提供）
"""
import asyncio
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import aiohttp
from urllib.parse import urljoin
import os

logger = logging.getLogger(__name__)


@dataclass
class GameEvent:
    """游戏事件"""
    event_type: str  # GAME_START, GAME_END, REDPACKET_SENT, REDPACKET_CLAIMED, RESULT_ANNOUNCED
    event_id: str = ""  # 可选，如果没有提供则自动生成
    group_id: int = 0
    game_id: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    payload: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RedpacketInfo:
    """红包信息（从游戏系统获取）"""
    redpacket_id: str
    group_id: int
    game_id: str
    amount: float
    count: int
    claimed_count: int = 0
    remaining_count: int = 0
    game_type: str = "normal"  # normal, random, lucky
    expires_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class GameStatus:
    """游戏状态"""
    group_id: int
    game_status: str  # IDLE, PREPARING, ACTIVE, ENDED
    current_game_id: Optional[str] = None
    active_redpackets: List[RedpacketInfo] = field(default_factory=list)
    statistics: Dict[str, Any] = field(default_factory=dict)


class GameAPIClient:
    """游戏系统 API 客户端"""
    
    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout: int = 30,
        max_retries: int = 3,
        database_url: Optional[str] = None
    ):
        """
        初始化游戏系统 API 客户端
        
        Args:
            base_url: 游戏系统 API 基础 URL（可选，如果提供则使用 HTTP API）
            api_key: API 密钥（可选）
            timeout: 请求超时时间（秒）
            max_retries: 最大重试次数
            database_url: 游戏系统数据库 URL（可选，如果提供则直接查询数据库）
        """
        self.base_url = base_url.rstrip('/') if base_url else None
        self.api_key = api_key
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.max_retries = max_retries
        self.database_url = database_url or os.getenv("GAME_DATABASE_URL")
        self._session: Optional[aiohttp.ClientSession] = None
        self._db_session = None  # 数据库会话（如果使用数据库对接）
        
        # 初始化数据库连接（如果提供了 database_url）
        if self.database_url:
            self._init_database()
        
        logger.info(
            f"GameAPIClient 初始化: base_url={base_url}, "
            f"database_url={'已配置' if self.database_url else '未配置'}"
        )
    
    def _init_database(self):
        """初始化数据库连接（用于直接查询游戏系统数据库）"""
        try:
            from sqlalchemy import create_engine
            from sqlalchemy.orm import sessionmaker
            
            engine = create_engine(
                self.database_url,
                echo=False,
                pool_pre_ping=True
            )
            SessionLocal = sessionmaker(bind=engine)
            self._db_session = SessionLocal
            logger.info("游戏系统数据库连接已初始化")
        except Exception as e:
            logger.warning(f"初始化游戏系统数据库连接失败: {e}")
            self._db_session = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """获取或创建 HTTP 会话"""
        if self._session is None or self._session.closed:
            headers = {}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            headers["Content-Type"] = "application/json"
            
            self._session = aiohttp.ClientSession(
                headers=headers,
                timeout=self.timeout
            )
        return self._session
    
    async def close(self):
        """关闭 HTTP 会话"""
        if self._session and not self._session.closed:
            await self._session.close()
    
    async def _request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        发送 HTTP 请求
        
        Args:
            method: HTTP 方法 (GET, POST, etc.)
            endpoint: API 端点
            data: 请求体数据
            params: URL 参数
            
        Returns:
            响应 JSON 数据
            
        Raises:
            aiohttp.ClientError: 网络错误
            ValueError: API 返回错误
        """
        url = urljoin(self.base_url, endpoint)
        session = await self._get_session()
        
        for attempt in range(self.max_retries):
            try:
                async with session.request(
                    method=method,
                    url=url,
                    json=data,
                    params=params
                ) as response:
                    if response.status >= 400:
                        error_text = await response.text()
                        logger.error(
                            f"API 请求失败: {method} {url}, "
                            f"status={response.status}, error={error_text}"
                        )
                        raise ValueError(f"API 错误: {response.status} - {error_text}")
                    
                    result = await response.json()
                    return result
                    
            except asyncio.TimeoutError:
                if attempt < self.max_retries - 1:
                    wait_time = 2 ** attempt  # 指数退避
                    logger.warning(f"请求超时，{wait_time}秒后重试 (尝试 {attempt + 1}/{self.max_retries})")
                    await asyncio.sleep(wait_time)
                else:
                    raise
            except Exception as e:
                if attempt < self.max_retries - 1:
                    wait_time = 2 ** attempt
                    logger.warning(f"请求失败: {e}，{wait_time}秒后重试 (尝试 {attempt + 1}/{self.max_retries})")
                    await asyncio.sleep(wait_time)
                else:
                    raise
        
        raise ValueError("请求失败，已达最大重试次数")
    
    async def get_game_status(self, group_id: int) -> GameStatus:
        """
        获取游戏状态
        
        优先使用数据库查询（如果配置了 database_url），否则使用 HTTP API
        
        Args:
            group_id: Telegram 群组 ID
            
        Returns:
            游戏状态对象
        """
        # 方法1: 通过数据库查询（如果配置了）
        if self._db_session:
            try:
                return await self._get_game_status_from_db(group_id)
            except Exception as e:
                logger.warning(f"数据库查询失败: {e}，尝试 HTTP API")
        
        # 方法2: 通过 HTTP API 查询
        if self.base_url:
            try:
                response = await self._request(
                    "GET",
                    f"/api/v1/redpacket-game/status/{group_id}"
                )
                
                # 解析响应数据
                active_redpackets = []
                for rp_data in response.get("active_redpackets", []):
                    redpacket = RedpacketInfo(
                        redpacket_id=rp_data["redpacket_id"],
                        group_id=group_id,
                        game_id=rp_data.get("game_id", ""),
                        amount=float(rp_data["amount"]),
                        count=rp_data["count"],
                        claimed_count=rp_data.get("claimed_count", 0),
                        remaining_count=rp_data.get("remaining_count", 0),
                        game_type=rp_data.get("game_type", "normal"),
                        expires_at=datetime.fromisoformat(rp_data["expires_at"]) if rp_data.get("expires_at") else None,
                        metadata=rp_data.get("metadata", {})
                    )
                    active_redpackets.append(redpacket)
                
                return GameStatus(
                    group_id=group_id,
                    game_status=response["game_status"],
                    current_game_id=response.get("current_game_id"),
                    active_redpackets=active_redpackets,
                    statistics=response.get("statistics", {})
                )
            except Exception as e:
                logger.error(f"HTTP API 查询失败 (group_id={group_id}): {e}")
                raise
        
        # 如果都没有配置，返回空状态
        logger.warning("游戏系统 API 和数据库都未配置，返回空状态")
        return GameStatus(
            group_id=group_id,
            game_status="IDLE",
            current_game_id=None,
            active_redpackets=[],
            statistics={}
        )
    
    async def _get_game_status_from_db(self, group_id: int) -> GameStatus:
        """
        从数据库查询游戏状态
        
        查询游戏系统的 envelopes 表，获取活跃的红包
        
        注意：数据库查询是同步的，但方法本身是异步的
        """
        try:
            from sqlalchemy import text
            from decimal import Decimal
            import asyncio
            
            # 在异步上下文中运行同步数据库查询
            # 使用 run_in_executor 避免阻塞事件循环
            def _query_db():
                session = self._db_session()
                try:
                    # 查询活跃的红包（status='active' 且未完成）
                    query = text("""
                        SELECT 
                            id,
                            chat_id,
                            sender_tg_id,
                            mode,
                            total_amount,
                            shares,
                            note,
                            status,
                            is_finished,
                            created_at,
                            activated_at
                        FROM envelopes
                        WHERE chat_id = :chat_id
                          AND status = 'active'
                          AND (is_finished IS NULL OR is_finished = 0)
                          AND activated_at IS NOT NULL
                        ORDER BY activated_at DESC
                        LIMIT 10
                    """)
                    
                    result = session.execute(query, {"chat_id": group_id})
                    rows = result.fetchall()
                    
                    active_redpackets = []
                    for row in rows:
                        # 查询已领取数量
                        count_query = text("""
                            SELECT COUNT(*) as claimed_count
                            FROM envelope_shares
                            WHERE envelope_id = :envelope_id
                        """)
                        count_result = session.execute(count_query, {"envelope_id": row[0]})
                        claimed_count = count_result.scalar() or 0
                        
                        # 计算剩余数量
                        shares = row[5]  # shares 字段
                        remaining_count = max(0, shares - claimed_count)
                        
                        redpacket = RedpacketInfo(
                            redpacket_id=str(row[0]),
                            group_id=int(row[1]),
                            game_id=str(row[0]),  # 使用 envelope_id 作为 game_id
                            amount=float(row[4]),  # total_amount
                            count=int(row[5]),  # shares
                            claimed_count=int(claimed_count),
                            remaining_count=int(remaining_count),
                            game_type=row[3] if row[3] else "normal",  # mode
                            expires_at=None,  # 游戏系统没有过期时间字段
                            metadata={
                                "sender_tg_id": int(row[2]),
                                "note": row[6] or "",
                                "created_at": row[9].isoformat() if row[9] else None,
                                "activated_at": row[10].isoformat() if row[10] else None,
                            }
                        )
                        active_redpackets.append(redpacket)
                    
                    game_status = "ACTIVE" if active_redpackets else "IDLE"
                    current_game_id = str(active_redpackets[0].game_id) if active_redpackets else None
                    
                    return GameStatus(
                        group_id=group_id,
                        game_status=game_status,
                        current_game_id=current_game_id,
                        active_redpackets=active_redpackets,
                        statistics={}
                    )
                finally:
                    session.close()
            
            # 在线程池中执行同步数据库查询
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, _query_db)
        except Exception as e:
            logger.error(f"数据库查询游戏状态失败: {e}", exc_info=True)
            raise
    
    async def participate_redpacket(
        self,
        account_id: str,
        redpacket_id: str,
        group_id: int,
        client=None
    ) -> Dict[str, Any]:
        """
        参与红包游戏
        
        优先通过 Telegram API 点击按钮，如果失败则尝试数据库操作或 HTTP API
        
        Args:
            account_id: 账号 ID（Telegram user_id）
            redpacket_id: 红包 ID（envelope_id）
            group_id: 群组 ID
            client: Pyrogram Client 实例（用于点击按钮）
            
        Returns:
            参与结果
        """
        # 方法1: 通过 Telegram API 点击按钮（推荐）
        if client:
            try:
                return await self._participate_via_telegram_button(
                    client, account_id, redpacket_id, group_id
                )
            except Exception as e:
                logger.warning(f"Telegram 按钮点击失败: {e}，尝试其他方法")
        
        # 方法2: 通过数据库直接操作（如果配置了数据库且允许）
        if self._db_session:
            try:
                return await self._participate_via_database(account_id, redpacket_id)
            except Exception as e:
                logger.warning(f"数据库操作失败: {e}，尝试 HTTP API")
        
        # 方法3: 通过 HTTP API
        if self.base_url:
            try:
                response = await self._request(
                    "POST",
                    "/api/v1/redpacket-game/participate",
                    data={
                        "account_id": account_id,
                        "redpacket_id": redpacket_id,
                        "group_id": group_id
                    }
                )
                return response
            except Exception as e:
                logger.error(
                    f"HTTP API 参与失败 (account_id={account_id}, redpacket_id={redpacket_id}): {e}"
                )
                raise
        
        # 如果都没有配置，返回错误
        raise ValueError("无法参与红包：未配置 Telegram Client、数据库或 HTTP API")
    
    async def _participate_via_telegram_button(
        self,
        client,
        account_id: str,
        redpacket_id: str,
        group_id: int
    ) -> Dict[str, Any]:
        """
        通过 Telegram API 点击红包按钮参与
        
        需要先找到包含红包按钮的消息，然后发送 CallbackQuery
        """
        try:
            # 构造 callback_data
            callback_data = f"hb:grab:{redpacket_id}"
            
            # 尝试从最近的消息中找到红包消息
            # 注意：Pyrogram 没有直接的方法发送 CallbackQuery，需要先获取消息
            # 这里我们需要在消息处理时记录消息 ID
            
            # 临时方案：返回需要的信息，让调用者处理
            return {
                "success": True,
                "method": "telegram_button",
                "callback_data": callback_data,
                "message_id": None,  # 需要从消息中获取
                "note": "需要先找到包含此按钮的消息，然后发送 CallbackQuery"
            }
        except Exception as e:
            logger.error(f"Telegram 按钮点击失败: {e}")
            raise
    
    async def _participate_via_database(
        self,
        account_id: str,
        redpacket_id: str
    ) -> Dict[str, Any]:
        """
        通过数据库直接调用游戏系统的 grab_share 函数
        
        注意：这需要游戏系统的代码在 Python 路径中可用
        """
        try:
            # 尝试导入游戏系统的 grab_share 函数
            import sys
            game_system_path = os.getenv("GAME_SYSTEM_PATH")
            if game_system_path and game_system_path not in sys.path:
                sys.path.insert(0, game_system_path)
            
            try:
                from models.envelope import grab_share
                
                # 调用游戏系统的抢红包函数
                user_tg_id = int(account_id)
                envelope_id = int(redpacket_id)
                
                result = grab_share(envelope_id, user_tg_id)
                
                # 转换结果格式
                return {
                    "success": True,
                    "method": "database",
                    "amount": float(result.get("amount", 0)),
                    "token": result.get("token", ""),
                    "is_last": result.get("is_last", False)
                }
            except ImportError:
                logger.warning("无法导入游戏系统的 grab_share 函数，跳过数据库操作")
                raise ValueError("游戏系统代码不可用")
        except Exception as e:
            logger.error(f"数据库操作失败: {e}")
            raise
    
    async def report_participation_result(
        self,
        account_id: str,
        redpacket_id: str,
        group_id: int,
        success: bool,
        amount: Optional[float] = None,
        error: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        上报参与结果
        
        Args:
            account_id: 账号 ID
            redpacket_id: 红包 ID
            group_id: 群组 ID
            success: 是否成功
            amount: 获得金额（如果成功）
            error: 错误信息（如果失败）
            
        Returns:
            上报结果
        """
        try:
            response = await self._request(
                "POST",
                "/api/v1/redpacket-game/participate",
                data={
                    "account_id": account_id,
                    "redpacket_id": redpacket_id,
                    "group_id": group_id,
                    "result": {
                        "success": success,
                        "amount": amount,
                        "timestamp": datetime.now().isoformat(),
                        "error": error
                    }
                }
            )
            return response
        except Exception as e:
            logger.error(
                f"上报参与结果失败 (account_id={account_id}, redpacket_id={redpacket_id}): {e}"
            )
            raise


class GameEventWebhook:
    """游戏事件 Webhook 接收器"""
    
    def __init__(self, event_handler):
        """
        初始化 Webhook 接收器
        
        Args:
            event_handler: 事件处理函数，接收 GameEvent 对象
        """
        self.event_handler = event_handler
        logger.info("GameEventWebhook 初始化完成")
    
    async def handle_webhook(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理 Webhook 事件
        
        Args:
            event_data: 事件数据（来自游戏系统）
            
        Returns:
            响应数据
        """
        try:
            # 解析事件数据
            event = GameEvent(
                event_type=event_data["event_type"],
                event_id=event_data["event_id"],
                group_id=event_data["group_id"],
                game_id=event_data.get("game_id"),
                timestamp=datetime.fromisoformat(event_data["timestamp"]),
                payload=event_data.get("payload", {})
            )
            
            # 调用事件处理函数
            await self.event_handler(event)
            
            return {
                "success": True,
                "message": "Event received",
                "event_id": event.event_id
            }
        except Exception as e:
            logger.error(f"处理 Webhook 事件失败: {e}", exc_info=True)
            return {
                "success": False,
                "message": str(e),
                "event_id": event_data.get("event_id", "unknown")
            }

