/**
 * 红包策略 API 客户端
 */

import { fetchWithAuth } from "./client"
import { getApiBaseUrl } from "./config"

const API_BASE = getApiBaseUrl()

export interface RedPacketStrategy {
  id: string
  name: string
  description?: string
  keywords: string[]
  delay_min: number
  delay_max: number
  target_groups: number[]
  probability?: number
  enabled: boolean
  created_by?: string
  created_at: string
  updated_at: string
}

export interface RedPacketStrategyCreate {
  name: string
  description?: string
  keywords: string[]
  delay_min: number
  delay_max: number
  target_groups: number[]
  probability?: number
  enabled?: boolean
}

export interface RedPacketStrategyUpdate {
  name?: string
  description?: string
  keywords?: string[]
  delay_min?: number
  delay_max?: number
  target_groups?: number[]
  probability?: number
  enabled?: boolean
}

export interface RedPacketStrategyListParams {
  skip?: number
  limit?: number
  enabled?: boolean
}

/**
 * 获取策略列表
 */
export async function getStrategies(params?: RedPacketStrategyListParams): Promise<RedPacketStrategy[]> {
  const queryParams = new URLSearchParams()
  if (params?.skip !== undefined) queryParams.append("skip", params.skip.toString())
  if (params?.limit !== undefined) queryParams.append("limit", params.limit.toString())
  if (params?.enabled !== undefined) queryParams.append("enabled", params.enabled.toString())
  
  const url = `${API_BASE}/strategies${queryParams.toString() ? `?${queryParams.toString()}` : ""}`
  const response = await fetchWithAuth(url)
  
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`)
  }
  
  return response.json()
}

/**
 * 获取策略详情
 */
export async function getStrategy(strategyId: string): Promise<RedPacketStrategy> {
  const response = await fetchWithAuth(`${API_BASE}/strategies/${strategyId}`)
  
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`)
  }
  
  return response.json()
}

/**
 * 创建策略
 */
export async function createStrategy(data: RedPacketStrategyCreate): Promise<RedPacketStrategy> {
  const response = await fetchWithAuth(`${API_BASE}/strategies`, {
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
 * 更新策略
 */
export async function updateStrategy(
  strategyId: string,
  data: RedPacketStrategyUpdate
): Promise<RedPacketStrategy> {
  const response = await fetchWithAuth(`${API_BASE}/strategies/${strategyId}`, {
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
 * 删除策略
 */
export async function deleteStrategy(strategyId: string): Promise<void> {
  const response = await fetchWithAuth(`${API_BASE}/strategies/${strategyId}`, {
    method: "DELETE",
  })
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: `HTTP ${response.status}` }))
    throw new Error(error.detail || `HTTP ${response.status}`)
  }
}

/**
 * 立即同步策略到所有 Agent
 * 通过触发所有策略的更新来广播（这会触发 WebSocket CONFIG 消息）
 */
export async function syncStrategies(): Promise<void> {
  // 获取所有启用的策略
  const strategies = await getStrategies({ enabled: true })
  
  if (strategies.length === 0) {
    return // 没有策略需要同步
  }
  
  // 触发每个策略的更新（这会触发 WebSocket 广播）
  // 注意：这是一个临时方案，理想情况下应该有专门的同步接口
  // 但通过更新策略也能达到同步的目的，因为后端会在更新时广播 CONFIG 消息
  const syncPromises = strategies.map(strategy => 
    updateStrategy(strategy.id, { enabled: strategy.enabled })
  )
  
  await Promise.all(syncPromises)
}
