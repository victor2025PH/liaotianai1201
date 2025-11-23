"""检查sessions目录和文件"""
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from group_ai_service.config import get_group_ai_config

config = get_group_ai_config()
sessions_dir = Path(config.session_files_directory)

print(f"Sessions目录配置: {config.session_files_directory}")
print(f"相对路径: {sessions_dir}")
print(f"绝对路径: {sessions_dir.resolve()}")
print(f"目录存在: {sessions_dir.exists()}")

if not sessions_dir.exists():
    # 尝试从项目根目录查找
    project_root = Path(__file__).parent.parent
    sessions_dir = project_root / config.session_files_directory
    print(f"\n尝试项目根目录: {sessions_dir}")
    print(f"目录存在: {sessions_dir.exists()}")

if sessions_dir.exists():
    print(f"\n目录内容:")
    all_files = list(sessions_dir.iterdir())
    print(f"  总文件数: {len(all_files)}")
    for f in all_files:
        print(f"  - {f.name} (类型: {'目录' if f.is_dir() else '文件'})")
    
    session_files = list(sessions_dir.glob("*.session"))
    print(f"\n.session 文件: {len(session_files)}")
    for f in session_files:
        print(f"  - {f.name} (大小: {f.stat().st_size} 字节)")
else:
    print("\n目录不存在！")

