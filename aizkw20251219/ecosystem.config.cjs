/**
 * PM2 生態系統配置文件
 * 用於管理 Node.js 應用程序的進程
 * 
 * 如果不需要後台運行，可以忽略此文件
 * 或者使用簡單配置用於未來擴展
 */

module.exports = {
  apps: [
    {
      name: 'aizkw20251219',
      script: 'npm',
      args: 'run preview',
      cwd: '/home/ubuntu/aizkw20251219',
      instances: 1,
      exec_mode: 'fork',
      watch: false,
      max_memory_restart: '500M',
      env: {
        NODE_ENV: 'production',
      },
      error_file: './logs/pm2-error.log',
      out_file: './logs/pm2-out.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
      merge_logs: true,
      autorestart: true,
      max_restarts: 10,
      min_uptime: '10s',
    },
  ],
};

