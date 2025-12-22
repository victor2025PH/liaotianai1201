/**
 * Agent API 客户端
 */

import { fetchWithAuth } from "./client"
import { getApiBaseUrl } from "./config"

const API_BASE = getApiBaseUrl()

export interface Agent {
  agent_id: string
  status: "online" | "offline" | "busy" | "error"
  connected_at: string
  last_heartbeat: string
  latency?: number
  metadata?: {
    version?: string
    platform?: string
    hostname?: string
    [key: string]: any
  }
}

export interface AgentListParams {
  page?: number
  page_size?: number
  status?: string
  search?: string
}

/**
 * 获取所有 Agent 列表
 */
export async function getAgents(params?: AgentListParams): Promise<Agent[]> {
  const queryParams = new URLSearchParams()
  if (params?.page) queryParams.append("page", params.page.toString())
  if (params?.page_size) queryParams.append("page_size", params.page_size.toString())
  if (params?.status) queryParams.append("status", params.status)
  if (params?.search) queryParams.append("search", params.search)
  
  const url = `${API_BASE}/agents${queryParams.toString() ? `?${queryParams.toString()}` : ""}`
  const response = await fetchWithAuth(url)
  
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`)
  }
  
  return response.json()
}

/**
 * 获取指定 Agent 信息
 */
export async function getAgent(agentId: string): Promise<Agent> {
  const response = await fetchWithAuth(`${API_BASE}/agents/${agentId}`)
  
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`)
  }
  
  return response.json()
}

/**
 * 向 Agent 发送指令
 */
export async function sendCommandToAgent(
  agentId: string,
  command: {
    action: string
    payload?: Record<string, any>
  }
): Promise<void> {
  const response = await fetchWithAuth(`${API_BASE}/agents/${agentId}/command`, {
    method: "POST",
    body: JSON.stringify(command),
  })
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: `HTTP ${response.status}` }))
    throw new Error(error.detail || `HTTP ${response.status}`)
  }
}

/**
 * 向所有 Agent 广播指令
 */
export async function broadcastCommand(command: {
  action: string
  payload?: Record<string, any>
  exclude?: string[]
}): Promise<void> {
  const response = await fetchWithAuth(`${API_BASE}/agents/broadcast`, {
    method: "POST",
    body: JSON.stringify(command),
  })
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: `HTTP ${response.status}` }))
    throw new Error(error.detail || `HTTP ${response.status}`)
  }
}

/**
 * 获取 Agent 统计信息
 */
export async function getAgentStatistics(): Promise<{
  total_connections: number
  online_connections: number
  offline_connections: number
  agents: Agent[]
}> {
  const response = await fetchWithAuth(`${API_BASE}/agents/statistics`)
  
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`)
  }
  
  return response.json()
}
