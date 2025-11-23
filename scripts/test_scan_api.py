"""直接测试扫描API的路径解析"""
import sys
from pathlib import Path

# 添加项目根目录
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 模拟API文件的路径
api_file = project_root / "admin-backend" / "app" / "api" / "group_ai" / "accounts.py"
print(f"API文件: {api_file}")
print(f"API文件存在: {api_file.exists()}")

# 测试向上5级
if api_file.exists():
    levels = []
    current = api_file
    for i in range(6):
        levels.append((i, str(current.resolve())))
        if i < 5:
            current = current.parent
    
    print("\n路径层级:")
    for level, path in levels:
        print(f"  向上{level}级: {path}")
    
    # 项目根目录应该是向上5级
    project_root_from_api = api_file.parent.parent.parent.parent.parent
    print(f"\n项目根目录（向上5级）: {project_root_from_api}")
    print(f"项目根目录存在: {project_root_from_api.exists()}")
    
    # sessions目录
    sessions_dir = project_root_from_api / "sessions"
    print(f"\nsessions目录: {sessions_dir}")
    print(f"sessions目录存在: {sessions_dir.exists()}")
    
    if sessions_dir.exists():
        files = list(sessions_dir.glob("*.session"))
        print(f"\n找到 {len(files)} 个 .session 文件:")
        for f in files:
            print(f"  - {f.name} ({f.stat().st_size} 字节)")

