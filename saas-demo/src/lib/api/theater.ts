/**
 * 智能剧场 API 客户端
 */

import { fetchWithAuth } from "./client"
import { getApiBaseUrl } from "./config"

const API_BASE = getApiBaseUrl()

export interface TimelineAction {
  time_offset: number
  role: string
  content: string
  action?: string
  payload?: Record<string, any>
}

export interface TheaterScenario {
  id: string
  name: string
  description?: string
  roles: string[]
  timeline: TimelineAction[]
  enabled: boolean
  created_by?: string
  created_at: string
  updated_at: string
}

export interface TheaterScenarioCreate {
  name: string
  description?: string
  roles: string[]
  timeline: TimelineAction[]
  enabled?: boolean
}

export interface TheaterScenarioUpdate {
  name?: string
  description?: string
  roles?: string[]
  timeline?: TimelineAction[]
  enabled?: boolean
}

export interface TheaterExecutionCreate {
  scenario_id: string
  group_id: string
  agent_mapping: Record<string, string>  // { "UserA": "agent_id_1", "UserB": "agent_id_2" }
}

export interface TheaterExecution {
  id: string
  scenario_id: string
  scenario_name: string
  group_id: string
  agent_mapping: Record<string, string>
  status: "pending" | "running" | "completed" | "failed" | "cancelled"
  started_at?: string
  completed_at?: string
  duration_seconds?: number
  executed_actions: any[]
  error_message?: string
  created_by?: string
  created_at: string
  updated_at: string
}

export interface TheaterScenarioListParams {
  skip?: number
  limit?: number
  enabled?: boolean
}

export interface TheaterExecutionListParams {
  skip?: number
  limit?: number
  status?: string
}

/**
 * 获取场景列表
 */
export async function getScenarios(params?: TheaterScenarioListParams): Promise<TheaterScenario[]> {
  const queryParams = new URLSearchParams()
  if (params?.skip !== undefined) queryParams.append("skip", params.skip.toString())
  if (params?.limit !== undefined) queryParams.append("limit", params.limit.toString())
  if (params?.enabled !== undefined) queryParams.append("enabled", params.enabled.toString())
  
  const url = `${API_BASE}/theater/scenarios${queryParams.toString() ? `?${queryParams.toString()}` : ""}`
  const response = await fetchWithAuth(url)
  
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`)
  }
  
  return response.json()
}

/**
 * 获取场景详情
 */
export async function getScenario(scenarioId: string): Promise<TheaterScenario> {
  const response = await fetchWithAuth(`${API_BASE}/theater/scenarios/${scenarioId}`)
  
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`)
  }
  
  return response.json()
}

/**
 * 创建场景
 */
export async function createScenario(data: TheaterScenarioCreate): Promise<TheaterScenario> {
  const response = await fetchWithAuth(`${API_BASE}/theater/scenarios`, {
    method: "POST",
    body: JSON.stringify(data),
  })
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: `HTTP ${response.status}` }))
    throw new Error(error.detail || `HTTP ${response.status}`)
  }
  
  return response.json()
}

/**
 * 更新场景
 */
export async function updateScenario(
  scenarioId: string,
  data: TheaterScenarioUpdate
): Promise<TheaterScenario> {
  const response = await fetchWithAuth(`${API_BASE}/theater/scenarios/${scenarioId}`, {
    method: "PUT",
    body: JSON.stringify(data),
  })
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: `HTTP ${response.status}` }))
    throw new Error(error.detail || `HTTP ${response.status}`)
  }
  
  return response.json()
}

/**
 * 删除场景
 */
export async function deleteScenario(scenarioId: string): Promise<void> {
  const response = await fetchWithAuth(`${API_BASE}/theater/scenarios/${scenarioId}`, {
    method: "DELETE",
  })
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: `HTTP ${response.status}` }))
    throw new Error(error.detail || `HTTP ${response.status}`)
  }
}

/**
 * 执行场景
 */
export async function executeScenario(data: TheaterExecutionCreate): Promise<TheaterExecution> {
  const response = await fetchWithAuth(`${API_BASE}/theater/execute`, {
    method: "POST",
    body: JSON.stringify(data),
  })
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: `HTTP ${response.status}` }))
    throw new Error(error.detail || `HTTP ${response.status}`)
  }
  
  return response.json()
}

/**
 * 获取执行记录列表
 */
export async function getExecutions(params?: TheaterExecutionListParams): Promise<TheaterExecution[]> {
  const queryParams = new URLSearchParams()
  if (params?.skip !== undefined) queryParams.append("skip", params.skip.toString())
  if (params?.limit !== undefined) queryParams.append("limit", params.limit.toString())
  if (params?.status) queryParams.append("status", params.status)
  
  const url = `${API_BASE}/theater/executions${queryParams.toString() ? `?${queryParams.toString()}` : ""}`
  const response = await fetchWithAuth(url)
  
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`)
  }
  
  return response.json()
}

/**
 * 取消执行
 */
export async function cancelExecution(executionId: string): Promise<void> {
  const response = await fetchWithAuth(`${API_BASE}/theater/executions/${executionId}/cancel`, {
    method: "POST",
  })
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: `HTTP ${response.status}` }))
    throw new Error(error.detail || `HTTP ${response.status}`)
  }
}
