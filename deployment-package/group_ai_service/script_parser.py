"""
劇本解析器 - 解析 YAML 格式的對話劇本
"""
import yaml
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class Trigger:
    """觸發條件"""
    type: str  # keyword, message, new_member, redpacket, etc.
    keywords: Optional[List[str]] = None
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    pattern: Optional[str] = None  # 正則表達式
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Response:
    """回復模板"""
    template: str
    ai_generate: bool = False
    context_window: int = 10
    temperature: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Scene:
    """場景定義"""
    id: str
    triggers: List[Trigger] = field(default_factory=list)
    responses: List[Response] = field(default_factory=list)
    next_scene: Optional[str] = None
    timeout: Optional[int] = None  # 超時時間（秒）
    on_timeout: Optional[str] = None  # 超時後執行的動作
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Script:
    """劇本定義"""
    script_id: str
    version: str
    description: Optional[str] = None
    scenes: Dict[str, Scene] = field(default_factory=dict)
    states: Dict[str, Any] = field(default_factory=dict)
    variables: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


class ScriptParser:
    """劇本解析器"""
    
    def __init__(self):
        self.scripts: Dict[str, Script] = {}
    
    def load_script(self, script_path: str) -> Script:
        """從文件加載劇本"""
        path = Path(script_path)
        if not path.exists():
            raise FileNotFoundError(f"劇本文件不存在: {script_path}")
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            
            # 驗證數據類型
            if data is None:
                raise ValueError("YAML 文件為空或格式不正確")
            if not isinstance(data, dict):
                raise ValueError(f"劇本數據格式錯誤：期望字典類型，實際為 {type(data).__name__}。請確保 YAML 文件包含 script_id 和 scenes 字段。")
            
            script = self._parse_script(data)
            self.scripts[script.script_id] = script
            logger.info(f"劇本加載成功: {script.script_id} v{script.version}")
            return script
        
        except yaml.YAMLError as e:
            raise ValueError(f"YAML 解析失敗: {e}")
        except Exception as e:
            raise ValueError(f"劇本解析失敗: {e}")
    
    def _parse_script(self, data: Dict[str, Any]) -> Script:
        """解析劇本數據"""
        # 確保 data 是字典類型
        if not isinstance(data, dict):
            raise ValueError(f"劇本數據格式錯誤：期望字典類型，實際為 {type(data).__name__}")
        
        script_id = data.get('script_id')
        if not script_id:
            raise ValueError("劇本缺少 script_id")
        
        version = data.get('version', '1.0')
        description = data.get('description')
        
        # 解析場景
        scenes = {}
        scenes_data = data.get('scenes', [])
        if not isinstance(scenes_data, list):
            raise ValueError(f"scenes 字段必須是列表類型，實際為 {type(scenes_data).__name__}")
        
        for scene_data in scenes_data:
            scene = self._parse_scene(scene_data)
            scenes[scene.id] = scene
        
        # 解析狀態
        states = data.get('states', {})
        
        # 解析變量
        variables = data.get('variables', {})
        
        # 元數據
        metadata = data.get('metadata', {})
        
        return Script(
            script_id=script_id,
            version=version,
            description=description,
            scenes=scenes,
            states=states,
            variables=variables,
            metadata=metadata
        )
    
    def _parse_scene(self, data: Dict[str, Any]) -> Scene:
        """解析場景"""
        scene_id = data.get('id')
        if not scene_id:
            raise ValueError("場景缺少 id")
        
        # 解析觸發條件
        triggers = []
        triggers_data = data.get('triggers', [])
        
        # 如果triggers为空或不存在，添加默认trigger
        if not triggers_data or len(triggers_data) == 0:
            triggers_data = [{"type": "message"}]
            logger.warning(f"場景 {scene_id} 缺少 triggers，已添加默認 trigger")
        
        for trigger_data in triggers_data:
            # 如果trigger_data不是字典，跳过或使用默认值
            if not isinstance(trigger_data, dict):
                logger.warning(f"場景 {scene_id} 的 trigger 不是字典類型，使用默認值")
                trigger_data = {"type": "message"}
            
            # 如果缺少type字段，添加默认值
            if "type" not in trigger_data:
                trigger_data["type"] = "message"
                logger.warning(f"場景 {scene_id} 的 trigger 缺少 type 字段，已添加默認值")
            
            trigger = self._parse_trigger(trigger_data)
            triggers.append(trigger)
        
        # 解析回復模板
        responses = []
        responses_data = data.get('responses', [])
        for response_data in responses_data:
            response = self._parse_response(response_data)
            responses.append(response)
        
        next_scene = data.get('next_scene')
        timeout = data.get('timeout')
        on_timeout = data.get('on_timeout')
        metadata = data.get('metadata', {})
        
        return Scene(
            id=scene_id,
            triggers=triggers,
            responses=responses,
            next_scene=next_scene,
            timeout=timeout,
            on_timeout=on_timeout,
            metadata=metadata
        )
    
    def _parse_trigger(self, data: Dict[str, Any]) -> Trigger:
        """解析觸發條件"""
        trigger_type = data.get('type')
        if not trigger_type:
            raise ValueError("觸發條件缺少 type")
        
        keywords = data.get('keywords')
        min_length = data.get('min_length')
        max_length = data.get('max_length')
        pattern = data.get('pattern')
        metadata = data.get('metadata', {})
        
        return Trigger(
            type=trigger_type,
            keywords=keywords,
            min_length=min_length,
            max_length=max_length,
            pattern=pattern,
            metadata=metadata
        )
    
    def _parse_response(self, data: Dict[str, Any]) -> Response:
        """解析回復模板"""
        template = data.get('template', '')
        ai_generate = data.get('ai_generate', False)
        context_window = data.get('context_window', 10)
        temperature = data.get('temperature')
        metadata = data.get('metadata', {})
        
        return Response(
            template=template,
            ai_generate=ai_generate,
            context_window=context_window,
            temperature=temperature,
            metadata=metadata
        )
    
    def get_script(self, script_id: str) -> Optional[Script]:
        """獲取已加載的劇本"""
        return self.scripts.get(script_id)
    
    def validate_script(self, script: Script) -> List[str]:
        """驗證劇本邏輯"""
        errors = []
        
        # 檢查場景引用
        for scene_id, scene in script.scenes.items():
            if scene.next_scene and scene.next_scene not in script.scenes:
                errors.append(f"場景 {scene_id} 引用了不存在的場景: {scene.next_scene}")
        
        # 檢查是否有初始場景
        if not script.scenes:
            errors.append("劇本沒有定義任何場景")
        
        return errors

