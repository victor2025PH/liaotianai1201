// 使用新的統一 API 客戶端
import { apiGet, apiPost, apiPut, apiDelete, ApiResult } from "./api-client";

// ==================== 類型定義 ====================

/**
 * Dashboard 統計數據
 */
export interface DashboardStats {
  today_sessions: number;
  sessions_change: string;
  success_rate: number;
  success_rate_change: string;
  token_usage: number;
  token_usage_change: string;
  error_count: number;
  error_count_change: string;
  avg_response_time: number;
  response_time_change: string;
  active_users: number;
  active_users_change: string;
}

/**
 * 最近會話項
 */
export interface RecentSession {
  id: string;
  user: string;
  messages: number;
  status: "completed" | "active" | "failed";
  duration: string;
  timestamp: string;
  started_at?: string;
}

/**
 * 最近錯誤項
 */
export interface RecentError {
  id: string;
  type: string;
  message: string;
  severity: "high" | "medium" | "low";
  timestamp: string;
}

/**
 * Dashboard 完整數據
 */
export interface DashboardData {
  stats: DashboardStats;
  recent_sessions: RecentSession[];
  recent_errors: RecentError[];
}

/**
 * 會話列表項
 */
export interface SessionListItem {
  id: string;
  user: string;
  status: "completed" | "active" | "failed";
  started_at: string;
  duration: string;
  messages: number;
  error_count?: number;
  token_usage?: number;
  model?: string;
}

/**
 * 會話列表響應
 */
export interface SessionList {
  items: SessionListItem[];
  total: number;
  page: number;
  page_size: number;
}

/**
 * 日誌條目
 */
export interface LogEntry {
  id: string;
  level: "error" | "warning" | "info";
  message: string;
  logger: string;
  timestamp: string;
  type?: string;
  severity?: "high" | "medium" | "low";
  source?: string;
  metadata?: Record<string, any>;
  stack_trace?: string;
  request_id?: string;
}

/**
 * 日誌列表響應
 */
export interface LogList {
  items: LogEntry[];
  total: number;
  page: number;
  page_size: number;
}

/**
 * 告警規則（匹配後端 Schema）
 */
export interface AlertRule {
  id: string;
  name: string;
  rule_type: string; // error_rate, response_time, system_errors, account_offline
  alert_level: "error" | "warning" | "info";
  threshold_value: number;
  threshold_operator: ">" | ">=" | "<" | "<=" | "==" | "!=";
  enabled: boolean;
  notification_method: "email" | "webhook" | "telegram";
  notification_target?: string; // 郵箱地址、Webhook URL、Telegram Chat ID
  rule_conditions?: Record<string, any>; // JSON 格式的規則條件
  description?: string;
  created_by?: string;
  created_at: string; // ISO 格式時間戳
  updated_at: string; // ISO 格式時間戳
}

/**
 * 創建告警規則請求
 */
export interface AlertRuleCreate {
  name: string;
  rule_type: string;
  alert_level?: "error" | "warning" | "info";
  threshold_value: number;
  threshold_operator?: ">" | ">=" | "<" | "<=" | "==" | "!=";
  enabled?: boolean;
  notification_method?: "email" | "webhook" | "telegram";
  notification_target?: string;
  rule_conditions?: Record<string, any>;
  description?: string;
}

/**
 * 更新告警規則請求
 */
export interface AlertRuleUpdate {
  name?: string;
  rule_type?: string;
  alert_level?: "error" | "warning" | "info";
  threshold_value?: number;
  threshold_operator?: ">" | ">=" | "<" | "<=" | "==" | "!=";
  enabled?: boolean;
  notification_method?: "email" | "webhook" | "telegram";
  notification_target?: string;
  rule_conditions?: Record<string, any>;
  description?: string;
}

/**
 * 告警規則列表響應
 */
export interface AlertRuleList {
  items: AlertRule[];
  total: number;
}

/**
 * 系統指標
 */
export interface SystemMetric {
  cpu_usage: number;
  memory_usage: number;
  disk_usage: number;
  network_in: number;
  network_out: number;
  qps: number;
  avg_response_time: number;
  error_rate: number;
}

// ==================== API 函數 ====================

// Dashboard API - 使用群組AI儀表板API（真實數據）
export async function getDashboardData(): Promise<ApiResult<DashboardData>> {
  // 直接使用兼容API，它會調用群組AI API獲取真實數據
  return apiGet<DashboardData>("/dashboard", { showErrorToast: false });
}

// Sessions API
export async function getSessions(
  page: number = 1,
  pageSize: number = 20
): Promise<ApiResult<SessionList>> {
  return apiGet<SessionList>(
    `/sessions?page=${page}&page_size=${pageSize}`,
    { showErrorToast: false }
  );
}

/**
 * 會話詳情
 */
export interface SessionDetail extends Omit<SessionListItem, "messages"> {
  messages: Array<{
    id: string;
    role: "user" | "assistant" | "system";
    content: string;
    timestamp: string;
  }>;
  ended_at?: string;
  error_message?: string;
  request_metadata?: Record<string, any>;
  response_metadata?: Record<string, any>;
}

export async function getSessionDetail(id: string): Promise<ApiResult<SessionDetail>> {
  return apiGet<SessionDetail>(`/sessions/${id}`, { showErrorToast: false });
}

// Logs API - 使用群組AI日誌API（真實日誌）
export async function getLogs(
  page: number = 1,
  pageSize: number = 20,
  level?: "error" | "warning" | "info",
  q?: string
): Promise<ApiResult<LogList>> {
  const params = new URLSearchParams({
    page: page.toString(),
    page_size: pageSize.toString(),
  });
  if (level) {
    params.append("level", level);
  }
  if (q) {
    params.append("q", q);
  }
  // 直接使用兼容API，它會調用群組AI API獲取真實日誌
  return apiGet<LogList>(`/logs?${params.toString()}`, { showErrorToast: false });
}

// Sessions API with search and filters
export async function getSessionsWithFilters(
  page: number = 1,
  pageSize: number = 20,
  q?: string,
  range?: string,
  startDate?: string,
  endDate?: string
): Promise<ApiResult<SessionList>> {
  const params = new URLSearchParams({
    page: page.toString(),
    page_size: pageSize.toString(),
  });
  if (q) {
    params.append("q", q);
  }
  if (range) {
    params.append("range", range);
  }
  if (startDate) {
    params.append("start_date", startDate);
  }
  if (endDate) {
    params.append("end_date", endDate);
  }
  return apiGet<SessionList>(`/sessions?${params.toString()}`, { showErrorToast: false });
}

// Metrics API
export interface ResponseTimeDataPoint {
  hour: number;
  timestamp: string;
  avg_response_time: number;
}

export interface ResponseTimeMetrics {
  data_points: ResponseTimeDataPoint[];
  average: number;
  min: number;
  max: number;
  trend: string;
}

export interface SystemStatusItem {
  label: string;
  status: string;
  value: string;
  description: string;
}

export interface SystemMetrics {
  status_items: SystemStatusItem[];
  last_updated: string;
}

export interface MetricsData {
  response_time: ResponseTimeMetrics;
  system_status: SystemMetrics;
}

export async function getMetrics(): Promise<ApiResult<MetricsData>> {
  return apiGet<MetricsData>("/metrics", { showErrorToast: false });
}

// Alert Settings API
export interface AlertSettings {
  error_rate_threshold: number;
  max_response_time: number;
  notification_method: "email" | "webhook";
  email_recipients?: string;
  webhook_url?: string;
  webhook_enabled: boolean;
}

export async function getAlertSettings(): Promise<ApiResult<AlertSettings>> {
  return apiGet<AlertSettings>("/settings/alerts", { showErrorToast: false });
}

export async function saveAlertSettings(settings: AlertSettings): Promise<ApiResult<{ success: boolean; message: string }>> {
  return apiPost<{ success: boolean; message: string }>(
    "/settings/alerts",
    settings,
    {
      showErrorToast: true,
      showSuccessToast: true,
      successMessage: "告警設置已保存",
    }
  );
}

/**
 * 獲取告警規則列表
 */
export async function getAlertRules(): Promise<ApiResult<AlertRuleList>> {
  return apiGet<AlertRuleList>("/group-ai/alert-rules/", { showErrorToast: false });
}

/**
 * 獲取單個告警規則
 */
export async function getAlertRule(ruleId: string): Promise<ApiResult<AlertRule>> {
  return apiGet<AlertRule>(`/group-ai/alert-rules/${ruleId}`, { showErrorToast: false });
}

/**
 * 創建告警規則
 */
export async function createAlertRule(rule: AlertRuleCreate): Promise<ApiResult<AlertRule>> {
  return apiPost<AlertRule>("/group-ai/alert-rules/", rule, {
    showErrorToast: true,
    showSuccessToast: true,
    successMessage: "告警規則已創建",
  });
}

/**
 * 更新告警規則
 */
export async function updateAlertRule(ruleId: string, updates: AlertRuleUpdate): Promise<ApiResult<AlertRule>> {
  return apiPut<AlertRule>(`/group-ai/alert-rules/${ruleId}`, updates, {
    showErrorToast: true,
    showSuccessToast: true,
    successMessage: "告警規則已更新",
  });
}

/**
 * 刪除告警規則
 */
export async function deleteAlertRule(ruleId: string): Promise<ApiResult<void>> {
  return apiDelete<void>(`/group-ai/alert-rules/${ruleId}`, {
    showErrorToast: true,
    showSuccessToast: true,
    successMessage: "告警規則已刪除",
  });
}

/**
 * 啟用告警規則
 */
export async function enableAlertRule(ruleId: string): Promise<ApiResult<AlertRule>> {
  return apiPost<AlertRule>(`/group-ai/alert-rules/${ruleId}/enable`, {}, {
    showErrorToast: true,
    showSuccessToast: true,
    successMessage: "告警規則已啟用",
  });
}

/**
 * 禁用告警規則
 */
export async function disableAlertRule(ruleId: string): Promise<ApiResult<AlertRule>> {
  return apiPost<AlertRule>(`/group-ai/alert-rules/${ruleId}/disable`, {}, {
    showErrorToast: true,
    showSuccessToast: true,
    successMessage: "告警規則已禁用",
  });
}

// System Monitor API
export interface SystemHealth {
  status: string;
  uptime_seconds: number;
  version: string;
  timestamp: string;
}

export interface SystemMetricsSchema {
  cpu_usage_percent: number;
  memory_usage_percent: number;
  disk_usage_percent: number;
  active_connections: number;
  queue_length: number;
  timestamp: string;
}

export interface SystemMonitorData {
  health: SystemHealth;
  metrics: SystemMetricsSchema;
  services: Record<string, any>;
}

export async function getSystemMonitor(): Promise<ApiResult<SystemMonitorData>> {
  return apiGet<SystemMonitorData>("/system/monitor", { showErrorToast: false });
}

