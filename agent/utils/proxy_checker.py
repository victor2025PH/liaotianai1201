"""
Proxy IP 绑定检查器 - Phase 4: 风控与指纹管理
确保 Agent 通过指定的 Proxy 连接，防止意外使用本地 IP
"""

import asyncio
import logging
import aiohttp
from typing import Optional, Tuple
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


async def check_proxy_ip(
    proxy_url: Optional[str],
    expected_ip: Optional[str] = None,
    timeout: int = 10
) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    检查 Proxy IP 绑定
    
    Args:
        proxy_url: Proxy URL (格式: http://user:pass@host:port 或 socks5://...)
        expected_ip: 期望的出口 IP（如果提供，会验证是否匹配）
        timeout: 请求超时时间（秒）
    
    Returns:
        (是否成功, 当前出口IP, 错误信息)
    
    注意:
        - 如果 proxy_url 为 None，返回 (False, None, "未配置 Proxy")
        - 如果请求失败，返回 (False, None, 错误信息)
        - 如果 expected_ip 不匹配，返回 (False, current_ip, "IP 不匹配")
    """
    if not proxy_url:
        return False, None, "未配置 Proxy，拒绝启动（防止意外使用本地 IP）"
    
    try:
        # 解析 Proxy URL
        parsed = urlparse(proxy_url)
        proxy_type = parsed.scheme.lower()
        
        if proxy_type not in ["http", "https", "socks5", "socks4"]:
            return False, None, f"不支持的 Proxy 类型: {proxy_type}"
        
        # 构建 aiohttp 的 proxy 参数
        proxy_aiohttp = proxy_url
        
        # 使用 aiohttp 通过 Proxy 请求 IP 检查服务
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=timeout)) as session:
            try:
                # 使用多个 IP 检查服务（提高可靠性）
                ip_check_urls = [
                    "https://api.ipify.org?format=json",
                    "https://api.myip.com",
                    "https://ipinfo.io/json"
                ]
                
                current_ip = None
                last_error = None
                
                for url in ip_check_urls:
                    try:
                        async with session.get(url, proxy=proxy_aiohttp) as response:
                            if response.status == 200:
                                data = await response.json()
                                
                                # 不同服务返回格式不同
                                if "ip" in data:
                                    current_ip = data["ip"]
                                elif "query" in data:
                                    current_ip = data["query"]
                                else:
                                    # 有些服务直接返回 IP 字符串
                                    text = await response.text()
                                    current_ip = text.strip()
                                
                                if current_ip:
                                    break
                    except Exception as e:
                        last_error = str(e)
                        logger.warning(f"IP 检查服务 {url} 失败: {e}")
                        continue
                
                if not current_ip:
                    return False, None, f"无法获取出口 IP: {last_error or '所有服务都失败'}"
                
                logger.info(f"当前出口 IP: {current_ip}")
                
                # 如果提供了期望 IP，进行验证
                if expected_ip:
                    if current_ip != expected_ip:
                        return (
                            False,
                            current_ip,
                            f"IP 不匹配: 期望 {expected_ip}, 实际 {current_ip}"
                        )
                    logger.info(f"IP 验证通过: {current_ip}")
                
                return True, current_ip, None
                
            except aiohttp.ClientError as e:
                return False, None, f"Proxy 连接失败: {str(e)}"
            except asyncio.TimeoutError:
                return False, None, f"Proxy 请求超时（{timeout}秒）"
            except Exception as e:
                return False, None, f"检查 Proxy IP 时发生错误: {str(e)}"
    
    except Exception as e:
        return False, None, f"解析 Proxy URL 失败: {str(e)}"


async def validate_proxy_binding(proxy_url: Optional[str], expected_ip: Optional[str] = None) -> None:
    """
    验证 Proxy 绑定（如果失败则抛出异常）
    
    Args:
        proxy_url: Proxy URL
        expected_ip: 期望的出口 IP
    
    Raises:
        RuntimeError: 如果 Proxy 检查失败
    """
    success, current_ip, error = await check_proxy_ip(proxy_url, expected_ip)
    
    if not success:
        error_msg = f"Proxy IP 绑定检查失败: {error}"
        if current_ip:
            error_msg += f" (当前 IP: {current_ip})"
        
        logger.error(error_msg)
        raise RuntimeError(error_msg)
    
    logger.info("Proxy IP 绑定检查通过")
