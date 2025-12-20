module.exports = {
  apps: [
    {
      name: "backend",
      cwd: "/home/ubuntu/telegram-ai-system/admin-backend",
      // 使用虚拟环境中的 uvicorn
      script: "/home/ubuntu/telegram-ai-system/admin-backend/venv/bin/uvicorn",
      args: "app.main:app --host 0.0.0.0 --port 8000",
      interpreter: "none",
      env: {
        PORT: 8000,
        PYTHONPATH: "/home/ubuntu/telegram-ai-system/admin-backend",
        PYTHONUNBUFFERED: "1",
        NODE_ENV: "production"
      },
      error_file: "/home/ubuntu/telegram-ai-system/logs/backend-error.log",
      out_file: "/home/ubuntu/telegram-ai-system/logs/backend-out.log",
      log_date_format: "YYYY-MM-DD HH:mm:ss Z",
      merge_logs: true,
      // 自动重启配置
      autorestart: true,
      watch: false,
      // 资源限制（防止 CPU 100%）
      max_memory_restart: "800M",  // 降低内存限制，更早重启防止内存泄漏
      // 重启策略
      min_uptime: "30s",           // 至少运行 30 秒才算成功
      max_restarts: 15,            // 最多重启 15 次
      restart_delay: 10000,        // 重启延迟 10 秒
      // 进程管理
      instances: 1,
      exec_mode: "fork",
      // 健康检查
      kill_timeout: 5000,
      wait_ready: false,
      listen_timeout: 10000
    },
    {
      name: "next-server",
      cwd: "/home/ubuntu/telegram-ai-system/saas-demo",
      script: "npm",
      args: "start",
      env: {
        PORT: 3000,
        NODE_ENV: "production",
        // 限制 Node.js 内存使用（防止内存泄漏）
        NODE_OPTIONS: "--max-old-space-size=1024 --max-semi-space-size=128"
      },
      error_file: "/home/ubuntu/telegram-ai-system/logs/frontend-error.log",
      out_file: "/home/ubuntu/telegram-ai-system/logs/frontend-out.log",
      log_date_format: "YYYY-MM-DD HH:mm:ss Z",
      merge_logs: true,
      // 自动重启配置
      autorestart: true,
      watch: false,
      // 资源限制（防止 CPU 100%）
      max_memory_restart: "800M",  // 降低内存限制
      // 重启策略
      min_uptime: "30s",           // 至少运行 30 秒才算成功
      max_restarts: 15,            // 最多重启 15 次
      restart_delay: 10000,        // 重启延迟 10 秒
      // 进程管理
      instances: 1,
      exec_mode: "fork",
      // 健康检查
      kill_timeout: 5000,
      wait_ready: false,
      listen_timeout: 10000
    }
  ]
};