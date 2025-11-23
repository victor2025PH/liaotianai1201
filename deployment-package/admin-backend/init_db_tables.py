"""
初始化数据库表
"""
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from app.db import engine, Base
from app.models import group_ai  # 确保导入所有模型
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_database():
    """初始化数据库表"""
    try:
        logger.info("开始创建数据库表...")
        # 创建所有表
        Base.metadata.create_all(bind=engine)
        logger.info("数据库表创建成功！")
        
        # 验证表是否存在
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        logger.info(f"数据库中的表: {', '.join(tables)}")
        
        # 检查关键表
        required_tables = [
            'group_ai_scripts',
            'group_ai_accounts',
            'group_ai_script_versions',
            'group_ai_dialogue_history',
            'group_ai_redpacket_logs'
        ]
        
        missing_tables = [t for t in required_tables if t not in tables]
        if missing_tables:
            logger.error(f"缺少表: {', '.join(missing_tables)}")
            return False
        else:
            logger.info("所有必需的表都已创建！")
            return True
            
    except Exception as e:
        logger.error(f"创建数据库表失败: {e}", exc_info=True)
        return False

if __name__ == "__main__":
    success = init_database()
    sys.exit(0 if success else 1)

