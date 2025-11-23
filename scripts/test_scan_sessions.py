"""测试扫描 sessions 文件"""
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from utils.session_encryption import get_session_manager
from group_ai_service.config import get_group_ai_config

config = get_group_ai_config()
sessions_dir = Path(config.session_files_directory)

print(f"配置的 sessions 目录: {config.session_files_directory}")
print(f"相对路径: {sessions_dir}")
print(f"绝对路径: {sessions_dir.resolve()}")
print(f"目录存在: {sessions_dir.exists()}")

# 尝试从项目根目录解析
if not sessions_dir.exists():
    sessions_dir = project_root / config.session_files_directory
    print(f"\n从项目根目录解析: {sessions_dir}")
    print(f"目录存在: {sessions_dir.exists()}")

if sessions_dir.exists():
    print(f"\n目录内容:")
    all_files = list(sessions_dir.iterdir())
    print(f"  总文件数: {len(all_files)}")
    for f in all_files[:10]:
        print(f"  - {f.name} (类型: {'目录' if f.is_dir() else '文件'})")
    
    session_files = list(sessions_dir.glob("*.session"))
    print(f"\n.session 文件: {len(session_files)}")
    for f in session_files[:10]:
        print(f"  - {f.name} (大小: {f.stat().st_size} 字节)")
    
    # 测试 SessionFileManager
    print(f"\n测试 SessionFileManager:")
    session_manager = get_session_manager()
    # 手动设置正确的目录
    session_manager.sessions_dir = sessions_dir
    all_sessions = session_manager.list_sessions()
    print(f"  SessionFileManager 找到 {len(all_sessions)} 个文件")
    for s in all_sessions[:10]:
        print(f"    - {s.name}")
else:
    print("\n目录不存在！")
