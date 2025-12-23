"""
联系表单管理 API
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel

from app.db import get_db_session
from app.crud import sites as crud_sites
from app.models.sites import ContactForm

router = APIRouter(prefix="/api/v1/contacts", tags=["contacts"])


class ContactFormCreate(BaseModel):
    site_id: int
    contact_type: str
    contact_value: str
    message: Optional[str] = None


class ContactFormUpdate(BaseModel):
    status: Optional[str] = None
    notes: Optional[str] = None


class ContactFormResponse(BaseModel):
    id: int
    site_id: int
    contact_type: str
    contact_value: str
    message: Optional[str]
    status: str
    notes: Optional[str]
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


@router.post("", response_model=ContactFormResponse)
async def create_contact_form(
    contact: ContactFormCreate,
    db: Session = Depends(get_db_session)
):
    """创建联系表单（前端提交）"""
    try:
        # 验证站点是否存在
        site = crud_sites.get_site(db, contact.site_id)
        if not site:
            raise HTTPException(status_code=404, detail="站点不存在")
        
        contact_form = crud_sites.create_contact_form(
            db=db,
            site_id=contact.site_id,
            contact_type=contact.contact_type,
            contact_value=contact.contact_value,
            message=contact.message
        )
        
        return {
            "id": contact_form.id,
            "site_id": contact_form.site_id,
            "contact_type": contact_form.contact_type,
            "contact_value": contact_form.contact_value,
            "message": contact_form.message,
            "status": contact_form.status,
            "notes": contact_form.notes,
            "created_at": contact_form.created_at.isoformat(),
            "updated_at": contact_form.updated_at.isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建联系表单失败: {str(e)}")


@router.get("", response_model=dict)
async def get_contact_forms(
    site_id: Optional[int] = Query(None, description="站点 ID"),
    status: Optional[str] = Query(None, description="状态"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db_session)
):
    """获取联系表单列表"""
    try:
        skip = (page - 1) * page_size
        contacts = crud_sites.get_contact_forms(
            db=db,
            site_id=site_id,
            status=status,
            skip=skip,
            limit=page_size
        )
        
        items = []
        for contact in contacts:
            items.append({
                "id": contact.id,
                "site_id": contact.site_id,
                "contact_type": contact.contact_type,
                "contact_value": contact.contact_value,
                "message": contact.message,
                "status": contact.status,
                "notes": contact.notes,
                "created_at": contact.created_at.isoformat(),
                "updated_at": contact.updated_at.isoformat()
            })
        
        # 计算总数（简化版，实际应该单独查询）
        total = len(contacts)
        
        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取联系表单列表失败: {str(e)}")


@router.get("/{contact_id}", response_model=ContactFormResponse)
async def get_contact_form(
    contact_id: int,
    db: Session = Depends(get_db_session)
):
    """获取联系表单详情"""
    contact = db.query(ContactForm).filter(ContactForm.id == contact_id).first()
    if not contact:
        raise HTTPException(status_code=404, detail="联系表单不存在")
    
    return {
        "id": contact.id,
        "site_id": contact.site_id,
        "contact_type": contact.contact_type,
        "contact_value": contact.contact_value,
        "message": contact.message,
        "status": contact.status,
        "notes": contact.notes,
        "created_at": contact.created_at.isoformat(),
        "updated_at": contact.updated_at.isoformat()
    }


@router.put("/{contact_id}", response_model=ContactFormResponse)
async def update_contact_form(
    contact_id: int,
    contact_update: ContactFormUpdate,
    db: Session = Depends(get_db_session)
):
    """更新联系表单状态"""
    update_data = contact_update.dict(exclude_unset=True)
    contact = crud_sites.update_contact_form_status(
        db=db,
        contact_id=contact_id,
        status=update_data.get("status"),
        notes=update_data.get("notes")
    )
    
    if not contact:
        raise HTTPException(status_code=404, detail="联系表单不存在")
    
    return {
        "id": contact.id,
        "site_id": contact.site_id,
        "contact_type": contact.contact_type,
        "contact_value": contact.contact_value,
        "message": contact.message,
        "status": contact.status,
        "notes": contact.notes,
        "created_at": contact.created_at.isoformat(),
        "updated_at": contact.updated_at.isoformat()
    }

