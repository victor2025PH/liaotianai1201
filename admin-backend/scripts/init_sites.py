"""
初始化三个站点数据
"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db import SessionLocal
from app.crud import sites as crud_sites


def init_sites():
    """初始化三个站点"""
    db = SessionLocal()
    
    try:
        # 检查是否已存在站点
        existing_sites = crud_sites.get_sites(db)
        if existing_sites:
            print(f"已存在 {len(existing_sites)} 个站点，跳过初始化。")
            return
        
        # 创建三个站点
        sites_data = [
            {
                "name": "智控王",
                "url": "https://aizkw.usdt2026.cc",
                "site_type": "aizkw",
                "config": {
                    "ai_model": "gemini",
                    "default_language": "zh-CN"
                }
            },
            {
                "name": "红包游戏",
                "url": "https://hongbao.usdt2026.cc",
                "site_type": "hongbao",
                "config": {
                    "ai_model": "gemini",
                    "default_language": "zh-CN"
                }
            },
            {
                "name": "TON Mini App",
                "url": "https://tgmini.usdt2026.cc",
                "site_type": "tgmini",
                "config": {
                    "ai_model": "gemini",
                    "default_language": "zh-CN"
                }
            }
        ]
        
        for site_data in sites_data:
            site = crud_sites.create_site(
                db=db,
                name=site_data["name"],
                url=site_data["url"],
                site_type=site_data["site_type"],
                config=site_data["config"]
            )
            print(f"✅ 创建站点: {site.name} ({site.site_type})")
        
        print("✅ 站点初始化完成！")
        
    except Exception as e:
        print(f"❌ 初始化失败: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    init_sites()

