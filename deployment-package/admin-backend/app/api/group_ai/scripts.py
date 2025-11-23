"""
劇本管理 API
"""
import logging
import sys
import yaml
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, HTTPException, status, Depends, UploadFile, File, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

# 添加項目根目錄到路徑
project_root = Path(__file__).parent.parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from group_ai_service import ScriptParser, Script
from group_ai_service.format_converter import FormatConverter
from group_ai_service.enhanced_format_converter import EnhancedFormatConverter
from app.db import get_db
from app.models.group_ai import GroupAIScript, GroupAIScriptVersion
from app.api.deps import get_current_active_user
from app.middleware.permission import check_permission
from app.core.permissions import PermissionCode
from app.models.user import User

# 導入緩存功能
from app.core.cache import cached, invalidate_cache

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Group AI Scripts"])

# 初始化劇本解析器
script_parser = ScriptParser()
format_converter = FormatConverter()
enhanced_converter = EnhancedFormatConverter()


class ScriptCreateRequest(BaseModel):
    """創建劇本請求"""
    script_id: str = Field(..., description="劇本 ID")
    name: str = Field(..., description="劇本名稱")
    version: str = Field(default="1.0", description="版本號")
    description: Optional[str] = Field(None, description="描述")
    yaml_content: str = Field(..., description="YAML 內容")


class ScriptUpdateRequest(BaseModel):
    """更新劇本請求"""
    name: Optional[str] = None
    version: Optional[str] = None
    description: Optional[str] = None
    yaml_content: Optional[str] = None


class ScriptResponse(BaseModel):
    """劇本響應"""
    script_id: str
    name: str
    version: str
    description: Optional[str] = None
    scene_count: int = 0
    status: Optional[str] = None  # 狀態：draft, reviewing, approved, rejected, published, disabled
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    
    class Config:
        from_attributes = True
    
    def model_dump(self, **kwargs):
        """重写model_dump以包含id字段"""
        data = super().model_dump(**kwargs)
        data['id'] = self.script_id
        return data
    
    def dict(self, **kwargs):
        """兼容旧版Pydantic的dict方法"""
        data = super().dict(**kwargs)
        data['id'] = self.script_id
        return data


class ScriptDetailResponse(ScriptResponse):
    """劇本詳情響應"""
    yaml_content: str
    scenes: List[dict] = []


@router.post("/", response_model=ScriptResponse, status_code=status.HTTP_201_CREATED)
async def create_script(
    request: ScriptCreateRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """創建劇本（需要 script:create 權限）"""
    check_permission(current_user, PermissionCode.SCRIPT_CREATE.value, db)
    # 創建後清除劇本列表緩存
    invalidate_cache("scripts_list")
    temp_path = None
    try:
        # 驗證 YAML 內容
        import tempfile
        import yaml
        
        # 在解析前，先使用增强转换器验证和修复YAML内容
        try:
            from group_ai_service.yaml_validator import YAMLValidator
            fixed_content, warnings = YAMLValidator.validate_and_fix_yaml_content(request.yaml_content)
            
            # 如果有修复，更新YAML内容
            if warnings:
                logger.info(f"YAML内容已修复，警告: {warnings}")
                request.yaml_content = fixed_content
        except Exception as e:
            logger.warning(f"YAML预处理失败，继续使用原始内容: {e}")
        
        # 創建臨時文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False, encoding='utf-8') as f:
            f.write(request.yaml_content)
            temp_path = f.name
        
        # 確保文件已寫入並關閉
        import os
        if not os.path.exists(temp_path):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="臨時文件創建失敗"
            )
        
        # 解析和驗證劇本
        try:
            script = script_parser.load_script(temp_path)
        except yaml.scanner.ScannerError as e:
            # YAML 掃描錯誤（語法錯誤，如缺少冒號、引號未閉合等）
            error_msg = str(e)
            line_info = ""
            if hasattr(e, 'problem_mark') and e.problem_mark:
                line = e.problem_mark.line + 1  # YAML 行號從 0 開始
                column = e.problem_mark.column + 1  # YAML 列號從 0 開始
                line_info = f"第 {line} 行，第 {column} 列"
            elif "line" in error_msg.lower():
                # 嘗試從錯誤信息中提取行號
                import re
                match = re.search(r'line\s+(\d+)', error_msg, re.IGNORECASE)
                if match:
                    line_info = f"第 {match.group(1)} 行"
            
            # 提取具體的問題描述
            problem_desc = ""
            if "could not find expected ':'" in error_msg or "找不到預期的 ':'" in error_msg:
                problem_desc = "缺少冒號（:）。YAML 格式要求鍵值對必須使用冒號分隔，例如：`key: value`"
            elif "could not find expected" in error_msg:
                problem_desc = "YAML 語法錯誤。可能是縮進不正確、缺少冒號或引號未閉合"
            elif "mapping values are not allowed" in error_msg:
                problem_desc = "映射值格式錯誤。檢查縮進是否正確，鍵值對是否使用冒號分隔"
            else:
                problem_desc = "YAML 語法錯誤"
            
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"YAML 解析失敗：{problem_desc}\n\n位置：{line_info if line_info else '未知'}\n\n建議：\n  • 檢查 YAML 格式是否正確（特別是縮進和冒號）\n  • 確保所有鍵值對都使用冒號分隔，例如：`key: value`\n  • 檢查引號是否正確閉合\n  • 如果是舊格式，請先使用「智能轉換」功能\n  • 可以使用在線 YAML 驗證工具檢查語法"
            )
        except yaml.parser.ParserError as e:
            # YAML 解析錯誤（結構錯誤）
            error_msg = str(e)
            line_info = ""
            if hasattr(e, 'problem_mark') and e.problem_mark:
                line = e.problem_mark.line + 1
                column = e.problem_mark.column + 1
                line_info = f"第 {line} 行，第 {column} 列"
            
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"YAML 解析失敗：YAML 結構錯誤\n\n位置：{line_info if line_info else '未知'}\n錯誤詳情：{error_msg}\n\n建議：\n  • 檢查 YAML 格式是否正確\n  • 確保包含 script_id、version 和 scenes 字段\n  • 檢查縮進是否一致（建議使用 2 個空格）\n  • 如果是舊格式，請先使用「智能轉換」功能"
            )
        except ValueError as e:
            # 提供更友好的錯誤信息
            error_msg = str(e)
            if "缺少 script_id" in error_msg or "script_id" in error_msg:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="劇本格式錯誤：缺少 script_id 字段。請確保 YAML 格式正確，包含 script_id、version 和 scenes 字段。\n\n建議：\n  • 如果是舊格式，請先使用「智能轉換」功能\n  • 檢查 YAML 文件是否包含 script_id 字段"
                )
            elif "缺少 id" in error_msg or ("scene" in error_msg.lower() and "id" in error_msg):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="劇本格式錯誤：場景缺少 id 字段。每個場景必須有唯一的 id。\n\n建議：\n  • 確保每個場景都有 id 字段\n  • 檢查場景結構是否正確"
                )
            elif "觸發條件缺少 type" in error_msg or "trigger" in error_msg.lower() and "type" in error_msg.lower():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="劇本格式錯誤：觸發條件缺少 type 字段。\n\n建議：\n  • 確保每個場景的 triggers 都包含至少一個 trigger\n  • 每個 trigger 必須包含 type 字段（如 \"message\"）\n  • 如果使用「智能轉換」功能，系統會自動修復此問題\n  • 手動編輯時，請確保格式如下：\n    triggers:\n      - type: message"
                )
            elif "格式錯誤" in error_msg or "期望" in error_msg:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"劇本格式錯誤：{error_msg}\n\n建議：\n  • 檢查 YAML 格式是否正確\n  • 確保使用字典格式（包含 script_id 和 scenes）\n  • 如果是舊格式，請先使用「智能轉換」功能"
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"劇本解析失敗: {error_msg}\n\n建議：\n  • 檢查 YAML 格式是否正確\n  • 確保包含 script_id、version 和 scenes 字段\n  • 如果是舊格式，請先使用「智能轉換」功能"
                )
        except FileNotFoundError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"無法讀取臨時文件: {str(e)}"
            )
        except Exception as e:
            # 其他未預期的錯誤
            error_msg = str(e)
            # 嘗試檢查是否包含 YAML 相關的錯誤信息
            if "yaml" in error_msg.lower() or "line" in error_msg.lower():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"劇本解析失敗：{error_msg}\n\n建議：\n  • 檢查 YAML 格式是否正確\n  • 確保包含 script_id、version 和 scenes 字段\n  • 如果是舊格式，請先使用「智能轉換」功能\n  • 檢查縮進和語法是否正確"
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"劇本解析失敗: {error_msg}\n\n建議：\n  • 檢查 YAML 格式是否正確\n  • 確保包含 script_id、version 和 scenes 字段\n  • 如果是舊格式，請先使用「智能轉換」功能"
                )
        
        errors = script_parser.validate_script(script)
        if errors:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"劇本驗證失敗: {', '.join(errors)}"
            )
        
        # 檢查是否已存在
        existing = db.query(GroupAIScript).filter(
            GroupAIScript.script_id == request.script_id
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"劇本 {request.script_id} 已存在"
            )
        
        # 保存到數據庫
        import uuid
        db_script = GroupAIScript(
            id=str(uuid.uuid4()),  # 生成UUID
            script_id=request.script_id,
            name=request.name,
            version=request.version,
            description=request.description,
            yaml_content=request.yaml_content,
            status="draft"  # 默認狀態為草稿
        )
        db.add(db_script)
        
        # 創建初始版本記錄
        version_record = GroupAIScriptVersion(
            script_id=request.script_id,
            version=request.version,
            yaml_content=request.yaml_content,
            description=request.description,
            change_summary="初始版本"
        )
        db.add(version_record)
        
        try:
            # 先 flush 確保數據寫入（但不提交事務）
            db.flush()
            # 然後提交事務
            db.commit()
            # 刷新對象以獲取最新數據（包括自動生成的字段）
            db.refresh(db_script)
            db.refresh(version_record)
            
            logger.info(f"劇本創建成功: {request.script_id} (ID: {db_script.id})")
            
            # 驗證數據是否已保存（使用新的會話確保讀取到最新數據）
            # 等待一小段時間確保數據庫寫入完成（特別是 WAL 模式）
            import time
            time.sleep(0.1)  # 等待 100ms 確保 WAL 寫入完成
            
            from app.db import SessionLocal as NewSessionLocal
            verify_db = NewSessionLocal()
            try:
                saved_script = verify_db.query(GroupAIScript).filter(
                    GroupAIScript.script_id == request.script_id
                ).first()
                if not saved_script:
                    logger.error(f"劇本創建後驗證失敗: {request.script_id} 在數據庫中不存在")
                    # 再次嘗試查詢（可能是 WAL 延遲）
                    time.sleep(0.2)
                    saved_script = verify_db.query(GroupAIScript).filter(
                        GroupAIScript.script_id == request.script_id
                    ).first()
                    if not saved_script:
                        logger.error(f"劇本驗證再次失敗: {request.script_id} 在數據庫中不存在")
                        raise HTTPException(
                            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="劇本保存失敗：數據未正確寫入數據庫。請檢查數據庫文件和權限。"
                        )
                logger.info(f"劇本驗證成功: {saved_script.script_id} 已持久化到數據庫 (ID: {saved_script.id})")
            finally:
                verify_db.close()
            
            # 清除緩存，確保新劇本能立即在列表中顯示（在驗證之後清除，確保數據已保存）
            cache_cleared = invalidate_cache("scripts_list*")
            logger.debug(f"已清除 {cache_cleared} 個劇本列表緩存鍵")
            
            return ScriptResponse(
                script_id=db_script.script_id,
                name=db_script.name,
                version=db_script.version,
                description=db_script.description,
                scene_count=len(script.scenes),
                status=db_script.status,
                created_at=db_script.created_at.isoformat() if db_script.created_at else None,
                updated_at=db_script.updated_at.isoformat() if db_script.updated_at else None
            )
        except HTTPException:
            db.rollback()
            raise
        except Exception as e:
            db.rollback()
            logger.error(f"保存劇本到數據庫失敗: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"保存劇本失敗: {str(e)}"
            )
    
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"創建劇本失敗: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"創建劇本失敗: {str(e)}"
        )
    finally:
        # 清理臨時文件
        if 'temp_path' in locals() and temp_path:
            try:
                import os
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
            except Exception as e:
                logger.warning(f"清理臨時文件失敗: {e}")


@router.get("/", response_model=List[ScriptResponse])
async def list_scripts(
    skip: int = Query(0, ge=0, description="跳過數量"),
    limit: int = Query(100, ge=1, le=1000, description="每頁數量"),
    search: Optional[str] = Query(None, description="搜索關鍵詞（名稱、ID、描述）"),
    status: Optional[str] = Query(None, description="狀態過濾（draft, reviewing, published, disabled）"),
    sort_by: Optional[str] = Query("created_at", description="排序字段（name, created_at, updated_at, status）"),
    sort_order: Optional[str] = Query("desc", description="排序順序（asc, desc）"),
    _t: Optional[int] = Query(None, description="強制刷新時間戳（繞過緩存）"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """列出所有劇本（需要 script:view 權限）"""
    check_permission(current_user, PermissionCode.SCRIPT_VIEW.value, db)
    
    # 生成緩存鍵（僅在無搜索/過濾且無強制刷新參數時使用緩存）
    use_cache = not (search or status or _t is not None)
    cache_key = None
    if use_cache:
        from app.core.cache import get_cache_manager, get_cache_key
        cache_manager = get_cache_manager()
        cache_key = get_cache_key(
            "scripts_list",
            skip=skip,
            limit=limit,
            sort_by=sort_by,
            sort_order=sort_order,
        )
        cached_result = cache_manager.get(cache_key)
        if cached_result:
            logger.debug(f"從緩存獲取劇本列表: skip={skip}, limit={limit}")
            return [ScriptResponse(**item) for item in cached_result]
    
    try:
        # 構建查詢
        query = db.query(GroupAIScript)
        
        # 搜索過濾
        if search:
            search_filter = f"%{search}%"
            query = query.filter(
                (GroupAIScript.script_id.like(search_filter)) |
                (GroupAIScript.name.like(search_filter)) |
                (GroupAIScript.description.like(search_filter))
            )
        
        # 狀態過濾
        if status:
            query = query.filter(GroupAIScript.status == status)
        
        # 排序
        if sort_by == "name":
            order_by = GroupAIScript.name
        elif sort_by == "updated_at":
            order_by = GroupAIScript.updated_at
        elif sort_by == "status":
            order_by = GroupAIScript.status
        else:  # 默認按創建時間
            order_by = GroupAIScript.created_at
        
        if sort_order == "asc":
            query = query.order_by(order_by.asc())
        else:
            query = query.order_by(order_by.desc())
        
        # 獲取總數
        total_count = query.count()
        logger.debug(f"查詢條件下劇本總數: {total_count}")
        
        # 分頁
        scripts = query.offset(skip).limit(limit).all()
        logger.debug(f"查詢到 {len(scripts)} 個劇本 (skip={skip}, limit={limit})")
        
        result = []
        for script in scripts:
            # 解析 YAML 獲取場景數
            scene_count = 0
            try:
                import tempfile
                with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False, encoding='utf-8') as f:
                    f.write(script.yaml_content)
                    temp_path = f.name
                try:
                    parsed = script_parser.load_script(temp_path)
                    scene_count = len(parsed.scenes)
                finally:
                    Path(temp_path).unlink()
            except:
                pass
            
            result.append(ScriptResponse(
                script_id=script.script_id,
                name=script.name,
                version=script.version,
                description=script.description,
                scene_count=scene_count,
                status=script.status,
                created_at=script.created_at.isoformat() if script.created_at else None,
                updated_at=script.updated_at.isoformat() if script.updated_at else None
            ))
        
        # 緩存結果（僅在無搜索/過濾時）
        if use_cache and cache_key:
            cache_manager.set(cache_key, [item.dict() for item in result], expire=120)  # 緩存120秒
        
        return result
    
    except Exception as e:
        logger.error(f"列出劇本失敗: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"列出劇本失敗: {str(e)}"
        )


@router.get("/{script_id}", response_model=ScriptDetailResponse)
async def get_script(
    script_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """獲取劇本詳情（需要 script:view 權限）"""
    check_permission(current_user, PermissionCode.SCRIPT_VIEW.value, db)
    script = db.query(GroupAIScript).filter(
        GroupAIScript.script_id == script_id
    ).first()
    
    if not script:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"劇本 {script_id} 不存在"
        )
    
    # 解析 YAML 獲取場景信息
    scenes = []
    try:
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False, encoding='utf-8') as f:
            f.write(script.yaml_content)
            temp_path = f.name
        try:
            parsed = script_parser.load_script(temp_path)
            scenes = [
                {
                    "id": scene.id,
                    "triggers_count": len(scene.triggers),
                    "responses_count": len(scene.responses),
                    "next_scene": scene.next_scene
                }
                for scene in parsed.scenes.values()
            ]
        finally:
            Path(temp_path).unlink()
    except Exception as e:
        logger.warning(f"解析劇本場景失敗: {e}")
    
    return ScriptDetailResponse(
        script_id=script.script_id,
        name=script.name,
        version=script.version,
        description=script.description,
        scene_count=len(scenes),
        yaml_content=script.yaml_content,
        scenes=scenes,
        created_at=script.created_at.isoformat() if script.created_at else None,
        updated_at=script.updated_at.isoformat() if script.updated_at else None
    )


@router.put("/{script_id}", response_model=ScriptResponse)
async def update_script(
    script_id: str,
    request: ScriptUpdateRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """更新劇本（需要 script:update 權限）"""
    check_permission(current_user, PermissionCode.SCRIPT_UPDATE.value, db)
    # 更新後清除劇本列表緩存
    invalidate_cache("scripts_list")
    script = db.query(GroupAIScript).filter(
        GroupAIScript.script_id == script_id
    ).first()
    
    if not script:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"劇本 {script_id} 不存在"
        )
    
    try:
        # 如果更新了 YAML 內容，需要驗證
        yaml_content = request.yaml_content or script.yaml_content
        if request.yaml_content:
            # 在解析前，先使用增强转换器验证和修复YAML内容
            try:
                from group_ai_service.yaml_validator import YAMLValidator
                fixed_content, warnings = YAMLValidator.validate_and_fix_yaml_content(yaml_content)
                
                # 如果有修复，更新YAML内容
                if warnings:
                    logger.info(f"YAML内容已修复，警告: {warnings}")
                    yaml_content = fixed_content
            except Exception as e:
                logger.warning(f"YAML预处理失败，继续使用原始内容: {e}")
            
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False, encoding='utf-8') as f:
                f.write(yaml_content)
                temp_path = f.name
            
            try:
                parsed = script_parser.load_script(temp_path)
                errors = script_parser.validate_script(parsed)
                if errors:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"劇本驗證失敗: {', '.join(errors)}"
                    )
            except HTTPException:
                raise
            except yaml.scanner.ScannerError as e:
                # YAML 掃描錯誤（語法錯誤）
                error_msg = str(e)
                line_info = ""
                if hasattr(e, 'problem_mark') and e.problem_mark:
                    line = e.problem_mark.line + 1
                    column = e.problem_mark.column + 1
                    line_info = f"第 {line} 行，第 {column} 列"
                elif "line" in error_msg.lower():
                    import re
                    match = re.search(r'line\s+(\d+)', error_msg, re.IGNORECASE)
                    if match:
                        line_info = f"第 {match.group(1)} 行"
                
                problem_desc = ""
                if "could not find expected ':'" in error_msg or "找不到預期的 ':'" in error_msg:
                    problem_desc = "缺少冒號（:）。YAML 格式要求鍵值對必須使用冒號分隔"
                elif "could not find expected" in error_msg:
                    problem_desc = "YAML 語法錯誤。可能是縮進不正確、缺少冒號或引號未閉合"
                elif "mapping values are not allowed" in error_msg:
                    problem_desc = "映射值格式錯誤。檢查縮進是否正確，鍵值對是否使用冒號分隔"
                else:
                    problem_desc = "YAML 語法錯誤"
                
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"YAML 解析失敗：{problem_desc}\n\n位置：{line_info if line_info else '未知'}\n\n建議：\n  • 檢查 YAML 格式是否正確（特別是縮進和冒號）\n  • 確保所有鍵值對都使用冒號分隔\n  • 如果是舊格式，請先使用「智能轉換」功能"
                )
            except yaml.parser.ParserError as e:
                # YAML 解析錯誤（結構錯誤）
                error_msg = str(e)
                line_info = ""
                if hasattr(e, 'problem_mark') and e.problem_mark:
                    line = e.problem_mark.line + 1
                    column = e.problem_mark.column + 1
                    line_info = f"第 {line} 行，第 {column} 列"
                
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"YAML 解析失敗：YAML 結構錯誤\n\n位置：{line_info if line_info else '未知'}\n錯誤詳情：{error_msg}\n\n建議：\n  • 檢查 YAML 格式是否正確\n  • 確保包含 script_id、version 和 scenes 字段\n  • 如果是舊格式，請先使用「智能轉換」功能"
                )
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"劇本解析失敗: {str(e)}\n\n建議：\n  • 檢查 YAML 格式是否正確\n  • 確保包含 script_id、version 和 scenes 字段\n  • 如果是舊格式，請先使用「智能轉換」功能"
                )
            finally:
                Path(temp_path).unlink()
        
        # 檢查是否有變更，如果有變更則創建版本記錄
        old_version = script.version
        old_yaml = script.yaml_content
        version_changed = request.version and request.version != old_version
        content_changed = request.yaml_content and yaml_content != old_yaml
        
        # 更新字段
        if request.name is not None:
            script.name = request.name
        if request.version is not None:
            script.version = request.version
        if request.description is not None:
            script.description = request.description
        if request.yaml_content is not None:
            # 使用修复后的YAML内容
            script.yaml_content = yaml_content  # 已经是修复后的内容
        
        # 如果版本或內容有變更，創建版本歷史記錄
        if version_changed or content_changed:
            # 先保存當前版本到歷史（如果內容不同）
            if old_yaml != yaml_content:
                old_version_record = GroupAIScriptVersion(
                    script_id=script_id,
                    version=old_version,
                    yaml_content=old_yaml,
                    description=script.description,
                    change_summary="更新前的版本"
                )
                db.add(old_version_record)
            
            # 創建新版本記錄
            new_version_record = GroupAIScriptVersion(
                script_id=script_id,
                version=script.version,
                yaml_content=script.yaml_content,
                description=script.description,
                change_summary=f"更新到版本 {script.version}" if version_changed else "內容更新"
            )
            db.add(new_version_record)
        
        db.commit()
        db.refresh(script)
        
        # 解析獲取場景數
        scene_count = 0
        try:
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False, encoding='utf-8') as f:
                f.write(script.yaml_content)
                temp_path = f.name
            try:
                parsed = script_parser.load_script(temp_path)
                scene_count = len(parsed.scenes)
            finally:
                Path(temp_path).unlink()
        except:
            pass
        
        logger.info(f"劇本更新成功: {script_id}")
        
        return ScriptResponse(
            script_id=script.script_id,
            name=script.name,
            version=script.version,
            description=script.description,
            scene_count=scene_count,
            status=script.status,
            created_at=script.created_at.isoformat() if script.created_at else None,
            updated_at=script.updated_at.isoformat() if script.updated_at else None
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新劇本失敗: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新劇本失敗: {str(e)}"
        )


@router.delete("/{script_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_script(
    script_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """刪除劇本（需要 script:delete 權限）"""
    check_permission(current_user, PermissionCode.SCRIPT_DELETE.value, db)
    
    # URL 解碼（FastAPI 應該自動解碼，但為了安全起見，手動解碼一次）
    import urllib.parse
    script_id = urllib.parse.unquote(script_id)
    
    # 刪除後清除劇本列表緩存
    invalidate_cache("scripts_list")
    
    try:
        script = db.query(GroupAIScript).filter(
            GroupAIScript.script_id == script_id
        ).first()
        
        if not script:
            logger.warning(f"嘗試刪除不存在的劇本: {script_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"劇本 {script_id} 不存在"
            )
        
        # 刪除劇本版本記錄
        versions = db.query(GroupAIScriptVersion).filter(
            GroupAIScriptVersion.script_id == script_id
        ).all()
        for version in versions:
            db.delete(version)
            logger.debug(f"刪除劇本版本: {version.id} (劇本: {script_id}, 版本: {version.version})")
        
        # 刪除劇本
        db.delete(script)
        
        # 先 flush 確保數據寫入
        db.flush()
        # 然後提交事務
        db.commit()
        
        logger.info(f"劇本刪除成功: {script_id} (已刪除 {len(versions)} 個版本記錄)")
        
        # 驗證數據是否已刪除（使用新的會話確保讀取到最新數據）
        from app.db import SessionLocal as NewSessionLocal
        verify_db = NewSessionLocal()
        try:
            deleted_script = verify_db.query(GroupAIScript).filter(
                GroupAIScript.script_id == script_id
            ).first()
            if deleted_script:
                logger.error(f"劇本刪除後驗證失敗: {script_id} 仍在數據庫中")
                # 不拋出異常，因為已經返回 204，避免客戶端重複請求
                logger.warning(f"劇本 {script_id} 可能未正確刪除，請檢查數據庫")
            else:
                logger.info(f"劇本刪除驗證成功: {script_id} 已從數據庫移除")
        finally:
            verify_db.close()
            
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"刪除劇本失敗: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"刪除劇本失敗: {str(e)}"
        )


class ScriptTestRequest(BaseModel):
    """測試劇本請求"""
    message_text: str


@router.post("/{script_id}/test", status_code=status.HTTP_200_OK)
async def test_script(
    script_id: str,
    request: ScriptTestRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """測試劇本（需要 script:test 權限）"""
    check_permission(current_user, PermissionCode.SCRIPT_TEST.value, db)
    script = db.query(GroupAIScript).filter(
        GroupAIScript.script_id == script_id
    ).first()
    
    if not script:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"劇本 {script_id} 不存在"
        )
    
    try:
        # 加載劇本
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False, encoding='utf-8') as f:
            f.write(script.yaml_content)
            temp_path = f.name
        
        try:
            parsed_script = script_parser.load_script(temp_path)
        finally:
            Path(temp_path).unlink()
        
        # 創建模擬消息
        from unittest.mock import Mock
        from pyrogram.types import Message, User, Chat
        
        user = Mock(spec=User)
        user.first_name = "測試用戶"
        user.id = 123456789
        
        chat_type = Mock()
        chat_type.name = "GROUP"
        
        chat = Mock(spec=Chat)
        chat.id = -1001234567890
        chat.type = chat_type
        
        message = Mock(spec=Message)
        message.text = request.message_text
        message.from_user = user
        message.chat = chat
        
        # 測試處理消息
        from group_ai_service import ScriptEngine
        engine = ScriptEngine()
        engine.initialize_account("test_account", parsed_script)
        
        reply = await engine.process_message("test_account", message, {})
        
        return {
            "script_id": script_id,
            "test_message": request.message_text,
            "reply": reply or "（無回復）",
            "current_scene": engine.get_current_scene("test_account")
        }
    
    except Exception as e:
        logger.error(f"測試劇本失敗: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"測試劇本失敗: {str(e)}"
        )


@router.post("/upload", response_model=ScriptResponse, status_code=status.HTTP_201_CREATED)
async def upload_script_file(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """上傳劇本文件（需要 script:create 權限）"""
    check_permission(current_user, PermissionCode.SCRIPT_CREATE.value, db)
    if not file.filename.endswith(('.yaml', '.yml')):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="只支持 YAML 文件"
        )
    
    try:
        content = await file.read()
        yaml_content = content.decode('utf-8')
        
        # 在解析前，先使用增强转换器验证和修复YAML内容
        try:
            from group_ai_service.yaml_validator import YAMLValidator
            fixed_content, warnings = YAMLValidator.validate_and_fix_yaml_content(yaml_content)
            
            # 如果有修复，更新YAML内容
            if warnings:
                logger.info(f"YAML内容已修复，警告: {warnings}")
                yaml_content = fixed_content
        except Exception as e:
            logger.warning(f"YAML预处理失败，继续使用原始内容: {e}")
        
        # 解析劇本獲取基本信息
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False, encoding='utf-8') as f:
            f.write(yaml_content)
            temp_path = f.name
        
        try:
            script = script_parser.load_script(temp_path)
            errors = script_parser.validate_script(script)
            if errors:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"劇本驗證失敗: {', '.join(errors)}"
                )
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"劇本解析失敗: {str(e)}"
            )
        finally:
            Path(temp_path).unlink()
        
        # 檢查是否已存在
        existing = db.query(GroupAIScript).filter(
            GroupAIScript.script_id == script.script_id
        ).first()
        
        if existing:
            # 更新現有劇本（使用修复后的YAML内容）
            existing.yaml_content = yaml_content  # 已经是修复后的内容
            existing.version = script.version
            if script.description:
                existing.description = script.description
            db.commit()
            db.refresh(existing)
            
            return ScriptResponse(
                script_id=existing.script_id,
                name=existing.name,
                version=existing.version,
                description=existing.description,
                scene_count=len(script.scenes),
                created_at=existing.created_at.isoformat() if existing.created_at else None,
                updated_at=existing.updated_at.isoformat() if existing.updated_at else None
            )
        else:
            # 創建新劇本（使用修复后的YAML内容）
            import uuid
            db_script = GroupAIScript(
                id=str(uuid.uuid4()),  # 生成UUID
                script_id=script.script_id,
                name=script.script_id,  # 使用 script_id 作為默認名稱
                version=script.version,
                description=script.description,
                yaml_content=yaml_content  # 已经是修复后的内容
            )
            db.add(db_script)
            db.commit()
            db.refresh(db_script)
            
            return ScriptResponse(
                script_id=db_script.script_id,
                name=db_script.name,
                version=db_script.version,
                description=db_script.description,
                scene_count=len(script.scenes),
                status=db_script.status,
                created_at=db_script.created_at.isoformat() if db_script.created_at else None,
                updated_at=db_script.updated_at.isoformat() if db_script.updated_at else None
            )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"上傳劇本失敗: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"上傳劇本失敗: {str(e)}"
        )


class FormatConvertRequest(BaseModel):
    """格式轉換請求"""
    yaml_content: str = Field(..., description="舊格式 YAML 內容")
    script_id: Optional[str] = Field(None, description="劇本 ID（可選）")
    script_name: Optional[str] = Field(None, description="劇本名稱（可選）")
    optimize: bool = Field(False, description="是否優化內容")


class FormatConvertResponse(BaseModel):
    """格式轉換響應"""
    success: bool
    yaml_content: str
    script_id: Optional[str] = None
    version: Optional[str] = None
    description: Optional[str] = None
    scene_count: int = 0
    message: Optional[str] = None


@router.post("/convert", response_model=FormatConvertResponse, status_code=status.HTTP_200_OK)
async def convert_format(
    request: FormatConvertRequest
):
    """智能格式轉換 - 將舊格式轉換為新格式"""
    try:
        # 使用增強轉換器進行轉換（支持多種格式和角色識別）
        converted_data, warnings = enhanced_converter.convert_with_enhanced_detection(
            content=request.yaml_content,
            script_id=request.script_id,
            script_name=request.script_name
        )
        
        # 驗證和修復
        converted_data, fix_warnings = enhanced_converter.validate_and_fix(converted_data)
        warnings.extend(fix_warnings)
        
        # 轉換為 YAML 字符串
        import yaml
        yaml_content = yaml.dump(converted_data, allow_unicode=True, default_flow_style=False)
        
        # 如果需要優化
        if request.optimize:
            yaml_content = format_converter.optimize_content(yaml_content, optimize_type="all")
            # 重新解析以獲取更新後的數據
            converted_data = yaml.safe_load(yaml_content)
        
        # 計算場景數
        scene_count = len(converted_data.get("scenes", []))
        
        # 確保 script_id 和 version 是字符串類型
        script_id_value = converted_data.get("script_id")
        if script_id_value is not None:
            script_id_value = str(script_id_value)
        
        version_value = converted_data.get("version", "1.0")
        if version_value is not None:
            version_value = str(version_value)
        
        # 構建消息（包含警告信息）
        message = "格式轉換成功"
        if warnings:
            warning_text = "；".join(warnings[:3])  # 只顯示前3個警告
            if len(warnings) > 3:
                warning_text += f"（還有 {len(warnings) - 3} 個警告）"
            message = f"{message}。注意：{warning_text}"
        
        return FormatConvertResponse(
            success=True,
            yaml_content=yaml_content,
            script_id=script_id_value,
            version=version_value,
            description=converted_data.get("description"),
            scene_count=scene_count,
            message=message
        )
    
    except ValueError as e:
        # 獲取轉換建議
        suggestions = enhanced_converter.get_conversion_suggestions(e)
        error_detail = f"格式轉換失敗: {str(e)}"
        if suggestions:
            error_detail += f"\n\n建議：\n" + "\n".join(f"  • {s}" for s in suggestions)
        
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_detail
        )
    except Exception as e:
        logger.error(f"格式轉換失敗: {e}", exc_info=True)
        suggestions = enhanced_converter.get_conversion_suggestions(e)
        error_detail = f"格式轉換失敗: {str(e)}"
        if suggestions:
            error_detail += f"\n\n建議：\n" + "\n".join(f"  • {s}" for s in suggestions)
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_detail
        )


class ContentOptimizeRequest(BaseModel):
    """內容優化請求"""
    yaml_content: str = Field(..., description="YAML 內容")
    optimize_type: str = Field("all", description="優化類型: all, grammar, expression, structure")


class ContentOptimizeResponse(BaseModel):
    """內容優化響應"""
    success: bool
    yaml_content: str
    message: Optional[str] = None


@router.post("/optimize", response_model=ContentOptimizeResponse, status_code=status.HTTP_200_OK)
async def optimize_content(
    request: ContentOptimizeRequest
):
    """智能內容優化"""
    try:
        optimized_content = format_converter.optimize_content(
            yaml_content=request.yaml_content,
            optimize_type=request.optimize_type
        )
        
        return ContentOptimizeResponse(
            success=True,
            yaml_content=optimized_content,
            message="內容優化成功"
        )
    
    except Exception as e:
        logger.error(f"內容優化失敗: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"內容優化失敗: {str(e)}"
        )


# ============ 批量操作 API ============

class BatchScriptRequest(BaseModel):
    """批量操作請求"""
    script_ids: List[str] = Field(..., description="劇本 ID 列表")
    action: str = Field(..., description="操作類型: delete, submit_review, publish, disable, revert_to_draft")


class BatchScriptResponse(BaseModel):
    """批量操作響應"""
    success_count: int
    failed_count: int
    success_ids: List[str] = []
    failed_items: List[dict] = []


@router.post("/batch", response_model=BatchScriptResponse, status_code=status.HTTP_200_OK)
async def batch_operate_scripts(
    request: BatchScriptRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """批量操作劇本（需要相應權限）"""
    if not request.script_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="請至少選擇一個劇本"
        )
    
    if len(request.script_ids) > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="一次最多批量操作 100 個劇本"
        )
    
    # 根據操作類型檢查權限
    permission_map = {
        "delete": PermissionCode.SCRIPT_DELETE.value,
        "submit_review": PermissionCode.SCRIPT_REVIEW.value,
        "publish": PermissionCode.SCRIPT_PUBLISH.value,
        "disable": PermissionCode.SCRIPT_DELETE.value,  # 停用使用刪除權限
        "revert_to_draft": PermissionCode.SCRIPT_REVIEW.value,
    }
    
    if request.action not in permission_map:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"不支持的操作類型: {request.action}"
        )
    
    check_permission(current_user, permission_map[request.action], db)
    
    # 清除緩存（在所有操作之前清除，確保操作後列表是最新的）
    cache_cleared = invalidate_cache("scripts_list*")
    logger.debug(f"批量操作前清除 {cache_cleared} 個劇本列表緩存鍵")
    
    success_count = 0
    failed_count = 0
    success_ids = []
    failed_items = []
    
    try:
        # URL 解碼所有 script_id（處理可能包含特殊字符的情況）
        import urllib.parse
        decoded_script_ids = [urllib.parse.unquote(sid) if "%" in sid else sid for sid in request.script_ids]
        
        for script_id in decoded_script_ids:
            try:
                script = db.query(GroupAIScript).filter(
                    GroupAIScript.script_id == script_id
                ).first()
                
                if not script:
                    # 記錄詳細日誌以便調試
                    logger.warning(f"批量操作時劇本不存在: {script_id} (原始: {request.script_ids[decoded_script_ids.index(script_id)] if script_id in decoded_script_ids else script_id})")
                    failed_items.append({
                        "script_id": script_id,
                        "error": "劇本不存在（可能已被刪除或從未存在）"
                    })
                    failed_count += 1
                    continue
                
                # 執行操作
                if request.action == "delete":
                    # 刪除劇本版本記錄
                    versions = db.query(GroupAIScriptVersion).filter(
                        GroupAIScriptVersion.script_id == script_id
                    ).all()
                    for version in versions:
                        db.delete(version)
                    
                    # 刪除劇本
                    db.delete(script)
                    db.flush()
                    db.commit()
                    success_ids.append(script_id)
                    success_count += 1
                    logger.info(f"批量刪除劇本成功: {script_id} (已刪除 {len(versions)} 個版本記錄)")
                
                elif request.action == "submit_review":
                    if script.status != "draft":
                        failed_items.append({
                            "script_id": script_id,
                            "error": f"劇本狀態為 {script.status}，無法提交審核（必須為 draft）"
                        })
                        failed_count += 1
                        continue
                    script.status = "reviewing"
                    db.commit()
                    success_ids.append(script_id)
                    success_count += 1
                    logger.info(f"批量提交審核成功: {script_id}")
                
                elif request.action == "publish":
                    if script.status not in ["approved", "reviewing"]:
                        failed_items.append({
                            "script_id": script_id,
                            "error": f"劇本狀態為 {script.status}，無法發布（必須為 approved 或 reviewing）"
                        })
                        failed_count += 1
                        continue
                    script.status = "published"
                    from datetime import datetime
                    script.published_at = datetime.utcnow()
                    db.commit()
                    success_ids.append(script_id)
                    success_count += 1
                    logger.info(f"批量發布劇本成功: {script_id}")
                
                elif request.action == "disable":
                    script.status = "disabled"
                    db.commit()
                    success_ids.append(script_id)
                    success_count += 1
                    logger.info(f"批量停用劇本成功: {script_id}")
                
                elif request.action == "revert_to_draft":
                    if script.status not in ["reviewing", "approved", "rejected"]:
                        failed_items.append({
                            "script_id": script_id,
                            "error": f"劇本狀態為 {script.status}，無法還原為草稿"
                        })
                        failed_count += 1
                        continue
                    script.status = "draft"
                    db.commit()
                    success_ids.append(script_id)
                    success_count += 1
                    logger.info(f"批量還原為草稿成功: {script_id}")
                
            except Exception as e:
                logger.error(f"批量操作劇本 {script_id} 失敗: {e}", exc_info=True)
                failed_items.append({
                    "script_id": script_id,
                    "error": str(e)
                })
                failed_count += 1
                db.rollback()
        
        # 批量操作完成後再次清除緩存，確保列表更新
        cache_cleared_after = invalidate_cache("scripts_list*")
        logger.debug(f"批量操作後清除 {cache_cleared_after} 個劇本列表緩存鍵")
        
        return BatchScriptResponse(
            success_count=success_count,
            failed_count=failed_count,
            success_ids=success_ids,
            failed_items=failed_items
        )
    
    except Exception as e:
        logger.error(f"批量操作劇本失敗: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"批量操作失敗: {str(e)}"
        )
