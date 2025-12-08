module.exports = {
  apps: [
    {
      name: "backend",
      // 1. 工作目录：绝对路径，防止迷路
      cwd: "/home/ubuntu/telegram-ai-system/admin-backend",
      
      // 2. 核心修改：直接运行 uvicorn 二进制文件 (不再运行 main.py)
      // 使用绝对路径指向虚拟环境里的 uvicorn
      script: "/home/ubuntu/telegram-ai-system/admin-backend/venv/bin/uvicorn",
      
      // 3. 启动参数：告诉 uvicorn 去哪里找 app 对象
      // 格式：模块名:变量名 --host --port
      args: "app.main:app --host 0.0.0.0 --port 8000",
      
      // 4. 关键设置：设置为 "none"
      // 这告诉 PM2："这是一个可执行程序，不要试图把它当 JS 或 Python 脚本去解析"
      // 这能直接解决 SyntaxError 报错
      interpreter: "none",
      
      env: { 
        PORT: 8000,
        // 强制添加 Python 路径，防止找不到 app 模块
        PYTHONPATH: "/home/ubuntu/telegram-ai-system/admin-backend"
      },
      
      // 日志配置
      error_file: "./logs/backend-error.log",
      out_file: "./logs/backend-out.log",
      merge_logs: true,
      min_uptime: "5s",       // 防止频繁重启
      max_restarts: 10        // 限制最大重启次数
    },
    {
      name: "frontend",
      cwd: "/home/ubuntu/telegram-ai-system/saas-demo",
      script: "npm",
      args: "start",
      env: { 
        PORT: 3000,
        NODE_ENV: "production"
      },
      error_file: "./logs/frontend-error.log",
      out_file: "./logs/frontend-out.log",
      merge_logs: true
    }
  ]
};