/**
 * PM2 進程守護配置
 * 用於管理前端應用的生產環境進程
 * 
 * 使用方式：
 * 1. 如果是純靜態項目（使用 Nginx 服務），可以忽略此文件
 * 2. 如果需要 PM2 管理，運行: pm2 start ecosystem.config.js
 * 3. 查看狀態: pm2 status
 * 4. 查看日誌: pm2 logs frontend
 * 5. 重啟: pm2 restart frontend
 * 6. 停止: pm2 stop frontend
 */

module.exports = {
  apps: [
    {
      name: "frontend", // 應用名稱，可根據項目修改（如 aizkw, tgmini, hongbao）
      script: "serve", // 使用 serve 來服務靜態文件
      args: "-s dist -l 3000", // serve 參數：-s 表示 SPA 模式，-l 指定端口
      instances: 1, // 實例數量
      exec_mode: "fork", // 執行模式：fork 或 cluster
      env: {
        NODE_ENV: "production",
        PORT: 3000, // 端口號，根據實際情況修改
      },
      // 日誌配置
      error_file: "./logs/pm2-error.log",
      out_file: "./logs/pm2-out.log",
      log_date_format: "YYYY-MM-DD HH:mm:ss Z",
      merge_logs: true,
      // 自動重啟配置
      watch: false, // 生產環境建議關閉
      max_memory_restart: "500M", // 內存超過 500M 自動重啟
      // 重啟策略
      min_uptime: "10s", // 最小運行時間
      max_restarts: 10, // 最大重啟次數
      restart_delay: 4000, // 重啟延遲
    },
  ],
  
  // 如果項目有 Node.js 後端，可以添加後端配置
  // 示例（根據實際情況修改）：
  /*
  apps: [
    {
      name: "frontend",
      script: "serve",
      args: "-s dist -l 3000",
      // ... 前端配置
    },
    {
      name: "backend",
      script: "server.js", // 或 "npm", "start"
      args: "start",
      cwd: "./backend", // 後端目錄
      env: {
        NODE_ENV: "production",
        PORT: 8000,
      },
      // ... 後端配置
    },
  ],
  */
};
