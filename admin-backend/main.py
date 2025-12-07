"""
FastAPI 应用入口点
用于从根目录直接启动应用
"""
import uvicorn
from app.main import app

if __name__ == "__main__":
    # 从环境变量读取配置，或使用默认值
    import os
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    
    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=os.getenv("ENV", "production") == "development"
    )

