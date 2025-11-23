#!/usr/bin/env python3
"""
Session 文件验证工具
用于验证 Session 文件是否可以在其他服务器上正常使用
"""
import sys
import argparse
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from utils.session_encryption import get_session_manager
from group_ai_service.config import get_group_ai_config


def verify_session(session_name: str, sessions_dir: Optional[Path] = None) -> dict:
    """
    验证 Session 文件
    
    Args:
        session_name: Session 文件名（不含扩展名）
        sessions_dir: Session 文件目录（可选）
    
    Returns:
        验证结果字典
    """
    config = get_group_ai_config()
    
    if sessions_dir is None:
        sessions_dir = Path(config.session_files_directory)
    
    if not sessions_dir.exists():
        return {
            "success": False,
            "error": f"Session 目录不存在: {sessions_dir}"
        }
    
    # 查找 Session 文件
    session_manager = get_session_manager()
    all_sessions = session_manager.list_sessions()
    
    session_file = None
    is_encrypted = False
    
    for s in all_sessions:
        if s.stem == session_name:
            session_file = s
            is_encrypted = session_manager.encryptor and session_manager.encryptor.is_encrypted_file(s)
            break
    
    if not session_file or not session_file.exists():
        return {
            "success": False,
            "error": f"Session 文件未找到: {session_name}"
        }
    
    result = {
        "success": True,
        "session_name": session_name,
        "file_path": str(session_file),
        "file_size": session_file.stat().st_size,
        "is_encrypted": is_encrypted,
        "readable": False,
        "valid": False,
        "issues": []
    }
    
    # 尝试读取文件
    try:
        if is_encrypted:
            if session_manager.encryptor:
                encrypted_data = session_file.read_bytes()
                decrypted_data = session_manager.encryptor.decrypt_session(encrypted_data)
                result["readable"] = True
                result["decrypted_size"] = len(decrypted_data)
            else:
                result["issues"].append("Session 文件已加密，但未配置加密密钥")
        else:
            data = session_file.read_bytes()
            result["readable"] = True
            result["decrypted_size"] = len(data)
    except Exception as e:
        result["issues"].append(f"无法读取文件: {str(e)}")
        result["success"] = False
    
    # 检查文件大小
    if result.get("decrypted_size", 0) == 0:
        result["issues"].append("Session 文件为空或无效")
        result["success"] = False
    else:
        result["valid"] = True
    
    # 检查文件权限
    try:
        import stat
        file_stat = session_file.stat()
        mode = stat.filemode(file_stat.st_mode)
        result["permissions"] = mode
        if mode != "-rw-------":
            result["issues"].append(f"文件权限可能不安全: {mode}，建议使用 600")
    except Exception as e:
        result["issues"].append(f"无法检查文件权限: {str(e)}")
    
    return result


def main():
    parser = argparse.ArgumentParser(description="验证 Session 文件")
    parser.add_argument("session_name", help="Session 文件名（不含扩展名）")
    parser.add_argument("--sessions-dir", type=Path, help="Session 文件目录（可选）")
    
    args = parser.parse_args()
    
    result = verify_session(args.session_name, args.sessions_dir)
    
    if result["success"]:
        print(f"✅ Session 文件验证通过: {args.session_name}")
        print(f"   文件路径: {result['file_path']}")
        print(f"   文件大小: {result['file_size']} 字节")
        print(f"   是否加密: {result['is_encrypted']}")
        if result.get("decrypted_size"):
            print(f"   解密后大小: {result['decrypted_size']} 字节")
        if result.get("permissions"):
            print(f"   文件权限: {result['permissions']}")
        if result.get("issues"):
            print(f"   ⚠️  警告: {', '.join(result['issues'])}")
        return 0
    else:
        print(f"❌ Session 文件验证失败: {args.session_name}")
        if "error" in result:
            print(f"   错误: {result['error']}")
        if result.get("issues"):
            print(f"   问题: {', '.join(result['issues'])}")
        return 1


if __name__ == "__main__":
    sys.exit(main())

