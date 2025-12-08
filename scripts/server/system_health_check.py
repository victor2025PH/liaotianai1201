#!/usr/bin/env python3
"""
系统健康检查脚本
检查系统状态、安全配置、备份状态等
"""
import sys
import os
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "admin-backend"))

import logging
from datetime import datetime
from typing import Dict, List, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def check_security_config() -> Dict[str, Any]:
    """检查安全配置"""
    print("\n=== 安全检查 ===")
    results = {
        "issues": [],
        "warnings": [],
        "passed": []
    }
    
    try:
        from app.core.config import get_settings
        settings = get_settings()
        
        # 检查JWT密钥
        if settings.jwt_secret == "change_me":
            results["issues"].append("JWT_SECRET 使用默认值，必须修改！")
        else:
            results["passed"].append("JWT_SECRET 已配置")
        
        # 检查管理员密码
        if settings.admin_default_password == "changeme123":
            results["warnings"].append("ADMIN_DEFAULT_PASSWORD 使用默认值，建议修改")
        else:
            results["passed"].append("管理员密码已修改")
        
        # 检查认证是否启用
        if settings.disable_auth:
            results["issues"].append("认证已禁用（disable_auth=True），生产环境不安全！")
        else:
            results["passed"].append("认证已启用")
        
        # 检查CORS配置
        if not settings.cors_origins or "http://localhost" in settings.cors_origins:
            if "*" in settings.cors_origins:
                results["warnings"].append("CORS配置允许所有来源（*），建议限制为特定域名")
            else:
                results["passed"].append("CORS配置已设置")
        
        # 检查HTTPS（通过环境变量或配置）
        # 这里只能检查配置，实际HTTPS需要Nginx配置
        
    except Exception as e:
        logger.error(f"安全检查失败: {e}", exc_info=True)
        results["issues"].append(f"安全检查异常: {e}")
    
    return results


def check_backup_status() -> Dict[str, Any]:
    """检查备份状态"""
    print("\n=== 备份状态检查 ===")
    results = {
        "enabled": False,
        "backup_count": 0,
        "latest_backup": None,
        "backup_dir": None
    }
    
    try:
        from app.core.config import get_settings
        from app.core.auto_backup import get_backup_manager
        
        settings = get_settings()
        backup_manager = get_backup_manager()
        
        results["enabled"] = backup_manager.auto_backup_enabled
        results["backup_dir"] = str(backup_manager.backup_dir)
        
        # 检查备份文件
        if backup_manager.backup_dir.exists():
            backup_files = list(backup_manager.backup_dir.glob("*.tar.gz"))
            results["backup_count"] = len(backup_files)
            
            if backup_files:
                # 获取最新的备份文件
                latest = max(backup_files, key=lambda p: p.stat().st_mtime)
                results["latest_backup"] = {
                    "file": latest.name,
                    "size": latest.stat().st_size,
                    "modified": datetime.fromtimestamp(latest.stat().st_mtime).isoformat()
                }
        
        if results["enabled"]:
            print(f"✓ 自动备份已启用")
            print(f"  - 备份目录: {results['backup_dir']}")
            print(f"  - 备份文件数: {results['backup_count']}")
            if results["latest_backup"]:
                print(f"  - 最新备份: {results['latest_backup']['file']} ({results['latest_backup']['size']} bytes)")
        else:
            print("⚠ 自动备份未启用")
        
    except Exception as e:
        logger.error(f"备份状态检查失败: {e}", exc_info=True)
        print(f"✗ 备份状态检查失败: {e}")
    
    return results


def check_database_status() -> Dict[str, Any]:
    """检查数据库状态"""
    print("\n=== 数据库状态检查 ===")
    results = {
        "connected": False,
        "type": "unknown",
        "table_count": 0,
        "issues": []
    }
    
    try:
        from app.db import SessionLocal, engine
        from sqlalchemy import inspect, text
        
        # 检查连接
        db = SessionLocal()
        try:
            db.execute(text("SELECT 1"))
            results["connected"] = True
            print("✓ 数据库连接正常")
        except Exception as e:
            results["issues"].append(f"数据库连接失败: {e}")
            print(f"✗ 数据库连接失败: {e}")
            return results
        finally:
            db.close()
        
        # 检查数据库类型
        db_url = str(engine.url)
        if "postgresql" in db_url:
            results["type"] = "PostgreSQL"
        elif "sqlite" in db_url:
            results["type"] = "SQLite"
        else:
            results["type"] = "Unknown"
        
        print(f"  - 数据库类型: {results['type']}")
        
        # 检查表数量
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        results["table_count"] = len(tables)
        print(f"  - 表数量: {results['table_count']}")
        
        # 检查关键表
        key_tables = ["users", "group_ai_accounts", "group_ai_scripts"]
        missing_tables = [t for t in key_tables if t not in tables]
        if missing_tables:
            results["issues"].append(f"缺少关键表: {', '.join(missing_tables)}")
        else:
            print("  - 关键表存在")
        
    except Exception as e:
        logger.error(f"数据库状态检查失败: {e}", exc_info=True)
        results["issues"].append(f"检查异常: {e}")
    
    return results


def check_service_status() -> Dict[str, Any]:
    """检查服务状态（通过健康检查端点）"""
    print("\n=== 服务状态检查 ===")
    results = {
        "backend": {"status": "unknown", "response_time": 0},
        "frontend": {"status": "unknown", "response_time": 0}
    }
    
    try:
        import requests
        import time
        
        # 检查后端
        try:
            start = time.time()
            response = requests.get("http://localhost:8000/health", timeout=5)
            elapsed = (time.time() - start) * 1000
            results["backend"] = {
                "status": "healthy" if response.status_code == 200 else "unhealthy",
                "status_code": response.status_code,
                "response_time": elapsed
            }
            print(f"✓ 后端服务: {results['backend']['status']} ({elapsed:.2f}ms)")
        except Exception as e:
            results["backend"] = {"status": "error", "error": str(e)}
            print(f"✗ 后端服务检查失败: {e}")
        
        # 检查前端
        try:
            start = time.time()
            response = requests.get("http://localhost:3000", timeout=5)
            elapsed = (time.time() - start) * 1000
            results["frontend"] = {
                "status": "healthy" if response.status_code == 200 else "unhealthy",
                "status_code": response.status_code,
                "response_time": elapsed
            }
            print(f"✓ 前端服务: {results['frontend']['status']} ({elapsed:.2f}ms)")
        except Exception as e:
            results["frontend"] = {"status": "error", "error": str(e)}
            print(f"✗ 前端服务检查失败: {e}")
        
    except ImportError:
        print("⚠ requests未安装，跳过服务状态检查")
    except Exception as e:
        logger.error(f"服务状态检查失败: {e}", exc_info=True)
    
    return results


def check_disk_space() -> Dict[str, Any]:
    """检查磁盘空间"""
    print("\n=== 磁盘空间检查 ===")
    results = {
        "total": 0,
        "used": 0,
        "available": 0,
        "percent": 0
    }
    
    try:
        import shutil
        total, used, free = shutil.disk_usage("/")
        results = {
            "total": total,
            "used": used,
            "available": free,
            "percent": (used / total) * 100
        }
        
        print(f"  - 总空间: {total / (1024**3):.2f} GB")
        print(f"  - 已使用: {used / (1024**3):.2f} GB ({results['percent']:.1f}%)")
        print(f"  - 可用空间: {free / (1024**3):.2f} GB")
        
        if results["percent"] > 90:
            print("  ⚠ 磁盘使用率超过90%，建议清理")
        elif results["percent"] > 80:
            print("  ⚠ 磁盘使用率超过80%，建议关注")
        else:
            print("  ✓ 磁盘空间充足")
        
    except Exception as e:
        logger.error(f"磁盘空间检查失败: {e}", exc_info=True)
    
    return results


def main():
    """主函数"""
    print("=" * 60)
    print("系统健康检查")
    print("=" * 60)
    print(f"检查时间: {datetime.now().isoformat()}")
    
    all_results = {}
    
    # 安全检查
    all_results["security"] = check_security_config()
    
    # 备份状态
    all_results["backup"] = check_backup_status()
    
    # 数据库状态
    all_results["database"] = check_database_status()
    
    # 服务状态
    all_results["services"] = check_service_status()
    
    # 磁盘空间
    all_results["disk"] = check_disk_space()
    
    # 总结
    print("\n" + "=" * 60)
    print("检查总结")
    print("=" * 60)
    
    # 统计问题
    total_issues = 0
    total_warnings = 0
    
    if "security" in all_results:
        total_issues += len(all_results["security"].get("issues", []))
        total_warnings += len(all_results["security"].get("warnings", []))
    
    if "database" in all_results:
        total_issues += len(all_results["database"].get("issues", []))
    
    # 输出问题
    if total_issues > 0:
        print(f"\n❌ 发现 {total_issues} 个严重问题:")
        if "security" in all_results:
            for issue in all_results["security"].get("issues", []):
                print(f"  - {issue}")
        if "database" in all_results:
            for issue in all_results["database"].get("issues", []):
                print(f"  - {issue}")
    
    if total_warnings > 0:
        print(f"\n⚠ 发现 {total_warnings} 个警告:")
        if "security" in all_results:
            for warning in all_results["security"].get("warnings", []):
                print(f"  - {warning}")
    
    if total_issues == 0 and total_warnings == 0:
        print("\n✓ 系统健康检查通过，未发现严重问题")
    
    # 输出建议
    print("\n" + "=" * 60)
    print("建议")
    print("=" * 60)
    
    suggestions = []
    
    if total_issues > 0:
        suggestions.append("1. 立即修复严重安全问题（JWT密钥、认证配置等）")
    
    if all_results.get("backup", {}).get("enabled") and all_results.get("backup", {}).get("backup_count", 0) == 0:
        suggestions.append("2. 检查自动备份是否正常工作")
    
    if all_results.get("disk", {}).get("percent", 0) > 80:
        suggestions.append("3. 清理磁盘空间或扩展存储")
    
    if not suggestions:
        suggestions.append("系统运行正常，建议定期执行健康检查")
    
    for suggestion in suggestions:
        print(f"  {suggestion}")
    
    return 0 if total_issues == 0 else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n操作已取消")
        sys.exit(1)
    except Exception as e:
        logger.error(f"执行失败: {e}", exc_info=True)
        sys.exit(1)

