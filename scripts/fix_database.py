"""
修復數據庫表 - 確保所有 Group AI 表已創建
"""
import sys
from pathlib import Path

# 添加項目根目錄到路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 添加 admin-backend 到路徑
admin_backend = project_root / "admin-backend"
sys.path.insert(0, str(admin_backend))

from app.db import Base, engine
from app.models import group_ai  # 確保導入所有 Group AI 模型

print("正在創建數據庫表...")
Base.metadata.create_all(bind=engine)
print("[OK] 所有數據庫表已創建完成！")

