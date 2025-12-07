module.exports = {
  apps: [
    {
      name: "backend",
      // 关键修改 1：使用绝对路径，彻底解决 "Interpreter NOT AVAILABLE" 错误
      cwd: "/home/ubuntu/telegram-ai-system/admin-backend",
      script: "main.py", // 根据你的清理报告，main.py 现在就在 backend 根目录下
      interpreter: "/home/ubuntu/telegram-ai-system/admin-backend/venv/bin/python",
      
      env: { 
        PORT: 8000,
        HOST: "0.0.0.0"
      },
      // 保留你的优秀配置
      error_file: "./logs/backend-error.log",
      out_file: "./logs/backend-out.log",
      log_date_format: "YYYY-MM-DD HH:mm:ss Z",
      merge_logs: true,
      autorestart: true,
      max_memory_restart: "1G"
    },
    {
      name: "frontend",
      // 关键修改 2：前端也用绝对路径，防止出错
      cwd: "/home/ubuntu/telegram-ai-system/saas-demo",
      script: "npm",
      args: "start",
      
      env: { 
        PORT: 3000,
        NODE_ENV: "production"
      },
      // 保留你的优秀配置
      error_file: "./logs/frontend-error.log",
      out_file: "./logs/frontend-out.log",
      log_date_format: "YYYY-MM-DD HH:mm:ss Z",
      merge_logs: true,
      autorestart: true,
      max_memory_restart: "500M"
    }
  ]
};