"""
站点管理 API
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, date
from pydantic import BaseModel

from app.api.deps import get_db_session
from app.crud import sites as crud_sites
from app.models.sites import Site, SiteVisit, AIConversation, ContactForm

router = APIRouter(prefix="/api/v1/sites", tags=["sites"])


# Pydantic 模型
class SiteBase(BaseModel):
    name: str
    url: str
    site_type: str
    config: Optional[dict] = None


class SiteCreate(SiteBase):
    pass


class SiteUpdate(BaseModel):
    name: Optional[str] = None
    url: Optional[str] = None
    status: Optional[str] = None
    config: Optional[dict] = None


class SiteResponse(SiteBase):
    id: int
    status: str
    created_at: datetime
    updated_at: datetime
    stats: Optional[dict] = None

    class Config:
        from_attributes = True


class SiteStatsResponse(BaseModel):
    today_pv: int
    today_uv: int
    today_conversations: int


@router.get("", response_model=dict)
async def get_sites(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db_session)
):
    """获取所有站点列表"""
    try:
        sites_list = crud_sites.get_sites(db, skip=skip, limit=limit)
        
        # 获取每个站点的今日统计
        items = []
        for site in sites_list:
            stats = crud_sites.get_site_stats_today(db, site.id)
            site_dict = {
                "id": site.id,
                "name": site.name,
                "url": site.url,
                "site_type": site.site_type,
                "status": site.status,
                "config": site.config or {},
                "stats": stats,
                "created_at": site.created_at,
                "updated_at": site.updated_at
            }
            items.append(site_dict)
        
        return {
            "items": items,
            "total": len(items)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取站点列表失败: {str(e)}")


@router.get("/{site_id}", response_model=SiteResponse)
async def get_site(
    site_id: int,
    db: Session = Depends(get_db_session)
):
    """获取站点详情"""
    site = crud_sites.get_site(db, site_id)
    if not site:
        raise HTTPException(status_code=404, detail="站点不存在")
    
    stats = crud_sites.get_site_stats_today(db, site_id)
    
    return {
        "id": site.id,
        "name": site.name,
        "url": site.url,
        "site_type": site.site_type,
        "status": site.status,
        "config": site.config or {},
        "stats": stats,
        "created_at": site.created_at,
        "updated_at": site.updated_at
    }


@router.put("/{site_id}", response_model=SiteResponse)
async def update_site(
    site_id: int,
    site_update: SiteUpdate,
    db: Session = Depends(get_db_session)
):
    """更新站点配置"""
    update_data = site_update.dict(exclude_unset=True)
    site = crud_sites.update_site(db, site_id, **update_data)
    
    if not site:
        raise HTTPException(status_code=404, detail="站点不存在")
    
    stats = crud_sites.get_site_stats_today(db, site_id)
    
    return {
        "id": site.id,
        "name": site.name,
        "url": site.url,
        "site_type": site.site_type,
        "status": site.status,
        "config": site.config or {},
        "stats": stats,
        "created_at": site.created_at,
        "updated_at": site.updated_at
    }


@router.get("/{site_id}/stats", response_model=SiteStatsResponse)
async def get_site_stats(
    site_id: int,
    db: Session = Depends(get_db_session)
):
    """获取站点统计数据"""
    site = crud_sites.get_site(db, site_id)
    if not site:
        raise HTTPException(status_code=404, detail="站点不存在")
    
    stats = crud_sites.get_site_stats_today(db, site_id)
    return stats

