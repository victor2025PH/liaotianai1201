/**
 * 日誌列表 Mock 數據
 */

import { LogEntry } from "@/lib/api";

export const mockLogs: LogEntry[] = [
  {
    id: "log-001",
    level: "error",
    logger: "api",
    type: "API_ERROR",
    message: "Failed to connect to database: Connection timeout after 30s",
    severity: "high",
    timestamp: new Date(Date.now() - 3600000).toISOString(),
    source: "api.database",
    metadata: {
      request_id: "req-12345",
      stack_trace: "Error: Connection timeout\n  at Database.connect()\n  at API.handleRequest()",
      endpoint: "/api/v1/sessions",
    },
  },
  {
    id: "log-002",
    level: "warning",
    logger: "monitor",
    type: "PERFORMANCE",
    message: "Response time exceeded threshold: 2.5s (threshold: 2s)",
    severity: "medium",
    timestamp: new Date(Date.now() - 1800000).toISOString(),
    source: "api.monitor",
    metadata: {
      response_time: 2500,
      threshold: 2000,
    },
  },
  {
    id: "log-003",
    level: "info",
    logger: "session",
    type: "SESSION",
    message: "New session created: session-001",
    severity: "low",
    timestamp: new Date(Date.now() - 900000).toISOString(),
    source: "api.sessions",
    metadata: {
      session_id: "session-001",
      user_id: "user-001",
    },
  },
  {
    id: "log-004",
    level: "error",
    logger: "auth",
    type: "AUTH_ERROR",
    message: "Invalid API key provided",
    severity: "high",
    timestamp: new Date(Date.now() - 600000).toISOString(),
    source: "api.auth",
    metadata: {
      api_key: "sk-***",
      ip_address: "192.168.1.100",
    },
  },
  {
    id: "log-005",
    level: "info",
    logger: "system",
    type: "SYSTEM",
    message: "System health check passed",
    severity: "low",
    timestamp: new Date(Date.now() - 300000).toISOString(),
    source: "system.health",
  },
];

