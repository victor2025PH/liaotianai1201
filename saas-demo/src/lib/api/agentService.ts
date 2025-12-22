/**
 * Agent 服务 - Phase 8: 前端集成与任务下发
 * 提供 Agent 管理和任务下发的 API 接口
 */

import { fetchWithAuth } from "./client"
import { getApiBaseUrl } from "./config"

const API_BASE = getApiBaseUrl()

/**
 * Agent 接口定义（与后端一致）
 */
export interface Agent {
  id: string
  agent_id: string
  phone_number?: string
  status: "online" | "offline" | "busy" | "error"
  current_task_id?: string
  device_info?: {
    device_model?: string
    system_version?: string
    app_version?: string
    [key: string]: any
  }
  agent_metadata?: {
    version?: string
    platform?: string
    hostname?: string
    [key: string]: any
  }
  last_active_time?: string
  created_at: string
  updated_at: string
}

/**
 * Agent 任务接口定义
 */
export interface AgentTask {
  id: string
  task_id: string
  agent_id?: string
  task_type: string
  scenario_data?: any
  variables?: Record<string, any>
  priority: number
  status: "pending" | "in_progress" | "completed" | "failed" | "cancelled"
  result_data?: any
  error_message?: string
  assigned_at?: string
  started_at?: string
  executed_at?: string
  created_at: string
  updated_at: string
}

/**
 * 创建任务请求
 */
export interface CreateTaskRequest {
  agent_id?: string  // 可选，如果不指定则由系统自动分配
  task_type: string  // "scenario_execute"
  scenario_data: {
    name: string
    timeline: any[]
    roles?: string[]
    [key: string]: any
  }
  variables?: Record<string, any>
  priority?: number  // 1-10，默认 1
}

/**
 * 创建任务响应
 */
export interface CreateTaskResponse {
  success: boolean
  task_id: string
  message: string
}

/**
 * 获取 Agent 列表
 */
export async function getAgents(): Promise<Agent[]> {
  const response = await fetchWithAuth(`${API_BASE}/agents`)
  
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`)
  }
  
  const agents: Agent[] = await response.json()
  // 确保每个 Agent 都有 id 属性（映射到 agent_id）
  return agents.map(agent => ({
    ...agent,
    id: agent.agent_id || agent.id
  }))
}

/**
 * 获取指定 Agent 信息
 */
export async function getAgent(agentId: string): Promise<Agent> {
  const response = await fetchWithAuth(`${API_BASE}/agents/${agentId}`)
  
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`)
  }
  
  const agent: Agent = await response.json()
  return {
    ...agent,
    id: agent.agent_id || agent.id
  }
}

/**
 * 创建任务并下发给 Agent
 */
export async function createTask(request: CreateTaskRequest): Promise<CreateTaskResponse> {
  const response = await fetchWithAuth(`${API_BASE}/tasks`, {
    method: "POST",
    body: JSON.stringify(request),
  })
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: `HTTP ${response.status}` }))
    throw new Error(error.detail || `HTTP ${response.status}`)
  }
  
  return response.json()
}

/**
 * 判断 Agent 是否在线
 * 根据 last_active_time 判断（1分钟内有心跳即为在线）
 */
export function isAgentOnline(agent: Agent): boolean {
  if (agent.status === "online" || agent.status === "busy") {
    if (agent.last_active_time) {
      const lastActive = new Date(agent.last_active_time)
      const now = new Date()
      const diffMinutes = (now.getTime() - lastActive.getTime()) / (1000 * 60)
      return diffMinutes <= 1  // 1分钟内活跃视为在线
    }
    return true  // 如果没有 last_active_time，但状态是 online/busy，也视为在线
  }
  return false
}

/**
 * 获取设备型号（从 device_info 中解析）
 */
export function getDeviceModel(agent: Agent): string {
  if (agent.device_info?.device_model) {
    return agent.device_info.device_model
  }
  return "未知设备"
}
