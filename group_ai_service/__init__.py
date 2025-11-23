"""
Telegram 群組多 AI 賬號智能管理系統
"""
__version__ = "0.1.0"

from group_ai_service.account_manager import AccountManager, AccountInstance
from group_ai_service.session_pool import ExtendedSessionPool
from group_ai_service.config import get_group_ai_config
from group_ai_service.script_parser import ScriptParser, Script
from group_ai_service.script_engine import ScriptEngine
from group_ai_service.variable_resolver import VariableResolver
from group_ai_service.ai_generator import AIGenerator, get_ai_generator
from group_ai_service.dialogue_manager import DialogueManager, DialogueContext
from group_ai_service.redpacket_handler import (
    RedpacketHandler,
    RedpacketInfo,
    RedpacketResult,
    RedpacketStrategy,
    RandomStrategy,
    TimeBasedStrategy,
    FrequencyStrategy,
    AmountBasedStrategy,
    CompositeStrategy,
)
from group_ai_service.monitor_service import MonitorService, AccountMetrics, SystemMetrics, Alert
from group_ai_service.format_converter import FormatConverter
from group_ai_service.enhanced_format_converter import EnhancedFormatConverter
from group_ai_service.text_parser import TextParser
from group_ai_service.yaml_validator import YAMLValidator
from group_ai_service.service_manager import ServiceManager

__all__ = [
    "AccountManager",
    "AccountInstance",
    "ExtendedSessionPool",
    "get_group_ai_config",
    "ScriptParser",
    "Script",
    "ScriptEngine",
    "VariableResolver",
    "AIGenerator",
    "get_ai_generator",
    "DialogueManager",
    "DialogueContext",
    "RedpacketHandler",
    "RedpacketInfo",
    "RedpacketResult",
    "RedpacketStrategy",
    "RandomStrategy",
    "TimeBasedStrategy",
    "FrequencyStrategy",
    "AmountBasedStrategy",
    "CompositeStrategy",
    "MonitorService",
    "AccountMetrics",
    "SystemMetrics",
    "Alert",
    "FormatConverter",
    "EnhancedFormatConverter",
    "TextParser",
    "YAMLValidator",
    "ServiceManager",
]

