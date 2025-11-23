/**
 * 系統監控統計 Mock 數據
 */

export const mockSystemStats = {
  health: {
    status: "healthy",
    uptime_seconds: 86400,
    version: "0.1.0",
    timestamp: new Date().toISOString(),
  },
  metrics: {
    cpu_usage_percent: 45.2,
    memory_usage_percent: 62.5,
    disk_usage_percent: 38.1,
    active_connections: 12,
    queue_length: 3,
    timestamp: new Date().toISOString(),
  },
  services: {
    api_server: { status: "running", uptime: 86400 },
    database: { status: "connected", response_time_ms: 5 },
    redis: { status: "connected", response_time_ms: 2 },
    session_service: { status: "running", active_sessions: 45 },
  },
  qps: 125.5,
  avg_response_time: 234,
};

