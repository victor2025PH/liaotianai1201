"""
站点管理 CRUD 操作
"""
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from datetime import datetime, timedelta, date
from typing import List, Optional, Dict
from app.models.sites import Site, SiteVisit, AIConversation, ContactForm, SiteAnalytics


def get_sites(db: Session, skip: int = 0, limit: int = 100) -> List[Site]:
    """获取所有站点"""
    return db.query(Site).offset(skip).limit(limit).all()


def get_site(db: Session, site_id: int) -> Optional[Site]:
    """获取单个站点"""
    return db.query(Site).filter(Site.id == site_id).first()


def get_site_by_type(db: Session, site_type: str) -> Optional[Site]:
    """根据站点类型获取站点"""
    return db.query(Site).filter(Site.site_type == site_type).first()


def create_site(db: Session, name: str, url: str, site_type: str, config: Optional[Dict] = None) -> Site:
    """创建站点"""
    site = Site(
        name=name,
        url=url,
        site_type=site_type,
        config=config or {}
    )
    db.add(site)
    db.commit()
    db.refresh(site)
    return site


def update_site(db: Session, site_id: int, **kwargs) -> Optional[Site]:
    """更新站点"""
    site = db.query(Site).filter(Site.id == site_id).first()
    if not site:
        return None
    
    for key, value in kwargs.items():
        if hasattr(site, key):
            setattr(site, key, value)
    
    site.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(site)
    return site


def get_site_stats_today(db: Session, site_id: int) -> Dict:
    """获取站点今日统计"""
    today = datetime.utcnow().date()
    today_start = datetime.combine(today, datetime.min.time())
    
    # PV
    pv = db.query(func.count(SiteVisit.id)).filter(
        and_(
            SiteVisit.site_id == site_id,
            SiteVisit.created_at >= today_start
        )
    ).scalar() or 0
    
    # UV
    uv = db.query(func.count(func.distinct(SiteVisit.session_id))).filter(
        and_(
            SiteVisit.site_id == site_id,
            SiteVisit.created_at >= today_start
        )
    ).scalar() or 0
    
    # 对话数
    conversations = db.query(func.count(AIConversation.id)).filter(
        and_(
            AIConversation.site_id == site_id,
            AIConversation.created_at >= today_start
        )
    ).scalar() or 0
    
    return {
        "today_pv": pv,
        "today_uv": uv,
        "today_conversations": conversations
    }


def create_site_visit(
    db: Session,
    site_id: int,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    referer: Optional[str] = None,
    page_path: Optional[str] = None,
    session_id: Optional[str] = None,
    visit_duration: Optional[int] = None
) -> SiteVisit:
    """创建访问记录"""
    visit = SiteVisit(
        site_id=site_id,
        ip_address=ip_address,
        user_agent=user_agent,
        referer=referer,
        page_path=page_path,
        session_id=session_id,
        visit_duration=visit_duration
    )
    db.add(visit)
    db.commit()
    db.refresh(visit)
    return visit


def create_ai_conversation(
    db: Session,
    site_id: int,
    session_id: str,
    user_message: str,
    ai_response: str,
    ai_provider: str,
    response_time: Optional[int] = None,
    tokens_used: Optional[int] = None
) -> AIConversation:
    """创建 AI 对话记录"""
    conversation = AIConversation(
        site_id=site_id,
        session_id=session_id,
        user_message=user_message,
        ai_response=ai_response,
        ai_provider=ai_provider,
        response_time=response_time,
        tokens_used=tokens_used
    )
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    return conversation


def create_contact_form(
    db: Session,
    site_id: int,
    contact_type: str,
    contact_value: str,
    message: Optional[str] = None
) -> ContactForm:
    """创建联系表单"""
    contact = ContactForm(
        site_id=site_id,
        contact_type=contact_type,
        contact_value=contact_value,
        message=message,
        status="pending"
    )
    db.add(contact)
    db.commit()
    db.refresh(contact)
    return contact


def get_contact_forms(
    db: Session,
    site_id: Optional[int] = None,
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 100
) -> List[ContactForm]:
    """获取联系表单列表"""
    query = db.query(ContactForm)
    
    if site_id:
        query = query.filter(ContactForm.site_id == site_id)
    if status:
        query = query.filter(ContactForm.status == status)
    
    return query.order_by(ContactForm.created_at.desc()).offset(skip).limit(limit).all()


def update_contact_form_status(
    db: Session,
    contact_id: int,
    status: str,
    notes: Optional[str] = None
) -> Optional[ContactForm]:
    """更新联系表单状态"""
    contact = db.query(ContactForm).filter(ContactForm.id == contact_id).first()
    if not contact:
        return None
    
    contact.status = status
    if notes:
        contact.notes = notes
    contact.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(contact)
    return contact


def get_analytics_overview(db: Session, days: int = 7) -> Dict:
    """获取概览数据"""
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # 总 PV
    total_pv = db.query(func.count(SiteVisit.id)).filter(
        SiteVisit.created_at >= start_date
    ).scalar() or 0
    
    # 总 UV
    total_uv = db.query(func.count(func.distinct(SiteVisit.session_id))).filter(
        SiteVisit.created_at >= start_date
    ).scalar() or 0
    
    # 总对话数
    total_conversations = db.query(func.count(AIConversation.id)).filter(
        AIConversation.created_at >= start_date
    ).scalar() or 0
    
    # 总联系数
    total_contacts = db.query(func.count(ContactForm.id)).filter(
        ContactForm.created_at >= start_date
    ).scalar() or 0
    
    # 转化率
    conversion_rate = (total_contacts / total_conversations * 100) if total_conversations > 0 else 0
    
    # 各站点统计
    sites = db.query(Site).all()
    sites_stats = []
    for site in sites:
        site_pv = db.query(func.count(SiteVisit.id)).filter(
            and_(
                SiteVisit.site_id == site.id,
                SiteVisit.created_at >= start_date
            )
        ).scalar() or 0
        
        site_uv = db.query(func.count(func.distinct(SiteVisit.session_id))).filter(
            and_(
                SiteVisit.site_id == site.id,
                SiteVisit.created_at >= start_date
            )
        ).scalar() or 0
        
        site_conversations = db.query(func.count(AIConversation.id)).filter(
            and_(
                AIConversation.site_id == site.id,
                AIConversation.created_at >= start_date
            )
        ).scalar() or 0
        
        sites_stats.append({
            "site_id": site.id,
            "site_name": site.name,
            "pv": site_pv,
            "uv": site_uv,
            "conversations": site_conversations
        })
    
    return {
        "total_pv": total_pv,
        "total_uv": total_uv,
        "total_conversations": total_conversations,
        "total_contacts": total_contacts,
        "conversion_rate": round(conversion_rate, 2),
        "sites": sites_stats
    }

