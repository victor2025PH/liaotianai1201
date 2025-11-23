/**
 * 群組 AI API 客戶端
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1/group-ai"

export interface Account {
  account_id: string
  session_file: string
  script_id: string
  server_id?: string | null  // 關聯的服務器ID
  status: string
  group_count: number
  message_count: number
  reply_count: number
  last_activity?: string
  // 帳號資料信息
  phone_number?: string | null
  username?: string | null
  first_name?: string | null
  last_name?: string | null
  display_name?: string | null
  avatar_url?: string | null
  bio?: string | null
  user_id?: number | null
}

export interface AccountMetrics {
  account_id: string
  message_count: number
  reply_count: number
  redpacket_count: number
  error_count: number
  last_activity?: string
}

export interface SystemMetrics {
  total_accounts: number
  online_accounts: number
  total_messages: number
  total_replies: number
  total_redpackets: number
  total_errors: number
  average_reply_time: number
  timestamp: string
}

export interface Alert {
  alert_id: string
  alert_type: string
  account_id?: string
  message: string
  timestamp: string
  resolved: boolean
}

export interface Event {
  type: string
  account_id?: string
  message_type?: string
  success?: boolean
  timestamp: string
  [key: string]: any
}

// 賬號管理 API
export interface AccountListParams {
  page?: number
  page_size?: number
  search?: string
  status_filter?: string
  script_id?: string
  server_id?: string
  active?: boolean
  sort_by?: string
  sort_order?: "asc" | "desc"
}

export async function getAccounts(params?: AccountListParams): Promise<Account[]> {
  try {
    const { fetchWithAuth } = await import("./client")
    const queryParams = new URLSearchParams()
    if (params?.page !== undefined) queryParams.append("page", params.page.toString())
    if (params?.page_size !== undefined) queryParams.append("page_size", params.page_size.toString())
    if (params?.search) queryParams.append("search", params.search)
    if (params?.status_filter) queryParams.append("status_filter", params.status_filter)
    if (params?.script_id) queryParams.append("script_id", params.script_id)
    if (params?.server_id) queryParams.append("server_id", params.server_id)
    if (params?.active !== undefined) queryParams.append("active", params.active.toString())
    if (params?.sort_by) queryParams.append("sort_by", params.sort_by)
    if (params?.sort_order) queryParams.append("sort_order", params.sort_order)
    
    const url = `${API_BASE}/accounts/${queryParams.toString() ? `?${queryParams.toString()}` : ""}`
    const response = await fetchWithAuth(url, {
      headers: {
        "Content-Type": "application/json",
      },
    })
    
    if (!response.ok) {
      // 嘗試獲取錯誤詳情
      let errorMessage = `HTTP ${response.status}`
      try {
        const errorData = await response.json()
        errorMessage = errorData.message || errorData.detail || errorMessage
      } catch {
        // 如果無法解析 JSON，使用默認錯誤消息
      }
      
      // 如果是 500 錯誤，返回空數組而不是拋出異常，避免前端崩潰
      if (response.status === 500) {
        console.error(`[API] 帳號 API 返回 500 錯誤: ${errorMessage}`)
        return [] // 返回空數組，讓前端可以正常顯示（即使沒有數據）
      }
      
      throw new Error(errorMessage)
    }
    
    const data = await response.json()
    return data.items || data || []
  } catch (error) {
    // 網絡錯誤或其他錯誤
    if (error instanceof TypeError && error.message.includes("fetch")) {
      console.error("[API] 網絡錯誤，無法連接到後端服務")
      return [] // 返回空數組
    }
    throw error
  }
}

export async function getAccount(accountId: string): Promise<Account> {
  const { fetchWithAuth } = await import("./client")
  const response = await fetchWithAuth(`${API_BASE}/accounts/${accountId}`)
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`)
  }
  return response.json()
}

export async function startAccount(accountId: string): Promise<Account> {
  try {
    const { fetchWithAuth } = await import("./client")
    const response = await fetchWithAuth(`${API_BASE}/accounts/${accountId}/start`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
    })
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: `HTTP ${response.status}` }))
      throw new Error(error.detail || `啟動賬號失敗: HTTP ${response.status}`)
    }
    return response.json()
  } catch (err) {
    if (err instanceof TypeError && err.message.includes("fetch")) {
      throw new Error("無法連接到後端服務，請檢查服務是否運行")
    }
    throw err
  }
}

export async function stopAccount(accountId: string): Promise<Account> {
  try {
    const { fetchWithAuth } = await import("./client")
    const response = await fetchWithAuth(`${API_BASE}/accounts/${accountId}/stop`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
    })
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: `HTTP ${response.status}` }))
      throw new Error(error.detail || `停止賬號失敗: HTTP ${response.status}`)
    }
    return response.json()
  } catch (err) {
    if (err instanceof TypeError && err.message.includes("fetch")) {
      throw new Error("無法連接到後端服務，請檢查服務是否運行")
    }
    throw err
  }
}

export async function updateAccount(
  accountId: string,
  request: {
    script_id?: string
    server_id?: string
    display_name?: string
    bio?: string
    active?: boolean
    reply_rate?: number
    redpacket_enabled?: boolean
    redpacket_probability?: number
    max_replies_per_hour?: number
    min_reply_interval?: number
    group_ids?: number[]
  }
): Promise<Account> {
  const { fetchWithAuth } = await import("./client")
  const response = await fetchWithAuth(`${API_BASE}/accounts/${accountId}`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(request),
  })
  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail || `HTTP ${response.status}`)
  }
  return response.json()
}

export async function deleteAccount(accountId: string): Promise<void> {
  const { fetchWithAuth } = await import("./client")
  const response = await fetchWithAuth(`${API_BASE}/accounts/${accountId}`, {
    method: "DELETE",
  })
  if (!response.ok) {
    const error = await response.json().catch(() => ({}))
    throw new Error(error.detail || `HTTP ${response.status}`)
  }
}

export interface AccountCreateRequest {
  account_id: string
  session_file: string
  script_id: string
  group_ids?: number[]
  active?: boolean
  reply_rate?: number
  redpacket_enabled?: boolean
  redpacket_probability?: number
  max_replies_per_hour?: number
  min_reply_interval?: number
}

// 群組管理API
export interface CreateGroupRequest {
  account_id: string
  title: string
  description?: string
  member_ids?: number[]
  auto_reply?: boolean
}

export interface JoinGroupRequest {
  account_id: string
  group_username?: string
  group_id?: number
  invite_link?: string
  auto_reply?: boolean
}

export interface StartGroupChatRequest {
  account_id: string
  group_id: number
  auto_reply?: boolean
}

export interface SendTestMessageRequest {
  account_id: string
  group_id: number
  message: string
  wait_for_reply?: boolean
  wait_timeout?: number
}

export interface SendTestMessageResponse {
  account_id: string
  group_id: number
  message_id?: number
  success: boolean
  message: string
  reply_received?: boolean
  reply_count_before?: number
  reply_count_after?: number
}

export interface GroupResponse {
  account_id: string
  group_id: number
  group_title?: string
  success: boolean
  message: string
}

export async function createGroup(request: CreateGroupRequest): Promise<GroupResponse> {
  const { fetchWithAuth } = await import("./client")
  const response = await fetchWithAuth(`${API_BASE}/groups/create`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(request),
  })
  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail || `HTTP ${response.status}`)
  }
  return response.json()
}

export async function joinGroup(request: JoinGroupRequest): Promise<GroupResponse> {
  const { fetchWithAuth } = await import("./client")
  const response = await fetchWithAuth(`${API_BASE}/groups/join`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(request),
  })
  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail || `HTTP ${response.status}`)
  }
  return response.json()
}

export async function startGroupChat(request: StartGroupChatRequest): Promise<GroupResponse> {
  const { fetchWithAuth } = await import("./client")
  const response = await fetchWithAuth(`${API_BASE}/groups/start-chat`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(request),
  })
  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail || `HTTP ${response.status}`)
  }
  return response.json()
}

export async function sendTestMessage(request: SendTestMessageRequest): Promise<SendTestMessageResponse> {
  const { fetchWithAuth } = await import("./client")
  const response = await fetchWithAuth(`${API_BASE}/groups/send-test-message`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(request),
  })
  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail || `HTTP ${response.status}`)
  }
  return response.json()
}

export async function createAccount(request: AccountCreateRequest): Promise<Account> {
  const { fetchWithAuth } = await import("./client")
  const response = await fetchWithAuth(`${API_BASE}/accounts/`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(request),
  })
  if (!response.ok) {
    let errorMessage = `HTTP ${response.status}`
    try {
      const error = await response.json()
      // UserFriendlyError 返回格式: { error_code: "...", message: "..." }
      // 也可能直接是 { detail: "..." }
      if (error.message) {
        // UserFriendlyError 格式
        errorMessage = error.message
        // 如果有 technical_detail（开发环境），也显示
        if (error.technical_detail) {
          errorMessage += `\n技術詳情: ${error.technical_detail}`
        }
      } else if (error.detail) {
        // 可能是 detail 字段（字符串或对象）
        if (typeof error.detail === 'string') {
          errorMessage = error.detail
        } else if (error.detail.message) {
          errorMessage = error.detail.message
        } else {
          errorMessage = JSON.stringify(error.detail)
        }
      } else {
        errorMessage = JSON.stringify(error)
      }
    } catch {
      // 如果无法解析 JSON，使用默认错误信息
      if (response.status === 404) {
        errorMessage = `Session 文件不存在: ${request.session_file}`
      } else if (response.status === 500) {
        errorMessage = `創建賬號失敗: ${request.account_id}`
      }
    }
    throw new Error(errorMessage)
  }
  return response.json()
}

export interface UploadSessionResponse {
  success: boolean
  message: string
  filename: string
  path: string
}

export async function uploadSessionFile(file: File): Promise<UploadSessionResponse> {
  const { fetchWithAuth } = await import("./client")
  const formData = new FormData()
  formData.append("file", file)
  
  const response = await fetchWithAuth(`${API_BASE}/accounts/upload-session`, {
    method: "POST",
    body: formData,
  })
  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail || `HTTP ${response.status}`)
  }
  return response.json()
}

export interface SessionFile {
  filename: string
  path: string
  size: number
  modified: number
}

export interface ScanSessionsResponse {
  sessions: SessionFile[]
  count: number
  directory?: string
  exists?: boolean
}

export async function scanSessions(): Promise<ScanSessionsResponse> {
  const { fetchWithAuth } = await import("./client")
  const response = await fetchWithAuth(`${API_BASE}/accounts/scan-sessions`)
  if (!response.ok) {
    const error = await response.json().catch(() => ({}))
    throw new Error(error.detail || `HTTP ${response.status}`)
  }
  return response.json()
}

// 監控 API
export async function getAccountMetrics(accountId?: string): Promise<AccountMetrics[]> {
  const { fetchWithAuth } = await import("./client")
  const url = accountId
    ? `${API_BASE}/monitor/accounts/metrics?account_id=${accountId}`
    : `${API_BASE}/monitor/accounts/metrics`
  const response = await fetchWithAuth(url)
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`)
  }
  return response.json()
}

export async function getSystemMetrics(): Promise<SystemMetrics> {
  const { fetchWithAuth } = await import("./client")
  const response = await fetchWithAuth(`${API_BASE}/monitor/system`)
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`)
  }
  return response.json()
}

export async function getAlerts(
  limit: number = 50,
  alertType?: string,
  resolved?: boolean
): Promise<Alert[]> {
  const { fetchWithAuth } = await import("./client")
  const params = new URLSearchParams()
  params.append("limit", limit.toString())
  if (alertType) params.append("alert_type", alertType)
  if (resolved !== undefined) params.append("resolved", resolved.toString())
  
  const response = await fetchWithAuth(`${API_BASE}/monitor/alerts?${params}`)
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`)
  }
  return response.json()
}

// ============ 監控增強 API ============

export interface MetricsHistoryData {
  metric_type: string
  data_points: Array<{
    timestamp: string
    value: number
  }>
  period: string
}

export interface MetricsStatistics {
  total_messages: number
  total_replies: number
  total_errors: number
  total_redpackets: number
  reply_rate: number
  error_rate: number
  average_reply_time: number
  period: string
  start_time: string
  end_time: string
}

/**
 * 獲取系統指標歷史數據
 */
export async function getSystemMetricsHistory(
  metricType: "messages" | "replies" | "errors" | "redpackets" = "messages",
  period: "1h" | "24h" | "7d" | "30d" = "24h"
): Promise<MetricsHistoryData> {
  const { fetchWithAuth } = await import("./client")
  const params = new URLSearchParams()
  params.append("metric_type", metricType)
  params.append("period", period)
  
  const response = await fetchWithAuth(`${API_BASE}/monitor/system/history?${params}`)
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`)
  }
  return response.json()
}

/**
 * 獲取賬號指標歷史數據
 */
export async function getAccountMetricsHistory(
  accountId: string,
  metricType: "messages" | "replies" | "errors" | "redpackets" = "messages",
  period: "1h" | "24h" | "7d" | "30d" = "24h"
): Promise<MetricsHistoryData> {
  const { fetchWithAuth } = await import("./client")
  const params = new URLSearchParams()
  params.append("metric_type", metricType)
  params.append("period", period)
  
  const response = await fetchWithAuth(`${API_BASE}/monitor/accounts/${accountId}/history?${params}`)
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`)
  }
  return response.json()
}

/**
 * 獲取系統指標統計
 */
export async function getSystemStatistics(
  period: "1h" | "24h" | "7d" | "30d" = "24h"
): Promise<MetricsStatistics> {
  const { fetchWithAuth } = await import("./client")
  const params = new URLSearchParams()
  params.append("period", period)
  
  const response = await fetchWithAuth(`${API_BASE}/monitor/system/statistics?${params}`)
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`)
  }
  return response.json()
}

export async function resolveAlert(alertId: string): Promise<void> {
  const { fetchWithAuth } = await import("./client")
  const response = await fetchWithAuth(`${API_BASE}/monitor/alerts/${alertId}/resolve`, {
    method: "POST",
  })
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`)
  }
}

// ============ 自動化任務 API ============

export interface AutomationTask {
  id: string
  name: string
  description?: string
  task_type: "scheduled" | "triggered" | "manual"
  task_action: string
  schedule_config?: Record<string, any>
  trigger_config?: Record<string, any>
  action_config: Record<string, any>
  enabled: boolean
  last_run_at?: string
  next_run_at?: string
  run_count: number
  success_count: number
  failure_count: number
  last_result?: string
  created_at: string
  updated_at: string
  created_by?: string
  dependent_tasks?: string[]
  notify_on_success?: boolean
  notify_on_failure?: boolean
  notify_recipients?: string[]
}

export interface AutomationTaskLog {
  id: string
  task_id: string
  status: "success" | "failure" | "running"
  started_at: string
  completed_at?: string
  duration_seconds?: number
  result?: string
  error_message?: string
  execution_data?: Record<string, any>
}

export interface AutomationTaskCreate {
  name: string
  description?: string
  task_type: "scheduled" | "triggered" | "manual"
  task_action: string
  schedule_config?: Record<string, any>
  trigger_config?: Record<string, any>
  action_config: Record<string, any>
  enabled?: boolean
  dependent_tasks?: string[]
  notify_on_success?: boolean
  notify_on_failure?: boolean
  notify_recipients?: string[]
}

export interface AutomationTaskUpdate {
  name?: string
  description?: string
  schedule_config?: Record<string, any>
  trigger_config?: Record<string, any>
  action_config?: Record<string, any>
  enabled?: boolean
  dependent_tasks?: string[]
  notify_on_success?: boolean
  notify_on_failure?: boolean
  notify_recipients?: string[]
}

/**
 * 創建自動化任務
 */
export async function createAutomationTask(task: AutomationTaskCreate): Promise<AutomationTask> {
  const { fetchWithAuth } = await import("./client")
  const response = await fetchWithAuth(`${API_BASE}/automation-tasks`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(task),
  })
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`)
  }
  return response.json()
}

/**
 * 列出自動化任務
 */
export async function listAutomationTasks(params?: {
  page?: number
  page_size?: number
  task_type?: string
  enabled?: boolean
}): Promise<AutomationTask[]> {
  const urlParams = new URLSearchParams()
  if (params?.page) urlParams.append("page", params.page.toString())
  if (params?.page_size) urlParams.append("page_size", params.page_size.toString())
  if (params?.task_type) urlParams.append("task_type", params.task_type)
  if (params?.enabled !== undefined) urlParams.append("enabled", params.enabled.toString())
  
  const { fetchWithAuth } = await import("./client")
  const response = await fetchWithAuth(`${API_BASE}/automation-tasks?${urlParams}`)
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`)
  }
  return response.json()
}

/**
 * 獲取自動化任務詳情
 */
export async function getAutomationTask(taskId: string): Promise<AutomationTask> {
  const { fetchWithAuth } = await import("./client")
  const response = await fetchWithAuth(`${API_BASE}/automation-tasks/${taskId}`)
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`)
  }
  return response.json()
}

/**
 * 更新自動化任務
 */
export async function updateAutomationTask(
  taskId: string,
  update: AutomationTaskUpdate
): Promise<AutomationTask> {
  const { fetchWithAuth } = await import("./client")
  const response = await fetchWithAuth(`${API_BASE}/automation-tasks/${taskId}`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(update),
  })
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`)
  }
  return response.json()
}

/**
 * 刪除自動化任務
 */
export async function deleteAutomationTask(taskId: string): Promise<void> {
  const { fetchWithAuth } = await import("./client")
  const response = await fetchWithAuth(`${API_BASE}/automation-tasks/${taskId}`, {
    method: "DELETE",
  })
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`)
  }
}

/**
 * 手動執行自動化任務
 */
export async function runAutomationTask(taskId: string): Promise<{ message: string; task_id: string; status: string }> {
  const { fetchWithAuth } = await import("./client")
  const response = await fetchWithAuth(`${API_BASE}/automation-tasks/${taskId}/run`, {
    method: "POST",
  })
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`)
  }
  return response.json()
}

/**
 * 獲取任務執行日誌
 */
export async function getTaskLogs(taskId: string, limit?: number): Promise<AutomationTaskLog[]> {
  const { fetchWithAuth } = await import("./client")
  const urlParams = new URLSearchParams()
  if (limit) urlParams.append("limit", limit.toString())
  
  const response = await fetchWithAuth(`${API_BASE}/automation-tasks/${taskId}/logs?${urlParams}`)
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`)
  }
  return response.json()
}

export async function getEvents(
  accountId?: string,
  eventType?: string,
  limit: number = 100
): Promise<Event[]> {
  const params = new URLSearchParams()
  if (accountId) params.append("account_id", accountId)
  if (eventType) params.append("event_type", eventType)
  params.append("limit", limit.toString())
  
  const { fetchWithAuth } = await import("./client")
  const response = await fetchWithAuth(`${API_BASE}/monitor/events?${params}`)
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`)
  }
  return response.json()
}

// 調控 API
export interface AccountParams {
  reply_rate?: number
  redpacket_enabled?: boolean
  redpacket_probability?: number
  max_replies_per_hour?: number
  min_reply_interval?: number
  active?: boolean
  // 新增：時間段控制
  work_hours_start?: number
  work_hours_end?: number
  work_days?: number[]
  // 新增：關鍵詞過濾
  keyword_whitelist?: string[]
  keyword_blacklist?: string[]
  // 新增：AI生成參數
  ai_temperature?: number
  ai_max_tokens?: number
  // 新增：群組特定設置
  group_specific_settings?: Record<number, Record<string, any>>
  // 新增：優先級控制
  reply_priority?: number
  // 自定義參數
  custom_params?: Record<string, any>
}

export async function updateAccountParams(
  accountId: string,
  params: AccountParams
): Promise<{ account_id: string; updated_params: Record<string, any>; success: boolean }> {
  const { fetchWithAuth } = await import("./client")
  const response = await fetchWithAuth(`${API_BASE}/control/accounts/${accountId}/params`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(params),
  })
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`)
  }
  return response.json()
}

export async function getAccountParams(accountId: string): Promise<AccountParams> {
  try {
    const { fetchWithAuth } = await import("./client")
    const response = await fetchWithAuth(`${API_BASE}/control/accounts/${accountId}/params`, {
      headers: {
        "Content-Type": "application/json",
      },
    })
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: `HTTP ${response.status}` }))
      throw new Error(error.detail || `獲取賬號參數失敗: HTTP ${response.status}`)
    }
    return response.json()
  } catch (err) {
    if (err instanceof TypeError && err.message.includes("fetch")) {
      throw new Error("無法連接到後端服務，請檢查服務是否運行")
    }
    throw err
  }
}

// 劇本管理 API
export interface Script {
  id: string
  script_id: string
  name: string
  version: string
  yaml_content: string
  description?: string
  status?: string  // draft, reviewing, approved, rejected, published, disabled
  created_at: string
  updated_at: string
}

export interface ScriptCreateRequest {
  script_id: string
  name: string
  version?: string
  yaml_content: string
  description?: string
}

export interface ScriptUpdateRequest {
  name?: string
  version?: string
  yaml_content?: string
  description?: string
}

export interface ScriptListResponse {
  items: Script[]
  total: number
}

export interface ScriptListParams {
  skip?: number
  limit?: number
  search?: string
  status?: string
  sort_by?: string
  sort_order?: "asc" | "desc"
  _t?: number // 强制刷新时间戳参数
}

export async function getScripts(params?: ScriptListParams): Promise<Script[]> {
  try {
    const { fetchWithAuth } = await import("./client")
    const queryParams = new URLSearchParams()
    if (params?.skip !== undefined) queryParams.append("skip", params.skip.toString())
    if (params?.limit !== undefined) queryParams.append("limit", params.limit.toString())
    if (params?.search) queryParams.append("search", params.search)
    if (params?.status) queryParams.append("status", params.status)
    if (params?.sort_by) queryParams.append("sort_by", params.sort_by)
    if (params?.sort_order) queryParams.append("sort_order", params.sort_order)
    // 添加强制刷新时间戳参数以绕过缓存
    if (params?._t !== undefined) queryParams.append("_t", params._t.toString())
    
    const url = `${API_BASE}/scripts/${queryParams.toString() ? `?${queryParams.toString()}` : ""}`
    const response = await fetchWithAuth(url, {
      headers: {
        "Content-Type": "application/json",
      },
    })
    
    if (!response.ok) {
      // 嘗試獲取錯誤詳情
      let errorMessage = `HTTP ${response.status}`
      try {
        const errorData = await response.json()
        errorMessage = errorData.message || errorData.detail || errorMessage
      } catch {
        // 如果無法解析 JSON，使用默認錯誤消息
      }
      
      // 如果是 500 或網絡錯誤，返回空數組而不是拋出異常，避免前端崩潰
      if (response.status === 500 || response.status === 404) {
        console.error(`[API] 劇本 API 返回 ${response.status} 錯誤: ${errorMessage}`)
        return [] // 返回空數組，讓前端可以正常顯示（即使沒有數據）
      }
      
      throw new Error(errorMessage)
    }
    
    const data = await response.json()
    // 后端返回的是数组，不是ScriptListResponse
    if (Array.isArray(data)) {
      return data.map((item: any) => ({
        ...item,
        id: item.script_id, // 添加id字段以兼容前端
      }))
    }
    // 如果是ScriptListResponse格式，返回items
    return (data.items || []).map((item: any) => ({
      ...item,
      id: item.script_id,
    }))
  } catch (error) {
    // 網絡錯誤或其他錯誤
    if (error instanceof TypeError && error.message.includes("fetch")) {
      console.error("[API] 網絡錯誤，無法連接到後端服務（劇本 API）")
      return [] // 返回空數組
    }
    // 如果是已經處理過的 HTTP 錯誤，重新拋出
    if (error instanceof Error && !error.message.includes("fetch")) {
      throw error
    }
    // 其他未知錯誤也返回空數組
    console.error("[API] 獲取劇本列表時發生未知錯誤:", error)
    return []
  }
}

export async function getScript(scriptId: string): Promise<Script> {
  const { fetchWithAuth } = await import("./client")
  const response = await fetchWithAuth(`${API_BASE}/scripts/${encodeURIComponent(scriptId)}`)
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: `HTTP ${response.status}` }))
    throw new Error(error.detail || `HTTP ${response.status}`)
  }
  return response.json()
}

export async function createScript(request: ScriptCreateRequest): Promise<Script> {
  const { fetchWithAuth } = await import("./client")
  const response = await fetchWithAuth(`${API_BASE}/scripts/`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(request),
  })
  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail || `HTTP ${response.status}`)
  }
  return response.json()
}

export async function updateScript(
  scriptId: string,
  request: ScriptUpdateRequest
): Promise<Script> {
  const { fetchWithAuth } = await import("./client")
  const response = await fetchWithAuth(`${API_BASE}/scripts/${encodeURIComponent(scriptId)}`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(request),
  })
  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail || `HTTP ${response.status}`)
  }
  return response.json()
}

export async function deleteScript(scriptId: string): Promise<void> {
  const { fetchWithAuth } = await import("./client")
  const response = await fetchWithAuth(`${API_BASE}/scripts/${encodeURIComponent(scriptId)}`, {
    method: "DELETE",
  })
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: `HTTP ${response.status}` }))
    throw new Error(error.detail || `HTTP ${response.status}`)
  }
}

export interface ScriptTestRequest {
  message_text: string
}

export interface ScriptTestResponse {
  reply: string
  matched_scene?: string
}

export async function testScript(
  scriptId: string,
  request: ScriptTestRequest
): Promise<ScriptTestResponse> {
  const { fetchWithAuth } = await import("./client")
  const response = await fetchWithAuth(`${API_BASE}/scripts/${encodeURIComponent(scriptId)}/test`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(request),
  })
  if (!response.ok) {
    let errorMessage = `HTTP ${response.status}`
    try {
      const error = await response.json()
      errorMessage = error.detail || error.message || errorMessage
    } catch {
      // 如果响应不是JSON，使用状态文本
      errorMessage = response.statusText || errorMessage
    }
    throw new Error(errorMessage)
  }
  return response.json()
}

// 格式转换 API
export interface FormatConvertRequest {
  yaml_content: string
  script_id?: string
  script_name?: string
  optimize?: boolean
}

export interface FormatConvertResponse {
  success: boolean
  yaml_content: string
  script_id?: string
  version?: string
  description?: string
  scene_count: number
  message?: string
}

export async function convertFormat(request: FormatConvertRequest): Promise<FormatConvertResponse> {
  const { fetchWithAuth } = await import("./client")
  const response = await fetchWithAuth(`${API_BASE}/scripts/convert`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(request),
  })
  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail || `HTTP ${response.status}`)
  }
  return response.json()
}

// 内容优化 API
export interface ContentOptimizeRequest {
  yaml_content: string
  optimize_type?: "all" | "grammar" | "expression" | "structure"
}

export interface ContentOptimizeResponse {
  success: boolean
  yaml_content: string
  message?: string
}

export async function optimizeContent(request: ContentOptimizeRequest): Promise<ContentOptimizeResponse> {
  const { fetchWithAuth } = await import("./client")
  const response = await fetchWithAuth(`${API_BASE}/scripts/optimize`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(request),
  })
  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail || `HTTP ${response.status}`)
  }
  return response.json()
}

// 角色分配 API
export interface Role {
  role_id: string
  role_name: string
  dialogue_count: number
  dialogue_weight: number
  metadata?: Record<string, any>
}

export interface ExtractRolesResponse {
  script_id: string
  roles: Role[]
  total_roles: number
}

export interface CreateAssignmentRequest {
  script_id: string
  account_ids: string[]
  mode: "auto" | "manual"
  manual_assignments?: Record<string, string>
}

export interface RoleAssignment {
  role_id: string
  account_id: string
  weight: number
  role_name: string
}

export interface AssignmentSummary {
  script_id: string
  total_roles: number
  total_accounts: number
  assignment_mode: string
  account_assignments: Record<string, {
    roles: Array<{
      role_id: string
      role_name: string
      weight: number
    }>
    total_weight: number
  }>
  role_statistics: Record<string, {
    name: string
    dialogue_count: number
    weight: number
  }>
}

export interface AssignmentResponse {
  script_id: string
  assignments: RoleAssignment[]
  summary: AssignmentSummary
  validation: {
    is_valid: boolean
    errors: string[]
  }
}

export async function extractRoles(scriptId: string): Promise<ExtractRolesResponse> {
  try {
    const { fetchWithAuth } = await import("./client")
    const response = await fetchWithAuth(`${API_BASE}/role-assignments/extract-roles`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ script_id: scriptId }),
    })
    
    if (!response.ok) {
      let errorMessage = `HTTP ${response.status}`
      try {
        const errorData = await response.json()
        errorMessage = errorData.message || errorData.detail || errorMessage
      } catch {
        // 如果無法解析 JSON，使用默認錯誤消息
      }
      throw new Error(errorMessage)
    }
    
    return response.json()
  } catch (error) {
    // 網絡錯誤
    if (error instanceof TypeError && error.message.includes("fetch")) {
      console.error("[API] 網絡錯誤，無法連接到後端服務")
      throw new Error("無法連接到後端服務，請檢查服務是否運行")
    }
    throw error
  }
}

export async function createAssignment(request: CreateAssignmentRequest): Promise<AssignmentResponse> {
  const { fetchWithAuth } = await import("./client")
  const response = await fetchWithAuth(`${API_BASE}/role-assignments/create-assignment`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(request),
  })
  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail || `HTTP ${response.status}`)
  }
  return response.json()
}

export async function applyAssignment(
  scriptId: string,
  assignments: Record<string, string>
): Promise<{ message: string; applied_count: number }> {
  const { fetchWithAuth } = await import("./client")
  const params = new URLSearchParams({ script_id: scriptId })
  const response = await fetchWithAuth(`${API_BASE}/role-assignments/apply-assignment?${params}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(assignments),
  })
  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail || `HTTP ${response.status}`)
  }
  return response.json()
}

// ============ 角色分配方案管理 API ============

export interface RoleAssignmentScheme {
  id: string
  name: string
  description?: string | null
  script_id: string
  script_name?: string | null
  assignments: Array<{
    role_id: string
    account_id: string
    weight?: number
    role_name?: string
  }>
  mode: string
  account_ids: string[]
  created_by?: string | null
  created_at: string
  updated_at: string
}

export interface SchemeCreateRequest {
  name: string
  description?: string
  script_id: string
  assignments: Array<{
    role_id: string
    account_id: string
    weight?: number
  }>
  mode?: string
  account_ids: string[]
}

export interface SchemeUpdateRequest {
  name?: string
  description?: string
  assignments?: Array<{
    role_id: string
    account_id: string
    weight?: number
  }>
  account_ids?: string[]
}

export interface SchemeListResponse {
  items: RoleAssignmentScheme[]
  total: number
}

export interface ApplySchemeRequest {
  account_ids?: string[]
}

export interface ApplySchemeResponse {
  message: string
  applied_count: number
  history_id: string
}

export interface AssignmentHistory {
  id: string
  scheme_id: string
  scheme_name?: string | null
  script_id: string
  account_id: string
  role_id: string
  applied_by?: string | null
  applied_at: string
  extra_data: Record<string, any>
}

export interface HistoryListResponse {
  items: AssignmentHistory[]
  total: number
}

export async function getRoleAssignmentSchemes(
  scriptId?: string,
  page: number = 1,
  pageSize: number = 20
): Promise<SchemeListResponse> {
  const { fetchWithAuth } = await import("./client")
  const params = new URLSearchParams()
  if (scriptId) params.append("script_id", scriptId)
  params.append("page", page.toString())
  params.append("page_size", pageSize.toString())
  
  const response = await fetchWithAuth(`${API_BASE}/role-assignment-schemes/?${params}`)
  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail || error.message || `HTTP ${response.status}`)
  }
  return response.json()
}

export async function getRoleAssignmentScheme(schemeId: string): Promise<RoleAssignmentScheme> {
  const { fetchWithAuth } = await import("./client")
  const response = await fetchWithAuth(`${API_BASE}/role-assignment-schemes/${schemeId}`)
  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail || error.message || `HTTP ${response.status}`)
  }
  return response.json()
}

export async function createRoleAssignmentScheme(
  request: SchemeCreateRequest
): Promise<RoleAssignmentScheme> {
  const { fetchWithAuth } = await import("./client")
  const response = await fetchWithAuth(`${API_BASE}/role-assignment-schemes/`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(request),
  })
  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail || error.message || `HTTP ${response.status}`)
  }
  return response.json()
}

export async function updateRoleAssignmentScheme(
  schemeId: string,
  request: SchemeUpdateRequest
): Promise<RoleAssignmentScheme> {
  const { fetchWithAuth } = await import("./client")
  const response = await fetchWithAuth(`${API_BASE}/role-assignment-schemes/${schemeId}`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(request),
  })
  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail || error.message || `HTTP ${response.status}`)
  }
  return response.json()
}

export async function deleteRoleAssignmentScheme(schemeId: string): Promise<void> {
  const { fetchWithAuth } = await import("./client")
  const response = await fetchWithAuth(`${API_BASE}/role-assignment-schemes/${schemeId}`, {
    method: "DELETE",
  })
  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail || error.message || `HTTP ${response.status}`)
  }
}

export async function applyRoleAssignmentScheme(
  schemeId: string,
  request: ApplySchemeRequest = {}
): Promise<ApplySchemeResponse> {
  const { fetchWithAuth } = await import("./client")
  const response = await fetchWithAuth(`${API_BASE}/role-assignment-schemes/${schemeId}/apply`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(request),
  })
  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail || error.message || `HTTP ${response.status}`)
  }
  return response.json()
}

export async function getRoleAssignmentSchemeHistory(
  schemeId: string,
  page: number = 1,
  pageSize: number = 20
): Promise<HistoryListResponse> {
  const { fetchWithAuth } = await import("./client")
  const params = new URLSearchParams()
  params.append("page", page.toString())
  params.append("page_size", pageSize.toString())
  
  const response = await fetchWithAuth(`${API_BASE}/role-assignment-schemes/${schemeId}/history?${params}`)
  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail || error.message || `HTTP ${response.status}`)
  }
  return response.json()
}

// ============ 數據導出 API ============

export type ExportFormat = "csv" | "excel" | "pdf"

/**
 * 導出劇本列表
 */
export async function exportScripts(format: ExportFormat): Promise<Blob> {
  const { fetchWithAuth } = await import("./client")
  const response = await fetchWithAuth(`${API_BASE}/export/scripts?format=${format}`)
  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail || error.message || `HTTP ${response.status}`)
  }
  return response.blob()
}

/**
 * 導出賬號列表
 */
export async function exportAccounts(format: ExportFormat): Promise<Blob> {
  const { fetchWithAuth } = await import("./client")
  const response = await fetchWithAuth(`${API_BASE}/export/accounts?format=${format}`)
  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail || error.message || `HTTP ${response.status}`)
  }
  return response.blob()
}

/**
 * 導出分配方案列表
 */
export async function exportSchemes(format: ExportFormat): Promise<Blob> {
  const { fetchWithAuth } = await import("./client")
  const response = await fetchWithAuth(`${API_BASE}/export/schemes?format=${format}`)
  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail || error.message || `HTTP ${response.status}`)
  }
  return response.blob()
}

/**
 * 導出分配方案詳情
 */
export async function exportSchemeDetails(
  schemeId: string,
  format: ExportFormat
): Promise<Blob> {
  const { fetchWithAuth } = await import("./client")
  const response = await fetchWithAuth(`${API_BASE}/export/schemes/${schemeId}/details?format=${format}`)
  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail || error.message || `HTTP ${response.status}`)
  }
  return response.blob()
}

/**
 * 下載 Blob 為文件
 */
export function downloadBlob(blob: Blob, filename: string) {
  const url = window.URL.createObjectURL(blob)
  const a = document.createElement("a")
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  window.URL.revokeObjectURL(url)
  document.body.removeChild(a)
}

// 劇本版本管理 API
export interface ScriptVersion {
  id: string
  script_id: string
  version: string
  description?: string
  created_by?: string
  change_summary?: string
  created_at: string
}

export interface ScriptVersionContent {
  script_id: string
  version: string
  yaml_content: string
  created_at: string
}

export interface VersionCompareResponse {
  version1: ScriptVersion
  version2: ScriptVersion
  differences: Array<{
    type: string
    description: string
  }>
}

export interface RestoreVersionRequest {
  change_summary?: string
}

export async function listScriptVersions(
  scriptId: string,
  skip: number = 0,
  limit: number = 100
): Promise<ScriptVersion[]> {
  const { fetchWithAuth } = await import("./client")
  const params = new URLSearchParams({
    skip: skip.toString(),
    limit: limit.toString(),
  })
  const response = await fetchWithAuth(`${API_BASE}/scripts/${encodeURIComponent(scriptId)}/versions?${params}`)
  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail || `HTTP ${response.status}`)
  }
  return response.json()
}

export async function getScriptVersion(
  scriptId: string,
  version: string
): Promise<ScriptVersion> {
  const { fetchWithAuth } = await import("./client")
  const response = await fetchWithAuth(`${API_BASE}/scripts/${encodeURIComponent(scriptId)}/versions/${encodeURIComponent(version)}`)
  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail || `HTTP ${response.status}`)
  }
  return response.json()
}

export async function getScriptVersionContent(
  scriptId: string,
  version: string
): Promise<ScriptVersionContent> {
  const { fetchWithAuth } = await import("./client")
  const response = await fetchWithAuth(`${API_BASE}/scripts/${encodeURIComponent(scriptId)}/versions/${encodeURIComponent(version)}/content`)
  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail || `HTTP ${response.status}`)
  }
  return response.json()
}

export async function compareScriptVersions(
  scriptId: string,
  version1: string,
  version2: string
): Promise<VersionCompareResponse> {
  const { fetchWithAuth } = await import("./client")
  const params = new URLSearchParams({
    version1,
    version2,
  })
  const response = await fetchWithAuth(`${API_BASE}/scripts/${encodeURIComponent(scriptId)}/versions/compare?${params}`)
  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail || `HTTP ${response.status}`)
  }
  return response.json()
}

export async function restoreScriptVersion(
  scriptId: string,
  version: string,
  request?: RestoreVersionRequest
): Promise<{ message: string; script_id: string; version: string }> {
  const { fetchWithAuth } = await import("./client")
  const response = await fetchWithAuth(`${API_BASE}/scripts/${encodeURIComponent(scriptId)}/versions/${encodeURIComponent(version)}/restore`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(request || {}),
  })
  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail || `HTTP ${response.status}`)
  }
  return response.json()
}

// 劇本審核與發布 API
export interface SubmitReviewRequest {
  change_summary?: string
}

export interface ReviewDecisionRequest {
  decision: "approve" | "reject"
  review_comment?: string
}

export interface PublishRequest {
  change_summary?: string
}

export interface ScriptReviewResponse {
  script_id: string
  status: string
  status_text: string
  message: string
  reviewed_by?: string
  reviewed_at?: string
  published_at?: string
}

export async function submitScriptReview(
  scriptId: string,
  request: SubmitReviewRequest = {}
): Promise<ScriptReviewResponse> {
  const { fetchWithAuth } = await import("./client")
  const response = await fetchWithAuth(`${API_BASE}/scripts/${encodeURIComponent(scriptId)}/submit-review`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(request),
  })
  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.message || error.detail || `HTTP ${response.status}`)
  }
  return response.json()
}

export async function reviewScript(
  scriptId: string,
  request: ReviewDecisionRequest
): Promise<ScriptReviewResponse> {
  const { fetchWithAuth } = await import("./client")
  const response = await fetchWithAuth(`${API_BASE}/scripts/${encodeURIComponent(scriptId)}/review`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(request),
  })
  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.message || error.detail || `HTTP ${response.status}`)
  }
  return response.json()
}

export async function publishScript(
  scriptId: string,
  request: PublishRequest = {}
): Promise<ScriptReviewResponse> {
  const { fetchWithAuth } = await import("./client")
  const response = await fetchWithAuth(`${API_BASE}/scripts/${encodeURIComponent(scriptId)}/publish`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(request),
  })
  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.message || error.detail || `HTTP ${response.status}`)
  }
  return response.json()
}

export async function disableScriptReview(scriptId: string): Promise<ScriptReviewResponse> {
  const { fetchWithAuth } = await import("./client")
  const response = await fetchWithAuth(`${API_BASE}/scripts/${encodeURIComponent(scriptId)}/disable`, {
    method: "POST",
  })
  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.message || error.detail || `HTTP ${response.status}`)
  }
  return response.json()
}

export async function revertScriptToDraft(scriptId: string): Promise<ScriptReviewResponse> {
  const { fetchWithAuth } = await import("./client")
  const response = await fetchWithAuth(`${API_BASE}/scripts/${encodeURIComponent(scriptId)}/revert-to-draft`, {
    method: "POST",
  })
  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.message || error.detail || `HTTP ${response.status}`)
  }
  return response.json()
}

// ============ 批量操作 API ============

export interface BatchScriptRequest {
  script_ids: string[]
  action: "delete" | "submit_review" | "publish" | "disable" | "revert_to_draft"
}

export interface BatchScriptResponse {
  success_count: number
  failed_count: number
  success_ids: string[]
  failed_items: Array<{
    script_id: string
    error: string
  }>
}

export async function batchOperateScripts(request: BatchScriptRequest): Promise<BatchScriptResponse> {
  const { fetchWithAuth } = await import("./client")
  const response = await fetchWithAuth(`${API_BASE}/scripts/batch`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(request),
  })
  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail || error.message || `HTTP ${response.status}`)
  }
  return response.json()
}

